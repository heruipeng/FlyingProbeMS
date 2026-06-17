#!/bin/python
# -*- coding: utf-8 -*-
"""
______________________________
Author      : rphe
Email       : 502614708@qq.com
CreateTime  : 2026-6-17 8:21
ProjectNmae : FlyingProbeMS
File        : delete_files.py
Software    : PyCharm
Use_For     :
______________________________
"""
import shutil
import sys, os, re, platform, json
from package.Oracle_DB import ORACLE_INIT

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

db = ORACLE_INIT()
db.DB_CONNECT()

sql = f"SELECT * FROM inp_flypin_probe_tool_alert WHERE REMARK LIKE  '%输出成功%' AND ATTRIBUTE10 = '0'"
data = db.SELECT_DIC(sql)
# print(data)

for info in data:
    w2 = os.path.join(info['DATA_PATH'],'2w',info['ITEM_NO'][3:6],info['ITEM_NO'].lower()+info['REV'].lower())
    w4 = os.path.join(info['DATA_PATH'],'4w',info['ITEM_NO'][3:6],info['ITEM_NO'].lower()+info['REV'].lower())
    for p in [w2,w4]:
        if os.path.exists(p):
            print(p)
            shutil.rmtree(p)