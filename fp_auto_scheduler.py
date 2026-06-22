#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#---------------------------------------------------------#
#               SUNTAK SOFTWARE GROUP                     #
#---------------------------------------------------------#
Author          : rphe
Email           : 502614708@qq.com
CreateTime      : 2026/04/14
ProjectName     : FlyingProbeMS
File            : fp_auto_scheduler.py
Description     : 【无人值守】飞针测试 - 任务调度总入口
功能：
    1. 从Oracle ERP自动拉取待处理任务
    2. 安全关闭残留进程，避免端口/文件占用
    3. 启动ezFixtureII执行自动化脚本
    4. 等待子进程完成后再执行下一个任务
    5. 超时保护、异常捕获、批量任务闭环
    6. 全程日志记录，支持7x24小时无人值守
#---------------------------------------------------------#
"""
import re
import subprocess
import sys
import os
import datetime
import logging
import time
import psutil

# 项目内部依赖
import package.Oracle_DB as Oracle_DB
import fp_config

# ======================== 全局核心配置（无人值守专用） ========================
LOG_TO_FILE = True  # 日志输出到文件
DEBUG_MODE = False  # 调试模式（仅跑1个任务）
TASK_PROCESS_TIMEOUT = 60  # 单个任务最大超时分钟
EZFIXTURE_EXE_PATH = r"D:\eastek-server\ezFixtureII\1.1\ezFixtureII.exe"
# FP_CORE_SCRIPT_PATH = r"D:\eastek-server\ezFixtureII\sys\scripts\FlyingProbeMS\fp_core_processor.py"
FP_CORE_SCRIPT_PATH = os.path.join(os.getcwd(), "fp_core_processor.py")
TARGET_PROCESS_NAME = "ezFixtureII.exe"
FACTORY_CODE_LIST = ["JM2"]  # 支持多工厂，逗号分隔
ORACLE_PATH = os.path.join(os.getcwd(), 'instantclient_19_21')


# ==============================================================================

def init_system_logger():
    """初始化系统日志（统一格式、支持文件+控制台、自动创建日志目录）"""
    logger = logging.getLogger("FP_TASK_SCHEDULER")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    log_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    # 文件输出
    if LOG_TO_FILE:
        log_dir = "./logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file_name = f"fp_scheduler_{datetime.datetime.now().strftime('%Y%m%d')}.log"
        log_file_path = os.path.join(log_dir, log_file_name)
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setFormatter(log_formatter)
        logger.addHandler(file_handler)

    return logger


# 全局日志实例
logger = init_system_logger()


def safe_kill_process(process_name):
    """安全杀死指定名称的进程，无人值守必备，防止进程卡死"""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info["name"] and proc.info["name"].lower() == process_name.lower():
                os.system(f"taskkill /f /pid {proc.info['pid']}")
                logger.info(f"[进程清理] 已强制关闭: {process_name} (PID: {proc.info['pid']})")
        except Exception:
            continue


def delayed_close_software():
    """后台延时3秒关闭ezFixtureII，不阻塞主程序，无人值守安全退出"""
    delay_seconds = 3
    kill_script = f'''
import psutil, time, os
time.sleep({delay_seconds})
for proc in psutil.process_iter(["pid", "name"]):
    try:
        if proc.info["name"] and proc.info["name"].lower() == "{TARGET_PROCESS_NAME}".lower():
            os.system(f"taskkill /f /pid {{proc.info['pid']}}")
    except:
        pass
'''
    subprocess.Popen(
        [sys.executable, "-c", kill_script],
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    logger.info(f"[退出安排] {delay_seconds}秒后后台自动关闭 {TARGET_PROCESS_NAME}")


class FlyingProbeTaskScheduler:
    """飞针测试 - 任务调度核心类（单工厂实例）"""

    def __init__(self, factory_code):
        self.factory_code = factory_code
        self.config_tool = fp_config.toolsMain()
        self.factory_info = self.config_tool.factory(factory_code)
        self.db_erp_connection = None
        self._init_oracle_environment()
        logger.info(f"[工厂初始化] {factory_code} 初始化完成")

    def _init_oracle_environment(self):
        """初始化Oracle客户端环境变量，避免依赖冲突"""
        try:
            system_path = os.getenv('PATH', '')
            cleaned_path = [p.strip() for p in system_path.split(';') if
                            p.strip() and not re.search(r'instantclient|python', p, re.I)]
            cleaned_path.append(ORACLE_PATH)
            os.putenv('PATH', ';'.join(cleaned_path))
        except Exception as e:
            logger.warning(f"[Oracle环境] 配置警告: {str(e)}")

    def _init_erp_database(self):
        """单例ERP数据库连接，避免重复创建"""
        if not self.db_erp_connection:
            self.db_erp_connection = Oracle_DB.ORACLE_INIT()
            self.db_erp_connection.DB_CONNECT(
                host="cderpdb-scan",
                servername="prod",
                port='1521',
                username="INP",
                passwd="INP"
            )
            logger.info("[ERP数据库] 连接成功")

    def close_database(self):
        """安全关闭数据库连接，释放资源"""
        if self.db_erp_connection:
            self.db_erp_connection.DB_CLOSE()
            logger.info("[ERP数据库] 连接已关闭")

    def get_waiting_task_list(self):
        """从数据库获取待处理任务（过滤已完成/异常/重复任务）"""
        try:
            self._init_erp_database()
            org_id = self.factory_info['orgId']
            sql = f"""
                SELECT 
                    us.data_id, US.item_no, us.rev, us.creation_date
                FROM 
                    INP.INP_FLYPIN_PROBE_TOOL_ALERT US
                WHERE 
                    US.OPERATON_CLASSCODE = 'ET_DATA'
                    AND US.ORG_ID = {org_id}
                    AND LENGTH(US.ITEM_NO) >= 15
                    --AND sysdate - us.creation_date < 2
                    AND (us.REMARK IS NULL OR 
                         (us.REMARK NOT LIKE '%网络异常%' 
                          AND us.REMARK NOT LIKE '%需手动%'
                          AND us.REMARK NOT LIKE '%输出成功%'
                          AND us.REMARK NOT LIKE '%已输出%'
                          --AND us.REMARK NOT LIKE '%软硬结合%'
                          --AND us.REMARK NOT LIKE '%重复任务%'
                         ))
                    AND us.attribute4 IS null --异常标记,0表示已同时两次触发
                    --AND us.item_no = '100139599T0499A'
                    --AND us.item_no not like '%____________23_%'
                ORDER BY 
                    us.creation_date DESC
            """
            return self.db_erp_connection.SELECT_DIC(sql)
        except Exception as e:
            logger.error(f"[任务拉取] 失败: {str(e)}")
            return []

    def _get_tool_status(self,job,rev):
        """获取工具状态"""
        try:
            self._init_erp_database()
            org_id = self.factory_info['orgId']
            sql = f"""
                SELECT
                    t.item,
                    t.ITEM_REV ,
                    t.ORGANIZATION_ID ,
                    t.CHECK_TYPE ,
                    t.CHECK_STATUS ,
                    t.CHECK_STRU ,
                    t.CHECK_MEMO ,
                    t.CREATION_DATE ,
                    t.LAST_UPDATE_DATE
                FROM
                    apps.CUX_MI_CHECKMT_V t
                WHERE
                    t.Item = '{job}'
                    AND t.ITEM_REV = '{rev}'
                    AND t.ORGANIZATION_ID = {org_id}
                    AND UPPER(t.CHECK_STATUS) = 'OK'
            """
            return self.db_erp_connection.SELECT_DIC(sql)
        except Exception as e:
            logger.error(f"[订单接入时间查询] 失败: {str(e)}")
            return []

    def get_job_order_time(self,job,rev,cut_time):
        """获取订单接入时间"""
        try:
            self._init_erp_database()
            org_id = self.factory_info['orgId']
            sql = f"""
                SELECT
                    cmd.CREATION_DATE
                FROM
                    apps.cux_mfg_mi_data_plan cmd
                WHERE
                    plan_id IN (
                    SELECT
                        plan_id
                    FROM
                        apps.cux_mi_data_plan_v
                    WHERE
                        organization_id = {org_id}
                        AND segment1 = '{job}'
                        AND revision = '{rev}')
                    --AND cmd.CREATION_DATE > TO_DATE('{cut_time}', 'YYYY-MM-DD')
            """
            return self.db_erp_connection.SELECT_DIC(sql)
        except Exception as e:
            logger.error(f"[订单接入时间查询] 失败: {str(e)}")
            return []

    def upload_result_to_database(self, id,job,msg,mode=None):
        """
        上传处理结果到数据库
        """
        try:
            self._init_erp_database()
            logger.info(f"【{job}】开始上报处理结果至数据库")

            STATUS = '已完成' if mode is None else '未输出'
            sql = f"""
            UPDATE 
                INP.INP_FLYPIN_PROBE_TOOL_ALERT 
            SET 
                WRITE_FLAG = 'Y', 
                remark = '{msg}', 
                write_date = SYSDATE, 
                write_by = 'sys_tem',
                STATUS = '{STATUS}'
            WHERE 
                data_id = {id}
            """
            logger.info(f"更新sql:{sql}")
            self.db_erp_connection.SQL_EXECUTE(sql)
            logger.info(f"【{job}】数据库上报成功")

        except Exception as e:
            logger.error(f"【{job}】数据库上报失败：{str(e)}")

    def execute_single_task(self, data_id, job_name):
        """
        执行单个PCB料号任务
        :return: True=成功 False=失败
        """
        logger.info(f"\n===== [开始任务] {job_name} | DATA_ID: {data_id} =====")

        # 清理旧标记
        for f in [f"{os.getcwd()}/task_success.flag", f"{os.getcwd()}/task_fail.flag"]:
            if os.path.exists(f):
                os.remove(f)

        # 清理残留进程，防止文件占用/端口冲突
        safe_kill_process(TARGET_PROCESS_NAME)
        time.sleep(2)

        # 如果发现上次有异常,则等待60s再执行
        error_file = f"{os.getcwd()}/task_fail_error.flag"
        if os.path.exists(error_file):
            wait = 180
            s = wait
            while True:
                time.sleep(1)
                s = s - 1
                logger.info(f'等待{wait}s开启新进程,倒计时开始:{s}...')
                if s == 0:
                    break
            os.remove(error_file)
        # print(self.factory_code,data_id,job_name)
        # sys.exit(0)
        try:
            start_time = datetime.datetime.now()
            # 启动ezFixtureII并执行核心脚本
            env = os.environ.copy()
            process = subprocess.Popen(
                [
                    EZFIXTURE_EXE_PATH,
                    "-u", "g",
                    "-p", "g",
                    "-s", FP_CORE_SCRIPT_PATH,
                    f"--script-param={self.factory_code},{data_id},{job_name},automatic,sys_tem,both"
                ],
                env=env,
                cwd=os.path.dirname(EZFIXTURE_EXE_PATH),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )

            # 等待进程执行完成（带超时，无人值守核心）
            return_code = process.wait(timeout=TASK_PROCESS_TIMEOUT * 60)

            success_flag = f"{os.getcwd()}/automatic_success.flag"
            fail_flag = f"{os.getcwd()}/automatic_fail.flag"
            cost_min = round((datetime.datetime.now() - start_time).total_seconds() / 60, 2)
            if os.path.exists(success_flag):
                logger.info(f"任务完成 | 总耗时：{cost_min} 分钟")
                success = True
            else:
                logger.info(f"任务失败 | 总耗时：{cost_min} 分钟")
                success = False

            if os.path.isfile(success_flag):
                os.remove(success_flag)

            if os.path.isfile(fail_flag):
                os.remove(fail_flag)

            return success

        except subprocess.TimeoutExpired:
            process.kill()
            logger.error(f"[任务超时] {job_name} 超过 {TASK_PROCESS_TIMEOUT} 分钟，已强制终止")
            return False
        except Exception as e:
            logger.error(f"[任务启动] 异常: {str(e)}")
            return False

    def run_batch_tasks(self):
        """批量执行所有待处理任务（无人值守闭环）"""
        task_list = self.get_waiting_task_list()
        total_count = len(task_list)
        success_count = 0
        fail_count = 0

        logger.info("\n" + "=" * 80)
        logger.info(f"[批量任务启动] 工厂: {self.factory_code} | 待处理总数: {total_count}")
        logger.info("=" * 80)

        for index, row in enumerate(task_list, 1):
            if DEBUG_MODE and index > 1:
                break

            # 解析料号信息
            job = row['ITEM_NO'].split('-')[0] if '-' in row['ITEM_NO'] else row['ITEM_NO']
            job_full_name = f"{job}{row['REV']}"
            data_id = row['DATA_ID']

            # cut_time = '2026-05-01'
            # info = self.get_job_order_time(job,row['REV'],cut_time)
            # order_time = None
            # if len(info) > 0:
            #     order_time = info[0]['CREATION_DATE']

            # if order_time is not None:
            #     cut_time = datetime.datetime.strptime(cut_time, "%Y-%m-%d")
            #     if order_time < cut_time:
            #         logger.info(f"[订单时间] {job_full_name}: {order_time},跳过不处理")
            #         self.upload_result_to_database(data_id, job, f'订单时间:{order_time},跳过不处理')
            #         fail_count += 1
            #         continue
            #     else:
            #         logger.info(f"[订单时间] {job_full_name}: {order_time}")
            # else:
            #     logger.info(f"[订单时间] {job_full_name}: 订单时间为空,跳过不处理...")
            #     fail_count += 1
            #     continue

            tool_status = self._get_tool_status(job,row['REV'])
            if len(tool_status) > 0:
                if tool_status[0]['CHECK_STATUS'] == 'OK':
                    logger.info(f"{job_full_name}: 当前料号已输出飞针资料,跳过不处理")
                    self.upload_result_to_database(data_id, job, f'ERP记录已输出')
                    fail_count += 1
                    continue

            # if job[12:14] == '23':
            #     logger.info(f"{job_full_name}: 此料号为软硬结合板,请手动输出")
            #     self.upload_result_to_database(data_id, job, f'此为软硬结合板,请手动输出',23)
            #     fail_count += 1
            #     continue

            try:
                if self.execute_single_task(data_id, job_full_name):
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                logger.error(f"[任务异常] {job_full_name}: {str(e)}")
                fail_count += 1

        self.close_database()
        # 任务统计输出
        logger.info("\n" + "=" * 80)
        logger.info(
            f"[批量任务结束] 工厂: {self.factory_code} | 总计: {total_count} | 成功: {success_count} | 失败: {fail_count}")
        logger.info("=" * 80)

# ======================== 主程序入口 ========================
if __name__ == '__main__':

    logger.info("=" * 80)
    logger.info("           飞针测试全自动无人值守系统 - 启动成功")
    logger.info("=" * 80)

    if len(sys.argv) == 1:
        logger.info("请传入工厂代码...")
        sys.exit(0)

    param = sys.argv[1:]

    # 循环处理所有工厂
    # for factory in FACTORY_CODE_LIST:
    for factory in param:
        try:
            scheduler = FlyingProbeTaskScheduler(factory)
            scheduler.run_batch_tasks()
        except Exception as e:
            logger.error(f"[工厂处理异常] {factory}: {str(e)}", exc_info=True)

    # 全部任务完成，延时退出
    delayed_close_software()
    logger.info("\n【无人值守】所有工厂任务处理完成！")
    sys.exit(0)