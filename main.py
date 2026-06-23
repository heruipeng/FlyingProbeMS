#!/bin/python
# -*- coding: utf-8 -*-
"""
#---------------------------------------------------------#
#               SUNTAK SOFTWARE GROUP                     #
#---------------------------------------------------------#
Author          : rphe
Email           : 502614708@qq.com
CreateTime      : 2026-4-28
ProjectName     : FlyingProbeMS
Description     : 飞针测试资料管理系统（修复详情空白+全局行号）
                  V2.1 - 新增左侧导航菜单 + 报表管理模块
#---------------------------------------------------------#
"""
import os
import re
import subprocess
import sys
import logging
import configparser
from datetime import datetime

import psutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QAbstractItemView,
                             QTableWidget, QTableWidgetItem, QPushButton, QLineEdit,
                             QLabel, QMessageBox, QSpinBox, QHeaderView, QComboBox,
                             QDateEdit, QFrame, QScrollArea, QSizePolicy,
                             QDialog, QFormLayout, QDialogButtonBox,
                             QStackedWidget, QFileDialog, QTabWidget)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QFont, QColor, QIcon
from PyQt5 import QtGui
import icon_rc
from collections import Counter

# 导入Oracle数据库模块
import package.Oracle_DB as Oracle_DB

# ======================== 全局核心配置 ========================
TASK_PROCESS_TIMEOUT = 60
EZFIXTURE_EXE_PATH = r"D:\eastek-server\ezFixtureII\1.1\ezFixtureII.exe"
FP_CORE_SCRIPT_PATH = os.path.join(os.getcwd(), "fp_core_processor.py")
TARGET_PROCESS_NAME = "ezFixtureII.exe"

# ===================== 全局日志配置 =====================
def setup_logger():
    logger = logging.getLogger("FlyPin_Info_Manager")
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    try:
        file_handler = logging.FileHandler("flypin_data.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"日志文件创建失败：{str(e)}")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    return logger

logger = setup_logger()

# ===================== 配置文件路径 =====================
CONFIG_PATH = os.path.join(os.getcwd(), "config.ini")

# ===================== 全局样式与字体规范 =====================
GLOBAL_FONT = QFont("微软雅黑", 9)
BOLD_FONT = QFont("微软雅黑", 9, QFont.Bold)
TITLE_FONT = QFont("微软雅黑", 11, QFont.Bold)
EMPTY_FONT = QFont("微软雅黑", 10)
LARGE_FONT = QFont("微软雅黑", 18, QFont.Bold)

PRIMARY_COLOR = "#409EFF"
PRIMARY_LIGHT = "#ECF5FF"
PRIMARY2_COLOR = "#FFAA00"
GRAY_LIGHT = "#F5F7FA"
GRAY_CARD = "#F8F9FA"
GRAY_BORDER = "#DCDFE6"
GRAY_TEXT_DARK = "#303133"
GRAY_TEXT_NORMAL = "#606266"
GRAY_TEXT_LIGHT = "#909399"
WHITE = "#FFFFFF"
SUCCESS_COLOR = "#67C23A"
DANGER_COLOR = "#F56C6C"
WARNING_COLOR = "#E6A23C"

GLOBAL_STYLE = f"""
QMainWindow{{background-color:{GRAY_LIGHT};}}
QLabel{{color:{GRAY_TEXT_DARK};font-family:微软雅黑;}}
QFrame{{font-family:微软雅黑;}}
QScrollArea{{border:none;background-color:{WHITE};border-radius:6px;}}
QScrollBar:vertical{{width:8px;background:{GRAY_LIGHT};border-radius:4px;}}
QScrollBar::handle:vertical{{background:{GRAY_BORDER};border-radius:4px;min-height:20px;}}
QScrollBar::handle:vertical:hover{{background:{PRIMARY_COLOR};}}
"""

TABLE_GLOBAL_STYLE = f"""
QTableWidget{{background:{WHITE};border:1px solid {GRAY_BORDER};border-radius:8px;gridline-color:{GRAY_BORDER};outline:none;}}
QTableWidget::item{{height:38px;padding:2px;}}
QTableWidget::item:selected {{background-color: #8d8ec8;color:{GRAY_TEXT_DARK};}}
QTableWidget::focus {{outline: none;}}
"""

HEADER_GLOBAL_STYLE = f"""
QHeaderView::section {{
    background: linear-gradient(#f6f7f9, #eef0f3);
    border:none; border-bottom:1px solid {GRAY_BORDER}; border-right:1px solid {GRAY_BORDER};
    font-weight:bold; color:{GRAY_TEXT_DARK}; height:40px; font-size:9pt; text-align:center;
}}
"""

BUTTON_NORMAL_STYLE = f"""
QPushButton{{border:1px solid {GRAY_BORDER};border-radius:4px;background-color:{WHITE};color:{GRAY_TEXT_DARK};font-family:微软雅黑;}}
QPushButton:hover{{border-color:{PRIMARY_COLOR};color:{PRIMARY_COLOR};}}
QPushButton:pressed{{background-color:{PRIMARY_LIGHT};}}
"""

BUTTON_PRIMARY_STYLE = f"""
QPushButton{{background:{PRIMARY_COLOR};color:{WHITE};border:none;border-radius:6px;font-family:微软雅黑;}}
QPushButton:hover{{background:#337ecc;}}
QPushButton:pressed{{background:#2b6cb0;}}
QPushButton:disabled{{background:#b3d8ff;color:#e6f2ff;}}
"""

BUTTON_WARN_STYLE = f"""
QPushButton{{background:{PRIMARY2_COLOR};color:#fff;border:none;border-radius:6px;font-family:微软雅黑;}}
QPushButton:hover{{background:#e68a00;}}
QPushButton:pressed{{background:#cc7a00;}}
QPushButton:disabled{{background:#ffe0b3;color:#fff7e6;}}
"""

BUTTON_SUCCESS_STYLE = f"""
QPushButton{{background:#67C23A;color:#fff;border:none;border-radius:6px;font-family:微软雅黑;}}
QPushButton:hover{{background:#529b2c;}}
QPushButton:pressed{{background:#458b24;}}
QPushButton:disabled{{background:#d9f7be;color:#f0ffe6;}}
"""

INPUT_NORMAL_STYLE = f"""
QLineEdit,QComboBox,QDateEdit{{border:1px solid {GRAY_BORDER};border-radius:6px;padding-left:10px;font-family:微软雅黑;color:{GRAY_TEXT_DARK};}}
QLineEdit:focus,QComboBox:focus,QDateEdit:focus{{border:1px solid {PRIMARY_COLOR};}}
"""

# ===================== 侧边栏导航样式 =====================
SIDEBAR_STYLE = f"""
QFrame#sidebar {{
    background: {WHITE};
    border: 1px solid {GRAY_BORDER};
    border-radius: 8px;
}}
"""

NAV_BTN_NORMAL = f"""
QPushButton {{
    background: {WHITE};
    color: {GRAY_TEXT_DARK};
    border: none;
    border-bottom: 1px solid {GRAY_BORDER};
    border-radius: 0px;
    font-family: 微软雅黑;
    font-size: 11pt;
    font-weight: bold;
    text-align: left;
    padding: 16px 20px;
}}
QPushButton:hover {{
    background: {PRIMARY_LIGHT};
    color: {PRIMARY_COLOR};
}}
QPushButton:checked {{
    background: {PRIMARY_LIGHT};
    color: {PRIMARY_COLOR};
    border-left: 3px solid {PRIMARY_COLOR};
}}
"""

SIDEBAR_HEADER_STYLE = f"""
QLabel {{
    color: {PRIMARY_COLOR};
    font-family: 微软雅黑;
    font-size: 13pt;
    font-weight: bold;
    padding: 16px 20px;
}}
"""

# ===================== 报表子标签样式 =====================
REPORT_TAB_BTN = f"""
QPushButton {{
    background: {WHITE};
    color: {GRAY_TEXT_NORMAL};
    border: none;
    border-bottom: 2px solid transparent;
    font-family: 微软雅黑;
    font-size: 10pt;
    font-weight: bold;
    padding: 10px 24px;
}}
QPushButton:hover {{
    color: {PRIMARY_COLOR};
}}
QPushButton:checked {{
    color: {PRIMARY_COLOR};
    border-bottom: 2px solid {PRIMARY_COLOR};
}}
"""

# ===================== 工厂映射配置 =====================
FACTORY_MAP = {"江门一厂": "85", "江门二厂": "107", "珠海一厂": "168", "珠海二厂": "228", "金州工厂": "84"}
FACTORY_MAP_NUM = {"JM1": "85", "JM2": "107", "ZH1": "168", "ZH2": "228", "DL": "84"}
FACTORY_ID_TO_NAME = {v: k for k, v in FACTORY_MAP.items()}
FACTORY_ID_TO_NUM = {v: k for k, v in FACTORY_MAP_NUM.items()}

def safe_kill_process(process_name):
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", process_name],
            capture_output=True,
            creationflags=0x08000000  # 隐藏cmd黑窗口
        )
    except:
        pass

# ===================== 配置读写工具 =====================
def save_config(factory, status, operation):
    try:
        conf = configparser.ConfigParser()
        conf["USER_SETTINGS"] = {"factory": factory, "status": status, "operation": operation}
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            conf.write(f)
    except:
        pass

def load_config():
    conf = configparser.ConfigParser()
    df, ds, dop = "江门二厂", "全部状态", "全部工序"
    if os.path.exists(CONFIG_PATH):
        try:
            conf.read(CONFIG_PATH, encoding="utf-8")
            df = conf.get("USER_SETTINGS", "factory", fallback=df)
            ds = conf.get("USER_SETTINGS", "status", fallback=ds)
            dop = conf.get("USER_SETTINGS", "operation", fallback=dop)
        except:
            pass
    return df, ds, dop


