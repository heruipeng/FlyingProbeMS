#!/bin/python
# -*- coding: utf-8 -*-
"""
#---------------------------------------------------------#
#               SUNTAK SOFTWARE GROUP                     #
#---------------------------------------------------------#
Author          : rphe
Email           : 502614708@qq.com
CreateTime      : 2026-04-14
ProjectName     : FlyingProbeMS
File            : fp_core_processor.py
Description     : 【无人值守】飞针测试 - 核心业务处理器
功能流程：
    *** 执行平台ezFixtureII ***
    1. 读取ezCAM运行UID，建立网关通信连接
    2. 加载任务参数与工程路径配置
    3. 导入PCB工程TGZ文件
    4. 清理无效图层，检查阻焊层完整性
    5. 板型合法性校验（半孔/阴阳板/灯板/软硬结合板）
    6. 自动判断二线/四线测试模式
    7. 工作稿 VS 原稿 网络比对（短路/开路检测）
    8. 自动导入原始Gerber数据并对齐坐标
    9. 生成飞针测试点并输出356测试文件
    10. 执行结果自动回写Oracle数据库
    11. 全程无人值守，异常自动捕获、自动上报、自动退出
#---------------------------------------------------------#
Change Log Details:
    一.产线反馈以下问题需修复G rphe 2026.6.4
        1.检查按钮不要禁止 --OK
        2.Npth线路删除 --OK
        3.钻孔不还原原稿 --还是按以前还原，仅还原镭射，埋孔(\d+d) --OK
        4.光学点删除 --暂无优化方法
        5.阻焊开窗处理掉开窗内小开窗 --调用内置去重PAD命令 --OK
            chklist_single,action=ezcam_dfm_nfp_removal,show=yes
            chklist_cupd,chklist=ezcam_dfm_nfp_removal,nact=1,params=((pp_layer=.affected)(pp_delete=Duplicate\;Drilled Over\;Covered)(pp_work=Features)(pp_drill=)(pp_non_drilled=No)(pp_in_selected=All)(pp_remove_mark=Remove)),mode=regular
            chklist_run,chklist=ezcam_dfm_nfp_removal,nact=1,area=Global
            chklist_close,chklist=ezcam_dfm_nfp_removal,mode=hide
        6.跑完后需要提示完成状态。 --OK
"""
import re
import subprocess
import sys
import os
import datetime
import logging
import traceback
import time
import shutil
import psutil
# 弹窗依赖
import ctypes
from ctypes import wintypes

# 项目内部依赖
import package.Oracle_DB as Oracle_DB
import fp_config
# from gateway import Gateway
from package.genCOM_36 import GEN_COM
# import ezcam.main as GEN_COM
from PyQt5.QtWidgets import QDialog, QApplication, QInputDialog
from package.MessageBox import MessageBox

# from package.wechat_robot import WechatRobotSender
# webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b3cd73ca-8988-49cb-8630-37c74aec1680"

# ======================== 系统全局配置 ========================
LOG_TO_FILE = True
CAM_BASE_PATH = r'D:\eastek-server\ezFixtureII'
UID_FILE_PATH = r'sys\scripts\ezcam_uid'
EZFIXTURE_PROCESS = "ezFixtureII.exe"

ORACLE_CLIENT_PATH = os.path.join(os.getcwd(), 'instantclient_19_21')
# ==============================================================

# 全局日志对象
logger = None
app = QApplication(sys.argv)

def show_error_message(title, msg):
    """半自动模式：弹出错误提示框"""
    m = MessageBox()
    d = m.warning(None, title, msg, btype=MessageBox.OK, btype1=MessageBox.CANCEL)
    return d

