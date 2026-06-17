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
                             QTableWidget, QTableWidgetItem, QPushButton, QLineEdit,
                             QLabel, QMessageBox, QSpinBox, QHeaderView, QComboBox,
                             QDateEdit, QFrame, QScrollArea, QSizePolicy,
                             QDialog, QFormLayout,QDialogButtonBox)
from PyQt5.QtCore import Qt, QDate, QTimer
from PyQt5.QtGui import QFont, QColor, QIcon
from PyQt5 import QtGui
import icon_rc
from datetime import datetime

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

# ===================== 工厂映射配置 =====================
FACTORY_MAP = {"江门一厂": "85", "江门二厂": "107", "珠海一厂": "168", "珠海二厂": "228", "大连电子": "84"}
FACTORY_MAP_NUM = {"JM1": "85", "JM2": "107", "ZH1": "168", "ZH2": "228", "DL": "84"}
FACTORY_ID_TO_NAME = {v: k for k, v in FACTORY_MAP.items()}
FACTORY_ID_TO_NUM = {v: k for k, v in FACTORY_MAP_NUM.items()}

def safe_kill_process(process_name):
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info["name"] and proc.info["name"].lower() == process_name.lower():
                    os.system(f"taskkill /f /pid {proc.info['pid']}")
            except:
                continue
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

    def init_ui(self):
        now = datetime.now().strftime("%Y-%m-%d")
        self.setWindowTitle(f"{self.SOFTWARE_NAME} {self.SOFTWARE_VERSION} | {now}  当前用户:{self.USER_NAME}")
        self.resize(1400, 800)
        self.setMinimumSize(1400, 600)
        self.setFont(GLOBAL_FONT)
        self.setStyleSheet(GLOBAL_STYLE)
        # icon_path = os.path.join(os.getcwd(), "logo.png")
        # if os.path.exists(icon_path):
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/logo/image/logo.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 12, 12, 12)

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
        self.cb_status.addItems(["全部状态", "未运行", "未输出", "未检查", "未转换", "已转换", "已完成"])
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
        main_layout.addWidget(search_frame)

        # 主体布局
        content_layout = QHBoxLayout()
        left_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setFont(GLOBAL_FONT)
        self.headers = ["DATA_ID", "厂区", "料号", "版本", "在线工序", "创建时间", "状态", "备注", "操作",
                        "输出路径", "输出人", "输出开始", "输出完成", "输出耗时", "2W", "4W", "检查人",
                        "检查开始", "检查完成", "检查耗时"]
        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)

        col_width = {0:75,1:85,2:140,3:60,4:110,5:140,6:80,7:200,8:0,9:0,10:0,11:0,12:0,13:0,14:0,15:0,16:0,17:0,18:0,19:0}
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

        # 右侧详情面板【修复详情布局】
        detail_frame = QFrame()
        detail_frame.setStyleSheet(f"QFrame{{background:{WHITE};border-radius:8px;border:1px solid {GRAY_BORDER};}}")
        detail_frame.setFixedWidth(400)
        detail_layout = QVBoxLayout(detail_frame)
        detail_layout.setContentsMargins(0,0,0,0)
        detail_layout.setSpacing(0)

        #标题栏
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

        #按钮栏
        btn_frame = QFrame()
        btn_frame.setStyleSheet(f"QFrame{{border-bottom:1px solid {GRAY_BORDER};}}")
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(12,10,12,10)
        btn_layout.setSpacing(12)
        self.btn_output = QPushButton("📤 输出")
        self.btn_4w_out = QPushButton("📦 4W输出")
        self.btn_check = QPushButton("📋 检查")
        self.btn_input = QPushButton("📋 导入")
        self.btn_convert = QPushButton("🔄 转换")
        for btn in [self.btn_output, self.btn_4w_out, self.btn_check, self.btn_input,self.btn_convert]:
            btn.setFixedSize(70,34)
        self.btn_output.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_4w_out.setStyleSheet(BUTTON_PRIMARY_STYLE)
        self.btn_check.setStyleSheet(BUTTON_WARN_STYLE)
        self.btn_input.setStyleSheet(BUTTON_WARN_STYLE)
        self.btn_convert.setStyleSheet(BUTTON_SUCCESS_STYLE)
        btn_layout.addWidget(self.btn_output)
        btn_layout.addWidget(self.btn_check)
        btn_layout.addWidget(self.btn_4w_out)
        btn_layout.addWidget(self.btn_input)
        btn_layout.addWidget(self.btn_convert)
        detail_layout.addWidget(btn_frame)

        #滚动详情区
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.setContentsMargins(12,12,12,12)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)
        detail_layout.addWidget(self.scroll_area)
        content_layout.addWidget(detail_frame, stretch=30)
        main_layout.addLayout(content_layout)

        # 按钮栏
        upload_frame = QFrame()
        upload_frame.setStyleSheet(f"QFrame{{border-bottom:1px solid {GRAY_BORDER};}}")
        upload_layout = QHBoxLayout(upload_frame)
        upload_layout.setContentsMargins(12, 10, 12, 10)
        upload_layout.setSpacing(12)
        self.upload_data = QPushButton("📤 上传ERP")
        self.upload_data.setFixedSize(300, 34)
        self.upload_data.setStyleSheet(BUTTON_PRIMARY_STYLE)
        upload_layout.addWidget(self.upload_data)
        detail_layout.addWidget(upload_frame)

        # 底部版权
        info_text = f"""<div style='line-height:1.5;'>
                <span style='font-size:10pt; font-weight:bold; color:{PRIMARY_COLOR};'>{self.SOFTWARE_NAME} {self.SOFTWARE_VERSION}</span><br/>
                <span style='font-size:9pt; color:{GRAY_TEXT_LIGHT};'>{self.COPYRIGHT_INFO}</span><br/>
                <span style='font-size:9pt; color:{GRAY_TEXT_LIGHT};'>开发者：{self.DEVELOPER} | 发布时间：{self.release_date}</span></div>
                """
        # bottom_label = QLabel(f"{self.SOFTWARE_NAME} {self.SOFTWARE_VERSION} | {self.DEVELOPER} | {self.COPYRIGHT_INFO}")
        bottom_label = QLabel(info_text)
        bottom_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(bottom_label)

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

        self.btn_output.clicked.connect(self.do_make)
        self.btn_4w_out.clicked.connect(self.do_4w_out)
        self.btn_check.clicked.connect(self.do_check)
        self.btn_input.clicked.connect(self.do_input)
        self.btn_convert.clicked.connect(self.do_convert)
        self.upload_data.clicked.connect(self.do_upload)

    def open_file_folder(self):
        """点击按钮打开文件所在文件夹"""
        path = self.current_file_path.strip()
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "提示", "文件路径不存在或为空！")
            return

        # 打开文件夹
        if os.path.isdir(path):
            os.startfile(path)
        else:
            folder_path = os.path.dirname(path)
            if os.path.exists(folder_path):
                os.startfile(folder_path)

    def update_detail(self):
        # 清空原有详情
        while self.scroll_layout.count() > 0:
            item = self.scroll_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        items = self.table.selectedItems()
        if not items:
            self.btn_output.setEnabled(False)
            self.btn_check.setEnabled(False)
            self.btn_convert.setEnabled(False)
            self.btn_4w_out.setEnabled(False)
            self.btn_input.setEnabled(False)
            self.upload_data.setEnabled(False)
            # 空白提示
            tip_label = QLabel("请在左侧表格选择一行数据查看详情")
            tip_label.setAlignment(Qt.AlignCenter)
            tip_label.setStyleSheet(f"color:{GRAY_TEXT_LIGHT};font-size:10pt;padding:40px 0;")
            self.scroll_layout.addWidget(tip_label)
            return

        row_idx = items[0].row()

        # 读取选中行各列
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
        self.current_file_path = get_cell(9)  # 保存当前路径
        self.current_test_point = get_cell(14)

        # self.upload_data.setEnabled(False)

        # 按钮可用状态
        self.btn_output.setEnabled(True)
        self.btn_check.setEnabled(True)
        self.btn_convert.setEnabled(True)
        self.btn_4w_out.setEnabled(True)
        self.btn_input.setEnabled(True)
        self.upload_data.setEnabled(True)
        if self.current_status in ["未运行", "未输出"]:
            self.btn_check.setEnabled(False)
            self.btn_convert.setEnabled(False)
            self.btn_4w_out.setEnabled(False)
            self.btn_input.setEnabled(False)
            self.upload_data.setEnabled(False)
        elif self.current_status == "未检查":
            self.btn_convert.setEnabled(False)
            self.btn_4w_out.setEnabled(False)
            self.btn_input.setEnabled(False)
            self.upload_data.setEnabled(False)
        elif self.current_status == "未转换":
            self.btn_check.setEnabled(False)
            self.btn_4w_out.setEnabled(False)
            self.upload_data.setEnabled(False)
        elif self.current_status == "已完成":
            self.btn_check.setEnabled(False)
            self.upload_data.setEnabled(False)

        # 详情字段配置（标题，列号）
        detail_list = [
            ("输出文件路径", 9),
            ("输出人", 10),
            ("输出开始时间", 11),
            ("输出完成时间", 12),
            ("输出总耗时", 13),
            ("2W测试点数", 14),
            ("4W测试点数", 15),
            ("检查人", 16),
            ("检查开始时间", 17),
            ("检查完成时间", 18),
            ("检查总耗时", 19)
        ]
        for title, col in detail_list:
            frame = QFrame()
            frame.setStyleSheet(f"QFrame{{background:{GRAY_CARD};border-radius:6px;border:1px solid {GRAY_BORDER};}}")
            hly = QHBoxLayout(frame)
            hly.setContentsMargins(10, 8, 10, 8)
            lab_name = QLabel(f"{title}：")
            lab_name.setFont(BOLD_FONT)
            lab_name.setFixedWidth(120)
            lab_name.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            val_txt = get_cell(col)
            val_label = QLabel(val_txt if val_txt else "无")
            val_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            val_label.setWordWrap(True)
            hly.addWidget(lab_name)
            hly.addWidget(val_label)

            # ====================== 核心修改 ======================
            # 只有【输出文件路径】添加按钮
            if title == "输出文件路径" and val_txt:
                path_btn = QPushButton("📂")
                path_btn.setFixedSize(30, 26)
                path_btn.setStyleSheet(BUTTON_PRIMARY_STYLE)
                # 绑定点击打开文件夹
                path_btn.clicked.connect(lambda: self.open_file_folder())
                hly.addWidget(path_btn)
            # =======================================================

            self.scroll_layout.addWidget(frame)

    def get_work_status(self, val):
        return str(val).strip() if val else "未运行"

    def get_status_color(self, s):
        if s == "已完成": return QColor(0,180,0)
        if s == "未检查": return QColor(255,140,0)
        if s == "未转换": return QColor(150,140,0)
        if s == "未输出": return QColor(220,0,0)
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
            sql = f"""SELECT * FROM (SELECT us.DATA_ID,us.ITEM_NO,us.REV,us.ORG_ID,us.CREATION_DATE,us.ATTRIBUTE16,us.REMARK,us.DATA_PATH,
            us.ATTRIBUTE6,us.ATTRIBUTE7,us.ATTRIBUTE8,us.ATTRIBUTE9,us.ATTRIBUTE10,us.ATTRIBUTE11,us.ATTRIBUTE12,us.ATTRIBUTE13,
            us.ATTRIBUTE14,us.ATTRIBUTE15,A.OPERATION_DESCRIPTION,
            ROW_NUMBER() OVER(PARTITION BY A.ORGANIZATION_ID,SUBSTR(A.SEGMENT1,1,15) ORDER BY A.OPERATION_SEQ_NUM DESC) RN
            FROM inp.inp_flypin_probe_tool_alert us
            JOIN APPS.CUX_WIP_TOINP_V A ON A.ORGANIZATION_ID=us.ORG_ID AND SUBSTR(A.SEGMENT1,1,15)=us.ITEM_NO
            WHERE US.OPERATON_CLASSCODE='ET_DATA' AND US.ORG_ID='{fid}'
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
            s = self.get_work_status(r.get("ATTRIBUTE16"))
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
            #原生行号赋值（分页自动累加）
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
            status = self.get_work_status(r.get("ATTRIBUTE16"))

            item_map = {
                0:did,1:factory,2:item,3:rev,4:op_desc,5:ctime,7:remark,
                9:v(r.get("DATA_PATH")),10:v(self.user_name.get(r.get("ATTRIBUTE6"))),11:v(r.get("ATTRIBUTE7")),
                12:v(r.get("ATTRIBUTE8")),13:v(r.get("ATTRIBUTE9")),14:v(r.get("ATTRIBUTE10")),
                15:v(r.get("ATTRIBUTE11")),16:v(self.user_name.get(r.get("ATTRIBUTE12"))),17:v(r.get("ATTRIBUTE13")),
                18:v(r.get("ATTRIBUTE14")),19:v(r.get("ATTRIBUTE15"))
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
            sql = f"SELECT * FROM (SELECT us.DATA_ID,us.ITEM_NO,us.REV,us.ORG_ID,us.CREATION_DATE,us.ATTRIBUTE16,us.REMARK,us.DATA_PATH,us.ATTRIBUTE6,us.ATTRIBUTE7,us.ATTRIBUTE8,us.ATTRIBUTE9,us.ATTRIBUTE10,us.ATTRIBUTE11,us.ATTRIBUTE12,us.ATTRIBUTE13,us.ATTRIBUTE14,us.ATTRIBUTE15,A.OPERATION_DESCRIPTION,ROW_NUMBER() OVER(PARTITION BY A.ORGANIZATION_ID,SUBSTR(A.SEGMENT1,1,15) ORDER BY A.OPERATION_SEQ_NUM DESC) RN FROM inp.inp_flypin_probe_tool_alert us JOIN APPS.CUX_WIP_TOINP_V A ON A.ORGANIZATION_ID=us.ORG_ID AND SUBSTR(A.SEGMENT1,1,15)=us.ITEM_NO WHERE US.DATA_ID='{did}') WHERE RN=1"
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
            status = self.get_work_status(r.get("ATTRIBUTE16"))
            cells = {1:factory,4:v(r.get("OPERATION_DESCRIPTION")),7:v(r.get("REMARK")),9:v(r.get("DATA_PATH")),10:v(self.user_name.get(r.get("ATTRIBUTE6"))),11:v(r.get("ATTRIBUTE7")),12:v(r.get("ATTRIBUTE8")),13:v(r.get("ATTRIBUTE9")),14:v(r.get("ATTRIBUTE10")),15:v(r.get("ATTRIBUTE11")),16:v(self.user_name.get(r.get("ATTRIBUTE12"))),17:v(r.get("ATTRIBUTE13")),18:v(r.get("ATTRIBUTE14")),19:v(r.get("ATTRIBUTE15"))}
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
            safe_kill_process(TARGET_PROCESS_NAME)
            script = FP_CORE_SCRIPT_PATH
            subprocess.Popen([EZFIXTURE_EXE_PATH,"-u","g","-p","g","-s",script,f"--script-param={fc},{did},{name},{mode},{user},{output_mode}"], env=os.environ.copy(), creationflags=subprocess.CREATE_NEW_CONSOLE).wait()
            ok = os.path.exists(f"{mode}_success.flag")
            for f in [f"{mode}_success.flag", f"{mode}_fail.flag"]:
                if os.path.exists(f): os.remove(f)
            return ok
        except:
            return False

    def do_make(self):
        if not all([self.current_did, self.current_org_id, self.current_pn]):
            QMessageBox.warning(self,"提示","请选择数据")
            return
        self.close()
        fc = FACTORY_ID_TO_NUM.get(self.current_org_id, self.current_org_id)
        ok = self.execute_single_task(fc, self.current_did, self.current_pn, self.LOGIN_USER, "task", "both")
        QMessageBox.information(self,"结果","输出成功" if ok else "输出失败")
        self.update_single_row(self.current_did)
        self.show()

    def do_check(self):
        if self.current_status != "未检查":
            QMessageBox.warning(self,"提示","状态不允许检查")
            return
        self.close()
        fc = FACTORY_ID_TO_NUM.get(self.current_org_id, self.current_org_id)
        ok = self.execute_single_task(fc, self.current_did, self.current_pn, self.LOGIN_USER, "check", "both")
        QMessageBox.information(self,"结果","检查成功" if ok else "检查失败")
        self.update_single_row(self.current_did)
        self.show()

    def do_input(self):
        # 替换你原来的那行代码
        # 创建自定义信息弹窗
        msg_box = QMessageBox()
        msg_box.setWindowTitle("温馨提示")  # 窗口标题
        msg_box.setText("请选择导入资料类型")  # 提示内容
        msg_box.setIcon(QMessageBox.Information)  # 信息图标

        # 添加自定义按钮（文字：2W、4W，自动带关闭按钮）
        btn_2w = msg_box.addButton("2W", QMessageBox.AcceptRole)
        btn_4w = msg_box.addButton("4W", QMessageBox.RejectRole)
        btn_close = msg_box.addButton("关闭", QMessageBox.RejectRole)

        # 显示弹窗并获取点击的按钮
        d = msg_box.exec_()

        input_mode = '2w'
        # 判断用户点击了哪个按钮
        if msg_box.clickedButton() == btn_2w:
            input_mode = '2w'
        elif msg_box.clickedButton() == btn_4w:
            input_mode = '4w'
        elif msg_box.clickedButton() == btn_close:
            return
        self.close()
        fc = FACTORY_ID_TO_NUM.get(self.current_org_id, self.current_org_id)
        ok = self.execute_single_task(fc, self.current_did, self.current_pn, self.LOGIN_USER, "input", input_mode)
        self.update_single_row(self.current_did)
        self.show()

    def do_convert(self):
        # if self.current_status != "未转换":
        #     QMessageBox.warning(self,"提示","状态不允许转换")
        #     return
        self.close()
        try:
            subprocess.Popen([r"D:\Tpg-e\TPG-E.exe"], creationflags=subprocess.CREATE_NEW_CONSOLE).wait()
        except:
            QMessageBox.critical(self,"错误","未找到转换程序")
            self.show()
            return
        QMessageBox.information(self,"成功","转换完成")
        db = self.init_erp_database_connection()
        if db:
            db.SQL_EXECUTE(f"UPDATE INP.INP_FLYPIN_PROBE_TOOL_ALERT SET ATTRIBUTE16='已转换' WHERE DATA_ID='{self.current_did}'")
        self.update_single_row(self.current_did)
        self.show()

    def do_4w_out(self):
        if not all([self.current_did, self.current_org_id, self.current_pn]):
            QMessageBox.warning(self,"提示","请选择数据")
            return
        self.close()
        fc = FACTORY_ID_TO_NUM.get(self.current_org_id, self.current_org_id)
        ok = self.execute_single_task(fc, self.current_did, self.current_pn, self.LOGIN_USER, "4w_out", "4w")
        QMessageBox.information(self,"结果","4W输出成功" if ok else "4W输出失败")
        self.update_single_row(self.current_did)
        self.show()

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
        # return
        db = self.init_erp_database_connection()
        if not db: return
        dt = db.SQL_EXECUTE(sql)
        return dt

    def do_upload(self):
        """
        上传ERP - 自定义弹窗表单
        """

        # 1. 基础校验
        if not self.current_pn or not self.current_org_id:
            QMessageBox.warning(self, "提示", "请先选择一条有效数据！")
            return

        # ============== 创建弹窗 ==============
        dialog = QDialog(self)
        dialog.setWindowTitle("ERP 上传表单")
        dialog.setFixedSize(450, 380)
        dialog.setFont(GLOBAL_FONT)

        layout = QFormLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # ---------------- 字段定义 ----------------
        # 1. CHECK TYPE
        self.cb_check_type = QComboBox()
        self.cb_check_type.addItems(["飞针", "通用"])
        self.cb_check_type.setCurrentText("飞针")
        self.cb_check_type.setStyleSheet(INPUT_NORMAL_STYLE)

        # 2. CHECK STATUS
        self.cb_check_status = QComboBox()
        self.cb_check_status.addItems(["OK", "待装"])
        self.cb_check_status.setCurrentText("OK")
        self.cb_check_status.setStyleSheet(INPUT_NORMAL_STYLE)

        # 3. CREATED_BY 创建人
        self.edit_created_by = QLineEdit()
        self.edit_created_by.setText(self.user_name_id.get(self.USER_NAME.strip()))
        self.edit_created_by.setStyleSheet(INPUT_NORMAL_STYLE)

        # 3. 备注 手填
        self.edit_remark = QLineEdit()
        self.edit_remark.setText('')
        self.edit_remark.setStyleSheet(INPUT_NORMAL_STYLE)

        # 5. CREATION_DATE 创建时间
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.lbl_create_date = QLabel(now_time)

        # 6. LAST_UPDATED_BY 更新人
        self.edit_last_updated_by = QLineEdit()
        self.edit_last_updated_by.setText(self.user_name_id.get(self.USER_NAME.strip()))
        self.edit_last_updated_by.setStyleSheet(INPUT_NORMAL_STYLE)

        # 7. LAST_UPDATE_DATE 更新时间
        self.lbl_update_date = QLabel(now_time)

        # 8. ATTRIBUTE1 测试点数
        self.edit_attribute1 = QLineEdit()
        self.edit_attribute1.setText(self.current_test_point.strip())
        self.edit_attribute1.setStyleSheet(INPUT_NORMAL_STYLE)

        # 9. JG_MB 架构/面板检查
        self.lbl_jg_mb = QLabel("Y")

        # 料号显示（只读）
        layout.addRow("<b>当前料号：</b>", QLabel(f"<b>{self.current_pn}</b>"))
        layout.addRow("──────────────────────────", QLabel(""))

        # 表单布局
        layout.addRow("CHECK TYPE（检查类型）：", self.cb_check_type)
        layout.addRow("CHECK_STATUS（检查状态）：", self.cb_check_status)
        layout.addRow("CHECK_MEMO 备注：", self.edit_remark)
        layout.addRow("CREATED_BY（创建人）：", self.edit_created_by)
        layout.addRow("CREATION_DATE（创建时间）：", self.lbl_create_date)
        layout.addRow("LAST_UPDATED_BY（更新人）：", self.edit_last_updated_by)
        layout.addRow("LAST_UPDATE_DATE（更新时间）：", self.lbl_update_date)
        layout.addRow("ATTRIBUTE1（测试点数）：", self.edit_attribute1)
        layout.addRow("JG_MB（架构/面板检查）：", self.lbl_jg_mb)

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, dialog
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)

        # ============== 打开弹窗，等待确认 ==============
        if not dialog.exec_():
            return  # 取消

        # ============== 获取表单值 ==============
        check_type = self.cb_check_type.currentText().strip()
        check_status = self.cb_check_status.currentText().strip()
        remark = self.edit_remark.text().strip()
        created_by = self.edit_created_by.text().strip()
        creation_date = self.lbl_create_date.text().strip()
        last_updated_by = self.edit_last_updated_by.text().strip()
        last_update_date = self.lbl_update_date.text().strip()
        attribute1 = self.edit_attribute1.text().strip()
        jg_mb = self.lbl_jg_mb.text().strip()

        # 非空校验
        if not created_by or not last_updated_by or not attribute1:
            QMessageBox.warning(self, "校验失败", "创建人、更新人、测试点数不能为空！")
            return

        # ============== 执行上传逻辑 ==============
        try:
            db = self.init_erp_database_connection()
            if not db:
                QMessageBox.critical(self, "错误", "数据库连接失败！")
                return

            # 你原来的 ERP 逻辑（保留）
            rep = self._get_erp_report()
            # print(rep)
            # return
            if not rep:
                QMessageBox.warning(self, "上传失败", f"未查询到 {self.current_pn} 对应ERP基础数据！")
                # return
            else:
                t = self._get_basic_table(rep['ORGANIZATION_ID'], rep['INVENTORY_ITEM_ID'], rep['ITEM_REV'])
                if t:
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
                    # else:
                    #     QMessageBox.information(self, "上传失败", f"{self.current_pn}:Cux_Mi_Checkmt,基表已存在数据。")
                    return
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
                        # 执行插入/更新（你可以把上面表单字段拼进 SQL）
                        # 这里只做成功提示
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
                db.SQL_EXECUTE(f"UPDATE INP.INP_FLYPIN_PROBE_TOOL_ALERT SET ATTRIBUTE16='已完成' WHERE DATA_ID='{self.current_did}'")
            self.update_single_row(self.current_did)

        except Exception as e:
            QMessageBox.critical(self, "上传异常", f"错误：{str(e)}")


    def closeEvent(self, e):
        self.refresh_timer.stop()
        e.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = FlyPinWindow("","Admin","飞针测试资料管理系统","V2.0","2026-01-01","rphe","SUNTAK SOFTWARE GROUP © All Rights Reserved")
    win.show()
    sys.exit(app.exec_())