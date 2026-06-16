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
File            : login.py
Description     : 【无人值守】飞针测试 - 登录页
功能流程：
    1. 飞针测试系统 登录页 + 独立注册弹窗 + 修改密码
    2. 数据库表：INP_FLYPIN_USER
    3. 工厂改为固定下拉列表
    4. 增加：记住密码 + 密码加密存储 + 自动加载
#---------------------------------------------------------#
"""
import sys, os, re
from datetime import datetime
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QDialog, QFormLayout, QHBoxLayout,
                             QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon

from package.Oracle_DB import ORACLE_INIT
from main import FlyPinWindow
import icon_rc

# ===================== 加密工具（修复可用版） =====================
def encrypt_text(text):
    try:
        key = "suntak_flypin_2025"
        encrypted = ''.join([chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(text)])
        return encrypted.encode('latin1').hex()
    except:
        return text

def decrypt_text(text):
    try:
        key = "suntak_flypin_2025"
        dec_bytes = bytes.fromhex(text)
        dec_str = dec_bytes.decode('latin1')
        return ''.join([chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(dec_str)])
    except:
        return ""

# ===================== 配置文件操作 =====================
CONFIG_FILE = "user_config.dat"

def save_user(user_id, pwd):
    try:
        data = f"{user_id}|{encrypt_text(pwd)}"
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(data)
    except:
        pass

def load_user():
    try:
        if not os.path.exists(CONFIG_FILE):
            return "", ""
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            txt = f.read().strip()
        if "|" not in txt:
            return "", ""
        uid, epwd = txt.split("|", 1)
        return uid.strip(), decrypt_text(epwd.strip())
    except:
        return "", ""

# ===================== 全局版本版权（统一入口） =====================
SOFTWARE_NAME = "崇达飞针测试管理系统"
SOFTWARE_VERSION = "V3.4 正式版"
release_date = "2026-06-16"
DEVELOPER = "何瑞鹏"
COPYRIGHT_INFO = "Copyright © SUNTAK 2026 All Rights Reserved."

# 全局样式配色
PRIMARY_COLOR = "#409EFF"
GRAY_LIGHT = "#F5F7FA"
GRAY_BORDER = "#DCDFE6"

# 工厂下拉固定选项
FACTORY_LIST = [
    "请选择工厂",
    "江门一厂",
    "江门二厂",
    "珠海一厂",
    "珠海二厂",
    "大连电子"
]


# ===================== 修改密码弹窗 =====================
class ChangePwdDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("修改密码")
        self.setFixedSize(360, 260)
        self.setStyleSheet(f"""
            QWidget{{background:{GRAY_LIGHT};}}
            QLineEdit{{
                border:1px solid {GRAY_BORDER};border-radius:4px;padding-left:8px;height:32px;
            }}
        """)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout()
        layout.setContentsMargins(30,30,30,20)
        layout.setSpacing(15)
        layout.setLabelAlignment(Qt.AlignRight)

        self.edit_user = QLineEdit()
        self.edit_old = QLineEdit()
        self.edit_new = QLineEdit()
        self.edit_confirm = QLineEdit()
        self.edit_old.setEchoMode(QLineEdit.Password)
        self.edit_new.setEchoMode(QLineEdit.Password)
        self.edit_confirm.setEchoMode(QLineEdit.Password)

        layout.addRow("用户ID：", self.edit_user)
        layout.addRow("原密码：", self.edit_old)
        layout.addRow("新密码：", self.edit_new)
        layout.addRow("确认密码：", self.edit_confirm)

        btn_layout = QHBoxLayout()
        btn_save = QPushButton("修改")
        btn_cancel = QPushButton("取消")
        btn_save.setMinimumHeight(34)
        btn_cancel.setMinimumHeight(34)

        btn_save.setStyleSheet("background:#409EFF;color:white;border:none;border-radius:4px;")
        btn_cancel.setStyleSheet("background:#999;color:white;border:none;border-radius:4px;")

        btn_save.clicked.connect(self.do_change)
        btn_cancel.clicked.connect(self.close)

        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)

        main = QVBoxLayout()
        main.addLayout(layout)
        main.addLayout(btn_layout)
        self.setLayout(main)

    def do_change(self):
        user_id = self.edit_user.text().strip()
        old_pwd = self.edit_old.text().strip()
        new_pwd = self.edit_new.text().strip()
        confirm_pwd = self.edit_confirm.text().strip()

        if not user_id or not old_pwd or not new_pwd or not confirm_pwd:
            QMessageBox.warning(self, "提示", "所有项均不能为空！")
            return

        if new_pwd != confirm_pwd:
            QMessageBox.warning(self, "提示", "两次新密码不一致！")
            return

        sql = f"SELECT PASS_WORD FROM INP_FLYPIN_USER WHERE USER_ID='{user_id}'"
        data = self.db.SELECT_DIC(sql)
        if not data:
            QMessageBox.warning(self, "错误", "用户ID不存在！")
            return

        if data[0]["PASS_WORD"] != old_pwd:
            QMessageBox.warning(self, "错误", "原密码错误！")
            return

        up_sql = f"""
            UPDATE INP_FLYPIN_USER
            SET PASS_WORD='{new_pwd}',
                UPDATE_BY='{user_id}',
                UPDATE_TIME=SYSDATE
            WHERE USER_ID='{user_id}'
        """
        ok = self.db.SQL_EXECUTE(up_sql)
        if ok:
            QMessageBox.information(self, "成功", "密码修改成功！")
            self.close()
        else:
            QMessageBox.critical(self, "失败", "修改失败！")


# ===================== 注册弹窗 =====================
class RegisterDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("新用户注册")
        self.setFixedSize(420, 380)
        self.setStyleSheet(f"""
        QWidget{{background:{GRAY_LIGHT};}}
        QLineEdit,QComboBox{{
            border:1px solid {GRAY_BORDER};
            border-radius:4px;
            padding-left:8px;
            height:32px;
            font-size:10pt;
        }}
        QLineEdit:focus,QComboBox:focus{{border-color:{PRIMARY_COLOR};}}
        """)
        self.init_ui()

    def init_ui(self):
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(30, 30, 30, 20)

        self.reg_verification_code = QLineEdit()
        self.edit_userid = QLineEdit()
        self.edit_pwd = QLineEdit()
        self.edit_pwd.setEchoMode(QLineEdit.Password)
        self.edit_username = QLineEdit()

        self.cb_role = QComboBox()
        self.cb_role.addItems(["普通用户", "管理员"])

        self.cb_factory = QComboBox()
        self.cb_factory.addItems(FACTORY_LIST)

        self.edit_email = QLineEdit()

        form_layout.addRow("注册验证码：", self.reg_verification_code)
        form_layout.addRow("用户ID：", self.edit_userid)
        form_layout.addRow("登录密码：", self.edit_pwd)
        form_layout.addRow("用户名称：", self.edit_username)
        form_layout.addRow("用户角色：", self.cb_role)
        form_layout.addRow("所属工厂：", self.cb_factory)
        form_layout.addRow("邮箱地址：", self.edit_email)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("确认注册")
        btn_cancel = QPushButton("取消")
        btn_ok.setMinimumHeight(35)
        btn_cancel.setMinimumHeight(35)

        btn_ok.setStyleSheet(f"""
        QPushButton{{background:{PRIMARY_COLOR};color:#fff;border:none;border-radius:4px;}}
        QPushButton:hover{{background:#337ecc;}}
        """)
        btn_cancel.setStyleSheet("""
        QPushButton{{background:#999;color:#fff;border:none;border-radius:4px;}}
        QPushButton:hover{{background:#777;}}
        """)

        btn_ok.clicked.connect(self.do_reg)
        btn_cancel.clicked.connect(self.close)

        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)

        main_layout = QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def do_reg(self):
        reg_verification_code = self.reg_verification_code.text().strip()
        user_id = self.edit_userid.text().strip()
        pwd = self.edit_pwd.text().strip()
        user_name = self.edit_username.text().strip()
        role_text = self.cb_role.currentText()
        factory = self.cb_factory.currentText().strip()
        email = self.edit_email.text().strip()

        if reg_verification_code != 'suntak-incam':
            QMessageBox.warning(self, "提示", "注册验证码错误,请联系管理员！")
            return

        if not user_id or not pwd or not user_name:
            QMessageBox.warning(self, "提示", "用户ID、密码、用户名称不能为空！")
            return

        if factory == "请选择工厂":
            QMessageBox.warning(self, "提示", "请选择所属工厂！")
            return

        role_val = "ADMIN" if role_text == "管理员" else "USER"

        chk_sql = f"SELECT 1 FROM INP_FLYPIN_USER WHERE USER_ID = '{user_id}'"
        res = self.db.SELECT_DIC(chk_sql)
        if res:
            QMessageBox.warning(self, "提示", "该用户ID已存在，请更换！")
            return

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        insert_sql = f"""
        INSERT INTO INP_FLYPIN_USER
            (
                ID,USER_ID,PASS_WORD,USER_NAME,USER_ROLE,PRIVILEGE,
                FACTORY,E_MAIL,STATUS,CREATE_BY,CREATE_TIME
            )
        VALUES
            (
                INP_FLYPIN_USER_SEQ.NEXTVAL,
                '{user_id}','{pwd}','{user_name}','{role_val}',1,
                '{factory}','{email}',0,'SELF',
                TO_DATE('{now_str}','YYYY-MM-DD HH24:MI:SS')
            )
        """
        ret = self.db.SQL_EXECUTE(insert_sql)
        if ret:
            QMessageBox.information(self, "成功", "注册成功！请返回登录")
            self.close()
        else:
            QMessageBox.critical(self, "失败", "注册写入数据库失败！")


# ===================== 主登录窗口 =====================
class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_oracle_env()
        self.setWindowTitle(f"{SOFTWARE_NAME} - 登录入口")
        self.setFixedSize(420, 350)

        # icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/logo/image/logo.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)

        self.setFont(QFont("微软雅黑", 10))
        self.db = ORACLE_INIT()
        self.db.DB_CONNECT()
        self.init_ui()

        # ========== 自动加载记住的账号密码 ==========
        uid, pwd = load_user()
        if uid:
            self.edit_user.setText(uid)
        if pwd:
            self.edit_pwd.setText(pwd)

    def init_oracle_env(self):
        try:
            current_path = os.getenv('PATH', '')
            path_list = [p for p in current_path.split(';') if p.strip()]
            new_path_list = []
            for p in path_list:
                if not re.search(r'instantclient|python', p, re.I):
                    new_path_list.append(p)
            oracle_path = os.path.join(os.getcwd(), 'instantclient_19_21')
            new_path_list.append(oracle_path)
            os.putenv('PATH', ';'.join(new_path_list))
        except Exception as e:
            print(f"Oracle环境配置警告：{str(e)}")

    def init_ui(self):
        self.setStyleSheet(f"""
        QWidget{{background:{GRAY_LIGHT};}}
        QLineEdit{{
            border:1px solid {GRAY_BORDER};
            border-radius:6px;
            padding-left:10px;
            height:36px;
            font-size:10pt;
        }}
        QLineEdit:focus{{border-color:{PRIMARY_COLOR};}}
        """)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(18)
        main_layout.setContentsMargins(50, 30, 50, 15)

        title = QLabel(SOFTWARE_NAME)
        title.setFont(QFont("微软雅黑", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"color:{PRIMARY_COLOR};")

        ver = QLabel(SOFTWARE_VERSION)
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet("color:#666; font-size:10pt;")

        self.edit_user = QLineEdit()
        self.edit_user.setPlaceholderText("请输入用户ID")

        self.edit_pwd = QLineEdit()
        self.edit_pwd.setPlaceholderText("请输入登录密码")
        self.edit_pwd.setEchoMode(QLineEdit.Password)

        # ---------- 按钮组：登录 + 注册 + 修改密码 ----------
        btn_layout = QHBoxLayout()
        btn_login = QPushButton("登 录")
        btn_reg = QPushButton("注 册")
        btn_chgpwd = QPushButton("修改密码")  # 这里加的

        btn_login.setMinimumHeight(38)
        btn_reg.setMinimumHeight(38)
        btn_chgpwd.setMinimumHeight(38)

        btn_login.setStyleSheet(f"""background:{PRIMARY_COLOR};color:#fff;border:none;border-radius:6px;""")
        btn_reg.setStyleSheet("""background:#6c757d;color:#fff;border:none;border-radius:6px;""")
        btn_chgpwd.setStyleSheet("""background:#28a745;color:#fff;border:none;border-radius:6px;""")

        btn_layout.addWidget(btn_login)
        btn_layout.addWidget(btn_reg)
        btn_layout.addWidget(btn_chgpwd)

        dev_label = QLabel(f"开发者：{DEVELOPER}")
        dev_label.setAlignment(Qt.AlignCenter)
        dev_label.setStyleSheet("color:#888; font-size:9pt; margin-top:10px;")

        copy_label = QLabel(COPYRIGHT_INFO)
        copy_label.setAlignment(Qt.AlignCenter)
        copy_label.setStyleSheet("color:#888; font-size:9pt;")

        main_layout.addWidget(title)
        main_layout.addWidget(ver)
        main_layout.addWidget(self.edit_user)
        main_layout.addWidget(self.edit_pwd)
        main_layout.addLayout(btn_layout)
        main_layout.addStretch()
        main_layout.addWidget(dev_label)
        main_layout.addWidget(copy_label)

        self.setLayout(main_layout)

        btn_login.clicked.connect(self.do_login)
        btn_reg.clicked.connect(self.open_register_dialog)
        btn_chgpwd.clicked.connect(self.open_chgpwd_dialog)  # 绑定
        self.edit_pwd.returnPressed.connect(self.do_login)

    def open_chgpwd_dialog(self):
        dlg = ChangePwdDialog(self.db, self)
        # 自动填入当前用户ID
        dlg.edit_user.setText(self.edit_user.text())
        dlg.exec_()

    def open_register_dialog(self):
        dlg = RegisterDialog(self.db, self)
        dlg.exec_()

    def do_login(self):
        user_id = self.edit_user.text().strip()
        pwd = self.edit_pwd.text().strip()

        if not user_id or not pwd:
            QMessageBox.warning(self, "提示", "用户ID和密码不能为空！")
            return

        sql = f"""
        SELECT USER_ID,PASS_WORD,USER_NAME,STATUS
        FROM INP_FLYPIN_USER
        WHERE USER_ID = '{user_id}'
        """
        data = self.db.SELECT_DIC(sql)
        if not data:
            QMessageBox.warning(self, "登录失败", "用户ID不存在！")
            return

        row = data[0]
        if row["PASS_WORD"] != pwd:
            QMessageBox.warning(self, "登录失败", "密码错误！")
            return

        if row["STATUS"] == 1:
            QMessageBox.warning(self, "登录失败", "账号已被停用，无法登录！")
            return

        # ========== 登录成功 → 保存账号密码（加密） ==========
        save_user(user_id, pwd)

        # QMessageBox.information(self, "登录成功", f"欢迎你：{row['USER_NAME']}")
        self.open_main_window(user_id, row['USER_NAME'])
        self.close()

    def open_main_window(self, login_user, user_name):
        self.main_win = FlyPinWindow(
            login_user=login_user,
            user_name=user_name,
            soft_name=SOFTWARE_NAME,
            soft_ver=SOFTWARE_VERSION,
            release_date=release_date,
            developer=DEVELOPER,
            copyright_info=COPYRIGHT_INFO
        )
        self.main_win.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = LoginWindow()
    win.show()
    sys.exit(app.exec_())