# ===================== 统计卡片组件 =====================
class StatCard(QFrame):
    """通用统计卡片"""
    def __init__(self, title, value="0", color=PRIMARY_COLOR, icon="📊", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: {WHITE};
                border: 1px solid {GRAY_BORDER};
                border-radius: 10px;
            }}
            QFrame:hover {{
                border-color: {color};
            }}
        """)
        self.setMinimumHeight(72)
        self.setMinimumWidth(95)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        title_layout = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("微软雅黑", 13))
        title_layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setFont(GLOBAL_FONT)
        title_label.setStyleSheet(f"color:{GRAY_TEXT_LIGHT};")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        self.value_label = QLabel(str(value))
        self.value_label.setFont(QFont("微软雅黑", 16, QFont.Bold))
        self.value_label.setStyleSheet(f"color:{color};")
        self.value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.value_label)

        # 双行值（默认隐藏）
        self.value_label2 = QLabel("")
        self.value_label2.setFont(QFont("微软雅黑", 11, QFont.Bold))
        self.value_label2.setStyleSheet(f"color:{color};")
        self.value_label2.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.value_label2.hide()
        layout.addWidget(self.value_label2)

    def set_value(self, val):
        self.value_label.setText(str(val))
        self.value_label2.hide()

    def set_double_value(self, line1, line2):
        self.value_label.setFont(QFont("微软雅黑", 12, QFont.Bold))
        self.value_label.setText(str(line1))
        self.value_label2.setFont(QFont("微软雅黑", 12, QFont.Bold))
        self.value_label2.setText(str(line2))
        self.value_label2.show()


# ===================== 主界面 =====================
class FlyPinWindow(QMainWindow):
    def __init__(self, login_user, user_name, soft_name, soft_ver, release_date, developer, copyright_info):
        super().__init__()
        self.init_oracle_env()
        self.LOGIN_USER = login_user
        self.USER_NAME = user_name
        self.SOFTWARE_NAME = soft_name
        self.SOFTWARE_VERSION = soft_ver
        self.release_date = release_date
        self.DEVELOPER = developer
        self.COPYRIGHT_INFO = copyright_info
        self.last_factory, self.last_status, self.last_operation = load_config()
        self.page_size = 20
        self.current_page = 1
        self.raw_cache_data = []
        self.filtered_data = []
        self._combo_ = []
        self.db = None

        self.current_org_id = ""
        self.current_did = ""
        self.current_pn = ""
        self.current_status = ""
        self.current_test_point = ''
        self.current_2w_test_point = ''
        self.current_4w_test_point = ''

        # 报表相关
        self.report_data = []
        self.report_page = 1
        self.report_page_size = 20

        self.init_database()
        self._get_user_name()
        self.init_ui()
        self.load_raw_data_from_db()
        self.filter_data_in_memory()
        self.load_operation_list()
        self.update_table_and_pagination()

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.force_refresh_data)

    def _get_user_name(self):
        """获取用户名"""
        sql = f"""
        SELECT
            u.USER_ID ,
            u.USER_NAME
        FROM
            INP.INP_FLYPIN_USER u"""
        db = self.init_erp_database_connection()
        info = db.SELECT_DIC(sql) if db else []
        self.user_name = {}
        self.user_name_id = {}
        for n in info:
            self.user_name.update({
                n['USER_ID']:n['USER_NAME']
            })
            self.user_name_id.update({
                n['USER_NAME']: n['USER_ID']
            })

    def init_oracle_env(self):
        try:
            p = os.getenv('PATH', '')
            pl = [x for x in p.split(';') if x.strip() and not re.search(r'instantclient|python', x, re.I)]
            op = os.path.join(os.getcwd(), 'instantclient_19_21')
            if os.path.exists(op):
                pl.append(op)
                os.putenv('PATH', ';'.join(pl))
        except:
            pass

    def init_database(self):
        if Oracle_DB is None:
            return
        try:
            self.db = Oracle_DB.ORACLE_INIT()
            self.db.DB_CONNECT()
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库初始化失败：{str(e)}")

    # ==================== 主界面（侧边导航 + StackedWidget 布局）====================
    def init_ui(self):
        now = datetime.now().strftime("%Y-%m-%d")
        self.setWindowTitle(f"{self.SOFTWARE_NAME} {self.SOFTWARE_VERSION} | {now}  当前用户:{self.USER_NAME}")
        self.resize(1600, 800)
        self.setMinimumSize(1400, 600)
        self.setFont(GLOBAL_FONT)
        self.setStyleSheet(GLOBAL_STYLE)

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/logo/image/logo.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # ========== 左侧导航菜单（自定义侧边栏）==========
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet(SIDEBAR_STYLE)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # 顶部标题
        header_label = QLabel("📋 导航菜单")
        header_label.setStyleSheet(SIDEBAR_HEADER_STYLE)
        header_label.setFixedHeight(52)
        sidebar_layout.addWidget(header_label)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"QFrame{{color:{GRAY_BORDER};margin:0 20px;}}")
        sidebar_layout.addWidget(sep)

        # 导航按钮
        self.btn_nav_task = QPushButton("📋  任务管理")
        self.btn_nav_report = QPushButton("📊  报表管理")

        self.btn_nav_task.setCheckable(True)
        self.btn_nav_report.setCheckable(True)
        self.btn_nav_task.setChecked(True)

        self.btn_nav_task.setFixedHeight(50)
        self.btn_nav_report.setFixedHeight(50)

        self.btn_nav_task.setStyleSheet(NAV_BTN_NORMAL)
        self.btn_nav_report.setStyleSheet(NAV_BTN_NORMAL)

        # 导航按钮组（互斥）
        self.nav_buttons = [self.btn_nav_task, self.btn_nav_report]
        for i, btn in enumerate(self.nav_buttons):
            btn.clicked.connect(lambda checked, idx=i: self.on_nav_clicked(idx))

        sidebar_layout.addWidget(self.btn_nav_task)
        sidebar_layout.addWidget(self.btn_nav_report)
        sidebar_layout.addStretch()

        # # 底部版权
        # footer_label = QLabel(f"<div style='text-align:center;line-height:1.4;'>"
        #                       f"<span style='font-size:8pt;color:{GRAY_TEXT_LIGHT};'>{self.SOFTWARE_NAME}</span><br>"
        #                       f"<span style='font-size:8pt;color:{GRAY_TEXT_LIGHT};'>V{self.SOFTWARE_VERSION}</span></div>")
        # footer_label.setFixedHeight(50)
        # footer_label.setAlignment(Qt.AlignCenter)
        # sidebar_layout.addWidget(footer_label)

        # 底部版权
        info_text = f"""<div style='line-height:1.5;'>
                        <span style='font-size:10pt; font-weight:bold; color:{PRIMARY_COLOR};'>{self.SOFTWARE_NAME}{self.SOFTWARE_VERSION}</span><br/>
                        <span style='font-size:9pt; color:{GRAY_TEXT_LIGHT};'>开发者：{self.DEVELOPER} <br/>发布时间：{self.release_date}</span><br/>
                        <span style='font-size:9pt; color:{GRAY_TEXT_LIGHT};'>{self.COPYRIGHT_INFO}</span></div>
                        """
        bottom_label = QLabel(info_text)
        bottom_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(bottom_label)

        # ========== 右侧 QStackedWidget 页面容器 ==========
        self.stacked = QStackedWidget()
        self.stacked.setStyleSheet(f"QStackedWidget{{background:{GRAY_LIGHT};}}")

        # 任务管理页面（原有全部功能）
        self.task_page = self.create_task_page()
        self.stacked.addWidget(self.task_page)

        # 报表管理页面（新增）
        self.report_page = self.create_report_page()
        self.stacked.addWidget(self.report_page)

        # 组装布局
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.stacked)

    def on_nav_clicked(self, index):
        """导航菜单切换"""
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        self.stacked.setCurrentIndex(index)
        if index == 1:
            self.refresh_report()

    # ==================== 任务管理页面 ====================
    def create_task_page(self):
        page = QWidget()
        page.setStyleSheet(f"background:{GRAY_LIGHT};")
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # 搜索区域
        search_frame = QFrame()
        search_frame.setStyleSheet(f"QFrame{{background:{WHITE};border-radius:8px;border:1px solid {GRAY_BORDER};}}")
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(16, 12, 16, 12)
        search_layout.setSpacing(12)

        self.le_search = QLineEdit()
        self.le_search.setPlaceholderText("料号")
        self.le_search.setMinimumHeight(34)
        self.le_search.setStyleSheet(INPUT_NORMAL_STYLE)

        self.cb_factory = QComboBox()
        self.cb_factory.addItems(FACTORY_MAP.keys())
        self.cb_factory.setCurrentText(self.last_factory)
        self.cb_factory.setFixedWidth(110)
        self.cb_factory.setMinimumHeight(34)
        self.cb_factory.setStyleSheet(INPUT_NORMAL_STYLE)

        self.cb_status = QComboBox()
        self.cb_status.addItems(["全部状态", "待后台处理", "待制作", "待检查", "待转换", "待上传ERP", "已完成"])
        self.cb_status.setCurrentText(self.last_status)
        self.cb_status.setFixedWidth(110)
        self.cb_status.setMinimumHeight(34)

        self.cb_operation = QComboBox()
        self.cb_operation.addItem("全部工序")
        self.cb_operation.setCurrentText(self.last_operation)
        self.cb_operation.setFixedWidth(130)
        self.cb_operation.setMinimumHeight(34)
        self.cb_operation.setStyleSheet(INPUT_NORMAL_STYLE)

        self.date_start = QDateEdit()
        self.date_end = QDateEdit()
        self.date_start.setDate(QDate.currentDate().addDays(-10))
        self.date_end.setDate(QDate.currentDate())
        self.date_start.setDisplayFormat("yyyy-MM-dd")
        self.date_end.setDisplayFormat("yyyy-MM-dd")
        self.date_start.setFixedWidth(125)
        self.date_start.setMinimumHeight(34)
        self.date_end.setFixedWidth(125)
        self.date_end.setMinimumHeight(34)
        self.date_start.setCalendarPopup(True)
        self.date_end.setCalendarPopup(True)
        self.date_start.setStyleSheet(INPUT_NORMAL_STYLE)
        self.date_end.setStyleSheet(INPUT_NORMAL_STYLE)

        self.btn_search = QPushButton("🔍 查询")
        self.btn_refresh = QPushButton("🔄 刷新")
        self.btn_search.setMinimumHeight(34)
        self.btn_refresh.setMinimumHeight(34)
        self.btn_search.setFixedWidth(100)
        self.btn_refresh.setFixedWidth(100)
        self.btn_search.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_refresh.setStyleSheet(BUTTON_PRIMARY_STYLE)

        search_items = [
            (QLabel("关键字："), self.le_search),
            (QLabel("工厂："), self.cb_factory),
            (QLabel("状态："), self.cb_status),
            (QLabel("工序："), self.cb_operation),
            (QLabel("日期："), self.date_start),
            (QLabel("到"), self.date_end),
            (None, self.btn_search),
            (None, self.btn_refresh)
        ]
        for label, widget in search_items:
            if label:
                label.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
                label.setFont(GLOBAL_FONT)
                search_layout.addWidget(label)
            search_layout.addWidget(widget)
        search_layout.addStretch()
        layout.addWidget(search_frame)

        # 主体布局（表格 + 详情）
        content_layout = QHBoxLayout()
        left_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setFont(GLOBAL_FONT)
        self.headers = ["DATA_ID", "厂区", "料号", "版本", "在线工序", "创建时间", "状态", "备注",
                        "2W输出路径", "2W输出人", "2W输出开始时间", "2W输出完成时间", "2W输出总耗时", "2W测试点", "2W检查人", "2W检查开始时间","2W检查完成时间","2W检查总耗时","2W最后更新时间","2W最后更新人",
                        "4W输出路径", "4W输出人", "4W输出开始时间", "4W输出完成时间", "4W输出总耗时", "4W测试点", "4W检查人", "4W检查开始时间","4W检查完成时间","4W检查总耗时","4W最后更新时间","4W最后更新人",
                        ]
        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)

        col_width = {0:75,1:85,2:140,3:60,4:110,5:140,6:80,7:200,8:0,9:0,10:0,11:0,12:0,13:0,14:0,15:0,16:0,17:0,18:0,19:0,20:0,21:0,22:0,23:0,24:0,25:0,26:0,27:0,28:0,29:0,30:0,31:0}
        hh = self.table.horizontalHeader()
        for c, w in col_width.items():
            hh.setSectionResizeMode(c, QHeaderView.Interactive)
            self.table.setColumnWidth(c, w)
        hh.setStretchLastSection(True)

        for col in range(8, self.table.columnCount()):
            self.table.setColumnHidden(col, True)

        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setStyleSheet(TABLE_GLOBAL_STYLE)
        self.table.horizontalHeader().setStyleSheet(HEADER_GLOBAL_STYLE)
        self.table.itemSelectionChanged.connect(self.update_detail)
        left_layout.addWidget(self.table)

        # 分页
        page_frame = QFrame()
        page_frame.setStyleSheet(f"QFrame{{background:{WHITE};border-radius:8px;border:1px solid {GRAY_BORDER};}}")
        page_layout = QHBoxLayout(page_frame)
        page_layout.setContentsMargins(15,10,15,10)

        self.btn_first = QPushButton("首页")
        self.btn_prev = QPushButton("上一页")
        self.btn_next = QPushButton("下一页")
        self.btn_last = QPushButton("尾页")
        self.spin_page = QSpinBox()
        self.spin_page.setFixedWidth(65)
        self.lab_page = QLabel("总页数：0")
        self.lab_count = QLabel("总数据：0 条")

        for btn in [self.btn_first, self.btn_prev, self.btn_next, self.btn_last]:
            btn.setFixedSize(75,30)
            btn.setStyleSheet(BUTTON_NORMAL_STYLE)
            btn.setFont(GLOBAL_FONT)

        page_layout.addStretch()
        page_layout.addWidget(self.btn_first)
        page_layout.addWidget(self.btn_prev)
        page_layout.addWidget(self.btn_next)
        page_layout.addWidget(self.btn_last)
        page_layout.addSpacing(15)
        page_layout.addWidget(QLabel("页码："))
        page_layout.addWidget(self.spin_page)
        page_layout.addSpacing(15)
        page_layout.addWidget(self.lab_page)
        page_layout.addSpacing(15)
        page_layout.addWidget(self.lab_count)
        page_layout.addStretch()
        left_layout.addWidget(page_frame)
        content_layout.addLayout(left_layout, stretch=70)

        # 右侧详情面板
        detail_frame = QFrame()
        detail_frame.setStyleSheet(f"QFrame{{background:{WHITE};border-radius:8px;border:1px solid {GRAY_BORDER};}}")
        detail_frame.setFixedWidth(400)
        detail_layout = QVBoxLayout(detail_frame)
        detail_layout.setContentsMargins(0,0,0,0)
        detail_layout.setSpacing(0)

        # 标题栏
        title_frame = QFrame()
        title_frame.setStyleSheet(f"QFrame{{background:{PRIMARY_LIGHT};border-top-left-radius:8px;border-top-right-radius:8px;border-bottom:1px solid {GRAY_BORDER};}}")
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(15,12,15,12)
        lab_title = QLabel("📋 资料详情信息")
        lab_title.setFont(TITLE_FONT)
        lab_title.setAlignment(Qt.AlignCenter)
        lab_title.setStyleSheet(f"color:{PRIMARY_COLOR};")
        title_layout.addWidget(lab_title)
        detail_layout.addWidget(title_frame)

        # ===== Tab Widget: 2W资料 / 4W资料 =====
        self.detail_tabs = QTabWidget()
        self.detail_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {WHITE};
            }}
            QTabBar::tab {{
                padding: 10px 24px;
                font-family: 微软雅黑;
                font-size: 10pt;
                font-weight: bold;
                color: {GRAY_TEXT_NORMAL};
                background: {GRAY_LIGHT};
                border: 1px solid {GRAY_BORDER};
                border-bottom: 2px solid {GRAY_BORDER};
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            QTabBar::tab:selected {{
                color: {PRIMARY_COLOR};
                background: {WHITE};
                border-bottom: 2px solid {PRIMARY_COLOR};
            }}
            QTabBar::tab:hover {{
                color: {PRIMARY_COLOR};
            }}
        """)

        # ----- 2W资料 Tab -----
        self.tab_2w = QWidget()
        tab_2w_layout = QVBoxLayout(self.tab_2w)
        tab_2w_layout.setContentsMargins(0, 0, 0, 0)
        tab_2w_layout.setSpacing(0)

        # 2W 按钮栏
        btn_2w_frame = QFrame()
        btn_2w_frame.setStyleSheet(f"QFrame{{border-bottom:1px solid {GRAY_BORDER};}}")
        btn_2w_layout = QHBoxLayout(btn_2w_frame)
        btn_2w_layout.setContentsMargins(12, 10, 12, 10)
        btn_2w_layout.setSpacing(8)
        self.btn_2w_output = QPushButton("📤 输出")
        self.btn_2w_check = QPushButton("📋 检查")
        self.btn_2w_input = QPushButton("📋 导入")
        self.btn_2w_convert = QPushButton("🔄 转换")
        for b in [self.btn_2w_output, self.btn_2w_check, self.btn_2w_input, self.btn_2w_convert]:
            b.setFixedSize(85, 34)
        self.btn_2w_output.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_2w_check.setStyleSheet(BUTTON_WARN_STYLE)
        self.btn_2w_input.setStyleSheet(BUTTON_WARN_STYLE)
        self.btn_2w_convert.setStyleSheet(BUTTON_SUCCESS_STYLE)
        btn_2w_layout.addWidget(self.btn_2w_output)
        btn_2w_layout.addWidget(self.btn_2w_check)
        btn_2w_layout.addWidget(self.btn_2w_input)
        btn_2w_layout.addWidget(self.btn_2w_convert)
        btn_2w_layout.addStretch()
        tab_2w_layout.addWidget(btn_2w_frame)

        # 2W 输出文件路径
        path_2w_frame = QFrame()
        path_2w_frame.setStyleSheet(f"QFrame{{background:{GRAY_CARD};border-bottom:1px solid {GRAY_BORDER};}}")
        path_2w_layout = QHBoxLayout(path_2w_frame)
        path_2w_layout.setContentsMargins(12, 8, 12, 8)
        path_2w_layout.setSpacing(6)
        lbl_2w_path = QLabel("输出文件路径：")
        lbl_2w_path.setFont(BOLD_FONT)
        lbl_2w_path.setStyleSheet(f"color:{GRAY_TEXT_NORMAL};")
        self.lbl_2w_path_val = QLabel("未选择")
        self.lbl_2w_path_val.setStyleSheet(f"color:{GRAY_TEXT_DARK};")
        self.lbl_2w_path_val.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_2w_path_val.setWordWrap(True)
        self.btn_2w_open_path = QPushButton("📂")
        self.btn_2w_open_path.setFixedSize(30, 26)
        self.btn_2w_open_path.setStyleSheet(BUTTON_PRIMARY_STYLE)
        path_2w_layout.addWidget(lbl_2w_path)
        path_2w_layout.addWidget(self.lbl_2w_path_val, stretch=1)
        path_2w_layout.addWidget(self.btn_2w_open_path)
        tab_2w_layout.addWidget(path_2w_frame)

        # 2W 详情滚动区
        self.scroll_2w = QScrollArea()
        self.scroll_2w.setWidgetResizable(True)
        self.scroll_content_2w = QWidget()
        self.scroll_layout_2w = QVBoxLayout(self.scroll_content_2w)
        self.scroll_layout_2w.setSpacing(6)
        self.scroll_layout_2w.setContentsMargins(12, 12, 12, 12)
        self.scroll_layout_2w.setAlignment(Qt.AlignTop)
        self.scroll_2w.setWidget(self.scroll_content_2w)
        tab_2w_layout.addWidget(self.scroll_2w, stretch=1)

        # 2W 上传ERP按钮
        upload_2w_frame = QFrame()
        upload_2w_frame.setStyleSheet(f"QFrame{{border-top:1px solid {GRAY_BORDER};}}")
        upload_2w_layout = QHBoxLayout(upload_2w_frame)
        upload_2w_layout.setContentsMargins(12, 10, 12, 10)
        self.btn_2w_upload = QPushButton("📤 上传ERP")
        self.btn_2w_upload.setFixedHeight(34)
        self.btn_2w_upload.setStyleSheet(BUTTON_PRIMARY_STYLE)
        upload_2w_layout.addWidget(self.btn_2w_upload)
        # tab_2w_layout.addWidget(upload_2w_frame)
        detail_layout.addWidget(upload_2w_frame)

        self.detail_tabs.addTab(self.tab_2w, "🔹 2W资料")

        # ----- 4W资料 Tab -----
        self.tab_4w = QWidget()
        tab_4w_layout = QVBoxLayout(self.tab_4w)
        tab_4w_layout.setContentsMargins(0, 0, 0, 0)
        tab_4w_layout.setSpacing(0)

        # 4W 按钮栏
        btn_4w_frame = QFrame()
        btn_4w_frame.setStyleSheet(f"QFrame{{border-bottom:1px solid {GRAY_BORDER};}}")
        btn_4w_layout = QHBoxLayout(btn_4w_frame)
        btn_4w_layout.setContentsMargins(12, 10, 12, 10)
        btn_4w_layout.setSpacing(8)
        self.btn_4w_output = QPushButton("📤 输出")
        self.btn_4w_check = QPushButton("📋 检查")
        self.btn_4w_input = QPushButton("📋 导入")
        self.btn_4w_convert = QPushButton("🔄 转换")
        for b in [self.btn_4w_output, self.btn_4w_check, self.btn_4w_input, self.btn_4w_convert]:
            b.setFixedSize(85, 34)
        self.btn_4w_output.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_4w_check.setStyleSheet(BUTTON_WARN_STYLE)
        self.btn_4w_input.setStyleSheet(BUTTON_WARN_STYLE)
        self.btn_4w_convert.setStyleSheet(BUTTON_SUCCESS_STYLE)
        btn_4w_layout.addWidget(self.btn_4w_output)
        btn_4w_layout.addWidget(self.btn_4w_check)
        btn_4w_layout.addWidget(self.btn_4w_input)
        btn_4w_layout.addWidget(self.btn_4w_convert)
        btn_4w_layout.addStretch()
        tab_4w_layout.addWidget(btn_4w_frame)

        # 4W 输出文件路径
        path_4w_frame = QFrame()
        path_4w_frame.setStyleSheet(f"QFrame{{background:{GRAY_CARD};border-bottom:1px solid {GRAY_BORDER};}}")
        path_4w_layout = QHBoxLayout(path_4w_frame)
        path_4w_layout.setContentsMargins(12, 8, 12, 8)
        path_4w_layout.setSpacing(6)
        lbl_4w_path = QLabel("输出文件路径：")
        lbl_4w_path.setFont(BOLD_FONT)
        lbl_4w_path.setStyleSheet(f"color:{GRAY_TEXT_NORMAL};")
        self.lbl_4w_path_val = QLabel("未选择")
        self.lbl_4w_path_val.setStyleSheet(f"color:{GRAY_TEXT_DARK};")
        self.lbl_4w_path_val.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lbl_4w_path_val.setWordWrap(True)
        self.btn_4w_open_path = QPushButton("📂")
        self.btn_4w_open_path.setFixedSize(30, 26)
        self.btn_4w_open_path.setStyleSheet(BUTTON_PRIMARY_STYLE)
        path_4w_layout.addWidget(lbl_4w_path)
        path_4w_layout.addWidget(self.lbl_4w_path_val, stretch=1)
        path_4w_layout.addWidget(self.btn_4w_open_path)
        tab_4w_layout.addWidget(path_4w_frame)

        # 4W 详情滚动区
        self.scroll_4w = QScrollArea()
        self.scroll_4w.setWidgetResizable(True)
        self.scroll_content_4w = QWidget()
        self.scroll_layout_4w = QVBoxLayout(self.scroll_content_4w)
        self.scroll_layout_4w.setSpacing(6)
        self.scroll_layout_4w.setContentsMargins(12, 12, 12, 12)
        self.scroll_layout_4w.setAlignment(Qt.AlignTop)
        self.scroll_4w.setWidget(self.scroll_content_4w)
        tab_4w_layout.addWidget(self.scroll_4w, stretch=1)

        # # 4W 上传ERP按钮
        # upload_4w_frame = QFrame()
        # upload_4w_frame.setStyleSheet(f"QFrame{{border-top:1px solid {GRAY_BORDER};}}")
        # upload_4w_layout = QHBoxLayout(upload_4w_frame)
        # upload_4w_layout.setContentsMargins(12, 10, 12, 10)
        # self.btn_4w_upload = QPushButton("📤 上传ERP")
        # self.btn_4w_upload.setFixedHeight(34)
        # self.btn_4w_upload.setStyleSheet(BUTTON_PRIMARY_STYLE)
        # upload_4w_layout.addWidget(self.btn_4w_upload)
        # tab_4w_layout.addWidget(upload_4w_frame)

        self.detail_tabs.addTab(self.tab_4w, "🔸 4W资料")

        detail_layout.addWidget(self.detail_tabs, stretch=1)

        # 保持兼容：旧引用指向新控件
        self.btn_output = self.btn_2w_output
        self.btn_4w_out = self.btn_4w_output
        self.btn_check = self.btn_2w_check
        self.btn_input = self.btn_2w_input
        self.btn_convert = self.btn_2w_convert
        self.scroll_area = self.scroll_2w
        self.scroll_layout = self.scroll_layout_2w
        self.upload_data = self.btn_2w_upload
        self.scroll_content = self.scroll_content_2w

        content_layout.addWidget(detail_frame, stretch=30)
        layout.addLayout(content_layout)

        # # 底部版权
        # info_text = f"""<div style='line-height:1.5;'>
        #         <span style='font-size:10pt; font-weight:bold; color:{PRIMARY_COLOR};'>{self.SOFTWARE_NAME} {self.SOFTWARE_VERSION}</span><br/>
        #         <span style='font-size:9pt; color:{GRAY_TEXT_LIGHT};'>{self.COPYRIGHT_INFO}</span><br/>
        #         <span style='font-size:9pt; color:{GRAY_TEXT_LIGHT};'>开发者：{self.DEVELOPER} | 发布时间：{self.release_date}</span></div>
        #         """
        # bottom_label = QLabel(info_text)
        # bottom_label.setAlignment(Qt.AlignCenter)
        # layout.addWidget(bottom_label)

        # 绑定事件
        self.btn_search.clicked.connect(self.do_search)
        self.btn_refresh.clicked.connect(self.force_refresh_data)
        self.le_search.returnPressed.connect(self.do_search)
        self.btn_first.clicked.connect(lambda: self.switch_page(1))
        self.btn_prev.clicked.connect(lambda: self.switch_page(self.current_page-1))
        self.btn_next.clicked.connect(lambda: self.switch_page(self.current_page+1))
        self.btn_last.clicked.connect(lambda: self.switch_page(self.total_page))
        self.spin_page.editingFinished.connect(lambda: self.switch_page(self.spin_page.value()))
        self.cb_factory.currentTextChanged.connect(self.on_factory_changed)
        self.cb_status.currentTextChanged.connect(self.do_search)
        self.cb_operation.currentTextChanged.connect(self.do_search)

        self.btn_2w_output.clicked.connect(self.do_2w_make)
        self.btn_2w_check.clicked.connect(self.do_2w_check)
        self.btn_2w_input.clicked.connect(self.do_input)
        self.btn_2w_convert.clicked.connect(self.do_convert)
        self.btn_4w_output.clicked.connect(self.do_4w_out)
        self.btn_4w_check.clicked.connect(self.do_4w_check)
        self.btn_4w_input.clicked.connect(self.do_input)
        self.btn_4w_convert.clicked.connect(self.do_convert)
        self.btn_2w_upload.clicked.connect(lambda: self.do_upload('2w'))
        # self.btn_4w_upload.clicked.connect(lambda: self.do_upload('4w'))
        self.btn_2w_open_path.clicked.connect(lambda: self.open_file_folder('2w'))
        self.btn_4w_open_path.clicked.connect(lambda: self.open_file_folder('4w'))

        return page

    # ==================== 报表管理页面 ====================
    def create_report_page(self):
        page = QWidget()
        page.setStyleSheet(f"background:{GRAY_LIGHT};")
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # ---- 标题栏 ----
        title_bar = QFrame()
        title_bar.setStyleSheet(f"QFrame{{background:{WHITE};border-radius:8px;border:1px solid {GRAY_BORDER};}}")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(16, 10, 16, 10)
        page_title = QLabel("📊 飞针测试数据报表")
        page_title.setFont(TITLE_FONT)
        page_title.setStyleSheet(f"color:{PRIMARY_COLOR};")
        title_layout.addWidget(page_title)

        self.lbl_report_time = QLabel(f"报表生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.lbl_report_time.setStyleSheet(f"color:{GRAY_TEXT_LIGHT};")
        title_layout.addWidget(self.lbl_report_time)
        title_layout.addStretch()
        layout.addWidget(title_bar)

        # ---- 筛选区域（两行）----
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"QFrame{{background:{WHITE};border-radius:8px;border:1px solid {GRAY_BORDER};}}")
        filter_outer = QVBoxLayout(filter_frame)
        filter_outer.setContentsMargins(16, 8, 16, 8)
        filter_outer.setSpacing(6)

        # 第一行：工厂 | 状态 | 输出人 | 检查人
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        self.report_cb_factory = QComboBox()
        self.report_cb_factory.addItems(["全部工厂"] + list(FACTORY_MAP.keys()))
        self.report_cb_factory.setFixedWidth(110); self.report_cb_factory.setMinimumHeight(34)
        self.report_cb_factory.setStyleSheet(INPUT_NORMAL_STYLE)
        row1.addWidget(QLabel("工厂：")); row1.addWidget(self.report_cb_factory)

        self.report_cb_status = QComboBox()
        self.report_cb_status.addItems(["全部状态", "待后台处理", "待制作", "待检查", "待转换", "待上传ERP", "已完成"])
        self.report_cb_status.setFixedWidth(110); self.report_cb_status.setMinimumHeight(34)
        row1.addWidget(QLabel("状态：")); row1.addWidget(self.report_cb_status)

        self.report_cb_output_user = QComboBox()
        self.report_cb_output_user.addItem("全部输出人")
        self.report_cb_output_user.addItems(sorted(self.user_name.values()))
        self.report_cb_output_user.setFixedWidth(110); self.report_cb_output_user.setMinimumHeight(34)
        row1.addWidget(QLabel("输出人：")); row1.addWidget(self.report_cb_output_user)

        self.report_cb_check_user = QComboBox()
        self.report_cb_check_user.addItem("全部检查人")
        self.report_cb_check_user.addItems(sorted(self.user_name.values()))
        self.report_cb_check_user.setFixedWidth(110); self.report_cb_check_user.setMinimumHeight(34)
        row1.addWidget(QLabel("检查人：")); row1.addWidget(self.report_cb_check_user)

        self.report_date_start = QDateEdit()
        self.report_date_end = QDateEdit()
        self.report_date_start.setDate(QDate.currentDate().addDays(-30))
        self.report_date_end.setDate(QDate.currentDate())
        self.report_date_start.setDisplayFormat("yyyy-MM-dd")
        self.report_date_end.setDisplayFormat("yyyy-MM-dd")
        self.report_date_start.setFixedWidth(125); self.report_date_end.setFixedWidth(125)
        self.report_date_start.setMinimumHeight(34); self.report_date_end.setMinimumHeight(34)
        self.report_date_start.setCalendarPopup(True); self.report_date_end.setCalendarPopup(True)
        self.report_date_start.setStyleSheet(INPUT_NORMAL_STYLE)
        self.report_date_end.setStyleSheet(INPUT_NORMAL_STYLE)

        row1.addWidget(QLabel("日期："));
        row1.addWidget(self.report_date_start)
        row1.addWidget(QLabel("到"));
        row1.addWidget(self.report_date_end)

        self.btn_report_query = QPushButton("🔍 查询")
        self.btn_report_query.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_report_query.setFixedSize(80, 34)
        self.btn_report_query.clicked.connect(self.query_report)
        row1.addWidget(self.btn_report_query)

        self.btn_report_refresh = QPushButton("🔄 刷新报表")
        self.btn_report_refresh.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_report_refresh.setFixedSize(80, 34)
        self.btn_report_refresh.clicked.connect(self.refresh_report)
        row1.addWidget(self.btn_report_refresh)

        self.btn_export_all = QPushButton("📥 导出CSV")
        self.btn_export_all.setStyleSheet(BUTTON_SUCCESS_STYLE)
        self.btn_export_all.setFixedSize(80, 34)
        self.btn_export_all.clicked.connect(self.export_report_csv)
        row1.addWidget(self.btn_export_all)

        row1.addStretch()
        filter_outer.addLayout(row1)

        layout.addWidget(filter_frame)

        # ---- 统计卡片（一行：11个紧凑卡片）----
        cards_frame = QFrame()
        cards_frame.setStyleSheet("QFrame{background:transparent;border:none;}")
        cards_layout = QHBoxLayout(cards_frame)
        cards_layout.setSpacing(4)
        cards_layout.setContentsMargins(0, 0, 0, 0)

        self.card_total = StatCard("总记录数", "0", PRIMARY_COLOR, "📦")
        self.card_not_run = StatCard("待后台处理", "0", "#909399", "⛔")
        self.card_make_pending = StatCard("待制作", "0", DANGER_COLOR, "🔧")
        self.card_check_pending = StatCard("待检查", "0", WARNING_COLOR, "🔍")
        self.card_convert_pending = StatCard("待转换", "0", "#A0522D", "🔄")
        self.card_erp_upload = StatCard("待上传ERP", "0", "#9B59B6", "📤")
        self.card_completed = StatCard("已完成", "0", SUCCESS_COLOR, "✅")
        self.card_avg_time_2w = StatCard("2W平均耗时min", "0", "#EC4899", "⏱️")
        self.card_avg_time_4w = StatCard("4W平均耗时min", "0", "#F472B6", "⏱️")
        self.card_points_2w = StatCard("2W 总点数/均PCS", "0", "#06B6D4", "🔌")
        self.card_points_4w = StatCard("4W 总点数/均PCS", "0", "#F59E0B", "🔋")

        for card in [self.card_total, self.card_not_run, self.card_make_pending,
                     self.card_check_pending, self.card_convert_pending,
                     self.card_erp_upload, self.card_completed,
                     self.card_avg_time_2w, self.card_avg_time_4w,
                     self.card_points_2w, self.card_points_4w]:
            cards_layout.addWidget(card)

        layout.addWidget(cards_frame)

        # ---- 子视图切换 Tab Bar ----
        tab_bar = QFrame()
        tab_bar.setStyleSheet(f"QFrame{{background:{WHITE};border-radius:8px 8px 0 0;border:1px solid {GRAY_BORDER};border-bottom:none;}}")
        tab_layout = QHBoxLayout(tab_bar)
        tab_layout.setContentsMargins(8, 4, 8, 0)
        tab_layout.setSpacing(2)

        self.btn_tab_detail = QPushButton("📋 数据明细")
        self.btn_tab_factory = QPushButton("🏭 工厂汇总")
        self.btn_tab_daily = QPushButton("📅 日报统计")

        self.btn_tab_detail.setCheckable(True)
        self.btn_tab_factory.setCheckable(True)
        self.btn_tab_daily.setCheckable(True)
        self.btn_tab_detail.setChecked(True)

        self.btn_tab_detail.setFixedHeight(36)
        self.btn_tab_factory.setFixedHeight(36)
        self.btn_tab_daily.setFixedHeight(36)

        self.btn_tab_detail.setStyleSheet(REPORT_TAB_BTN)
        self.btn_tab_factory.setStyleSheet(REPORT_TAB_BTN)
        self.btn_tab_daily.setStyleSheet(REPORT_TAB_BTN)

        self.report_tab_btns = [self.btn_tab_detail, self.btn_tab_factory, self.btn_tab_daily]
        for i, btn in enumerate(self.report_tab_btns):
            btn.clicked.connect(lambda checked, idx=i: self.switch_report_view(idx))

        tab_layout.addWidget(self.btn_tab_detail)
        tab_layout.addWidget(self.btn_tab_factory)
        tab_layout.addWidget(self.btn_tab_daily)
        tab_layout.addStretch()
        layout.addWidget(tab_bar)

        # ---- 三个子视图 ----
        self.report_view_stack = QStackedWidget()
        self.report_view_stack.setStyleSheet(
            f"QStackedWidget{{background:{WHITE};border:1px solid {GRAY_BORDER};border-radius:0 0 8px 8px;border-top:none;}}")

        # 视图1：数据明细
        detail_view = QWidget()
        detail_layout = QVBoxLayout(detail_view)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        self.report_detail_table = QTableWidget()
        self.report_detail_table.setFont(GLOBAL_FONT)
        self.report_detail_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.report_headers = ["厂区", "料号", "版本", "状态", "创建时间", "备注",
                        "2W输出路径", "2W输出人", "2W输出开始时间", "2W输出完成时间", "2W输出总耗时", "2W测试点", "2W检查人", "2W检查开始时间","2W检查完成时间","2W检查总耗时","2W最后更新时间","2W最后更新人",
                        "4W输出路径", "4W输出人", "4W输出开始时间", "4W输出完成时间", "4W输出总耗时", "4W测试点", "4W检查人", "4W检查开始时间","4W检查完成时间","4W检查总耗时","4W最后更新时间","4W最后更新人",
                        ]
        self.report_detail_table.setColumnCount(len(self.report_headers))
        self.report_detail_table.setHorizontalHeaderLabels(self.report_headers)
        rpt_col_width = {0: 85, 1: 140, 2: 55, 3: 80, 4: 140, 5: 180, 6: 70, 7: 70,
                         8: 75, 9: 140, 10: 75, 11: 75, 12: 140, 13: 75,
                         14: 75, 15: 140, 16: 75, 17: 75, 18: 140, 19: 75,
                         20: 75, 21: 140, 22: 75, 23: 75, 24: 140, 25: 75,
                         26: 75, 27: 140, 28: 75, 29: 75
                         }
        for c, w in rpt_col_width.items():
            self.report_detail_table.setColumnWidth(c, w)
        self.report_detail_table.horizontalHeader().setStretchLastSection(True)
        self.report_detail_table.verticalHeader().setDefaultSectionSize(38)
        self.report_detail_table.verticalHeader().setFixedWidth(45)
        self.report_detail_table.setWordWrap(False)
        self.report_detail_table.verticalHeader().setVisible(True)
        self.report_detail_table.setStyleSheet(TABLE_GLOBAL_STYLE)
        self.report_detail_table.horizontalHeader().setStyleSheet(HEADER_GLOBAL_STYLE)
        detail_layout.addWidget(self.report_detail_table)
        self.report_view_stack.addWidget(detail_view)

        # 视图2：工厂汇总
        factory_view = QWidget()
        factory_layout = QVBoxLayout(factory_view)
        factory_layout.setContentsMargins(0, 0, 0, 0)
        self.report_factory_table = QTableWidget()
        self.report_factory_table.setFont(GLOBAL_FONT)
        self.report_factory_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.factory_headers = ["厂区", "总记录",
                                "待后台处理", "待制作", "待检查", "待转换", "待上传ERP",
                                "已完成", "完成率", "2W点数", "4W点数", "平均耗时(min)", "输出人TOP3"]
        self.report_factory_table.setColumnCount(len(self.factory_headers))
        self.report_factory_table.setHorizontalHeaderLabels(self.factory_headers)
        fac_col_w = {0: 110, 1: 70, 2: 80, 3: 65, 4: 65, 5: 65, 6: 80, 7: 70, 8: 65, 9: 90, 10: 90, 11: 100, 12: 180}
        fhh = self.report_factory_table.horizontalHeader()
        for c, w in fac_col_w.items():
            self.report_factory_table.setColumnWidth(c, w)
        fhh.setStretchLastSection(True)
        self.report_factory_table.verticalHeader().setDefaultSectionSize(42)
        self.report_factory_table.setWordWrap(True)
        self.report_factory_table.verticalHeader().setVisible(True)
        self.report_factory_table.setStyleSheet(TABLE_GLOBAL_STYLE)
        self.report_factory_table.horizontalHeader().setStyleSheet(HEADER_GLOBAL_STYLE)
        factory_layout.addWidget(self.report_factory_table)
        self.report_view_stack.addWidget(factory_view)

        # 视图3：日报统计
        daily_view = QWidget()
        daily_layout = QVBoxLayout(daily_view)
        daily_layout.setContentsMargins(0, 0, 0, 0)
        self.report_daily_table = QTableWidget()
        self.report_daily_table.setFont(GLOBAL_FONT)
        self.report_daily_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.daily_headers = ["日期", "记录数",
                              "待后台处理", "待制作", "待检查", "待转换", "待上传ERP",
                              "已完成", "完成率", "2W点数", "4W点数", "输出用户数"]
        self.report_daily_table.setColumnCount(len(self.daily_headers))
        self.report_daily_table.setHorizontalHeaderLabels(self.daily_headers)
        day_col_w = {0: 120, 1: 70, 2: 75, 3: 60, 4: 60, 5: 60, 6: 80, 7: 65, 8: 60, 9: 100, 10: 100, 11: 85}
        dhh = self.report_daily_table.horizontalHeader()
        for c, w in day_col_w.items():
            self.report_daily_table.setColumnWidth(c, w)
        dhh.setStretchLastSection(True)
        self.report_daily_table.verticalHeader().setDefaultSectionSize(38)
        self.report_daily_table.setWordWrap(False)
        self.report_daily_table.verticalHeader().setVisible(True)
        self.report_daily_table.setStyleSheet(TABLE_GLOBAL_STYLE)
        self.report_daily_table.horizontalHeader().setStyleSheet(HEADER_GLOBAL_STYLE)
        daily_layout.addWidget(self.report_daily_table)
        self.report_view_stack.addWidget(daily_view)

        layout.addWidget(self.report_view_stack)

        # ---- 分页 ----
        rpt_page_frame = QFrame()
        rpt_page_frame.setStyleSheet(f"QFrame{{background:{WHITE};border-radius:8px;border:1px solid {GRAY_BORDER};}}")
        rpt_page_layout = QHBoxLayout(rpt_page_frame)
        rpt_page_layout.setContentsMargins(15, 10, 15, 10)

        self.rpt_btn_first = QPushButton("首页")
        self.rpt_btn_prev = QPushButton("上一页")
        self.rpt_btn_next = QPushButton("下一页")
        self.rpt_btn_last = QPushButton("尾页")
        self.rpt_spin_page = QSpinBox()
        self.rpt_spin_page.setFixedWidth(65)
        self.rpt_lab_page = QLabel("总页数：0")
        self.rpt_lab_count = QLabel("总数据：0 条")

        for btn in [self.rpt_btn_first, self.rpt_btn_prev, self.rpt_btn_next, self.rpt_btn_last]:
            btn.setFixedSize(75, 30)
            btn.setStyleSheet(BUTTON_NORMAL_STYLE)
            btn.setFont(GLOBAL_FONT)

        rpt_page_layout.addStretch()
        rpt_page_layout.addWidget(self.rpt_btn_first)
        rpt_page_layout.addWidget(self.rpt_btn_prev)
        rpt_page_layout.addWidget(self.rpt_btn_next)
        rpt_page_layout.addWidget(self.rpt_btn_last)
        rpt_page_layout.addSpacing(15)
        rpt_page_layout.addWidget(QLabel("页码："))
        rpt_page_layout.addWidget(self.rpt_spin_page)
        rpt_page_layout.addSpacing(15)
        rpt_page_layout.addWidget(self.rpt_lab_page)
        rpt_page_layout.addSpacing(15)
        rpt_page_layout.addWidget(self.rpt_lab_count)
        rpt_page_layout.addStretch()
        layout.addWidget(rpt_page_frame)

        # 分页事件
        self.rpt_btn_first.clicked.connect(lambda: self.switch_report_page(1))
        self.rpt_btn_prev.clicked.connect(lambda: self.switch_report_page(self.report_page - 1))
        self.rpt_btn_next.clicked.connect(lambda: self.switch_report_page(self.report_page + 1))
        self.rpt_btn_last.clicked.connect(lambda: self.switch_report_page(self.report_total_page))
        self.rpt_spin_page.editingFinished.connect(
            lambda: self.switch_report_page(self.rpt_spin_page.value()))

        self.report_view_index = 0
        return page

    # ==================== 报表逻辑 ====================
    def refresh_report(self):
        """刷新报表（重新查DB+全部重算）"""
        self.lbl_report_time.setText(f"报表生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.load_report_data()
        self.update_report_cards()
        self._precompute_report_cache()
        self.report_page = 1

        self.report_view_stack.setUpdatesEnabled(False)
        self.current_report_view()
        self.report_view_stack.setUpdatesEnabled(True)

    def query_report(self):
        """筛选条件变化，重新加载"""
        self.report_page = 1
        self.refresh_report()

    def switch_report_view(self, index):
        """切换子视图（纯UI切换，不重新计算）"""
        for i, btn in enumerate(self.report_tab_btns):
            btn.setChecked(i == index)
        self.report_view_index = index
        self.report_view_stack.setCurrentIndex(index)
        self.report_page = 1
        self.report_view_stack.setUpdatesEnabled(False)
        self.current_report_view()
        self.report_view_stack.setUpdatesEnabled(True)

    def load_report_data(self):
        """从DB加载数据"""
        try:
            factory_text = self.report_cb_factory.currentText()
            status_text = self.report_cb_status.currentText()
            sd = self.report_date_start.date().toString("yyyy-MM-dd")
            ed = self.report_date_end.date().toString("yyyy-MM-dd")

            where_clauses = [
                "US.OPERATON_CLASSCODE='ET_DATA'",
                "(US.REMARK IS NULL OR  US.REMARK NOT LIKE '%ERP记录已输出%')",
                f"TRUNC(us.CREATION_DATE) BETWEEN TO_DATE('{sd}','YYYY-MM-DD') AND TO_DATE('{ed}','YYYY-MM-DD')"
            ]
            if factory_text != "全部工厂":
                fid = FACTORY_MAP.get(factory_text, "")
                if fid:
                    where_clauses.append(f"US.ORG_ID='{fid}'")

            where_sql = " AND ".join(where_clauses)

            sql = f"""
            SELECT 
                US.DATA_ID,
                US.ITEM_NO,
                US.REV,
                US.ORG_ID,
                US.CREATION_DATE,
                US.STATUS,
                US.REMARK ,
                US.OUTPUT_PATH_2W,
                US.OUTPUT_BY_2W,
                US.OUTPUT_START_2W,
                US.OUTPUT_FINISH_TIME_2W,
                US.TOTAL_OUTPUT_MS_2W,
                US.TEST_POINT_2W,
                US.CHECK_BY_2W,
                US.CHECK_START_2W,
                US.CHECK_FINISH_TIME_2W,
                US.TOTAL_CHECK_MS_2W,
                US.LAST_UPDATE_DATE_2W,
                US.LAST_UPDATED_BY_2W,
                US.OUTPUT_PATH_4W,
                US.OUTPUT_BY_4W,
                US.OUTPUT_START_4W,
                US.OUTPUT_FINISH_TIME_4W,
                US.TOTAL_OUTPUT_MS_4W,
                US.TEST_POINT_4W,
                US.CHECK_BY_4W,
                US.CHECK_START_4W,
                US.CHECK_FINISH_TIME_4W,
                US.TOTAL_CHECK_MS_4W,
                US.LAST_UPDATE_DATE_4W,
                US.LAST_UPDATED_BY_4W
            FROM 
                inp.inp_flypin_probe_tool_alert us
            WHERE {where_sql}
            ORDER BY us.CREATION_DATE DESC"""

            db = self.init_erp_database_connection()
            raw = db.SELECT_DIC(sql) if db else []

            if status_text != "全部状态":
                self.report_data = [
                    r for r in raw
                    if self.get_work_status(r.get("STATUS")) == status_text
                ]
            else:
                self.report_data = raw

            # 先刷新下拉列表（基于状态筛选后的数据）
            self._refresh_user_combos()

            # 输出人筛选
            output_user = self.report_cb_output_user.currentText()
            if output_user != "全部输出人":
                output_id = self.user_name_id.get(output_user, output_user)
                self.report_data = [
                    r for r in self.report_data
                    if str(r.get("OUTPUT_BY_2W") or "") == output_id
                ]

            # 检查人筛选
            check_user = self.report_cb_check_user.currentText()
            if check_user != "全部检查人":
                check_id = self.user_name_id.get(check_user, check_user)
                self.report_data = [
                    r for r in self.report_data
                    if str(r.get("CHECK_BY_2W") or "") == check_id
                ]

        except Exception as e:
            logger.error(f"报表数据加载失败：{e}")
            self.report_data = []

    def _parse_output_time(self, val):
        """解析输出耗时 HH:MM:SS -> 分钟"""
        try:
            s = str(val).strip()
            if not s or s == '0':
                return 0
            parts = s.split(':')
            if len(parts) == 3:
                return int(parts[0]) * 60 + int(parts[1]) + int(parts[2]) / 60.0
            return float(s)
        except:
            return 0

    def _top_users(self, counter, max_n=3):
        """从Counter提取TOP N用户"""
        if not counter:
            return ""
        items = sorted(counter.items(), key=lambda x: x[1], reverse=True)[:max_n]
        return ", ".join([f"{k}({v})" for k, v in items])

    def _refresh_user_combos(self):
        """从已加载的报表数据中提取输出人/检查人，动态填充下拉列表"""
        output_users = set()
        check_users = set()
        user_name = self.user_name
        for r in self.report_data:
            def _v(x): return str(x) if x else ""
            ou = _v(r.get("OUTPUT_BY_2W"))
            if ou:
                output_users.add(user_name.get(ou, ou))
            cu = _v(r.get("CHECK_BY_2W"))
            if cu:
                check_users.add(user_name.get(cu, cu))

        # 更新输出人下拉（保留之前的选择）
        prev_out = self.report_cb_output_user.currentText()
        self.report_cb_output_user.blockSignals(True)
        self.report_cb_output_user.clear()
        self.report_cb_output_user.addItem("全部输出人")
        self.report_cb_output_user.addItems(sorted(output_users))
        idx = self.report_cb_output_user.findText(prev_out)
        if idx >= 0:
            self.report_cb_output_user.setCurrentIndex(idx)
        self.report_cb_output_user.blockSignals(False)

        # 更新检查人下拉
        prev_chk = self.report_cb_check_user.currentText()
        self.report_cb_check_user.blockSignals(True)
        self.report_cb_check_user.clear()
        self.report_cb_check_user.addItem("全部检查人")
        self.report_cb_check_user.addItems(sorted(check_users))
        idx = self.report_cb_check_user.findText(prev_chk)
        if idx >= 0:
            self.report_cb_check_user.setCurrentIndex(idx)
        self.report_cb_check_user.blockSignals(False)

    # ---------- 缓存机制：一次计算，三视图复用 ----------

    def _precompute_report_cache(self):
        """数据加载后一次性预计算工厂汇总+日报统计"""
        cache = {
            'factory_summary': {},
            'daily_stats': {}
        }

        user_name = self.user_name
        get_status = self.get_work_status

        # 工厂汇总
        for r in self.report_data:
            def _v(x): return str(x) if x else ""
            org = _v(r.get("ORG_ID"))
            factory = FACTORY_ID_TO_NAME.get(org, org)
            if factory not in cache['factory_summary']:
                cache['factory_summary'][factory] = {
                    "total": 0, "completed": 0,
                    "not_run": 0, "make_pending": 0, "check_pending": 0,
                    "convert_pending": 0, "erp_upload": 0,
                    "2w": 0, "4w": 0, "times": [], "operators": Counter()
                }
            fm = cache['factory_summary'][factory]
            fm["total"] += 1
            status = get_status(r.get("STATUS"))
            if status == "已完成":
                fm["completed"] += 1
            elif status == "待后台处理":
                fm["not_run"] += 1
            elif status == "待制作":
                fm["make_pending"] += 1
            elif status == "待检查":
                fm["check_pending"] += 1
            elif status == "待转换":
                fm["convert_pending"] += 1
            elif status == "待上传ERP":
                fm["erp_upload"] += 1
            try:
                fm["2w"] += int(r.get("TEST_POINT_2W") or 0)
                fm["4w"] += int(r.get("TEST_POINT_4W") or 0)
            except:
                pass
            t_out = self._parse_output_time(r.get("TOTAL_OUTPUT_MS_2W"))
            if t_out > 0:
                fm["times"].append(t_out)
            op = user_name.get(_v(r.get("OUTPUT_BY_2W")), "")
            if op:
                fm["operators"][op] += 1

        # 日报统计
        for r in self.report_data:
            def _v(x): return str(x) if x else ""
            ct = _v(r.get("CREATION_DATE"))
            date_str = ct[:10] if ct else "未知"
            if date_str not in cache['daily_stats']:
                cache['daily_stats'][date_str] = {
                    "total": 0, "completed": 0,
                    "not_run": 0, "make_pending": 0, "check_pending": 0,
                    "convert_pending": 0, "erp_upload": 0,
                    "2w": 0, "4w": 0, "users": set()
                }
            dm = cache['daily_stats'][date_str]
            dm["total"] += 1
            status = get_status(r.get("STATUS"))
            if status == "已完成":
                dm["completed"] += 1
            elif status == "待后台处理":
                dm["not_run"] += 1
            elif status == "待制作":
                dm["make_pending"] += 1
            elif status == "待检查":
                dm["check_pending"] += 1
            elif status == "待转换":
                dm["convert_pending"] += 1
            elif status == "待上传ERP":
                dm["erp_upload"] += 1
            try:
                dm["2w"] += int(r.get("TEST_POINT_2W") or 0)
                dm["4w"] += int(r.get("TEST_POINT_4W") or 0)
            except:
                pass
            op = _v(r.get("OUTPUT_BY_2W"))
            if op:
                dm["users"].add(op)

        self._report_cache = cache

    def update_report_cards(self):
        """更新统计卡片"""
        total = len(self.report_data)
        completed = 0
        not_run = 0          # 待后台处理
        make_pending = 0     # 待制作
        check_pending = 0    # 待检查
        convert_pending = 0  # 待转换
        erp_upload = 0       # 待上传ERP
        total_2w = 0
        total_4w = 0
        total_time_2w = 0
        time_2w_count = 0
        total_check_2w_time = 0
        check_2w_time_count = 0
        total_time_4w = 0
        time_4w_count = 0
        total_check_4w_time = 0
        check_4w_time_count = 0
        get_status = self.get_work_status
        average_value_2w = 0
        average_value_4w = 0
        for r in self.report_data:
            status = get_status(r.get("STATUS"))
            if status == "已完成":
                completed += 1
            elif status == "待后台处理":
                not_run += 1
            elif status == "待制作":
                make_pending += 1
            elif status == "待检查":
                check_pending += 1
            elif status == "待转换":
                convert_pending += 1
            elif status == "待上传ERP":
                erp_upload += 1
            try:
                total_2w += int(r.get("TEST_POINT_2W") or 0)
                total_4w += int(r.get("TEST_POINT_4W") or 0)
                if int(r.get("TEST_POINT_2W")) > 0:
                    average_value_2w += 1
                if int(r.get("TEST_POINT_4W")) > 0:
                    average_value_4w += 1
            except:
                pass
            t2w = self._parse_output_time(r.get("TOTAL_OUTPUT_MS_2W"))
            if t2w > 0:
                total_time_2w += t2w
                time_2w_count += 1
            ct2w = self._parse_output_time(r.get("TOTAL_CHECK_MS_2W"))
            if ct2w > 0:
                # 输出完成时间==检查完成时间，说明未实际检查，不计入检查耗时
                out_finish_2w = str(r.get("OUTPUT_FINISH_TIME_2W") or "")
                chk_finish_2w = str(r.get("CHECK_FINISH_TIME_2W") or "")
                if out_finish_2w != chk_finish_2w:
                    total_check_2w_time += ct2w
                    check_2w_time_count += 1
            t4w = self._parse_output_time(r.get("TOTAL_OUTPUT_MS_4W"))
            if t4w > 0:
                total_time_4w += t4w
                time_4w_count += 1
            ct4w = self._parse_output_time(r.get("TOTAL_CHECK_MS_4W"))
            if ct4w > 0:
                out_finish_4w = str(r.get("OUTPUT_FINISH_TIME_4W") or "")
                chk_finish_4w = str(r.get("CHECK_FINISH_TIME_4W") or "")
                if out_finish_4w != chk_finish_4w:
                    total_check_4w_time += ct4w
                    check_4w_time_count += 1

        out_2w_avg = f"{total_time_2w / time_2w_count:.1f}" if time_2w_count > 0 else "0"
        chk_2w_avg = f"{total_check_2w_time / check_2w_time_count:.1f}" if check_2w_time_count > 0 else "0"
        out_4w_avg = f"{total_time_4w / time_4w_count:.1f}" if time_4w_count > 0 else "0"
        chk_4w_avg = f"{total_check_4w_time / check_4w_time_count:.1f}" if check_4w_time_count > 0 else "0"
        self.card_total.set_value(total)
        self.card_not_run.set_value(not_run)
        self.card_make_pending.set_value(make_pending)
        self.card_check_pending.set_value(check_pending)
        self.card_convert_pending.set_value(convert_pending)
        self.card_erp_upload.set_value(erp_upload)
        self.card_completed.set_value(completed)
        self.card_avg_time_2w.set_double_value(f"制作 {out_2w_avg}", f"检查 {chk_2w_avg}")
        self.card_avg_time_4w.set_double_value(f"制作 {out_4w_avg}", f"检查 {chk_4w_avg}")
        self.card_points_2w.set_double_value(f"{total_2w:,}", f"{int(total_2w / average_value_2w) if average_value_2w != 0 else 0}/PCS")
        self.card_points_4w.set_double_value(f"{total_4w:,}", f"{int(total_4w / average_value_4w) if average_value_4w != 0 else 0}/PCS")

    def current_report_view(self):
        """根据当前视图索引渲染表格（从缓存读取）"""
        if self.report_view_index == 0:
            self._render_detail_table()
        elif self.report_view_index == 1:
            self._render_factory_summary()
        elif self.report_view_index == 2:
            self._render_daily_stats()

    def _render_detail_table(self):
        """数据明细 - 从原始数据分页渲染"""
        total = len(self.report_data)
        self.report_total_page = max(1, (total + self.report_page_size - 1) // self.report_page_size)
        self.report_page = min(self.report_page, self.report_total_page)
        self.rpt_spin_page.setRange(1, self.report_total_page)
        self.rpt_spin_page.setValue(self.report_page)
        self.rpt_lab_page.setText(f"总页数：{self.report_total_page}")
        self.rpt_lab_count.setText(f"总数据：{total} 条")

        table = self.report_detail_table
        table.setRowCount(0)
        s = (self.report_page - 1) * self.report_page_size
        e = s + self.report_page_size
        rows = self.report_data[s:e]

        user_name = self.user_name
        get_status = self.get_work_status
        status_color = self.get_status_color

        for i, r in enumerate(rows):
            table.insertRow(i)
            # 左侧行号 = 全局序号（随分页递增）
            row_no = QTableWidgetItem(str(s + i + 1))
            row_no.setTextAlignment(Qt.AlignCenter)
            row_no.setFont(GLOBAL_FONT)
            table.setVerticalHeaderItem(i, row_no)
            bg = QColor("#fff") if i % 2 == 0 else QColor("#f8f9fa")

            org = str(r.get("ORG_ID") or "")
            factory = FACTORY_ID_TO_NAME.get(org, org)
            status = get_status(r.get("STATUS"))

            remark = str(r.get("REMARK") or "")
            # 截断过长备注
            if len(remark) > 60:
                remark = remark[:57] + "..."

            items_data = [
                factory,                                                     # 0  厂区
                str(r.get("ITEM_NO") or ""),                                # 2  料号
                str(r.get("REV") or ""),                                    # 3  版本
                status,                                                      # 4  状态
                str(r.get("CREATION_DATE") or ""),                           # 5  创建时间
                remark,                                                      # 6  备注
                str(r.get("OUTPUT_PATH_2W") or ""),                          # 7  2W输出路径
                user_name.get(str(r.get("OUTPUT_BY_2W") or ""), ""),         # 8  2W输出人
                str(r.get("OUTPUT_START_2W") or ""),                         # 9  2W输出开始时间
                str(r.get("OUTPUT_FINISH_TIME_2W") or ""),                   # 10 2W输出完成时间
                str(r.get("TOTAL_OUTPUT_MS_2W") or ""),                      # 11 2W输出总耗时
                str(r.get("TEST_POINT_2W") or ""),                           # 12 2W测试点
                user_name.get(str(r.get("CHECK_BY_2W") or ""), ""),          # 13 2W检查人
                str(r.get("CHECK_START_2W") or ""),                          # 14 2W检查开始时间
                str(r.get("CHECK_FINISH_TIME_2W") or ""),                    # 15 2W检查完成时间
                str(r.get("TOTAL_CHECK_MS_2W") or ""),                       # 16 2W检查总耗时
                str(r.get("LAST_UPDATE_DATE_2W") or ""),                     # 17 2W最后更新时间
                user_name.get(str(r.get("LAST_UPDATED_BY_2W") or ""), ""),   # 18 2W最后更新人
                str(r.get("OUTPUT_PATH_4W") or ""),                          # 19 4W输出路径
                user_name.get(str(r.get("OUTPUT_BY_4W") or ""), ""),         # 20 4W输出人
                str(r.get("OUTPUT_START_4W") or ""),                         # 21 4W输出开始时间
                str(r.get("OUTPUT_FINISH_TIME_4W") or ""),                   # 22 4W输出完成时间
                str(r.get("TOTAL_OUTPUT_MS_4W") or ""),                      # 23 4W输出总耗时
                str(r.get("TEST_POINT_4W") or ""),                           # 24 4W测试点
                user_name.get(str(r.get("CHECK_BY_4W") or ""), ""),          # 25 4W检查人
                str(r.get("CHECK_START_4W") or ""),                          # 26 4W检查开始时间
                str(r.get("CHECK_FINISH_TIME_4W") or ""),                    # 27 4W检查完成时间
                str(r.get("TOTAL_CHECK_MS_4W") or ""),                       # 28 4W检查总耗时
                str(r.get("LAST_UPDATE_DATE_4W") or ""),                     # 29 4W最后更新时间
                user_name.get(str(r.get("LAST_UPDATED_BY_4W") or ""), ""),   # 30 4W最后更新人
            ]

            for col, txt in enumerate(items_data):
                cell = QTableWidgetItem(txt)
                cell.setTextAlignment(Qt.AlignCenter)
                cell.setBackground(bg)
                table.setItem(i, col, cell)

            st_item = table.item(i, 4)
            if st_item:
                st_item.setForeground(status_color(status))

        table.resizeColumnsToContents()

    def _render_factory_summary(self):
        """工厂汇总 - 从缓存渲染"""
        cache = getattr(self, '_report_cache', {})
        factory_data = cache.get('factory_summary', {})
        if not factory_data:
            return

        table = self.report_factory_table
        table.setRowCount(0)
        sorted_factories = sorted(factory_data.keys())

        for i, fac in enumerate(sorted_factories):
            fm = factory_data[fac]
            table.insertRow(i)
            bg = QColor("#fff") if i % 2 == 0 else QColor("#f8f9fa")
            rate = f"{fm['completed'] * 100 // fm['total']}%" if fm['total'] > 0 else "0%"
            avg_t = f"{(sum(fm['times']) / len(fm['times'])):.1f}" if fm['times'] else "-"
            top_ops = self._top_users(fm['operators'])

            row_data = [
                fac, str(fm['total']),
                str(fm['not_run']), str(fm['make_pending']),
                str(fm['check_pending']), str(fm['convert_pending']),
                str(fm['erp_upload']), str(fm['completed']),
                rate, f"{fm['2w']:,}", f"{fm['4w']:,}", avg_t, top_ops
            ]
            for col, txt in enumerate(row_data):
                cell = QTableWidgetItem(txt)
                cell.setTextAlignment(Qt.AlignCenter)
                cell.setBackground(bg)
                table.setItem(i, col, cell)

            rate_item = table.item(i, 8)
            if rate_item:
                try:
                    pct = int(rate.replace('%', ''))
                    if pct >= 80:
                        rate_item.setForeground(QColor(SUCCESS_COLOR))
                    elif pct >= 50:
                        rate_item.setForeground(QColor(WARNING_COLOR))
                    else:
                        rate_item.setForeground(QColor(DANGER_COLOR))
                except:
                    pass

        self.rpt_lab_page.setText("工厂汇总")
        self.rpt_lab_count.setText(f"共 {len(sorted_factories)} 个厂区")
        self.rpt_spin_page.setRange(1, 1)

    def _render_daily_stats(self):
        """日报统计 - 从缓存渲染"""
        cache = getattr(self, '_report_cache', {})
        daily_data = cache.get('daily_stats', {})
        if not daily_data:
            return

        table = self.report_daily_table
        table.setRowCount(0)
        sorted_dates = sorted(daily_data.keys(), reverse=True)

        for i, dt in enumerate(sorted_dates):
            dm = daily_data[dt]
            table.insertRow(i)
            bg = QColor("#fff") if i % 2 == 0 else QColor("#f8f9fa")
            rate = f"{dm['completed'] * 100 // dm['total']}%" if dm['total'] > 0 else "0%"

            row_data = [
                dt, str(dm['total']),
                str(dm['not_run']), str(dm['make_pending']),
                str(dm['check_pending']), str(dm['convert_pending']),
                str(dm['erp_upload']), str(dm['completed']),
                rate, f"{dm['2w']:,}", f"{dm['4w']:,}",
                str(len(dm['users']))
            ]
            for col, txt in enumerate(row_data):
                cell = QTableWidgetItem(txt)
                cell.setTextAlignment(Qt.AlignCenter)
                cell.setBackground(bg)
                table.setItem(i, col, cell)

            rate_item = table.item(i, 7)
            if rate_item:
                try:
                    pct = int(rate.replace('%', ''))
                    if pct >= 80:
                        rate_item.setForeground(QColor(SUCCESS_COLOR))
                    elif pct >= 50:
                        rate_item.setForeground(QColor(WARNING_COLOR))
                    else:
                        rate_item.setForeground(QColor(DANGER_COLOR))
                except:
                    pass

        self.rpt_lab_page.setText("日报统计")
        self.rpt_lab_count.setText(f"共 {len(sorted_dates)} 天")

    def switch_report_page(self, p):
        """分页切换（仅明细表需要）"""
        if 1 <= p <= self.report_total_page:
            self.report_page = p
            self.rpt_spin_page.setValue(p)
            self.report_view_stack.setUpdatesEnabled(False)
            self.current_report_view()
            self.report_view_stack.setUpdatesEnabled(True)

    def export_report_csv(self):
        """导出当前视图数据为CSV"""
        if not self.report_data:
            QMessageBox.warning(self, "提示", "暂无数据可导出！")
            return

        if self.report_view_index == 0:
            pre = "飞针测试数据明细"
            headers = self.report_headers
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出明细CSV", f"{pre}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV文件 (*.csv)"
            )
            if not file_path:
                return
            try:
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    for r in self.report_data:
                        org = str(r.get("ORG_ID") or "")
                        factory = FACTORY_ID_TO_NAME.get(org, org)
                        status = self.get_work_status(r.get("STATUS"))
                        writer.writerow([
                            factory, str(r.get("ITEM_NO") or ""), str(r.get("REV") or ""),
                            status, str(r.get("CREATION_DATE") or ""),
                            str(r.get("REMARK") or ""),
                            str(r.get("OUTPUT_PATH_2W") or ""),
                            self.user_name.get(str(r.get("OUTPUT_BY_2W") or ""), ""),
                            str(r.get("OUTPUT_START_2W") or ""),
                            str(r.get("OUTPUT_FINISH_TIME_2W") or ""),
                            str(r.get("TOTAL_OUTPUT_MS_2W") or ""),
                            str(r.get("TEST_POINT_2W") or ""),
                            self.user_name.get(str(r.get("CHECK_BY_2W") or ""), ""),
                            str(r.get("CHECK_START_2W") or ""),
                            str(r.get("CHECK_FINISH_TIME_2W") or ""),
                            str(r.get("TOTAL_CHECK_MS_2W") or ""),
                            str(r.get("LAST_UPDATE_DATE_2W") or ""),
                            self.user_name.get(str(r.get("LAST_UPDATED_BY_2W") or ""), ""),
                            str(r.get("OUTPUT_PATH_4W") or ""),
                            self.user_name.get(str(r.get("OUTPUT_BY_4W") or ""), ""),
                            str(r.get("OUTPUT_START_4W") or ""),
                            str(r.get("OUTPUT_FINISH_TIME_4W") or ""),
                            str(r.get("TOTAL_OUTPUT_MS_4W") or ""),
                            str(r.get("TEST_POINT_4W") or ""),
                            self.user_name.get(str(r.get("CHECK_BY_4W") or ""), ""),
                            str(r.get("CHECK_START_4W") or ""),
                            str(r.get("CHECK_FINISH_TIME_4W") or ""),
                            str(r.get("TOTAL_CHECK_MS_4W") or ""),
                            str(r.get("LAST_UPDATE_DATE_4W") or ""),
                            self.user_name.get(str(r.get("LAST_UPDATED_BY_4W") or ""), ""),
                        ])
                QMessageBox.information(self, "导出成功", f"✅ 数据明细已导出到：\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"错误：{str(e)}")

        elif self.report_view_index == 1:
            pre = "飞针测试工厂汇总"
            headers = self.factory_headers
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出工厂汇总CSV", f"{pre}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV文件 (*.csv)"
            )
            if not file_path:
                return
            try:
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    table = self.report_factory_table
                    for row in range(table.rowCount()):
                        row_data = []
                        for col in range(table.columnCount()):
                            it = table.item(row, col)
                            row_data.append(it.text() if it else "")
                        writer.writerow(row_data)
                QMessageBox.information(self, "导出成功", f"✅ 工厂汇总已导出到：\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"错误：{str(e)}")

        elif self.report_view_index == 2:
            pre = "飞针测试日报统计"
            headers = self.daily_headers
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出日报CSV", f"{pre}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV文件 (*.csv)"
            )
            if not file_path:
                return
            try:
                import csv
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    table = self.report_daily_table
                    for row in range(table.rowCount()):
                        row_data = []
                        for col in range(table.columnCount()):
                            it = table.item(row, col)
                            row_data.append(it.text() if it else "")
                        writer.writerow(row_data)
                QMessageBox.information(self, "导出成功", f"✅ 日报统计已导出到：\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"错误：{str(e)}")
    # ==================== 原有任务管理方法（保持不变）====================
    def open_file_folder(self,mode='2w'):
        """点击按钮打开文件所在文件夹"""
        path = (self.current_2w_file_path if mode == '2w' else self.current_4w_file_path).strip()
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "提示", "文件路径不存在或为空！")
            return

        if os.path.isdir(path):
            os.startfile(path)
        else:
            folder_path = os.path.dirname(path)
            if os.path.exists(folder_path):
                os.startfile(folder_path)

    def update_detail(self):
        # 清空原有详情（2W和4W）
        for layout in [self.scroll_layout_2w, self.scroll_layout_4w]:
            while layout.count() > 0:
                item = layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()

        items = self.table.selectedItems()
        if not items:
            for btn in [self.btn_2w_output, self.btn_2w_check, self.btn_2w_input, self.btn_2w_convert,
                        self.btn_4w_output, self.btn_4w_check, self.btn_4w_input, self.btn_4w_convert,
                        self.btn_2w_upload]:
                btn.setEnabled(False)
            self.lbl_2w_path_val.setText("未选择")
            self.lbl_4w_path_val.setText("未选择")
            tip_label = QLabel("请在左侧表格选择一行数据查看详情")
            tip_label.setAlignment(Qt.AlignCenter)
            tip_label.setStyleSheet(f"color:{GRAY_TEXT_LIGHT};font-size:10pt;padding:40px 0;")
            self.scroll_layout_2w.addWidget(tip_label)
            tip_label2 = QLabel("请在左侧表格选择一行数据查看详情")
            tip_label2.setAlignment(Qt.AlignCenter)
            tip_label2.setStyleSheet(f"color:{GRAY_TEXT_LIGHT};font-size:10pt;padding:40px 0;")
            self.scroll_layout_4w.addWidget(tip_label2)
            return

        row_idx = items[0].row()

        def get_cell(col):
            it = self.table.item(row_idx, col)
            return it.text().strip() if it else ""

        factory_name = get_cell(1)
        self.current_org_id = FACTORY_MAP.get(factory_name, "")
        self.current_did = get_cell(0)
        item_no = get_cell(2)
        rev = get_cell(3)
        self.current_pn = f"{item_no}{rev}"
        self.current_status = get_cell(6)
        self.current_2w_file_path = get_cell(8)
        self.current_4w_file_path = get_cell(20)
        self.current_2w_test_point = get_cell(13)
        self.current_4w_test_point = get_cell(25)
        # 保留兼容
        self.current_test_point = self.current_2w_test_point

        # ===== 2W 按钮状态 =====
        self.btn_2w_output.setEnabled(True)
        self.btn_2w_check.setEnabled(True)
        self.btn_2w_input.setEnabled(True)
        self.btn_2w_convert.setEnabled(True)
        self.btn_2w_upload.setEnabled(True)
        if self.current_status in ["待后台处理", "待制作"]:
            self.btn_2w_check.setEnabled(False)
            self.btn_2w_input.setEnabled(False)
            self.btn_2w_convert.setEnabled(False)
            self.btn_2w_upload.setEnabled(False)
        elif self.current_status == "待检查":
            self.btn_2w_convert.setEnabled(False)
            self.btn_2w_input.setEnabled(False)
            self.btn_2w_upload.setEnabled(False)
        elif self.current_status == "待转换":
            self.btn_2w_check.setEnabled(False)
            self.btn_2w_input.setEnabled(False)
            self.btn_2w_upload.setEnabled(False)
        elif self.current_status == "已完成":
            self.btn_2w_check.setEnabled(False)
            self.btn_2w_input.setEnabled(False)
            self.btn_2w_upload.setEnabled(False)

        # ===== 4W 按钮状态 =====
        self.btn_4w_output.setEnabled(True)
        self.btn_4w_check.setEnabled(True)
        self.btn_4w_input.setEnabled(True)
        self.btn_4w_convert.setEnabled(True)
        # self.btn_4w_upload.setEnabled(True)
        if self.current_status in ["待后台处理", "待制作"]:
            # self.btn_4w_output.setEnabled(False)
            self.btn_4w_check.setEnabled(False)
            self.btn_4w_input.setEnabled(False)
            self.btn_4w_convert.setEnabled(False)
            # self.btn_4w_upload.setEnabled(False)
        elif self.current_status == "待检查":
            # self.btn_4w_output.setEnabled(False)
            self.btn_4w_convert.setEnabled(False)
            self.btn_4w_input.setEnabled(False)
            # self.btn_4w_upload.setEnabled(False)
        elif self.current_status == "待转换":
            self.btn_4w_check.setEnabled(True)
            self.btn_4w_input.setEnabled(False)
            # self.btn_4w_upload.setEnabled(False)
        elif self.current_status == "已完成":
            # self.btn_4w_output.setEnabled(False)
            self.btn_4w_check.setEnabled(False)
            self.btn_4w_input.setEnabled(False)
            # self.btn_4w_upload.setEnabled(False)

        # ===== 更新路径标签 =====
        self.lbl_2w_path_val.setText(self.current_2w_file_path if self.current_2w_file_path else "无")
        self.lbl_4w_path_val.setText(self.current_4w_file_path if self.current_4w_file_path else "无")

        """
        8: v(r.get("OUTPUT_PATH_2W")),
        9: v(self.user_name.get(r.get("OUTPUT_BY_2W"))),
        10: v(r.get("OUTPUT_START_2W")),
        11: v(r.get("OUTPUT_FINISH_TIME_2W")),
        12: v(r.get("TOTAL_OUTPUT_MS_2W")),
        13: v(r.get("TEST_POINT_2W")),
        14: v(self.user_name.get(r.get("CHECK_BY_2W"))),
        15: v(r.get("CHECK_START_2W")),
        16: v(r.get("CHECK_FINISH_TIME_2W")),
        17: v(r.get("TOTAL_CHECK_MS_2W")),
        18: v(r.get("LAST_UPDATE_DATE_2W")),
        19: v(self.user_name.get(r.get("LAST_UPDATED_BY_2W"))),
        20: v(r.get("OUTPUT_PATH_4W")),
        21: v(self.user_name.get(r.get("OUTPUT_BY_4W"))),
        22: v(r.get("OUTPUT_START_4W")),
        23: v(r.get("OUTPUT_FINISH_TIME_4W")),
        24: v(r.get("TOTAL_OUTPUT_MS_4W")),
        25: v(r.get("TEST_POINT_4W")),
        26: v(self.user_name.get(r.get("CHECK_BY_4W"))),
        27: v(r.get("CHECK_START_4W")),
        28: v(r.get("CHECK_FINISH_TIME_4W")),
        29: v(r.get("TOTAL_CHECK_MS_4W")),
        30: v(r.get("LAST_UPDATE_DATE_4W")),
        31: v(self.user_name.get(r.get("LAST_UPDATED_BY_4W"))),
        """

        # ===== 2W Tab 详情 =====
        detail_2w = [
            ("输出人", 9),
            ("输出开始时间", 10),
            ("输出完成时间", 11),
            ("输出总耗时", 12),
            ("2W测试点数", 13),
            ("检查人", 14),
            ("检查开始时间", 15),
            ("检查完成时间", 16),
            ("检查总耗时", 17),
            ("最后更新时间", 18),
            ("最后更新人", 19)
        ]
        self._populate_detail_layout(self.scroll_layout_2w, detail_2w, get_cell)

        # ===== 4W Tab 详情 =====
        detail_4w = [
            ("输出人", 21),
            ("输出开始时间", 22),
            ("输出完成时间", 23),
            ("输出总耗时", 24),
            ("4W测试点数", 25),
            ("检查人", 26),
            ("检查开始时间", 27),
            ("检查完成时间", 28),
            ("检查总耗时", 29),
            ("最后更新时间", 30),
            ("最后更新人", 31)
        ]
        self._populate_detail_layout(self.scroll_layout_4w, detail_4w, get_cell)

    def _populate_detail_layout(self, layout, detail_list, get_cell_fn):
        """填充详情信息到指定的 layout"""
        for title, col in detail_list:
            frame = QFrame()
            frame.setStyleSheet(f"QFrame{{background:{GRAY_CARD};border-radius:6px;border:1px solid {GRAY_BORDER};}}")
            hly = QHBoxLayout(frame)
            hly.setContentsMargins(10, 8, 10, 8)
            lab_name = QLabel(f"{title}：")
            lab_name.setFont(BOLD_FONT)
            lab_name.setFixedWidth(110)
            lab_name.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            val_txt = get_cell_fn(col)
            val_label = QLabel(val_txt if val_txt else "无")
            val_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            val_label.setWordWrap(True)
            hly.addWidget(lab_name)
            hly.addWidget(val_label)
            layout.addWidget(frame)

    def get_work_status(self, val):
        return str(val).strip() if val else "待后台处理"

    def get_status_color(self, s):
        if s == "已完成": return QColor(0,180,0)
        if s == "待检查": return QColor(255,140,0)
        if s == "待转换": return QColor(150,140,0)
        if s == "待制作": return QColor(220,0,0)
        return QColor(100,100,100)

    def init_erp_database_connection(self):
        if not self.db:
            try:
                self.db = Oracle_DB.ORACLE_INIT()
                self.db.DB_CONNECT(host="cderpdb-scan", servername="prod", port=1521, username="INP", passwd="INP")
            except:
                return None
        return self.db

    def load_raw_data_from_db(self):
        try:
            fid = FACTORY_MAP[self.cb_factory.currentText()]
            sd = self.date_start.date().toString("yyyy-MM-dd")
            ed = self.date_end.date().toString("yyyy-MM-dd")
            sql = f"""
            SELECT * FROM (
                SELECT 
                    US.DATA_ID,
                    US.ITEM_NO,
                    US.REV,
                    US.ORG_ID,
                    US.CREATION_DATE,
                    US.STATUS,
                    US.REMARK ,
                    US.OUTPUT_PATH_2W,
                    US.OUTPUT_BY_2W,
                    US.OUTPUT_START_2W,
                    US.OUTPUT_FINISH_TIME_2W,
                    US.TOTAL_OUTPUT_MS_2W,
                    US.TEST_POINT_2W,
                    US.CHECK_BY_2W,
                    US.CHECK_START_2W,
                    US.CHECK_FINISH_TIME_2W,
                    US.TOTAL_CHECK_MS_2W,
                    US.LAST_UPDATE_DATE_2W,
                    US.LAST_UPDATED_BY_2W,
                    US.OUTPUT_PATH_4W,
                    US.OUTPUT_BY_4W,
                    US.OUTPUT_START_4W,
                    US.OUTPUT_FINISH_TIME_4W,
                    US.TOTAL_OUTPUT_MS_4W,
                    US.TEST_POINT_4W,
                    US.CHECK_BY_4W,
                    US.CHECK_START_4W,
                    US.CHECK_FINISH_TIME_4W,
                    US.TOTAL_CHECK_MS_4W,
                    US.LAST_UPDATE_DATE_4W,
                    US.LAST_UPDATED_BY_4W,
                    A.OPERATION_DESCRIPTION,
                    ROW_NUMBER() OVER(PARTITION BY A.ORGANIZATION_ID,SUBSTR(A.SEGMENT1,1,15) ORDER BY A.OPERATION_SEQ_NUM DESC) RN
            FROM inp.inp_flypin_probe_tool_alert us
            JOIN APPS.CUX_WIP_TOINP_V A ON A.ORGANIZATION_ID=us.ORG_ID AND SUBSTR(A.SEGMENT1,1,15)=us.ITEM_NO
            WHERE US.OPERATON_CLASSCODE='ET_DATA' AND US.ORG_ID='{fid}'
            AND (US.REMARK IS NULL OR  US.REMARK NOT LIKE '%ERP记录已输出%')
            AND TRUNC(us.CREATION_DATE) BETWEEN TO_DATE('{sd}','YYYY-MM-DD') AND TO_DATE('{ed}','YYYY-MM-DD')) WHERE RN=1 ORDER BY CREATION_DATE DESC"""
            db = self.init_erp_database_connection()
            self.raw_cache_data = db.SELECT_DIC(sql) if db else []
        except:
            self.raw_cache_data = []

    def filter_data_in_memory(self):
        kw = self.le_search.text().lower()
        st = self.cb_status.currentText()
        op = self.cb_operation.currentText()
        res = []
        ops = set()
        for r in self.raw_cache_data:
            sop = str(r.get("OPERATION_DESCRIPTION","")).strip()
            ops.add(sop)
            if kw and kw not in str(r.get("ITEM_NO","")).lower(): continue
            s = self.get_work_status(r.get("STATUS"))
            if st != "全部状态" and s != st: continue
            if op != "全部工序" and sop != op: continue
            res.append(r)
        self._combo_ = list(ops)
        self.filtered_data = res

    def update_table_and_pagination(self):
        total = len(self.filtered_data)
        self.total_page = max(1, (total+19)//20)
        self.current_page = min(self.current_page, self.total_page)
        self.spin_page.setRange(1, self.total_page)
        self.spin_page.setValue(self.current_page)
        self.lab_page.setText(f"总页数：{self.total_page}")
        self.lab_count.setText(f"总数据：{total} 条")
        self.update_table()

    def update_table(self):
        self.table.setRowCount(0)
        s = (self.current_page-1)*20
        e = s+20
        rows = self.filtered_data[s:e]
        start_num = (self.current_page-1)*self.page_size

        for i, r in enumerate(rows):
            self.table.insertRow(i)
            real_row = start_num + i + 1
            self.table.setVerticalHeaderItem(i, QTableWidgetItem(str(real_row)))

            bg = QColor("#fff") if i%2==0 else QColor("#f8f9fa")
            def v(x): return str(x) if x else ""
            did = v(r.get("DATA_ID"))
            org = v(r.get("ORG_ID"))
            factory = FACTORY_ID_TO_NAME.get(org, org)
            item = v(r.get("ITEM_NO"))
            rev = v(r.get("REV"))
            op_desc = v(r.get("OPERATION_DESCRIPTION"))
            ctime = v(r.get("CREATION_DATE"))
            remark = v(r.get("REMARK"))
            status = self.get_work_status(r.get("STATUS"))

            # item_map = {
            #     0:did,1:factory,2:item,3:rev,4:op_desc,5:ctime,7:remark,
            #     9:v(r.get("DATA_PATH")),10:v(self.user_name.get(r.get("ATTRIBUTE6"))),11:v(r.get("ATTRIBUTE7")),
            #     12:v(r.get("ATTRIBUTE8")),13:v(r.get("ATTRIBUTE9")),14:v(r.get("ATTRIBUTE10")),
            #     15:v(r.get("ATTRIBUTE11")),16:v(self.user_name.get(r.get("ATTRIBUTE12"))),17:v(r.get("ATTRIBUTE13")),
            #     18:v(r.get("ATTRIBUTE14")),19:v(r.get("ATTRIBUTE15"))
            # }

            """
            ["DATA_ID", "厂区", "料号", "版本", "在线工序", "创建时间", "状态", "备注",
            "2W输出路径", "2W输出人", "2W输出开始时间", "2W输出完成时间", "2W输出总耗时", "2W测试点", "2W检查人", "2W检查开始时间","2W检查完成时间","2W检查总耗时","2W最后更新时间","2W最后更新人",
            "4W输出路径", "4W输出人", "4W输出开始时间", "4W输出完成时间", "4W输出总耗时", "4W测试点", "4W检查人", "4W检查开始时间","4W检查完成时间","4W检查总耗时","4W最后更新时间","4W最后更新人",
            ]
            """
            item_map = {
                0:did,
                1:factory,
                2:item,
                3:rev,
                4:op_desc,
                5:ctime,
                7: remark,
                8: v(r.get("OUTPUT_PATH_2W")),
                9: v(self.user_name.get(r.get("OUTPUT_BY_2W"))),
                10: v(r.get("OUTPUT_START_2W")),
                11: v(r.get("OUTPUT_FINISH_TIME_2W")),
                12: v(r.get("TOTAL_OUTPUT_MS_2W")),
                13: v(r.get("TEST_POINT_2W")),
                14: v(self.user_name.get(r.get("CHECK_BY_2W"))),
                15: v(r.get("CHECK_START_2W")),
                16: v(r.get("CHECK_FINISH_TIME_2W")),
                17: v(r.get("TOTAL_CHECK_MS_2W")),
                18: v(r.get("LAST_UPDATE_DATE_2W")),
                19: v(self.user_name.get(r.get("LAST_UPDATED_BY_2W"))),
                20: v(r.get("OUTPUT_PATH_4W")),
                21: v(self.user_name.get(r.get("OUTPUT_BY_4W"))),
                22: v(r.get("OUTPUT_START_4W")),
                23: v(r.get("OUTPUT_FINISH_TIME_4W")),
                24: v(r.get("TOTAL_OUTPUT_MS_4W")),
                25: v(r.get("TEST_POINT_4W")),
                26: v(self.user_name.get(r.get("CHECK_BY_4W"))),
                27: v(r.get("CHECK_START_4W")),
                28: v(r.get("CHECK_FINISH_TIME_4W")),
                29: v(r.get("TOTAL_CHECK_MS_4W")),
                30: v(r.get("LAST_UPDATE_DATE_4W")),
                31: v(self.user_name.get(r.get("LAST_UPDATED_BY_4W"))),
            }
            for col, txt in item_map.items():
                cell = QTableWidgetItem(txt)
                cell.setTextAlignment(Qt.AlignCenter)
                cell.setBackground(bg)
                self.table.setItem(i, col, cell)

            st_cell = QTableWidgetItem(status)
            st_cell.setTextAlignment(Qt.AlignCenter)
            st_cell.setForeground(self.get_status_color(status))
            st_cell.setBackground(bg)
            self.table.setItem(i,6,st_cell)

    def do_search(self):
        self.current_page = 1
        self.filter_data_in_memory()
        self.update_table_and_pagination()

    def force_refresh_data(self):
        self.current_page = 1
        self.load_raw_data_from_db()
        self.filter_data_in_memory()
        self.load_operation_list()
        self.update_table_and_pagination()

    def on_factory_changed(self):
        save_config(self.cb_factory.currentText(), self.cb_status.currentText(), self.cb_operation.currentText())
        self.force_refresh_data()

    def load_operation_list(self):
        self.cb_operation.clear()
        self.cb_operation.addItem("全部工序")
        self.cb_operation.addItems(sorted(self._combo_))

    def switch_page(self, p):
        if 1 <= p <= self.total_page:
            self.current_page = p
            self.spin_page.setValue(p)
            self.update_table()

    def update_single_row(self, did):
        try:
            sql = f"""
            SELECT * FROM (
                SELECT 
                    US.DATA_ID,
                    US.ITEM_NO,
                    US.REV,
                    US.ORG_ID,
                    US.CREATION_DATE,
                    US.STATUS,
                    US.REMARK ,
                    US.OUTPUT_PATH_2W,
                    US.OUTPUT_BY_2W,
                    US.OUTPUT_START_2W,
                    US.OUTPUT_FINISH_TIME_2W,
                    US.TOTAL_OUTPUT_MS_2W,
                    US.TEST_POINT_2W,
                    US.CHECK_BY_2W,
                    US.CHECK_START_2W,
                    US.CHECK_FINISH_TIME_2W,
                    US.TOTAL_CHECK_MS_2W,
                    US.LAST_UPDATE_DATE_2W,
                    US.LAST_UPDATED_BY_2W,
                    US.OUTPUT_PATH_4W,
                    US.OUTPUT_BY_4W,
                    US.OUTPUT_START_4W,
                    US.OUTPUT_FINISH_TIME_4W,
                    US.TOTAL_OUTPUT_MS_4W,
                    US.TEST_POINT_4W,
                    US.CHECK_BY_4W,
                    US.CHECK_START_4W,
                    US.CHECK_FINISH_TIME_4W,
                    US.TOTAL_CHECK_MS_4W,
                    US.LAST_UPDATE_DATE_4W,
                    US.LAST_UPDATED_BY_4W,
                    A.OPERATION_DESCRIPTION,
                    ROW_NUMBER() OVER(PARTITION BY A.ORGANIZATION_ID,SUBSTR(A.SEGMENT1,1,15) ORDER BY A.OPERATION_SEQ_NUM DESC) RN 
            FROM 
                inp.inp_flypin_probe_tool_alert us 
                JOIN APPS.CUX_WIP_TOINP_V A ON A.ORGANIZATION_ID=us.ORG_ID AND SUBSTR(A.SEGMENT1,1,15)=us.ITEM_NO 
            WHERE US.DATA_ID='{did}') WHERE RN=1"""
            db = self.init_erp_database_connection()
            if not db: return
            dt = db.SELECT_DIC(sql)
            if not dt: return
            r = dt[0]
            tr = -1
            for row in range(self.table.rowCount()):
                it = self.table.item(row,0)
                if it and it.text() == str(did):
                    tr = row
                    break
            if tr == -1: return
            bg = self.table.item(tr,0).background()
            def v(x): return str(x) if x else ""
            factory = FACTORY_ID_TO_NAME.get(v(r.get("ORG_ID")), v(r.get("ORG_ID")))
            status = self.get_work_status(r.get("STATUS"))

            """
            ["DATA_ID", "厂区", "料号", "版本", "在线工序", "创建时间", "状态", "备注",
            "2W输出路径", "2W输出人", "2W输出开始时间", "2W输出完成时间", "2W输出总耗时", "2W测试点", "2W检查人", "2W检查开始时间","2W检查完成时间","2W检查总耗时","2W最后更新时间","2W最后更新人",
            "4W输出路径", "4W输出人", "4W输出开始时间", "4W输出完成时间", "4W输出总耗时", "4W测试点", "4W检查人", "4W检查开始时间","4W检查完成时间","4W检查总耗时","4W最后更新时间","4W最后更新人",
            ]
            """
            cells = {
                1:factory,
                4:v(r.get("OPERATION_DESCRIPTION")),
                7:v(r.get("REMARK")),
                8:v(r.get("OUTPUT_PATH_2W")),
                9:v(self.user_name.get(r.get("OUTPUT_BY_2W"))),
                10:v(r.get("OUTPUT_START_2W")),
                11:v(r.get("OUTPUT_FINISH_TIME_2W")),
                12:v(r.get("TOTAL_OUTPUT_MS_2W")),
                13:v(r.get("TEST_POINT_2W")),
                14:v(self.user_name.get(r.get("CHECK_BY_2W"))),
                15:v(r.get("CHECK_START_2W")),
                16:v(r.get("CHECK_FINISH_TIME_2W")),
                17:v(r.get("TOTAL_CHECK_MS_2W")),
                18:v(r.get("LAST_UPDATE_DATE_2W")),
                19:v(self.user_name.get(r.get("LAST_UPDATED_BY_2W"))),
                20: v(r.get("OUTPUT_PATH_4W")),
                21: v(self.user_name.get(r.get("OUTPUT_BY_4W"))),
                22: v(r.get("OUTPUT_START_4W")),
                23: v(r.get("OUTPUT_FINISH_TIME_4W")),
                24: v(r.get("TOTAL_OUTPUT_MS_4W")),
                25: v(r.get("TEST_POINT_4W")),
                26: v(self.user_name.get(r.get("CHECK_BY_4W"))),
                27: v(r.get("CHECK_START_4W")),
                28: v(r.get("CHECK_FINISH_TIME_4W")),
                29: v(r.get("TOTAL_CHECK_MS_4W")),
                30: v(r.get("LAST_UPDATE_DATE_4W")),
                31: v(self.user_name.get(r.get("LAST_UPDATED_BY_4W"))),
            }
            for c,t in cells.items():
                item = QTableWidgetItem(t)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(bg)
                self.table.setItem(tr,c,item)
            st_item = QTableWidgetItem(status)
            st_item.setTextAlignment(Qt.AlignCenter)
            st_item.setForeground(self.get_status_color(status))
            st_item.setBackground(bg)
            self.table.setItem(tr,6,st_item)
        except:
            pass

    def execute_single_task(self, fc, did, name, user, mode, output_mode):
        try:
            for f in [f"{mode}_success.flag", f"{mode}_fail.flag"]:
                if os.path.exists(f): os.remove(f)

            os.getenv('hostname')

            safe_kill_process(TARGET_PROCESS_NAME)
            script = FP_CORE_SCRIPT_PATH
            subprocess.Popen([EZFIXTURE_EXE_PATH,"-u","g","-p","g","-s",script,f"--script-param={fc},{did},{name},{mode},{user},{output_mode}"], env=os.environ.copy(), creationflags=subprocess.CREATE_NEW_CONSOLE).wait()
            ok = os.path.exists(f"{mode}_success.flag")
            for f in [f"{mode}_success.flag", f"{mode}_fail.flag"]:
                if os.path.exists(f): os.remove(f)
            return ok
        except:
            return False

    def do_2w_make(self):
        """2W资料输出"""
        if not all([self.current_did, self.current_org_id, self.current_pn]):
            QMessageBox.warning(self,"提示","请选择数据")
            return
        fc = FACTORY_ID_TO_NUM.get(self.current_org_id, self.current_org_id)
        ok = self.execute_single_task(fc, self.current_did, self.current_pn, self.LOGIN_USER, "task", "2w")
        self.showNormal()
        self.activateWindow()
        QMessageBox.information(self,"结果","2W输出成功" if ok else "2W输出失败")
        self.update_single_row(self.current_did)

    def do_2w_check(self):
        """2W资料检查"""
        if self.current_status != "待检查":
            QMessageBox.warning(self,"提示","状态不允许检查")
            return
        fc = FACTORY_ID_TO_NUM.get(self.current_org_id, self.current_org_id)
        ok = self.execute_single_task(fc, self.current_did, self.current_pn, self.LOGIN_USER, "check", "2w")
        self.showNormal()
        self.activateWindow()
        QMessageBox.information(self,"结果","2W检查成功" if ok else "2W检查失败")
        self.update_single_row(self.current_did)

    def do_4w_check(self):
        """4W资料检查"""
        if self.current_status != "待检查":
            QMessageBox.warning(self,"提示","状态不允许检查")
            return
        self.showMinimized()
        fc = FACTORY_ID_TO_NUM.get(self.current_org_id, self.current_org_id)
        ok = self.execute_single_task(fc, self.current_did, self.current_pn, self.LOGIN_USER, "check", "4w")
        self.showNormal()
        self.activateWindow()
        QMessageBox.information(self,"结果","4W检查成功" if ok else "4W检查失败")
        self.update_single_row(self.current_did)

    def do_make(self):
        """兼容旧版：2W输出"""
        self.do_2w_make()

    def do_check(self):
        """兼容旧版：2W检查"""
        self.do_2w_check()

    def do_input(self):
        msg_box = QMessageBox()
        msg_box.setWindowTitle("温馨提示")
        msg_box.setText("请选择导入资料类型")
        msg_box.setIcon(QMessageBox.Information)

        btn_2w = msg_box.addButton("2W", QMessageBox.AcceptRole)
        btn_4w = msg_box.addButton("4W", QMessageBox.RejectRole)
        btn_close = msg_box.addButton("关闭", QMessageBox.RejectRole)

        d = msg_box.exec_()

        input_mode = '2w'
        if msg_box.clickedButton() == btn_2w:
            input_mode = '2w'
        elif msg_box.clickedButton() == btn_4w:
            input_mode = '4w'
        elif msg_box.clickedButton() == btn_close:
            return
        fc = FACTORY_ID_TO_NUM.get(self.current_org_id, self.current_org_id)
        ok = self.execute_single_task(fc, self.current_did, self.current_pn, self.LOGIN_USER, "input", input_mode)
        self.update_single_row(self.current_did)

    def do_convert(self):
        # if self.current_status != "待转换":
        #     QMessageBox.warning(self,"提示","状态不允许转换")
        #     return
        try:
            subprocess.Popen([r"D:\Tpg-e\TPG-E.exe"], creationflags=subprocess.CREATE_NEW_CONSOLE).wait()
        except:
            QMessageBox.critical(self,"错误","未找到转换程序")
            return
        QMessageBox.information(self,"成功","转换完成")
        db = self.init_erp_database_connection()
        if db:
            db.SQL_EXECUTE(f"UPDATE INP.INP_FLYPIN_PROBE_TOOL_ALERT SET STATUS='待上传ERP' WHERE DATA_ID='{self.current_did}'")
        self.update_single_row(self.current_did)

    def do_4w_out(self):
        if not all([self.current_did, self.current_org_id, self.current_pn]):
            QMessageBox.warning(self,"提示","请选择数据")
            return
        fc = FACTORY_ID_TO_NUM.get(self.current_org_id, self.current_org_id)
        ok = self.execute_single_task(fc, self.current_did, self.current_pn, self.LOGIN_USER, "task", "4w")
        self.showNormal()
        self.activateWindow()
        QMessageBox.information(self,"结果","4W输出成功" if ok else "4W输出失败")
        self.update_single_row(self.current_did)

    def _get_erp_report(self):
        sql = f"""
        
        SELECT
            t.*,
            bso.operation_code
        FROM
            apps.CUX_MI_CHECKMT_VQ t,
            APPS.BOM_OPERATION_SEQUENCES BOS,
            bom_standard_operations bso
        WHERE
            1 = 1
            AND t.operation_sequence_id = bos.operation_sequence_id
            AND t.routing_sequence_id = bos.routing_sequence_id
            AND t.operation_seq_num = bos.operation_seq_num
            AND bos.standard_operation_id = bso.standard_operation_id
            AND t.ORGANIZATION_ID = bso.organization_id
            AND t.Item = '{self.current_pn[:15]}'
            AND t.ITEM_REV = '{self.current_pn[15:]}'
            AND t.ORGANIZATION_ID = {self.current_org_id}"""
        logger.info(f"""查询CUX_MI_CHECKMT_VQ是否有数据:\n{sql}""")
        db = self.init_erp_database_connection()
        if not db: return
        dt = db.SELECT_DIC(sql)
        if len(dt) > 0:
            return dt[0]
        else:
            return dict()

    def _get_basic_table(self,ORGANIZATION_ID,INVENTORY_ITEM_ID,ITEM_REV):
        sql = f"""SELECT
            *
        FROM 
            Cux.Cux_Mi_Checkmt tt
        WHERE
            tt.ORGANIZATION_ID = {ORGANIZATION_ID}
            AND tt.INVENTORY_ITEM_ID = {INVENTORY_ITEM_ID}
            AND tt.REVISION = {ITEM_REV}
            """
        logger.info(f"""通过ID查询Cux_Mi_Checkmt基表是否有数据:\n{sql}""")
        db = self.init_erp_database_connection()
        if not db: return
        dt = db.SELECT_DIC(sql)
        if len(dt) > 0:
            return dt[0]
        else:
            return dict()

    def _update_basic_table(self, *kwargs):
        """更新ERP数据"""

        sql = f"""
            UPDATE
                Cux.Cux_Mi_Checkmt
            SET 
                CHECK_TYPE = '{kwargs[0]}' ,
                CHECK_STATUS = '{kwargs[1]}' ,
                MAKE_DATE = TO_DATE('{kwargs[2]}','YYYY-MM-DD HH24:MI:SS'),
                LAST_UPDATE_DATE = TO_DATE('{kwargs[3]}','YYYY-MM-DD HH24:MI:SS'),
                LAST_UPDATED_BY = {kwargs[4]},
                CHECK_MEMO = '{kwargs[5]}',
                ATTRIBUTE1 = '{kwargs[6]}'
            WHERE
                ORGANIZATION_ID = {kwargs[7]}
                AND INVENTORY_ITEM_ID = {kwargs[8]}
                AND REVISION = {kwargs[9]}
        """
        logger.info(f"""查询Cux_Mi_Checkmt没数据，则插入数据:\n{sql}""")
        db = self.init_erp_database_connection()
        if not db: return
        dt = db.SQL_EXECUTE(sql)
        return dt

    def _insert_basic_table(self,*kwargs):
        """插入ERP数据"""
        sql = f"""
        INSERT INTO
            Cux.Cux_Mi_Checkmt (
                ORGANIZATION_ID,
                INVENTORY_ITEM_ID,
                REVISION_ID,
                ROUTING_SEQUENCE_ID,
                OPERATION_SEQUENCE_ID,
                CHECK_TYPE ,
                CHECK_STATUS ,
                CHECK_MEMO,
                MAKE_DATE,
                LAST_UPDATE_DATE ,
                LAST_UPDATED_BY ,
                CREATION_DATE ,
                CREATED_BY ,
                ATTRIBUTE1 ,
                JG_MB,
                OPERATION_CODE,
                OPERATION_DESC,
                REVISION
            )
            VALUES (
                {kwargs[0]},
                {kwargs[1]},
                {kwargs[2]},
                {kwargs[3]},
                {kwargs[4]},
                '{kwargs[5]}',
                '{kwargs[6]}',
                '{kwargs[7]}',
                TO_DATE('{kwargs[8]}','YYYY-MM-DD HH24:MI:SS'),
                TO_DATE('{kwargs[9]}','YYYY-MM-DD HH24:MI:SS'),
                {kwargs[10]},
                TO_DATE('{kwargs[11]}','YYYY-MM-DD HH24:MI:SS'),
                {kwargs[12]},
                '{kwargs[13]}',
                '{kwargs[14]}',
                '{kwargs[15]}',
                '{kwargs[16]}',
                '{kwargs[17]}'
            )
        """
        logger.info(f"""查询Cux_Mi_Checkmt没数据，则插入数据:\n{sql}""")
        db = self.init_erp_database_connection()
        if not db: return
        dt = db.SQL_EXECUTE(sql)
        return dt

    def do_upload(self, layer='2w'):
        """
        上传ERP - 自定义弹窗表单
        layer: '2w' 或 '4w'，用于区分上传来源
        """

        if not self.current_pn or not self.current_org_id:
            QMessageBox.warning(self, "提示", "请先选择一条有效数据！")
            return

        dialog = QDialog(self)
        title_layer = "2W" if layer == '2w' else "4W"
        dialog.setWindowTitle(f"ERP 上传表单 [{title_layer}资料]")
        dialog.setFixedSize(450, 380)
        dialog.setFont(GLOBAL_FONT)

        layout = QFormLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        self.cb_check_type = QComboBox()
        self.cb_check_type.addItems(["飞针", "通用"])
        self.cb_check_type.setCurrentText("飞针")
        self.cb_check_type.setStyleSheet(INPUT_NORMAL_STYLE)

        self.cb_check_status = QComboBox()
        self.cb_check_status.addItems(["OK", "待装"])
        self.cb_check_status.setCurrentText("OK")
        self.cb_check_status.setStyleSheet(INPUT_NORMAL_STYLE)

        self.edit_created_by = QLineEdit()
        self.edit_created_by.setText(self.user_name_id.get(self.USER_NAME.strip()))
        self.edit_created_by.setStyleSheet(INPUT_NORMAL_STYLE)

        self.edit_remark = QLineEdit()
        self.edit_remark.setText('')
        self.edit_remark.setStyleSheet(INPUT_NORMAL_STYLE)

        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.lbl_create_date = QLabel(now_time)

        self.edit_last_updated_by = QLineEdit()
        self.edit_last_updated_by.setText(self.user_name_id.get(self.USER_NAME.strip()))
        self.edit_last_updated_by.setStyleSheet(INPUT_NORMAL_STYLE)

        self.lbl_update_date = QLabel(now_time)

        test_point = self.current_2w_test_point if layer == '2w' else self.current_4w_test_point
        self.edit_attribute1 = QLineEdit()
        self.edit_attribute1.setText(test_point.strip() if test_point else '')
        self.edit_attribute1.setStyleSheet(INPUT_NORMAL_STYLE)

        self.lbl_jg_mb = QLabel("Y")

        layout.addRow("<b>当前料号：</b>", QLabel(f"<b>{self.current_pn}</b>"))
        layout.addRow("──────────────────────────", QLabel(""))

        layout.addRow("CHECK TYPE（检查类型）：", self.cb_check_type)
        layout.addRow("CHECK_STATUS（检查状态）：", self.cb_check_status)
        layout.addRow("CHECK_MEMO 备注：", self.edit_remark)
        layout.addRow("CREATED_BY（创建人）：", self.edit_created_by)
        layout.addRow("CREATION_DATE（创建时间）：", self.lbl_create_date)
        layout.addRow("LAST_UPDATED_BY（更新人）：", self.edit_last_updated_by)
        layout.addRow("LAST_UPDATE_DATE（更新时间）：", self.lbl_update_date)
        layout.addRow("ATTRIBUTE1（测试点数）：", self.edit_attribute1)
        layout.addRow("JG_MB（架构/面板检查）：", self.lbl_jg_mb)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, dialog
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        if not dialog.exec_():
            return

        check_type = self.cb_check_type.currentText().strip()
        check_status = self.cb_check_status.currentText().strip()
        remark = self.edit_remark.text().strip()
        created_by = self.edit_created_by.text().strip()
        creation_date = self.lbl_create_date.text().strip()
        last_updated_by = self.edit_last_updated_by.text().strip()
        last_update_date = self.lbl_update_date.text().strip()
        attribute1 = self.edit_attribute1.text().strip()
        jg_mb = self.lbl_jg_mb.text().strip()

        if not created_by or not last_updated_by or not attribute1:
            QMessageBox.warning(self, "校验失败", "创建人、更新人、测试点数不能为空！")
            return

        try:
            db = self.init_erp_database_connection()
            if not db:
                QMessageBox.critical(self, "错误", "数据库连接失败！")
                return

            rep = self._get_erp_report()
            if not rep:
                QMessageBox.warning(self, "上传失败", f"未查询到 {self.current_pn} 对应ERP基础数据！")
            else:
                t = self._get_basic_table(rep['ORGANIZATION_ID'], rep['INVENTORY_ITEM_ID'], rep['ITEM_REV'])
                if t:
                    if t['CHECK_STATUS'] is None or t['CHECK_STATUS'].strip() == '':
                        self._update_basic_table(
                            check_type,
                            check_status,
                            last_update_date,
                            last_update_date,
                            last_updated_by,
                            remark,
                            attribute1,
                            rep['ORGANIZATION_ID'],
                            rep['INVENTORY_ITEM_ID'],
                            rep['ITEM_REV']
                        )
                        QMessageBox.information(
                            self, "更新成功",
                            f"✅ 更新成功！\n\n"
                            f"检查类型：{check_type}\n"
                            f"检查状态：{check_status}\n"
                            f"备注：{remark}\n"
                            f"测试点数：{attribute1}\n"
                            f"创建人：{created_by}"
                        )
                    else:
                        QMessageBox.information(self, "上传失败", f"{self.current_pn}:Cux_Mi_Checkmt,治具状态不是空,不更新。如需更新请登入ERP手动更新")
                else:
                    s = self._insert_basic_table(
                        rep['ORGANIZATION_ID'],
                        rep['INVENTORY_ITEM_ID'],
                        rep['REVISION_ID'],
                        rep['ROUTING_SEQUENCE_ID'],
                        rep['OPERATION_SEQUENCE_ID'],
                        check_type,
                        check_status,
                        remark,
                        last_update_date,
                        last_update_date,
                        last_updated_by,
                        creation_date,
                        created_by,
                        attribute1,
                        jg_mb,
                        rep['OPERATION_CODE'],
                        rep['OPERATION_DESCRIPTION'],
                        rep['ITEM_REV']
                    )

                    if s:
                        QMessageBox.information(
                            self, "上传成功",
                            f"✅ 上传完成！\n\n"
                            f"检查类型：{check_type}\n"
                            f"检查状态：{check_status}\n"
                            f"备注：{remark}\n"
                            f"测试点数：{attribute1}\n"
                            f"创建人：{created_by}"
                        )
                    else:
                        QMessageBox.warning(
                            self, "上传失败",
                            f"检查类型：{check_type}\n"
                            f"检查状态：{check_status}\n"
                            f"备注：{remark}\n"
                            f"测试点数：{attribute1}\n"
                            f"创建人：{created_by}"
                        )

            if db:
                db.SQL_EXECUTE(f"UPDATE INP.INP_FLYPIN_PROBE_TOOL_ALERT SET STATUS='已完成' WHERE DATA_ID='{self.current_did}'")
            self.update_single_row(self.current_did)

        except Exception as e:
            QMessageBox.critical(self, "上传异常", f"错误：{str(e)}")

    def closeEvent(self, e):
        self.refresh_timer.stop()
        e.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = FlyPinWindow("","Admin","飞针测试资料管理系统","V2.1","2026-01-01","rphe","SUNTAK SOFTWARE GROUP © All Rights Reserved")
    win.show()
    sys.exit(app.exec_())
