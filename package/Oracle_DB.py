#!/bin/python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    LiuChuang
# @Mail         :    Chuang_cs@163.com
# @Date         :    2019/01/15
# @Revision     :    1.0.0
# @File         :    MySQL_DB.py
# @Software     :    PyCharm
# @Usefor       :    Oracle连接等操作
# ---------------------------------------------------------#

# --导入Package
import os
import platform
import re
import time

import cx_Oracle

os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'


def rows_as_dicts(cursor):
    """
    转换为字典
    :param cursor:
    :return:
    """
    col_names = [i[0] for i in cursor.description]
    return [dict(zip(col_names, row)) for row in cursor]


# --公用的Class
class ORACLE_INIT:
    __config = {
        'host': "cderpdb-scan.suntakpcb.com",
        'port': 1521,
        'username': "INP",
        'password': "INP",
        # 'database': "EngTechnology",
        'serName': 'prod',
        'charset': "utf8"
    }

    def __init__(self, file=None, tnsName='service_name'):
        # --获取系统类型返回结果“Windows” or "Linux"
        self.dbc = None
        self.tns = None
        self.tnsName = tnsName
        self.system = platform.system()
        self.logFile = file
        # 记录最后一次操作时间，用于检测超时
        self.last_operate_time = None

    # --连接Oracle数据库
    def DB_CONNECT(self, host=__config['host'], servername=__config['serName'],
                   port=__config['port'], username=__config['username'], passwd=__config['password']):
        """
        Oracle数据库连接（增加重连逻辑）
        :param host: 主机名
        :param servername: 服务名
        :param prod: 端口号
        :param username: 登录用户名
        :param passwd: 登录用户密码
        :return: 登录结果
        """
        # 如果已有连接，先尝试关闭
        if self.dbc is not None:
            try:
                self.dbc.close()
            except:
                pass
            self.dbc = None

        try:
            if self.tnsName == 'service_name':
                self.tns = cx_Oracle.makedsn(host, port, service_name=servername)
                self.dbc = cx_Oracle.connect(username, passwd, self.tns, encoding="UTF-8", nencoding="UTF-8")
            else:
                self.tns = cx_Oracle.makedsn(host, port, sid=servername)
                self.dbc = cx_Oracle.connect(username, passwd, self.tns, encoding="UTF-8", nencoding="UTF-8")
            # 设置连接不自动关闭（禁用超时）
            self.dbc.ping()  # 验证连接有效性
            self.last_operate_time = time.time()
            print("Oracle (Host:%s) connection successful !" % host)
        except Exception as e:
            print("Oracle (Host:%s) connection failed !(%s)" % (host, e))
            self.dbc = None
            return None

        # --返回链接
        return self.dbc

    # 新增：检测连接是否有效，无效则自动重连
    def check_connection(self):
        """
        检查连接是否存活，失效则自动重连
        :return: 有效连接对象
        """
        try:
            # 1. 连接为空，直接重连
            if self.dbc is None:
                return self.DB_CONNECT()
            # 2. 检测连接是否存活
            self.dbc.ping()
            self.last_operate_time = time.time()
            return self.dbc
        except (cx_Oracle.DatabaseError, AttributeError):
            # 连接失效，重新连接
            print("Oracle connection lost, try to reconnect...")
            return self.DB_CONNECT()

    # --关闭Oracle
    def DB_CLOSE(self):  # 移除多余的dbc参数，直接使用实例属性
        """
        关闭数据库连接
        :return: None
        """
        if self.dbc is not None:
            try:
                self.dbc.close()
                print("Oracle connection closed successfully")
            except Exception as e:
                print(f"Close Oracle connection failed: {e}")

    # --执行SQL语句
    def SQL_EXECUTE(self, sql):
        """
        执行传入的SQL语句，并返回相关信息（增加连接检测）
        :param sql: 查询的SQL语句
        :return: 当为select开头的SQL时，返回列表；其他语句返回True/False
        """
        # 执行前先检查连接有效性
        self.dbc = self.check_connection()
        if self.dbc is None:
            print("SQL execute failed: no valid database connection")
            return False

        # --定义匹配规则(re.I不区分大小写)
        match_sql = re.compile(r'^(\s+)?(\n+)?select', re.I)
        m = match_sql.search(sql)
        # --执行sql语句
        cursor = None
        try:
            cursor = self.dbc.cursor()
            cursor.execute(sql)
            # --记录更新的SQL列表
            try:
                self.LOG(sql)
            except:
                print(sql)

            # --当匹配通过时（以select开头，并无大小写区分）
            if m:
                sql_info = cursor.fetchall()
                return sql_info if sql_info is not None else []
            else:
                self.dbc.commit()
                return True
        except Exception as e:
            print(f"SQL execute error: {e}, SQL: {sql}")
            if not m:
                try:
                    self.dbc.rollback()
                except:
                    pass
            return [] if m else False
        finally:
            if cursor is not None:
                cursor.close()

    def SELECT_DIC(self, sql):
        """
        使用键值对的方法，由键名字来获取数据，只接收Select开头的sql（增加连接检测）
        :param sql:查询的SQL语句
        :return:以栏位名为key的字典列表，失败返回空列表 []
        """
        # 执行前先检查连接有效性
        self.dbc = self.check_connection()
        if self.dbc is None:
            print("SELECT_DIC failed: no valid database connection")
            return []  # 改为返回空列表，不返回False

        # --定义匹配规则(re.I不区分大小写)
        match_sql = re.compile(r'^(\s+)?(\n+)?select', re.I)
        m = match_sql.search(sql)
        if not m:
            print("SELECT_DIC only support SELECT SQL!")
            return []  # 改为返回空列表

        # --执行sql语句
        cursor = None
        try:
            cursor = self.dbc.cursor()
            cursor.execute(sql)
            # --记录更新的SQL列表
            try:
                self.LOG(sql)
            except:
                print(sql)

            data = rows_as_dicts(cursor)
            # --返回数据（一定是列表）
            return data if data is not None else []
        except Exception as e:
            print(f"SELECT_DIC error: {e}, SQL: {sql}")
            return []  # 异常返回空列表
        finally:
            if cursor is not None:
                cursor.close()

    # --记录日志
    def LOG(self, log_msg):
        """
        记录日志文件至tmp盘
        :param log_msg: 传入的日志信息
        :return: None
        """
        import time
        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

        # --开始执行转换
        try:
            log_msg = (str(now_time) + ":" + log_msg)
        except:
            log_msg = log_msg
        # --打印Log
        print(log_msg)

        # --是否打印至文本
        if self.logFile is not None:
            try:
                with open(self.logFile, 'a', encoding='utf-8') as f:
                    f.write(log_msg + '\n')
            except Exception as e:
                print(f"Write log failed: {e}")


if __name__ == '__main__':
    M = ORACLE_INIT()
    dbc_o = M.DB_CONNECT()
    if dbc_o:
        dataVal = M.SELECT_DIC('SELECT * FROM INP_DFM_PRE_USER')
        print(dataVal)
        M.DB_CLOSE()