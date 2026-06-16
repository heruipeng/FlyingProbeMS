#!/bin/python3
# -*- coding: UTF-8 -*-
# --------------------------------------------------------- #
#                    SL SOFTWARE GROUP                      #
# --------------------------------------------------------- #
# @Author       :    AresHe
# @Mail         :    502614708@qq.com
# @DateTime     :    2023/4/24 15:51
# @Revision     :    1.0.0
# @File         :    MessageBox.py
# @Software     :    PyCharm
# @Usefor       :
# --------------------------------------------------------- #
import sys

_header = {
    'description': '''
    -> 本程序任何其他团体或个人如需使用，必须经作者的批准，并遵守以下约定；
    1> 本着尊重创作者的劳动成果，任何团体或个人在使用此程序的时候，均需要知会此程序的原始创作者；
    2> 在任何场合宣导、宣传，在任何文件、报告、邮件中提及本程序的全部或部分功能，均需要声明此程序的
       原始创作者；
    3> 在任何时候对本程序做部分修改或者是升级时，必须要保留文件的原始信息，包括原始文件名、创作者及
       联系方式、创作日期等信息，且不得删除程序中的源代码，只能进行注释处理；
'''
}
'''
                   _ooOoo_
                  o8888888o
                  88" . "88
                  (| -_- |)
                  O\  =  /O
               ____/`---'\____
             .'  \\|     |//  `.
            /  \\|||  :  |||//  \
           /  _||||| -:- |||||-  \
           |   | \\\  -  /// |   |
           | \_|  ''\---/''  |   |
           \  .-\__  `-`  ___/-. /
         ___`. .'  /--.--\  `. . __
      ."" '<  `.___\_<|>_/___.'  >'"".
     | | :  `- \`.;`\ _ /`;.`/ - ` : | |
     \  \ `-.   \_ __\ /__ _/   .-` /  /
======`-.____`-.___\_____/___.-`____.-'======
                   `=---='
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
           佛祖保佑       永无BUG
'''
from PyQt5.QtWidgets import QDialog, QApplication, QPushButton, QSizePolicy
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QIcon
from package.Ui_MessageBox import Ui_Dialog

class MessageBox(QDialog):
    """ 自定义MessageBox，继承自QDialog
    其中有3个static method可用: information, warning, error，使用方法与QMessageBox基本一致
    Args:
        parent: 父窗口
        title: MessageBox窗口标题 Window Title
        text: 消息文本
        btype: 按钮，有五种类型按钮：YES, NO, CANCLE, CLOSE, OK
        default: 默认按钮，默认值为YES
    """
    # 仅支持这几个按键
    YES = 0x01
    NO = 0x02
    CANCEL = 0x04
    CLOSE = 0x08
    OK = 0x10
    # 返回值
    retValue = 0

    def __init__(self, parent=None, title='', text='', btype=YES, btype1=None,default=YES):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon(QPixmap("image/logo.png")))
        self.setWindowModality(Qt.ApplicationModal)
        self.setAttribute(Qt.WA_QuitOnClose, True)
        self.setWindowTitle(title)
        self.btnList = {}
        self.ui.lb_text.setText(text)
        self.create_button(btype)
        self.set_default_btn(btype, default)
        if btype1 is not None:
            self.create_button(btype1)
            self.set_default_btn(btype1, default)

    def create_button(self, btype):
        # 如果按钮是ok
        if btype & MessageBox.YES == MessageBox.YES:
            self.yesbtn = QPushButton(self)
            self.set_button(self.yesbtn, u'是')
            self.btnList[MessageBox.YES] = self.yesbtn
            self.yesbtn.clicked.connect(self.btn_yes)
        # 如果按钮是no
        if btype & MessageBox.NO == MessageBox.NO:
            self.nobtn = QPushButton(self)
            self.set_button(self.nobtn, u'否')
            self.btnList[MessageBox.NO] = self.nobtn
            self.nobtn.clicked.connect(self.btn_no)
        # 如果按钮是cancel
        if btype & MessageBox.CANCEL == MessageBox.CANCEL:
            self.cancelbtn = QPushButton(self)
            self.set_button(self.cancelbtn, u'取消')
            self.btnList[MessageBox.CANCEL] = self.cancelbtn
            self.cancelbtn.clicked.connect(self.btn_cancel)
        # 如果按钮是close
        if btype & MessageBox.CLOSE == MessageBox.CLOSE:
            self.closebtn = QPushButton(self)
            self.set_button(self.closebtn, '关闭')
            self.btnList[MessageBox.CLOSE] = self.closebtn
            self.closebtn.clicked.connect(self.btn_close)
        # 如果按钮是ok
        if btype & MessageBox.OK == MessageBox.OK:
            self.okbtn = QPushButton(self)
            self.set_button(self.okbtn, '确定')
            self.btnList[MessageBox.OK] = self.okbtn
            self.okbtn.clicked.connect(self.btn_ok)

    def set_default_btn(self, btype, default):
        # default键必须是一个独立的按键
        if default not in {MessageBox.YES, MessageBox.NO, MessageBox.CANCEL, MessageBox.OK, MessageBox.CLOSE}:
            return
        if default & btype != 0:
            self.btnList[default].setDefault(True)

    def set_button(self, btn: QPushButton, text: str):
        # 设置按钮的一些参数
        btn.setText(text)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.setFixedSize(QSize(50, 27))
        self.ui.horizontalLayout_2.addWidget(btn)

    def btn_yes(self):
        MessageBox.retValue = MessageBox.YES
        self.close()

    def btn_no(self):
        MessageBox.retValue = MessageBox.NO
        self.close()

    def btn_cancel(self):
        MessageBox.retValue = MessageBox.CANCEL
        self.close()

    def btn_close(self):
        MessageBox.retValue = MessageBox.CLOSE
        self.close()

    def btn_ok(self):
        MessageBox.retValue = MessageBox.OK
        self.close()

    def ret_val(self):
        return MessageBox.retValue

    # 使用时调用的静态方法
    @staticmethod
    def information(parent, title, text, btype=YES, btype1=None, default=YES):
        box = MessageBox(parent, title, text, btype, btype1, default)
        box.ui.labelPixmap.setPixmap(QPixmap("image/finish.png").scaled(48, 48, Qt.KeepAspectRatio))
        box.exec()
        return box.ret_val()

    @staticmethod
    def warning(parent, title, text, btype=YES, btype1=None, default=YES):
        box = MessageBox(parent, title, text, btype, btype1, default)
        box.ui.labelPixmap.setPixmap(QPixmap("image/warning.png").scaled(48, 48, Qt.KeepAspectRatio))
        box.exec()
        return box.ret_val()

    @staticmethod
    def error(parent, title, text, btype=YES, btype1=None, default=YES):
        box = MessageBox(parent, title, text, btype, btype1,default)
        box.ui.labelPixmap.setPixmap(QPixmap("image/error.png").scaled(48, 48, Qt.KeepAspectRatio))
        box.exec()
        return box.ret_val()

if __name__ == '__main__':
    app = QApplication([])
    m = MessageBox()
    d = m.warning(None, '系统警告', '账号不存在,请检查...', btype=MessageBox.OK, btype1=MessageBox.CANCEL)
    print(d)
    # sys.exit(app.exec_())