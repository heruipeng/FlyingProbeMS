#!/bin/python
# -*- coding: utf-8 -*-
"""
______________________________
Author      : rphe
Email       : 502614708@qq.com
CreateTime  : 2026-6-08 8:21
ProjectNmae : flying_probe_test_management
File        : update_tools.py
Software    : PyCharm
Use_For     :
______________________________
"""
import sys, os, re, shutil
from datetime import datetime
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QProgressDialog
from PyQt5.QtCore import Qt, QPoint
from package.MessageBox import MessageBox
from configparser import ConfigParser
import icon_rc
version = '3.0'
class MAIN():
    def __init__(self,current_path=None):
        self.canelCopy = False
        config = ConfigParser()
        if current_path is not None:
            config.read(os.path.join(current_path,'config.ini'),encoding='utf-8')
        else:
            config.read('config.ini',encoding='utf-8')
        self.siteId = config.get('site', 'siteId')
        self.siteDes = config.get('site', 'siteDes')
        self.softPath = config.get('site', 'softPath')
        self.flying_probe = config.get('site', 'flying_probe')

    def udpateFile(self, sourePath, targetPath, progress_Dialog):
        '''
        更新文件(文件夹-文件夹)
        :param sourePath: 源文件夹
        :param targetPath:目标文件夹
        :return:
        '''
        if os.path.exists(targetPath) is False:
            os.mkdir(targetPath)
        # 目标路径不存在排查复制
        if os.path.isdir(sourePath) and os.path.isdir(targetPath):
            filelist_src = os.listdir(sourePath)
            for file in filelist_src:
                soureFile = os.path.join(os.path.abspath(sourePath), file)
                if os.path.isdir(soureFile):
                    targetFile = os.path.join(os.path.abspath(targetPath), file)
                    if not os.path.exists(targetFile):
                        os.mkdir(targetFile)
                    self.udpateFile(soureFile, targetFile, progress_Dialog)
                else:
                    targetFile = os.path.join(targetPath, file)
                    if os.path.exists(targetFile):
                        if os.stat(soureFile).st_mtime != os.stat(targetFile).st_mtime:
                            self.copy_files(soureFile, targetFile)
                    else:
                        self.copy_files(soureFile, targetFile)
                    if self.canelCopy:
                        return 'cancel'
                    else:
                        if progress_Dialog:
                            # 更新进度条
                            self.progressDialog.setValue(self.progressDialog.value() + 1)
            return True
        else:
            return False

    def copy_files(self,soure,target):
        try:
            # 尝试复制文件
            shutil.copy2(soure, target)
            # print(f"Copied {soure} to {target}")
        except PermissionError:
            # 捕获权限不足异常，并打印提示信息
            print(f"Skipped {soure} due to permission error")
        except Exception as e:
            # 捕获其他可能的异常，并打印错误信息和堆栈跟踪
            print(f"Failed to copy {soure} to {target}: {e}")
            # 可选：打印堆栈跟踪以进行调试
            # import traceback
            # traceback.print_exc()

    def countFiles(self,path,check_status=False):
        '''获取目录所有文件数量'''
        file_count = 0
        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            if os.path.isfile(file_path):
                file_count += 1
            elif os.path.isdir(file_path):
                file_count += self.countFiles(file_path,check_status)  # 递归调用
        return file_count

    def scriptsUpdate(self):
        '''
        更新脚本、hooks、配置文件
        :return:
        '''
        netPath = os.path.join(self.softPath,'login')
        # print(netPath)
        # sys.exit(0)
        localPath = self.flying_probe
        update_version_log = 'update_version.ini'
        if os.path.exists(netPath + '\\' + update_version_log) and os.path.exists(
                localPath + '\\' + update_version_log):
            if os.stat(netPath + '\\' + update_version_log).st_mtime == os.stat(
                    localPath + '\\' + update_version_log).st_mtime:
                # 启动软件
                self.run_flying_probe_test(localPath)
                sys.exit(0)

        desktop = QtWidgets.QApplication.desktop()
        SCREEN_WEIGHT = desktop.width()
        self.progressDialog = QProgressDialog()
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/logo/image/logo.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.progressDialog.setWindowIcon(icon)
        self.progressDialog.resize(300,40)
        self.progressDialog.setMinimumSize(300,40)
        # self.progressDialog.setMaximumSize(600,85)
        self.progressDialog.move(QPoint(int(SCREEN_WEIGHT / 2 - 400 / 2), 0))
        self.progressDialog.setWindowTitle(self.siteDes + '=>系统文件更新Ver:' + version)
        self.progressDialogLabel = QtWidgets.QLabel()
        self.progressDialogLabel.setText('更新中...')
        self.progressDialogLabel.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        self.progressDialog.setLabel(self.progressDialogLabel)
        self.progressDialog.open()
        self.progressDialog.setStyleSheet("QPushButton{\n"
                                        "    border:0px solid #fff;\n"
                                        "    padding:5px;\n"
                                        "    border-style:none;\n"
                                        "    border-radius:5px;\n"
                                        "    background-color: rgb(94, 159, 255);\n"
                                        "    background:rgb(94, 159, 255);\n"
                                        "    color:#fff;\n"
                                        "    min-height:20px;\n"
                                        "    selection-background-color: rgb(170, 255, 0);\n"
                                        "}\n"
                                        "QPushButton:hover{\n"
                                        "    border-color:#fff;\n"
                                        "    border-radius:5px;\n"
                                        "    background:rgb(253, 119, 87);\n"
                                        "    color:#fff}\n"
                                        "QPushButton:pressed{\n"
                                        "    background:lightblue;\n"
                                        "    border-style:hidden;\n"
                                        "    background:rgb(253, 85, 45);\n"
                                        "    color:#fff\n"
                                        "}")

        # file_count = self.countFiles(netPath)
        # # 设置进度长度
        # self.progressDialog.setValue(0)
        # self.progressDialog.setRange(0, file_count)
        # 绑定进度条取消信号
        self.progressDialog.canceled.connect(self.setCopyStatus)
        if os.path.exists(netPath):
            if os.path.exists(localPath) is False:
                try:
                    os.makedirs(localPath)
                except Exception as e:
                    print(e)
            # 有程序需要引用此文件夹
            if os.path.exists('C:/temp') is False:
                os.mkdir('C:/temp')
            '''新增部分系统目录更新，不加载进度条'''

            self.progressDialogLabel.setText('正在更新:{0}'.format(localPath))
            file_count = self.countFiles(netPath,check_status=True)
            # # 设置进度长度
            self.progressDialog.setValue(0)
            self.progressDialog.setRange(0, file_count)
            status = self.udpateFile(netPath, localPath, True)
            if status is True:
                pass
            elif status == 'cancel':
                M = MessageBox()
                M.warning(None,'提示信息', '取消更新!', MessageBox.OK)
            else:
                M = MessageBox()
                M.error(None,'提示信息', '更新异常,请检查!', MessageBox.OK)
        else:
            M = MessageBox()
            M.error(None,'提示信息', netPath+',网络不通,请检查网络!', MessageBox.OK)

        # 启动软件
        self.run_flying_probe_test(localPath)
        sys.exit(0)

    def run_flying_probe_test(self,localPath):
        '''启动genesis'''
        # 选择启动对应版本软件
        soft_path = os.path.join(localPath,'login.exe')
        if os.path.isfile(soft_path):
            import subprocess
            # 传入厂区标识
            work_dir = os.path.dirname(soft_path)
            subprocess.Popen(soft_path, stdin=subprocess.PIPE, cwd=work_dir, stdout=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            print(soft_path + '\t' + 'no exists')

    def setCopyStatus(self):
        '''设置复制状态,取消时,销毁进度条'''
        self.canelCopy = True
        if self.progressDialog.wasCanceled():
            self.progressDialog.deleteLater()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    if len(sys.argv) > 1:
        Main = MAIN(sys.argv[1])
    else:
        Main = MAIN()
    # 弹出消息框,不退出整个应用程序
    # app.setQuitOnLastWindowClosed(False)
    Main.scriptsUpdate()
    sys.exit(app.exec_())