def init_task_logger(job_name):
    """
    初始化单任务日志系统
    按料号分文件输出，便于问题追溯，支持控制台+文件双输出
    """
    global logger
    logger = logging.getLogger("FP_CORE_PROCESSOR")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    log_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    if LOG_TO_FILE:
        log_dir = "./logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, f"fp_core_{datetime.datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setFormatter(log_formatter)
        logger.addHandler(file_handler)

    return logger


def delayed_exit_clean():
    """
    无人值守安全退出机制
    后台延时3秒强制关闭ezFixtureII进程，避免文件占用与进程残留
    """
    delay_seconds = 3
    kill_script = f'''
import psutil, time, os
time.sleep({delay_seconds})
for proc in psutil.process_iter(["pid","name"]):
    try:
        if proc.info["name"] and proc.info["name"].lower() == "{EZFIXTURE_PROCESS}".lower():
            os.system(f"taskkill /f /pid {{proc.info['pid']}}")
    except:
        pass
'''
    # subprocess.Popen(
    #     [sys.executable, "-c", kill_script],
    #     creationflags=subprocess.CREATE_NO_WINDOW
    # )

    subprocess.run(
        ["taskkill", "/F", "/IM", EZFIXTURE_PROCESS],
        capture_output=True,
        creationflags=0x08000000  # 隐藏cmd黑窗口
    )


class FlyingProbeCoreProcessor:
    """飞针测试核心业务处理器（单任务实例）"""

    def __init__(self, factory_code, data_id, job_name, mode, user_id, output_mode):
        self._init_oracle_env()
        self.factory_code = factory_code
        self.data_id = data_id
        self.job_name = job_name
        self.mode = mode.strip().lower()
        self.user_id = user_id
        self.output_mode = output_mode  # 2w / 4w / both
        self.uid = self._read_ezcam_uid()
        self.gen = None
        self.config_tool = fp_config.toolsMain()
        self.factory_info = self.config_tool.factory(factory_code)
        self.system_config = self.config_tool.config(factory_code)

        # 业务参数
        self.raw_job = None
        self.internal_job = None
        self.run_step = "edit"
        self.output_path = None
        self.output_2w_path = None
        self.output_2w_path_network = None
        self.output_4w_path = None
        self.output_4w_path_network = None
        self.output_tgz_path = None
        self.output_tgz_path_network = None
        self.tgz_file = None
        self.org_gerber_path = None
        self.net_compare_step = None
        self.cut_job = None

        # 数据库连接
        self.db_erp = None
        self.db_inp = None

        # UID合法性检查
        if not self.uid:
            err = "[ezCAM] UID获取失败，请检查ezFixtureII是否正常运行"
            logger.error(err)
            if self.is_auto_mode():
                raise Exception("UID获取失败，请检查ezFixtureII是否正常运行")
            else:
                show_error_message("错误", err)
                raise Exception(err)

        self.gen = GEN_COM()
        logger.info("[核心处理器] 初始化完成")

    def is_auto_mode(self):
        """判断是否为全自动模式"""
        return self.mode == "automatic"

    def _read_ezcam_uid(self):
        """读取ezCAM运行时UID，建立网关通信"""
        uid_file = os.path.join(CAM_BASE_PATH, UID_FILE_PATH)
        if os.path.isfile(uid_file):
            try:
                with open(uid_file, 'r', encoding='utf-8') as f:
                    return f.readline().strip()
            except:
                return None
        return None

    def _init_oracle_env(self):
        """初始化Oracle客户端环境变量，避免依赖冲突"""
        try:
            system_path = os.getenv('PATH', '')
            path_list = [p.strip() for p in system_path.split(';') if p.strip() and not re.search(r'instantclient|python', p, re.I)]
            path_list.append(ORACLE_CLIENT_PATH)
            os.putenv('PATH', ';'.join(path_list))
        except Exception as e:
            logger.warning(f"[Oracle环境] 配置警告: {str(e)}")

    def close_all_connections(self):
        """安全关闭所有数据库连接，释放资源"""
        if self.db_erp:
            self.db_erp.DB_CLOSE()
        if self.db_inp:
            self.db_inp.DB_CLOSE()

    def init_erp_conn(self):
        """ERP数据库单例连接"""
        if not self.db_erp:
            self.db_erp = Oracle_DB.ORACLE_INIT()
            self.db_erp.DB_CONNECT(host="cderpdb-scan", servername="prod", port='1521', username="INP", passwd="INP")

    def init_inp_conn(self):
        """INP数据库单例连接"""
        if not self.db_inp:
            self.db_inp = Oracle_DB.ORACLE_INIT()
            self.db_inp.DB_CONNECT(host="inplan001", servername="inmind.fls", port='1521', username="STARRY", passwd="STARRY")

    def load_task_parameters(self):
        """
        加载任务核心参数
        包含料号名称、内部工程名、输出路径、TGZ路径、原稿路径、比对步骤
        """
        self.raw_job = self.job_name.lower()
        self.cut_job = self.raw_job[3:6]
        self.internal_job = self._generate_internal_job_name()
        self.output_path = self.system_config['output_ipc_path_network']
        self.output_2w_path = os.path.join(self.system_config['output_ipc_path'], '2w', self.cut_job, self.raw_job)
        self.output_2w_path_network = os.path.join(self.system_config['output_ipc_path_network'], '2w', self.cut_job, self.raw_job)
        self.output_4w_path = os.path.join(self.system_config['output_ipc_path'], '4w', self.cut_job, self.raw_job)
        self.output_4w_path_network = os.path.join(self.system_config['output_ipc_path_network'], '4w', self.cut_job, self.raw_job)
        self.output_tgz_path = os.path.join(self.system_config['output_tgz_path'],'待检查TGZ')
        self.output_tgz_path_network = os.path.join(self.system_config['output_tgz_path_network'],'待检查TGZ')
        # self.tgz_file = self._build_tgz_file_path()
        self.org_gerber_path = self._build_original_gerber_path()
        self.net_compare_step = self.system_config['net_step']
        logger.info(f"[参数加载] 料号: {self.raw_job} | 内部工程名: {self.internal_job}")

    def _generate_internal_job_name(self):
        """生成工厂规则的ezCAM内部工程名"""
        if self.factory_code in ['JM2', 'ZH2']:
            p1 = self.raw_job[3:12]
            p2 = self.raw_job[14]
            p3 = str(int(self.raw_job[15:17]))
            return p1 + p2 + p3
        return self.raw_job

    def _build_tgz_file_path(self,job):
        """构建TGZ工程文件路径"""
        folder = self.raw_job[3:6]
        if self.mode in ['check','input']:
            return os.path.join(self.output_tgz_path_network, f"{job}.tgz".lower())
        else:
            return os.path.join(self.system_config['tgz'], folder, f"{job}.tgz".lower())

    def _build_original_gerber_path(self):
        """构建原始Gerber文件路径"""
        if self.factory_code in ['JM1', 'ZH1', 'DL']:
            cus_code = self._get_customer_code()
            code = cus_code[0]['CUS_CODE'] if cus_code else ''
            return os.path.join(self.system_config['org'], code, self.raw_job, 'yg')
        elif self.factory_code in ['JM2', 'ZH2']:
            folder = self.raw_job[3:6]
            return os.path.join(self.system_config['org'], folder, self.raw_job, 'yg')
        return ""

    def _get_customer_code(self):
        """从ERP获取客户代码"""
        try:
            self.init_erp_conn()
            sql = f"SELECT DISTINCT CI.cus_code FROM cux_inp_fg_prms_v CI WHERE CI.item_number='{self.internal_job[:15].upper()}' AND CI.revision='{self.internal_job[15:]}'"
            return self.db_erp.SELECT_DIC(sql)
        except:
            return []

    def _get_cus_code(self, job, ver):
        """从数据库获取客户代码"""
        try:
            self.init_erp_conn()
            sql = f'''
            SELECT DISTINCT
                CI.cus_code
            FROM
                cux_inp_fg_prms_v CI
            WHERE
                CI.item_number = '{job}'
                AND CI.revision = '{ver}'
            '''
            logger.info(f"执行sql:{sql}")
            return self.db_erp.SELECT_DIC(sql)
        except Exception as e:
            logger.error("获取客户代码失败：%s", str(e))
            return []

    def check_board_type(self):
        """
        检查板型是否支持自动处理
        不支持则直接抛出异常，转人工处理
        """
        logger.info(f"【{self.raw_job}】开始检查板型是否支持自动输出")

        check_rules = [
            # (self.raw_job[12:14] == '23', "软硬结合板"),
            (self.is_half_hole_board(), "半孔板"),
            (self.is_flip_panel(), "阴阳拼板"),
        ]

        for condition, board_type in check_rules:
            if condition:
                err_msg = f"此为{board_type}，需手动输出飞针资料"
                logger.error(err_msg)
                if self.is_auto_mode():
                    raise Exception(err_msg)
                else:
                    s = show_error_message("板型不支持", err_msg + '\n是否继续执行？')
                    if s != 16:
                        raise Exception(err_msg)

        if self.get_special_process_type():
            err_msg = f"此为灯板/直流电阻测试，需手动输出飞针资料"
            logger.error(err_msg)
            if self.is_auto_mode():
                raise Exception(err_msg)
            else:
                s = show_error_message("特殊工艺", err_msg + '\n是否继续执行？')
                if s != 16:
                    raise Exception(err_msg)

        logger.info(f"【{self.raw_job}】板型检查通过，支持自动输出")

    def is_half_hole_board(self):
        """
        通过EZCAM图形检查是否为半孔板
        返回 True/False
        """
        logger.info(f"【{self.raw_job}】检查是否为半孔板")
        self.gen.COM(
            f'open_entity,job={self.internal_job},type=step,name={self.run_step},iconic=no,custom_appearance=yes,left=-8,top=-8,width=1920,height=1017,stay_on_top=no'
        )
        self.gen.COM('clear_layers')
        self.gen.COM('affected_layer,name=,mode=all,affected=no')
        self.gen.COM('filter_reset,filter_name=popup')

        drill_layer = 'drl'
        if self.gen.DO_INFO(f'-t layer -e {self.internal_job}/{self.run_step}/{drill_layer} -d EXISTS -m script')['gEXISTS'] != 'yes':
            logger.info(f"【{self.raw_job}】未检测到钻孔层，判定非半孔板")
            return False

        tmp_layer1 = drill_layer + '_tmp_'
        tmp_layer2 = drill_layer + '_tmp_2'
        self.delete_layers(tmp_layer1, tmp_layer2)

        self.gen.COM(f'create_layer,layer={tmp_layer1},context=misc,type=signal,polarity=positive,ins_layer=,location=before')
        self.gen.COM(f'create_layer,layer={tmp_layer2},context=misc,type=signal,polarity=positive,ins_layer=,location=before')

        self.gen.COM(f'affected_layer,name={tmp_layer2},mode=single,affected=yes')
        self.gen.COM(
            'sr_fill,polarity=positive,step_margin_x=0,step_margin_y=0,step_max_dist_x=100,step_max_dist_y=100,sr_margin_x=0,sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no'
        )

        self.gen.COM(f'affected_layer,name={tmp_layer2},mode=single,affected=no')

        self.gen.COM(f'affected_layer,name={drill_layer},mode=single,affected=yes')
        self.gen.COM(
            f'sel_copy_other,dest=layer_name,target_layer={tmp_layer1},invert=no,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0,mirror=none,rotation=0'
        )
        self.gen.COM(f'affected_layer,name={drill_layer},mode=single,affected=no')

        self.gen.COM(f'affected_layer,name={tmp_layer1},mode=single,affected=yes')
        self.gen.COM('filter_atr_set,filter_name=popup,attribute=.drill,condition=yes,text=,option=non_plated,min_int_val=,max_int_val=,min_float_val=,max_float_val=')
        self.gen.COM('filter_area_strt')
        self.gen.COM('filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no,lines_only=no,ovals_only=no,min_len=0,max_len=100,min_angle=0,max_angle=0')
        self.gen.COM('get_select_count')
        if int(self.gen.COMANS) > 0:
            self.gen.COM('sel_delete')
        self.gen.COM('filter_reset,filter_name=popup')

        self.gen.COM(f'sel_ref_feat,layers={tmp_layer2},use=filter,mode=cover,f_types=line\;pad\;arc\;text\;surface,polarity=positive\;negative,include_syms=,exclude_syms=,pads_as=shape,tolerance=0,negative_union=yes')
        self.gen.COM('get_select_count')
        if int(self.gen.COMANS) > 0:
            self.gen.COM('sel_delete')

        self.gen.COM('filter_reset,filter_name=popup')
        self.gen.COM('filter_area_strt')
        self.gen.COM('filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no,lines_only=no,ovals_only=no,min_len=0,max_len=100,min_angle=0,max_angle=0')
        self.gen.COM('get_select_count')
        is_half_hole = int(self.gen.COMANS)
        self.gen.COM('filter_reset,filter_name=popup')
        self.gen.COM(f'affected_layer,name={tmp_layer1},mode=single,affected=no')
        self.delete_layers(tmp_layer1, tmp_layer2)
        logger.info(f"【{self.raw_job}】半孔板检查结果：{is_half_hole}")
        return is_half_hole > 0

    def is_flip_panel(self):
        """检查是否为阴阳拼板"""
        logger.info(f"【{self.raw_job}】检查是否为阴阳拼板")
        check_steps = ['set', 'panel']
        for step_name in check_steps:
            if self.gen.DO_INFO(f'-t step -e {self.internal_job}/{step_name} -d EXISTS -m script')['gEXISTS'] == 'yes':
                info = self.gen.DO_INFO(
                    f'-t step -e {self.internal_job}/{step_name} -d SR -m script'
                )
                for i in range(len(info['gSRstep'])):
                    # if info['gSRmirror'][i] == 'yes':
                    if re.search(re.compile('flip$'),info['gSRstep'][i]):
                        logger.info(f"【{self.raw_job}】检测到阴阳拼板")
                        return True
        return False

    def get_special_process_type(self):
        """
        查询ERP流程，判断是否为灯板/直流电阻板
        返回：False / DC_RESISTANCE / LIGHT_BOARD
        """
        logger.info(f"【{self.raw_job}】查询是否为灯板/直流电阻板")
        try:
            job_upper = self.raw_job.upper()
            sql = f'''
            SELECT a.operation_code,a.description,b.note_string_
            FROM suntak.rpt_job_trav_sect_list a
            LEFT JOIN suntak.trav_sect_da b ON b.item_id=a.item_id AND b.revision_id=a.revision_id AND b.sequential_index=a.sequential_index
            WHERE a.job_name = '{job_upper}'
            '''

            sql2 = sql.replace(job_upper, f"{job_upper}-A")
            self.init_inp_conn()
            logger.info(f"执行sql:{sql}")
            data_list = self.db_inp.SELECT_DIC(sql)
            if not data_list:
                logger.info(f"执行sql:{sql2}")
                data_list = self.db_inp.SELECT_DIC(sql2)

            pattern = re.compile(r'灯板')
            for item in data_list:
                desc = item.get('DESCRIPTION', '')
                note = item.get('NOTE_STRING_', '')

                if desc == '直流电阻测试':
                    return 'DC_RESISTANCE'
                if desc == '外层沉铜' and note and pattern.search(note):
                    return 'LIGHT_BOARD'

            return False

        except Exception as e:
            logger.error(f"【{self.raw_job}】查询特殊工艺失败：{str(e)}")
            return False

    def check_four_line_test_mode(self):
        """
        查询工艺流程，判断是否需要四线测试
        返回 '2w' 或 '4w'
        """
        logger.info(f"【{self.raw_job}】检查是否为四线测试流程")
        try:
            job_upper = self.raw_job.upper()
            sql = f'''
            SELECT a.operation_code,a.description,b.note_string_
            FROM suntak.rpt_job_trav_sect_list a
            LEFT JOIN suntak.trav_sect_da b ON b.item_id=a.item_id AND b.revision_id=a.revision_id AND b.sequential_index=a.sequential_index
            WHERE a.job_name = '{job_upper}'
            '''
            self.init_inp_conn()
            sql2 = sql.replace(job_upper, f"{job_upper}-A")
            data_list = self.db_inp.SELECT_DIC(sql)
            logger.info(f"执行sql:{sql}")
            if not data_list:
                logger.info(f"执行sql:{sql2}")
                data_list = self.db_inp.SELECT_DIC(sql2)

            for item in data_list:
                desc = item.get('DESCRIPTION', '')
                if re.search(r'四线', desc):
                    logger.info(f"【{self.raw_job}】检测到四线测试流程")
                    return '4w'

            logger.info(f"【{self.raw_job}】使用二线测试模式")
            return '2w'

        except Exception as e:
            logger.error(f"【{self.raw_job}】查询四线流程失败：{str(e)}")
            return '2w'

    def delete_layers(self, *layers):
        """批量删除指定图层"""
        for layer_name in layers:
            if self.gen.DO_INFO(f'-t layer -e {self.internal_job}/{self.run_step}/{layer_name} -d EXISTS -m script')['gEXISTS'] == 'yes':
                self.gen.COM(f'delete_layer,layer={layer_name}')

    def delete_non_board_layers(self):
        """删除非board属性图层，仅保留board层与外形/钻孔层"""
        logger.info(f"【{self.raw_job}】开始清理非board属性图层")
        info = self.gen.DO_INFO(f'-t matrix -e {self.internal_job}/matrix -d ROW -m script')
        for n in range(len(info['gROWname'])):
            layer_name = info['gROWname'][n]
            context = info['gROWcontext'][n]
            if context != 'board' and not re.search(r'^drill|gdg$', layer_name):
                self.gen.COM(f'delete_layer,layer={layer_name}')
        logger.info(f"【{self.raw_job}】非board图层清理完成")

    def check_mask_layers(self):
        """检查阻焊层是否存在，不存在则报错"""
        logger.info(f"【{self.raw_job}】检查阻焊层是否存在")
        info = self.gen.DO_INFO(f'-t matrix -e {self.internal_job}/matrix -d ROW -m script')
        for n in range(len(info['gROWname'])):
            if info['gROWcontext'][n] == 'board' and info['gROWlayer_type'][n] == 'solder_mask':
                logger.info(f"【{self.raw_job}】阻焊层检查通过")
                return
        err = f"未检测到阻焊层，需手动处理"
        if self.is_auto_mode():
            raise Exception(err)
        else:
            s = show_error_message("阻焊层缺失", err + '\n是否继续?')
            if s != 16:
                raise Exception(err)
            else:
                # s = show_error_message("阻焊层检查", f'{err}...\n是否继续?')
                # if s != 16:
                #     raise Exception(err)
                # else:
                self.gen.PAUSE(err)
                logger.info(f"【{self.raw_job}】阻焊层检查通过")
                return

    def run_net_compare(self, comp_step, note):
        """
        执行网络比对并判断结果
        :param comp_step: 要比对的Step
        :param note: 日志标识（工作稿/原稿）
        """
        logger.info(f"【{self.raw_job}】开始【{note}】网络比对")
        short_cnt, open_cnt = self.execute_net_compare(comp_step)

        if short_cnt != '0':
            err = f"{note}网络异常：存在 {short_cnt} 处短路"
            if self.is_auto_mode():
                raise Exception(err)
            else:
                # show_error_message("网络异常", err)
                self.gen.PAUSE(err)
        if open_cnt != '0':
            err = f"{note}网络异常：存在 {open_cnt} 处开路"
            if self.is_auto_mode():
                raise Exception(err)
            else:
                # show_error_message("网络异常", err)
                self.gen.PAUSE(err)

        logger.info(f"【{self.raw_job}】【{note}】网络比对通过（无短路、无开路）")

    def execute_net_compare(self, comp_step):
        """底层执行网络比对命令"""
        open_cmd = f'netlist_page_open,set=yes,job1={self.internal_job},step1={self.net_compare_step},type1=ref,job2={self.internal_job},step2={comp_step},type2=cur'
        self.gen.COM(open_cmd)
        self.gen.COM(f'netlist_recalc,job={self.internal_job},step={self.net_compare_step},type=cur,display=top')
        self.gen.COM(f'netlist_recalc,job={self.internal_job},step={comp_step},type=cur,display=bottom')

        compare_cmd = (
            f'netlist_compare,job1={self.internal_job},step1={self.net_compare_step},type1=cur,job2={self.internal_job},step2={comp_step},type2=cur,display=yes,'
            'filter_ignore_net_names=no,filter_cad_problem=no,filter_nfp=no,filter_attr_diff=no,filter_extra_on_pad=no'
        )
        self.gen.COM(compare_cmd)
        short_cnt, open_cnt = self.parse_net_result()
        self.gen.COM('netlist_page_close')
        return short_cnt, open_cnt

    def _get_board_signal_layer(self):
        """获取board信号层"""
        logger.info(f"【{self.raw_job}】获线路层")
        info = self.gen.DO_INFO(f'-t matrix -e {self.internal_job}/matrix -d ROW -m script')
        signal = []
        for n in range(len(info['gROWname'])):
            if info['gROWcontext'][n] == 'board' and info['gROWlayer_type'][n] == 'signal':
                signal.append(info['gROWname'][n])
        if len(signal) > 0:
            logger.info(f"【{self.raw_job}】获线路层完成.{signal}")
            return '\;'.join(signal)
        else:
            err = f"未检测线路层,无法网络比对"
            if self.is_auto_mode():
                raise Exception(err)
            else:
                show_error_message("线路层缺失", err)
                raise Exception(err)

    def parse_net_result(self):
        """解析网络比对返回结果"""
        res_text = self.gen.COMANS
        parts = res_text.split(' ')
        return parts[0], parts[2]

    def import_original_gerber_layers(self):
        """
        导入原稿Gerber文件并自动坐标对齐
        返回图层映射关系
        """
        logger.info(f"【{self.raw_job}】开始导入原稿Gerber图层")
        layer_map = {}
        if self.is_auto_mode():
            # pattern = re.compile(r'^(gtl|gbl|l\d+[sn])\.mi')
            pattern = re.compile(r'^(gtl|gbl|l\d+[sn]|\d+d)\.mi')
        else:
            pattern = re.compile(r'^(gtl|gbl|drl|l\d+[sn]|\d+d)\.mi')

        if not os.path.exists(self.org_gerber_path):
            logger.warning(f"【{self.raw_job}】原稿路径不存在：{self.org_gerber_path}")
            return layer_map
        else:
            logger.info(f"【{self.raw_job}】原稿路径：{self.org_gerber_path}")

        x, y = 0, 0
        get_coord = False

        for filename in os.listdir(self.org_gerber_path):
            match = pattern.search(filename)
            if not match:
                continue

            key = match.group(1)
            full_path = os.path.join(self.org_gerber_path, filename)
            logger.info(f"gerber file:{full_path}")
            target_layer = filename + '_et'
            layer_map[key] = target_layer

            cmd = ('input_manual_set,path=%s,job=%s,step=%s,format=Gerber274x,data_type=Ascii,units=mm,'
                   'coordinates=absolute,zeroes=leading,nf1=4,nf2=5,decimal=no,separator=,tool_units=inch,'
                   'layer=%s,wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.0024,signed_coords=no,'
                   'break_sr=no,drill_only=no,merge_by_rule=no,threshold=0,resolution=0')

            self.gen.COM('input_manual_reset')
            self.gen.COM(cmd % (full_path, self.internal_job, self.run_step, target_layer))

            if self.gen.STATUS == 0 and not get_coord and re.search(r'drl|\d+d', key):
                if self.gen.DO_INFO(f'-t step -e {self.internal_job}/orig -d EXISTS -m script')['gEXISTS'] == 'no':
                    t_limit = self.gen.DO_INFO(
                        f'-t layer -e {self.internal_job}/{self.run_step}/{target_layer} -d LIMITS -m script',
                        units='inch')
                    w_limit = self.gen.DO_INFO(f'-t layer -e {self.internal_job}/orig/{key} -d LIMITS -m script',
                                               units='inch')
                    x = float(w_limit['gLIMITSxmin']) - float(t_limit['gLIMITSxmin'])
                    y = float(w_limit['gLIMITSymin']) - float(t_limit['gLIMITSymin'])
                    get_coord = True

        if x != 0 or y != 0:
            self.gen.COM('clear_layers')
            self.gen.COM('affected_layer,name=,mode=all,affected=no')
            for layer in layer_map.values():
                self.gen.COM(f'affected_layer,name={layer},mode=single,affected=yes')
                self.gen.COM(f'sel_move,dx={x},dy={y}')
                self.gen.COM(f'affected_layer,name={layer},mode=single,affected=no')

        logger.info(f"【{self.raw_job}】原稿Gerber图层导入完成")
        return layer_map

    def restore_original_layer_to_workstep(self, layer_map):
        """将导入的原稿图层覆盖到工作稿"""
        logger.info(f"【{self.raw_job}】开始将原稿图层还原到工作稿")
        self.gen.COM('editor_page_close')
        self.gen.COM(f'open_entity,job={self.internal_job},type=step,name={self.run_step},iconic=no,custom_appearance=yes,left=-8,top=-8,width=1920,height=1017,stay_on_top=no')

        self.gen.COM('clear_layers')
        self.gen.COM('affected_layer,name=,mode=all,affected=no')

        for work_layer, org_layer in layer_map.items():
            # if work_layer == 'drl' :
            #     continue

            if re.search(re.compile(r'^drl'),work_layer):
                continue

            work_exists = self.gen.DO_INFO(f'-t layer -e {self.internal_job}/{self.run_step}/{work_layer} -d EXISTS -m script')['gEXISTS'] == 'yes'
            org_exists = self.gen.DO_INFO(f'-t layer -e {self.internal_job}/{self.run_step}/{org_layer} -d EXISTS -m script')['gEXISTS'] == 'yes'

            if work_exists and org_exists:
                self.gen.COM(f'affected_layer,name={work_layer},mode=single,affected=yes')
                self.gen.COM('sel_delete')
                self.gen.COM(f'affected_layer,name={work_layer},mode=single,affected=no')

                self.gen.COM(f'affected_layer,name={org_layer},mode=single,affected=yes')
                self.gen.COM(f'sel_copy_other,dest=layer_name,target_layer={work_layer}')
                self.gen.COM(f'affected_layer,name={org_layer},mode=single,affected=no')

                self.gen.COM(f'affected_layer,name={work_layer},mode=single,affected=yes')
                self.gen.COM('filter_reset,filter_name=popup')
                self.gen.COM('filter_set,filter_name=popup,update_popup=no,profile=out')
                self.gen.COM('filter_area_strt')
                self.gen.COM('filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no,lines_only=no,ovals_only=no,min_len=0,max_len=100,min_angle=0,max_angle=0')
                self.gen.COM('get_select_count')
                if int(self.gen.COMANS) > 0:
                    self.gen.COM('sel_delete')
                self.gen.COM(f'affected_layer,name={work_layer},mode=single,affected=no')

        self._dispose_npth(layer_map.keys())
        self.gen.COM('editor_page_close')
        logger.info(f"【{self.raw_job}】原稿图层还原完成")

    def import_orig(self):
        """从内部orig步骤还原图层"""
        logger.info(f"【{self.raw_job}】从内部orig步骤还原图层")
        copy_layers = []
        self.open_step(self.internal_job, self.run_step)
        if self.gen.DO_INFO(f'-t step -e {self.internal_job}/orig -d EXISTS -m script')['gEXISTS'] == 'yes':
            info = self.gen.DO_INFO(f'-t matrix -e {self.internal_job}/matrix -d ROW -m script')
            for n in range(len(info['gROWname'])):
                name = info['gROWname'][n]
                ctx = info['gROWcontext'][n]
                typ = info['gROWlayer_type'][n]
                side = info['gROWside'][n]
                if ctx == 'board':
                    if typ == 'drill' and re.match(r'^\d+d$', name):
                        copy_layers.append(name)
                    elif typ == 'signal' and re.search(r'top|bottom', side):
                        copy_layers.append(name)

        self.gen.COM('clear_layers')
        self.gen.COM('affected_layer,name=,mode=all,affected=no')
        for layer in copy_layers:
            self.gen.COM(f'copy_layer,source_job={self.internal_job},source_step=orig,source_layer={layer},dest=layer_name,dest_layer={layer},mode=replace,invert=no,copy_notes=no,copy_attrs=no')

            self.gen.COM(f'affected_layer,name={layer},mode=single,affected=yes')
            self.gen.COM('filter_reset,filter_name=popup')
            self.gen.COM('filter_set,filter_name=popup,update_popup=no,profile=out')
            self.gen.COM('filter_area_strt')
            self.gen.COM('filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no,lines_only=no,ovals_only=no,min_len=0,max_len=100,min_angle=0,max_angle=0')
            self.gen.COM('get_select_count')
            if int(self.gen.COMANS) > 0:
                self.gen.COM('sel_delete')
            self.gen.COM(f'affected_layer,name={layer},mode=single,affected=no')

        self._dispose_npth(copy_layers)
        logger.info(f"【{self.raw_job}】orig步骤图层还原完成")

    def create_flying_test_points(self, job, mode='2w'):
        """生成飞针测试点（支持2w/4w两种模式）"""
        logger.info(f"【{self.raw_job}】开始生成{mode}测试点")
        if mode == '2w':
            command = f'script_run,name=D:/eastek-server/ezFixtureII/sys/scripts/select_2w.csh,dirmode=global,params=,env1=JOB={self.internal_job},env2=STEP={self.run_step}'
        else:
            command = f'script_run,name=D:/eastek-server/ezFixtureII/sys/scripts/select_4w.csh,dirmode=global,params=,env1=JOB={self.internal_job},env2=STEP={self.run_step}'
        self.gen.COM(command)
        logger.info(f"【{self.raw_job}】{mode}测试点生成完成")

    def export_flying_probe_files(self, job, mode='2w'):
        """导出356飞针测试文件"""
        logger.info(f"【{self.raw_job}】开始导出{mode}飞针测试文件")
        suffix = f'-{mode}' if mode == '4w' else ''
        base_params = (
            'mode=atg356,output_backdrill_ipc=no,auto_select_fiducial=yes,inch=yes,'
            'adjacent_method=absolute,resolution=1,adj_net_dist=50,output_trace=yes,output_gerber=no,output_testpoint_gerber=no,'
            'multiple_master=no,export_4w=yes,output_middle_point=yes,output_report=yes'
        )

        if mode == '2w':
            output_path = self.output_2w_path
            output_path_network = self.output_2w_path_network
        else:
            output_path = self.output_4w_path
            output_path_network = self.output_4w_path_network

        if not os.path.exists(output_path):
            os.makedirs(output_path)
        if not os.path.exists(output_path_network):
            os.makedirs(output_path_network)

        # 邻近网络距离设定（解析度）
        if self.factory_code == 'JM2':
            adj_net_dist = 50
        else:
            adj_net_dist = 80
        # 非全自动模式：弹窗允许手动输入邻近网络距离
        if not self.is_auto_mode():
            adj_net_dist, ok = QInputDialog.getInt(
                None, '邻近网络距离设定',
                f'当前工厂: {self.factory_code}\n请输入邻近网络距离 (mil):',
                value=adj_net_dist, min=1, max=1000, step=1
            )
            if not ok:
                adj_net_dist = 50  # 用户取消时使用默认值50
            logger.info(f"【{self.raw_job}】手动设定邻近网络距离: {adj_net_dist} mil")

        steps = self.gen.DO_INFO(f'-t job -e {job} -d STEPS_LIST -m script')['gSTEPS_LIST']
        if 'set' in steps:
            self.gen.COM('ezfix_flyoutput_drc,chk_min_tst_dis=yes,min_tst_dis=3,chk_bigger_hole=yes,bigger_hole=120,chk_illegal_pos_tst=yes,chk_illegal_net_tst=yes')
            # cmd = f'ezfix_output_flying_probe,path={output_path}/{self.raw_job}-set{suffix}.356,{base_params},optimum_step_and_repeat=yes,step_and_repeat_command=yes,step_and_repeat_command_step=set'
            cmd = f'ezfix_output_flying_probe,mode=emma356,output_backdrill_ipc=no,auto_select_fiducial=yes,path={output_path}/{self.raw_job}-set{suffix},inch=yes,adjacent_method=absolute,resolution=1,adj_net_dist={adj_net_dist},output_trace=yes,output_gerber=no,output_testpoint_gerber=no,step_and_repeat_command=yes,step_and_repeat_command_step=set,step_and_repeat_file_command=no,step_and_repeat_file_command_step=,multiple_master=no,multiple_master_step=,adj_3dnet=no,ivh_adj_3dnet=no,adj_net_in_clear=yes,roundrect_trans=no,roundrect_trans_maxradius=0,mapping_number=no,mapping_number_comp=,mapping_number_sold=,remapping_number=no,remapping_number_comp=,remapping_number_sold=,resismin_4w=0,resismax_4w=0,resismiddle_4w=0,mnf2_outline_enlarge_mil=0,mnf2_pthmove=no,ivh_3d_drilllyr=0,ivh_3d_clearanc=0,check_illegal_testpoint=yes,show_dlg=yes,hioki_thickness=0,hioki_sfd=no,hioki_nnd=no,hioki_ftd=no,hioki_spd=no,hioki_spd_f=no,hioki_spd_b=no,hioki_side_sort=no,hioki_csv=no,hioki_sma=no,output_middle_point=yes,optimum_step_and_repeat=yes,output_report=yes,multiple_master_combined=no,export_4w=yes,output_trace_layer=,output_trace_surface=yes,output_trace_outlayer_only=no,outline_to_npth=no,drill_to_npth=no,drill_to_npth_layer='
            self.gen.COM(cmd)
            test_point = self._cal_test_points(f"{output_path}/{self.raw_job}-set{suffix}_356",mode)
            self._move_file_to_network(f'{output_path}/{self.raw_job}-set{suffix}.356',output_path_network)
            self._del_map_file(f"{output_path}/{self.raw_job}-set{suffix}")
        else:
            # cmd = f'ezfix_output_flying_probe,path={output_path}/{self.raw_job}-edit{suffix}.356,{base_params},optimum_step_and_repeat=no'
            cmd = f'ezfix_output_flying_probe,mode=emma356,output_backdrill_ipc=no,auto_select_fiducial=yes,path={output_path}/{self.raw_job}-edit{suffix},inch=yes,adjacent_method=absolute,resolution=1,adj_net_dist={adj_net_dist},output_trace=yes,output_gerber=no,output_testpoint_gerber=no,step_and_repeat_command=no,step_and_repeat_command_step=,step_and_repeat_file_command=no,step_and_repeat_file_command_step=,multiple_master=no,multiple_master_step=,adj_3dnet=no,ivh_adj_3dnet=no,adj_net_in_clear=yes,roundrect_trans=no,roundrect_trans_maxradius=0,mapping_number=no,mapping_number_comp=,mapping_number_sold=,remapping_number=no,remapping_number_comp=,remapping_number_sold=,resismin_4w=0,resismax_4w=0,resismiddle_4w=0,mnf2_outline_enlarge_mil=0,mnf2_pthmove=no,ivh_3d_drilllyr=0,ivh_3d_clearanc=0,check_illegal_testpoint=yes,show_dlg=yes,hioki_thickness=0,hioki_sfd=no,hioki_nnd=no,hioki_ftd=no,hioki_spd=no,hioki_spd_f=no,hioki_spd_b=no,hioki_side_sort=no,hioki_csv=no,hioki_sma=no,output_middle_point=yes,optimum_step_and_repeat=no,output_report=yes,multiple_master_combined=no,export_4w=yes,output_trace_layer=,output_trace_surface=yes,output_trace_outlayer_only=no,outline_to_npth=no,drill_to_npth=no,drill_to_npth_layer='
            self.gen.COM(cmd)
            test_point = self._cal_test_points(f"{output_path}/{self.raw_job}-edit{suffix}_356",mode)
            self._move_file_to_network(f'{output_path}/{self.raw_job}-edit{suffix}.356',output_path_network)
            self._del_map_file(f"{output_path}/{self.raw_job}-edit{suffix}")

        if 'panel' in steps:
            # cmd_panel = f'ezfix_output_flying_probe,path={output_path}/{self.raw_job}-panel{suffix}.356,{base_params},optimum_step_and_repeat=yes,step_and_repeat_command=yes,step_and_repeat_command_step=panel'
            cmd_panel = f'ezfix_output_flying_probe,mode=emma356,output_backdrill_ipc=no,auto_select_fiducial=yes,path={output_path}/{self.raw_job}-panel{suffix},inch=yes,adjacent_method=absolute,resolution=1,adj_net_dist={adj_net_dist},output_trace=yes,output_gerber=no,output_testpoint_gerber=no,step_and_repeat_command=yes,step_and_repeat_command_step=panel,step_and_repeat_file_command=no,step_and_repeat_file_command_step=,multiple_master=no,multiple_master_step=,adj_3dnet=no,ivh_adj_3dnet=no,adj_net_in_clear=yes,roundrect_trans=no,roundrect_trans_maxradius=0,mapping_number=no,mapping_number_comp=,mapping_number_sold=,remapping_number=no,remapping_number_comp=,remapping_number_sold=,resismin_4w=0,resismax_4w=0,resismiddle_4w=0,mnf2_outline_enlarge_mil=0,mnf2_pthmove=no,ivh_3d_drilllyr=0,ivh_3d_clearanc=0,check_illegal_testpoint=yes,show_dlg=yes,hioki_thickness=0,hioki_sfd=no,hioki_nnd=no,hioki_ftd=no,hioki_spd=no,hioki_spd_f=no,hioki_spd_b=no,hioki_side_sort=no,hioki_csv=no,hioki_sma=no,output_middle_point=yes,optimum_step_and_repeat=yes,output_report=yes,multiple_master_combined=no,export_4w=yes,output_trace_layer=,output_trace_surface=yes,output_trace_outlayer_only=no,outline_to_npth=no,drill_to_npth=no,drill_to_npth_layer='
            self.gen.COM(cmd_panel)
            self._move_file_to_network(f'{output_path}/{self.raw_job}-panel{suffix}.356', output_path_network)
            self._del_map_file(f"{output_path}/{self.raw_job}-panel{suffix}")

        if 'panela' in steps:
            # cmd_panel = f'ezfix_output_flying_probe,path={output_path}/{self.raw_job}-panela{suffix}.356,{base_params},optimum_step_and_repeat=yes,step_and_repeat_command=yes,step_and_repeat_command_step=panela'
            cmd_panel = f'ezfix_output_flying_probe,mode=emma356,output_backdrill_ipc=no,auto_select_fiducial=yes,path={output_path}/{self.raw_job}-panela{suffix},inch=yes,adjacent_method=absolute,resolution=1,adj_net_dist={adj_net_dist},output_trace=yes,output_gerber=no,output_testpoint_gerber=no,step_and_repeat_command=yes,step_and_repeat_command_step=panela,step_and_repeat_file_command=no,step_and_repeat_file_command_step=,multiple_master=no,multiple_master_step=,adj_3dnet=no,ivh_adj_3dnet=no,adj_net_in_clear=yes,roundrect_trans=no,roundrect_trans_maxradius=0,mapping_number=no,mapping_number_comp=,mapping_number_sold=,remapping_number=no,remapping_number_comp=,remapping_number_sold=,resismin_4w=0,resismax_4w=0,resismiddle_4w=0,mnf2_outline_enlarge_mil=0,mnf2_pthmove=no,ivh_3d_drilllyr=0,ivh_3d_clearanc=0,check_illegal_testpoint=yes,show_dlg=yes,hioki_thickness=0,hioki_sfd=no,hioki_nnd=no,hioki_ftd=no,hioki_spd=no,hioki_spd_f=no,hioki_spd_b=no,hioki_side_sort=no,hioki_csv=no,hioki_sma=no,output_middle_point=yes,optimum_step_and_repeat=yes,output_report=yes,multiple_master_combined=no,export_4w=yes,output_trace_layer=,output_trace_surface=yes,output_trace_outlayer_only=no,outline_to_npth=no,drill_to_npth=no,drill_to_npth_layer='

            self.gen.COM(cmd_panel)
            self._move_file_to_network(f'{output_path}/{self.raw_job}-panela{suffix}.356', output_path_network)
            self._del_map_file(f"{output_path}/{self.raw_job}-panela{suffix}")

        if 'panelb' in steps:
            # cmd_panel = f'ezfix_output_flying_probe,path={output_path}/{self.raw_job}-panelb{suffix}.356,{base_params},optimum_step_and_repeat=yes,step_and_repeat_command=yes,step_and_repeat_command_step=panelb'
            cmd_panel = f'ezfix_output_flying_probe,mode=emma356,output_backdrill_ipc=no,auto_select_fiducial=yes,path={output_path}/{self.raw_job}-panelb{suffix},inch=yes,adjacent_method=absolute,resolution=1,adj_net_dist={adj_net_dist},output_trace=yes,output_gerber=no,output_testpoint_gerber=no,step_and_repeat_command=yes,step_and_repeat_command_step=panelb,step_and_repeat_file_command=no,step_and_repeat_file_command_step=,multiple_master=no,multiple_master_step=,adj_3dnet=no,ivh_adj_3dnet=no,adj_net_in_clear=yes,roundrect_trans=no,roundrect_trans_maxradius=0,mapping_number=no,mapping_number_comp=,mapping_number_sold=,remapping_number=no,remapping_number_comp=,remapping_number_sold=,resismin_4w=0,resismax_4w=0,resismiddle_4w=0,mnf2_outline_enlarge_mil=0,mnf2_pthmove=no,ivh_3d_drilllyr=0,ivh_3d_clearanc=0,check_illegal_testpoint=yes,show_dlg=yes,hioki_thickness=0,hioki_sfd=no,hioki_nnd=no,hioki_ftd=no,hioki_spd=no,hioki_spd_f=no,hioki_spd_b=no,hioki_side_sort=no,hioki_csv=no,hioki_sma=no,output_middle_point=yes,optimum_step_and_repeat=yes,output_report=yes,multiple_master_combined=no,export_4w=yes,output_trace_layer=,output_trace_surface=yes,output_trace_outlayer_only=no,outline_to_npth=no,drill_to_npth=no,drill_to_npth_layer='

            self.gen.COM(cmd_panel)
            self._move_file_to_network(f'{output_path}/{self.raw_job}-panelb{suffix}.356', output_path_network)
            self._del_map_file(f"{output_path}/{self.raw_job}-panelb{suffix}")
        # sys.exit(0)
        logger.info(f"【{self.raw_job}】{mode}飞针测试文件导出完成")
        return test_point

    def _cal_test_points(self,file,mode):
        '''提取测试点'''
        _MAP_Report = file + '_Report'
        logger.info(f"【{self.raw_job}】{mode}开始计算测试点数 {_MAP_Report}")
        Comp_Point_Count = 0
        Sold_Point_Count = 0
        if os.path.isfile(_MAP_Report):
            with open(_MAP_Report,'r',encoding='utf-8') as f:
                for line in f.readlines():
                    if Comp_Point_Count == 0 and re.search(re.compile('Comp'), line):
                        info = line.split('=')
                        Comp_Point_Count = int(info[-1].strip())
                    if Sold_Point_Count == 0 and re.search(re.compile('Sold'), line):
                        info = line.split('=')
                        Sold_Point_Count = int(info[-1].strip())
        total = Comp_Point_Count + Sold_Point_Count
        logger.info(f"【{self.raw_job}】{mode}测试点数：{total}")
        return total

    def _del_map_file(self,file):
        '''删除残留文件'''
        MAP = file + '.MAP'
        _MAP_Report = file + '_MAP_Report'
        for n in [MAP,_MAP_Report]:
            if os.path.isfile(n):
                os.unlink(n)

    def _move_file_to_network(self,local_file_path,network_dest_path):
        """移动文件到网络盘"""
        if not os.path.exists(local_file_path):
            logger.info(f"错误：本地文件不存在 → {local_file_path}")
            return
        dest_file = os.path.join(network_dest_path, os.path.basename(local_file_path))
        shutil.move(local_file_path, dest_file)
        logger.info(f"文件移动成功：{dest_file}")

    def export_job_to_tgz(self, job_name, out_dir,net_dir):
        """导出EZCAM工程为TGZ压缩包"""
        logger.info(f"【{self.raw_job}】导出工程TGZ")
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        cmd = 'export_job,job=%s,path=%s,mode=tar_gzip,units=metric,submode=full,overwrite=no'
        self.gen.COM(cmd % (job_name, out_dir))
        self._move_file_to_network(f'{out_dir}/{job_name}.tgz',net_dir)

    def create_and_output_test_files(self, mode='2w',job=None):
        """统一创建测试点并输出所有文件（独立流程）"""
        logger.info(f"\n=============== 开始输出【{mode}】资料 ===============")
        if self.mode in ['check','input']:
            self.gen.PAUSE('请检查系统生成的测试点是否正确,如有问题修正后需重新输出...')
            s = show_error_message("温馨提示", f'是否需要重新输出{mode}资料?...')
            if s != 16:
                return ''
            else:
                # 保存资料
                self.gen.COM(f'save_job,job={job},override=no')
        else:
            # self._sel_pad2line()
            self.create_flying_test_points(job, mode)
            if not self.is_auto_mode():
                # show_error_message('检查测试点',f'{mode}测试点创建完成，请检查')
                self.gen.PAUSE(f'{mode}测试点创建完成，请检查')

        test_point = self.export_flying_probe_files(job, mode)
        self.export_job_to_tgz(job, self.output_tgz_path, self.output_tgz_path_network)
        self.gen.COM('ezfix_close_job,check_in=yes')
        self.gen.COM(f'check_inout,mode=in,type=job,job={job}')
        self.gen.COM(f'close_job,job={job}')
        # if self.is_auto_mode():
        #     self.clean_existing_job(job)
        logger.info(f"=============== 【{mode}】资料输出完成 ===============\n")
        return test_point

    def _sel_pad2line(self):
        self.gen.COM(f'ezfix_open_job,job={self.internal_job}')
        self.gen.COM(f'ezfix_open_step,job={self.internal_job},step={self.run_step},open_top=no')
        self.gen.COM('affected_layer,name=,mode=all,affected=no')
        self.gen.COM('filter_reset,filter_name=popup')
        info = self.gen.DO_INFO(f'-t matrix -e {self.internal_job}/matrix -d ROW -m script')
        for n in range(len(info['gROWname'])):
            layer_name = info['gROWname'][n]
            context = info['gROWcontext'][n]
            side = info['gROWside'][n]
            if context == 'board' and info['gROWlayer_type'][n] == 'signal' and side in ['top','bottom']:
                self.gen.COM(f'ezfix_display_layer,name={layer_name},display=yes')
                # import pyautogui
                # # 直接触发windows本地快捷键P/T,选择PAD，然后PAD2LINE
                # # 按下字母P
                # pyautogui.press('P')
                # time.sleep(1)
                # pyautogui.press('T')
                self.gen.COM(f'ezfix_display_layer,name={layer_name},display=no')
        self.gen.COM('filter_reset,filter_name=popup')

    def clean_existing_job(self, job):
        """清理已存在的旧工程，避免冲突"""
        if self.gen.DO_INFO(f'-t job -e {job} -d EXISTS -m script')['gEXISTS'] == 'yes':
            self.gen.COM(f'check_inout,mode=in,type=job,job={job}')
            self.gen.COM(f'close_job,job={job}')
            self.gen.COM(f'delete_entity,job=,type=job,name={job}')
            logger.info(f"【{self.raw_job}】旧工程已清理")

    def import_job_from_tgz(self,job):
        """从TGZ文件导入工程"""
        tgz_file = self._build_tgz_file_path(job)
        logger.info(f"【{self.raw_job}】开始导入TGZ：{tgz_file}")
        if not os.path.exists(tgz_file):
            err = f"TGZ文件不存在：{tgz_file}"
            if self.is_auto_mode():
                raise Exception(err)
            else:
                s = show_error_message("文件缺失", err + '\n是否手动导入继续？')
                if s != 16:
                    raise Exception(err)
                else:
                    self.gen.PAUSE('请手动导入TGZ')
                    return
        self.gen.COM(f'import_job,db=ezcam,path={tgz_file},name={job},analyze_surfaces=yes')
        logger.info(f"【{self.raw_job}】TGZ工程导入成功")

    def open_job(self, job):
        """打开指定Job"""
        logger.info(f"【{self.raw_job}】打开工程：{job}/{self.run_step}")
        self.gen.COM(f'ezfix_open_job,job={job}')

    def open_step(self, job, step):
        """打开指定Step"""
        self.gen.COM(f'ezfix_open_step,job={job},step={step},open_top=yes')
        self.gen.COM(f'open_entity,job={job},type=step,name={step},iconic=no,skip_gui=yes')

    def _get_drill_layer(self):
        """获取钻孔层"""
        info = self.gen.DO_INFO(F'-t matrix -e {self.internal_job}/matrix -d ROW -m script')
        drill_layer = []
        for k in range(len(info['gROWname'])):
            if info['gROWcontext'][k] == 'board' and info['gROWlayer_type'][k] == 'drill' and re.search(re.compile('drl|\d+nd'),info['gROWname'][k]):
                drill_layer.append(info['gROWname'][k])
        return drill_layer

    def _delete_outside_features(self):
        """删除板外物件、外形线"""
        logger.info(f"【{self.raw_job}】开始清理板外物件、外形线")
        self.gen.COM('clear_layers')
        self.gen.COM('affected_layer,name=,mode=all,affected=no')
        self.gen.COM('filter_reset,filter_name=popup')
        out = 'outline'
        self.delete_layers(out)
        self.gen.COM(f'profile_to_rout,layer={out},width=40,create_sr=no')

        info = self.gen.DO_INFO(f'-t matrix -e {self.internal_job}/matrix -d ROW -m script')
        for n in range(len(info['gROWname'])):
            name = info['gROWname'][n]
            ctx = info['gROWcontext'][n]
            typ = info['gROWlayer_type'][n]
            side = info['gROWside'][n]
            if ctx == 'board':
                self.gen.COM(f'affected_layer,name={name},mode=single,affected=yes')
                # self.gen.COM('clip_area_strt')
                # self.gen.COM('clip_area_end,layers_mode=affected_layers,layer=,area=profile,area_type=,inout=outside,contour_cut=no,margin=-2,feat_types=line\;pad\;surface\;arc\;text,ref_layer=')
                self.gen.COM(f'sel_ref_feat,layers={out},use=filter,mode=cover,f_types=line\;pad\;arc\;text\;surface,polarity=positive\;negative,include_syms=,exclude_syms=,pads_as=shape,tolerance=0,negative_union=yes')
                self.gen.COM('get_select_count')
                if int(self.gen.COMANS) > 0:
                    self.gen.COM('sel_delete')
                self.gen.COM(f'affected_layer,name={name},mode=single,affected=no')
        # self.gen.COM('affected_layer,name=,mode=all,affected=no')
        logger.info(f"【{self.raw_job}】完成清理板外物件、外形线")

    def _add_drill_attr(self):
        """添加钻孔属性"""
        logger.info(f"【{self.raw_job}】开始添加镭射、埋孔钻孔属性")
        self.gen.COM('clear_layers')
        self.gen.COM('affected_layer,name=,mode=all,affected=no')
        self.gen.COM('filter_reset,filter_name=popup')
        info = self.gen.DO_INFO(f'-t matrix -e {self.internal_job}/matrix -d ROW -m script')
        for n in range(len(info['gROWname'])):
            name = info['gROWname'][n]
            ctx = info['gROWcontext'][n]
            typ = info['gROWlayer_type'][n]
            side = info['gROWside'][n]
            if ctx == 'board' and typ == 'drill' and re.search(re.compile('^\d+d$|sz'),name):
                self.gen.COM(f'affected_layer,name={name},mode=single,affected=yes')
                self.gen.COM('filter_area_strt')
                self.gen.COM('filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no,lines_only=no,ovals_only=no,min_len=0,max_len=100,min_angle=0,max_angle=0')
                self.gen.COM('get_select_count')
                if int(self.gen.COMANS) > 0:
                    self.gen.COM('cur_atr_set,attribute=.drill,option=via')
                    self.gen.COM('sel_change_atr,mode=replace')
                self.gen.COM(f'affected_layer,name={name},mode=single,affected=no')
        # self.gen.PAUSE('xxxxxxxxxxx')
        logger.info(f"【{self.raw_job}】完成添加镭射、埋孔钻孔属性")

    def _dfm_nfp_removal(self):
        """清理阻焊小开窗，重PAD"""
        logger.info(f"【{self.raw_job}】开始清理阻焊小开窗")
        self.gen.COM('clear_layers')
        self.gen.COM('affected_layer,name=,mode=all,affected=no')
        info = self.gen.DO_INFO(f'-t matrix -e {self.internal_job}/matrix -d ROW -m script')
        sel_mark = False
        for n in range(len(info['gROWname'])):
            layer_name = info['gROWname'][n]
            context = info['gROWcontext'][n]
            gROWlayer_type = info['gROWlayer_type'][n]
            if context == 'board' and gROWlayer_type == 'solder_mask':
                self.gen.COM(f'affected_layer,name={layer_name},mode=single,affected=yes')
                sel_mark = True
        if sel_mark:
            self.gen.COM('chklist_single,action=ezcam_dfm_nfp_removal,show=yes')
            self.gen.COM('chklist_cupd,chklist=ezcam_dfm_nfp_removal,nact=1,params=((pp_layer=.affected)(pp_delete=Duplicate\;Drilled Over\;Covered)(pp_work=Features)(pp_drill=)(pp_non_drilled=No)(pp_in_selected=All)(pp_remove_mark=Remove)),mode=regular')
            self.gen.COM('chklist_run,chklist=ezcam_dfm_nfp_removal,nact=1,area=Global')
            self.gen.COM('chklist_close,chklist=ezcam_dfm_nfp_removal,mode=hide')

        self.gen.COM('clear_layers')
        self.gen.COM('affected_layer,name=,mode=all,affected=no')
        logger.info(f"【{self.raw_job}】完成清理阻焊小开窗")

    def _dispose_npth(self,signal_layer):
        """处理无铜孔"""
        if len(signal_layer) == 0:
            logger.info(f"【{self.raw_job}】 处理无铜孔 | 检测不到线路层")
            return
        drill_layers = self._get_drill_layer()
        if len(drill_layers) == 0:
            logger.info(f"【{self.raw_job}】 处理无铜孔 | 检测不到钻孔层")
            return

        logger.info(f"【{self.raw_job}】 处理无铜孔 | 开始处理")
        self.gen.COM('clear_layers')
        self.gen.COM('affected_layer,name=,mode=all,affected=no')
        self.gen.COM('filter_reset,filter_name=popup')

        npth_drill = 'npth_drill'
        self.delete_layers(npth_drill)

        for n in drill_layers:
            self.gen.COM(f'affected_layer,name={n},mode=single,affected=yes')

        self.gen.COM('filter_atr_set,filter_name=popup,attribute=.drill,condition=yes,text=,option=non_plated,min_int_val=,max_int_val=,min_float_val=,max_float_val=')
        self.gen.COM('filter_area_strt')
        self.gen.COM('filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no,lines_only=no,ovals_only=no,min_len=0,max_len=100,min_angle=0,max_angle=0')
        self.gen.COM('get_select_count')
        if int(self.gen.COMANS) > 0:
            self.gen.COM(f'sel_copy_other,dest=layer_name,target_layer={npth_drill},invert=no,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0,mirror=none,rotation=0')

        self.gen.COM('clear_layers')
        self.gen.COM('affected_layer,name=,mode=all,affected=no')
        self.gen.COM('filter_reset,filter_name=popup')

        if self.gen.DO_INFO(f'-t layer -e {self.internal_job}/{self.run_step}/{npth_drill} -d EXISTS -m script')['gEXISTS'] == 'yes':
            self.gen.COM(f'affected_layer,name={npth_drill},mode=single,affected=yes')
            for k in signal_layer:
                if re.search(re.compile('\d+d'),k):continue
                self.gen.COM(f'sel_copy_other,dest=layer_name,target_layer={k},invert=yes,dx=0,dy=0,size=20,x_anchor=0,y_anchor=0,mirror=none,rotation=0')
            self.gen.COM(f'affected_layer,name={npth_drill},mode=single,affected=no')

        self.delete_layers(npth_drill)
        logger.info(f"【{self.raw_job}】 处理无铜孔 | 处理完成...")

    # ====================== 核心修改：独立 2W / 4W 流程 ======================
    def prepare_common_process(self,m,job):
        """公共前置流程：只执行一次（导入TGZ、清理图层、板型检查、网络比对等）"""
        self.clean_existing_job(job)
        # 如果是自动模式+4W输出，则复制一个料号出来
        if self.is_auto_mode() and m == '4w':
            self.gen.COM(f'copy_entity,type=job,source_job={self.internal_job},source_name={self.internal_job},dest_job={job},dest_name={job},dest_database=ezcam,copy_step_mode=all_layer,lyrs=')
            self.gen.COM(f'check_inout,mode=out,type=job,job={job}')
            self.open_job(job)
            self.open_step(job, self.run_step)
            return

        self.import_job_from_tgz(job)
        self.gen.COM(f'check_inout,mode=out,type=job,job={job}')
        self.open_job(job)
        self.open_step(job, self.run_step)
        self.gen.COM('units,type=inch')
        self.delete_non_board_layers()
        self.check_mask_layers()

        if self.is_auto_mode():
            self.check_board_type()

        if self.mode in ['check','input']:
            # show_error_message("温馨提示", '请认真核对生成的测试点资料是否正确,如有问题,请修正后重新输出...')
            # self.gen.PAUSE('请核对生成的测试点资料是否正确,如有问题,请修正后重新输出...')
            return

        # 网络比对检查
        check_net = True
        if self.gen.DO_INFO(f'-t step -e {self.internal_job}/{self.net_compare_step} -d EXISTS -m script')['gEXISTS'] == 'no':
            self.net_compare_step = 'orig'
            if self.gen.DO_INFO(f'-t step -e {self.internal_job}/{self.net_compare_step} -d EXISTS -m script')['gEXISTS'] == 'no':
                err = f"网络对比STEP不存在"
                if self.is_auto_mode():
                    raise Exception(err)
                else:
                    show_error_message("STEP缺失", "请手动处理网络比对")
                    check_net = False

        if check_net and self.is_auto_mode():
            self.run_net_compare(self.run_step, '工作稿')
            # layer_map = self.import_original_gerber_layers()
            # if layer_map:
            #     self.restore_original_layer_to_workstep(layer_map)
            # else:
            #     self.import_orig()
            self.import_orig()
            self._dfm_nfp_removal()
            self._add_drill_attr()
            self._delete_outside_features()
            self.run_net_compare(self.run_step, '原稿')

    def process_single_mode(self, test_mode,job):
        """单独输出一种模式：2W 或 4W（完全独立）"""
        logger.info(f"\n#################### 执行输出：{test_mode} ####################")
        point = self.create_and_output_test_files(test_mode,job)
        return point

    def get_job_status(self):
        """获取料号状态"""
        try:
            self.init_erp_conn()
            sql = f"""
                SELECT 
                    us.data_id, us.ORG_ID ,US.item_no, us.rev, us.creation_date,us.STATUS  
                FROM 
                    INP.INP_FLYPIN_PROBE_TOOL_ALERT US
                WHERE US.DATA_ID = {self.data_id}
            """
            return self.db_erp.SELECT_DIC(sql)
        except Exception as e:
            logger.error(f"[料号状态] 失败: {str(e)}")
            return []

    def run_full_auto_process(self, operation_class_code=''):
        """
        【已重构】全自动主流程：2W / 4W 完全独立，循环执行
        output_mode = 2w → 只输出2w
        output_mode = 4w → 只输出4w
        output_mode = both → 先2w后4w
        """
        try:
            logger.info("\n==================== 【全自动流程开始】 ====================")
            # 加载参数
            self.load_task_parameters()
            # ====== 1. 获取要输出的模式列表 ======
            if self.output_mode == "2w":
                mode_list = ["2w"]
            elif self.output_mode == "4w":
                mode_list = ["4w"]
            else:
                # both：自动判断流程
                system_mode = self.check_four_line_test_mode()
                if system_mode == "4w":
                    mode_list = ["2w", "4w"]
                else:
                    mode_list = ["2w"]

            for m in mode_list:
                if self.mode not in ['input','check']:
                    # 避免重复生成
                    output_path_network = self.output_2w_path_network
                    if m == '4w':
                        output_path_network = self.output_4w_path_network

                    output_file = output_path_network + '\\' + self.raw_job + '-panel.356'
                    output_file_emm = output_path_network + '\\' + self.raw_job + '-panel.emm'
                    output_file_a = output_path_network + '\\' + self.raw_job + '-panela.356'
                    output_file_a_emm = output_path_network + '\\' + self.raw_job + '-panela.emm'
                    js = self.get_job_status()
                    for p in [output_file, output_file_emm, output_file_a, output_file_a_emm]:
                        if os.path.exists(p):
                            if self.is_auto_mode():
                                if len(js) > 0:
                                    if js[0]['STATUS'] in ['已完成','待转换','待检查']:
                                        if js[0]['STATUS'] == '待检查' and js[0]['TEST_POINT_2W'] == '':
                                            break
                                        return True
                            else:
                                s = show_error_message("温馨提示", f"{self.raw_job} 飞针资料已输出,是否继续？ \n{p}")
                                if s != 16:
                                    return False
                                else:
                                    logger.info(f"【{self.raw_job}】飞针资料已输出,继续输出.")
                                    break

            start_time = datetime.datetime.now()
            # ====== 3. 循环独立输出 2W / 4W ======
            for m in mode_list:
                # ====== 2. 公共准备（只做一次）======
                if m == "2w":
                    start_time_2W = datetime.datetime.now()
                    job = self.internal_job
                    self.prepare_common_process(m,job)
                    test_point = self.process_single_mode(m,job)
                    end_time_2W = datetime.datetime.now()
                    cost_min = round((end_time_2W - start_time_2W).total_seconds() / 60, 2)

                    # if self.mode not in ['input']:
                    self.upload_result_to_database(
                        start_time=start_time,
                        end_time=datetime.datetime.now(),
                        cost_seconds=str(cost_min),
                        test_point=str(test_point),
                        output_mode=m
                    )

                elif m == "4w":
                    start_time_4W = datetime.datetime.now()
                    job = self.internal_job + '-4w'
                    self.prepare_common_process(m,job)
                    test_point = self.process_single_mode(m,job)
                    end_time_4W = datetime.datetime.now()
                    cost_min = round((end_time_4W - start_time_4W).total_seconds() / 60, 2)

                    # if self.mode not in ['input']:
                    self.upload_result_to_database(
                        start_time=start_time,
                        end_time=datetime.datetime.now(),
                        cost_seconds=str(cost_min),
                        test_point=str(test_point),
                        output_mode=m
                    )

            if self.is_auto_mode():
                if '2w' in mode_list:
                    self.clean_existing_job(self.internal_job)
                if '4w' in mode_list:
                    self.clean_existing_job(self.internal_job + '4w')

            # ====== 4. 完成上报 ======
            cost_min = round((datetime.datetime.now() - start_time).total_seconds() / 60, 2)
            logger.info(f"\n流程全部完成 | 总耗时：{cost_min} 分钟")

            if not self.is_auto_mode():
                if self.mode == 'task':
                    show_error_message("完成", f"{self.raw_job} 飞针资料输出完成")
                elif self.mode == 'check':
                    show_error_message("完成", f"{self.raw_job} 飞针资料检查完成")
                elif self.mode == 'input':
                    show_error_message("完成", f"{self.raw_job} 导入资料处理完成")
            return True

        except Exception as e:
            err_msg = str(e)[:120]
            logger.error(f"流程失败：{err_msg}")
            logger.error(traceback.format_exc())
            if self.is_auto_mode():
                self.upload_result_to_database(error_msg=err_msg)
            return False

    def upload_result_to_database(self,is_exist=False,start_time=None,end_time=None,error_msg=None,cost_seconds='',test_point='',output_mode=None):
        """上传处理结果到数据库"""
        try:
            self.init_erp_conn()
            logger.info(f"【{self.raw_job}】上报数据库")

            if error_msg:
                STATUS = '待制作'
                info = self._get_remark(self.data_id)
                if error_msg == info and re.search(re.compile('Invalid argument|when reading a line'), error_msg):
                    sql = f"""
                    UPDATE INP.INP_FLYPIN_PROBE_TOOL_ALERT 
                        SET WRITE_FLAG='Y', remark='{error_msg}', write_date=SYSDATE, write_by='sys_tem', STATUS='{STATUS}', attribute4='0'
                    WHERE data_id={self.data_id}
                    """
                else:
                    sql = f"""
                    UPDATE INP.INP_FLYPIN_PROBE_TOOL_ALERT 
                    SET WRITE_FLAG='Y', remark='{error_msg}', write_date=SYSDATE, write_by='sys_tem', STATUS='{STATUS}'
                    WHERE data_id={self.data_id}
                    """
                self.db_erp.SQL_EXECUTE(sql)
            else:

                start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
                end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

                if output_mode == '2w':
                    output_path = self.output_2w_path_network
                else:
                    output_path = self.output_4w_path_network

                if self.mode in ['input']:
                    if test_point != '':
                        if output_mode == '2w':
                            sql = f"""
                            UPDATE
                                INP.INP_FLYPIN_PROBE_TOOL_ALERT
                            SET
                                TEST_POINT_2W = '{test_point}',
                                LAST_UPDATE_DATE_2W = SYSDATE,
                                LAST_UPDATED_BY_2W = '{self.user_id}'
                            WHERE
                                data_id = {self.data_id}
                            """
                        else:
                            sql = f"""
                            UPDATE
                                INP.INP_FLYPIN_PROBE_TOOL_ALERT
                            SET
                                TEST_POINT_4W = '{test_point}',
                                LAST_UPDATE_DATE_4W = SYSDATE,
                                LAST_UPDATED_BY_4W = '{self.user_id}'
                            WHERE
                                data_id = {self.data_id}
                            """
                    else:
                        return
                elif self.mode in ['check']:
                    STATUS = '待转换'
                    if output_mode == '2w':
                        if test_point != '':
                            sql = f"""
                            UPDATE
                                INP.INP_FLYPIN_PROBE_TOOL_ALERT
                            SET
                                STATUS = '{STATUS}',
                                OUTPUT_PATH_2W = '{output_path}',
                                OUTPUT_BY_2W = '{self.user_id}',
                                OUTPUT_START_2W = TO_DATE('{start_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                OUTPUT_FINISH_TIME_2W = TO_DATE('{end_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                TOTAL_OUTPUT_MS_2W = '{cost_seconds}',
                                TEST_POINT_2W = '{test_point}',
                                LAST_UPDATE_DATE_2W = SYSDATE,
                                LAST_UPDATED_BY_2W = '{self.user_id}',
                                CHECK_BY_2W = '{self.user_id}',
                                CHECK_START_2W = TO_DATE('{start_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                CHECK_FINISH_TIME_2W = TO_DATE('{end_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                TOTAL_CHECK_MS_2W = '{cost_seconds}'
                            WHERE
                                data_id = {self.data_id}
                            """
                        else:
                            sql = f"""
                            UPDATE
                                INP.INP_FLYPIN_PROBE_TOOL_ALERT
                            SET
                                STATUS = '{STATUS}',
                                CHECK_BY_2W = '{self.user_id}',
                                CHECK_START_2W = TO_DATE('{start_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                CHECK_FINISH_TIME_2W = TO_DATE('{end_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                TOTAL_CHECK_MS_2W = '{cost_seconds}'
                            WHERE
                                data_id = {self.data_id}
                            """
                    else:
                        if test_point != '':
                            sql = f"""
                            UPDATE
                                INP.INP_FLYPIN_PROBE_TOOL_ALERT
                            SET
                                STATUS= '{STATUS}',
                                OUTPUT_PATH_4W = '{output_path}',
                                OUTPUT_BY_4W = '{self.user_id}',
                                OUTPUT_START_4W = TO_DATE('{start_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                OUTPUT_FINISH_TIME_4W = TO_DATE('{end_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                TOTAL_OUTPUT_MS_4W = '{cost_seconds}',
                                TEST_POINT_4W = '{test_point}',
                                LAST_UPDATE_DATE_4W = SYSDATE,
                                LAST_UPDATED_BY_4W = '{self.user_id}',
                                CHECK_BY_4W = '{self.user_id}',
                                CHECK_START_4W = TO_DATE('{start_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                CHECK_FINISH_TIME_4W = TO_DATE('{end_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                TOTAL_CHECK_MS_4W = '{cost_seconds}'
                            WHERE
                                data_id = {self.data_id}
                            """
                        else:
                            sql = f"""
                            UPDATE
                                INP.INP_FLYPIN_PROBE_TOOL_ALERT
                            SET
                                STATUS= '{STATUS}',
                                CHECK_BY_4W = '{self.user_id}',
                                CHECK_START_4W = TO_DATE('{start_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                CHECK_FINISH_TIME_4W = TO_DATE('{end_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                TOTAL_CHECK_MS_4W = '{cost_seconds}'
                            WHERE
                                data_id = {self.data_id}
                            """
                else:
                    remark = '已输出' if is_exist else '输出成功，软硬结合板类型' if self.raw_job[12:14] == '23' else '输出成功'
                    STATUS = '待检查'
                    if self.is_auto_mode():
                        if output_mode == '2w':
                            sql = f"""
                            UPDATE
                                INP.INP_FLYPIN_PROBE_TOOL_ALERT
                            SET
                                WRITE_FLAG = 'Y',
                                write_date = SYSDATE,
                                write_by = 'sys_tem',
                                remark = '{remark}',
                                STATUS= '{STATUS}',
                                OUTPUT_PATH_2W = '{output_path}',
                                OUTPUT_BY_2W = '{self.user_id}',
                                OUTPUT_START_2W = TO_DATE('{start_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                OUTPUT_FINISH_TIME_2W = TO_DATE('{end_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                TOTAL_OUTPUT_MS_2W = '{cost_seconds}',
                                TEST_POINT_2W = '{test_point}',
                                LAST_UPDATE_DATE_2W = SYSDATE,
                                LAST_UPDATED_BY_2W = '{self.user_id}'
                            WHERE
                                data_id = {self.data_id}
                            """
                        else:
                            sql = f"""
                            UPDATE
                                INP.INP_FLYPIN_PROBE_TOOL_ALERT
                            SET
                                WRITE_FLAG = 'Y',
                                write_date = SYSDATE,
                                write_by = 'sys_tem',
                                remark = '{remark}',
                                STATUS= '{STATUS}',
                                OUTPUT_PATH_4W = '{output_path}',
                                OUTPUT_BY_4W = '{self.user_id}',
                                OUTPUT_START_4W = TO_DATE('{start_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                OUTPUT_FINISH_TIME_4W = TO_DATE('{end_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                TOTAL_OUTPUT_MS_4W = '{cost_seconds}',
                                TEST_POINT_4W = '{test_point}',
                                LAST_UPDATE_DATE_4W = SYSDATE,
                                LAST_UPDATED_BY_4W = '{self.user_id}'
                            WHERE
                                data_id = {self.data_id}
                            """
                    else:
                        STATUS = '待转换'
                        if output_mode == '2w':
                            sql = f"""
                            UPDATE
                                INP.INP_FLYPIN_PROBE_TOOL_ALERT
                            SET
                                WRITE_FLAG = 'Y',
                                write_date = SYSDATE,
                                write_by = 'sys_tem',
                                remark = '{remark}',
                                STATUS= '{STATUS}',
                                OUTPUT_PATH_2W = '{output_path}',
                                OUTPUT_BY_2W = '{self.user_id}',
                                OUTPUT_START_2W = TO_DATE('{start_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                OUTPUT_FINISH_TIME_2W = TO_DATE('{end_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                TOTAL_OUTPUT_MS_2W = '{cost_seconds}',
                                TEST_POINT_2W = '{test_point}',
                                LAST_UPDATE_DATE_2W = SYSDATE,
                                LAST_UPDATED_BY_2W = '{self.user_id}',
                                CHECK_BY_2W = '{self.user_id}',
                                CHECK_START_2W = TO_DATE('{start_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                CHECK_FINISH_TIME_2W = TO_DATE('{end_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                TOTAL_CHECK_MS_2W = '{cost_seconds}'
                            WHERE
                                data_id = {self.data_id}
                            """
                        else:
                            sql = f"""
                            UPDATE
                                INP.INP_FLYPIN_PROBE_TOOL_ALERT
                            SET
                                WRITE_FLAG = 'Y',
                                write_date = SYSDATE,
                                write_by = 'sys_tem',
                                remark = '{remark}',
                                STATUS= '{STATUS}',
                                OUTPUT_PATH_4W = '{output_path}',
                                OUTPUT_BY_4W = '{self.user_id}',
                                OUTPUT_START_4W = TO_DATE('{start_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                OUTPUT_FINISH_TIME_4W = TO_DATE('{end_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                TOTAL_OUTPUT_MS_4W = '{cost_seconds}',
                                TEST_POINT_4W = '{test_point}',
                                LAST_UPDATE_DATE_4W = SYSDATE,
                                LAST_UPDATED_BY_4W = '{self.user_id}',
                                CHECK_BY_4W = '{self.user_id}',
                                CHECK_START_4W = TO_DATE('{start_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                CHECK_FINISH_TIME_4W = TO_DATE('{end_time_str}','YYYY-MM-DD HH24:MI:SS'),
                                TOTAL_CHECK_MS_4W = '{cost_seconds}'
                            WHERE
                                data_id = {self.data_id}
                            """
            logger.info(sql)
            self.db_erp.SQL_EXECUTE(sql)
            logger.info("上报成功")
        except Exception as e:
            logger.error(f"上报失败：{e}")

    def _get_remark(self,id):
        try:
            self.init_erp_conn()
            sql = f"SELECT remark FROM INP.INP_FLYPIN_PROBE_TOOL_ALERT WHERE DATA_ID='{id}'"
            info = self.db_erp.SELECT_DIC(sql)
            return info[0]['REMARK'] if info else ''
        except:
            return ''

    def run_task(self):
        return self.run_full_auto_process('ET_DATA')


# ======================== 主程序入口 ========================
if __name__ == '__main__':
    exit_code = 1
    job_name = 'none'
    processor = None
    mode = None
    try:
        if len(sys.argv) != 2:
            sys.exit(exit_code)

        params = sys.argv[1].strip().split(',')
        factory_code, data_id, job_name, mode, user_id, output_mode = params[0], params[1], params[2], params[3], params[4], params[5]

        logger = init_task_logger(job_name)
        processor = FlyingProbeCoreProcessor(factory_code, data_id, job_name, mode, user_id, output_mode)
        success = processor.run_task()
        processor.close_all_connections()
        if success:
            exit_code = 0

    except Exception as e:
        if logger:
            logger.error(f"[致命异常] {str(e)}")

    if exit_code == 0:
        with open(f"{os.getcwd()}/{mode}_success.flag", "w", encoding='utf-8') as f:
            f.write("ok")
    else:
        with open(f"{os.getcwd()}/{mode}_fail.flag", "w", encoding='utf-8') as f:
            f.write("fail")

    delayed_exit_clean()
    sys.exit(exit_code)