#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
#---------------------------------------------------------#
#               SUNTAK SOFTWARE GROUP                     #
#---------------------------------------------------------#
@Author       :    rphe
@Mail         :    502614708@.com
@Date         :    2026/4/14
@Revision     :    1.0.0
@File         :    fp_config.py
@Software     :    PyCharm
@Usefor       :    配置文件
'''

# --面向对象进行完成
class toolsMain:
    def __init__(self):
        # print u'此段暂时预留出来...\n'
        pass

    def factory(self, site, Des=None):
        """
        工厂信息定义
        :param site:工厂代码
        :param Des: 需要返回的说明代码
        :return:
        """
        self.factoryDes={
            'JM1': {
                'siteDes'   : u'江门一厂',
                'orgId'     : 85,
                'orgcode'   : 108,
                'inPlanid'  : 2
            },
            'JM2': {
                'siteDes'   : u'江门二厂',
                'orgId'     : 107,
                'orgcode'   : 108,
                'inPlanid'  : 4
            },
            'DL': {
                'siteDes'   : u'大连工厂',
                'orgId'     : 84,
                'orgcode'   : 103,
                'inPlanid'  : 3
            },
            'ZH1': {
                'siteDes'   : u'珠海一厂',
                'orgId'     : 168,
                'orgcode'   : 110,
                'inPlanid'  : 5
            },
            'ZH2': {
                'siteDes'   : u'珠海二厂',
                'orgId'     : 228,
                'orgcode'   : 113,
                'inPlanid'  : 5
            }
        }

        # --根据传入参数，返回数据
        if Des:
            return self.factoryDes[site][Des]
        else:
            return self.factoryDes[site]

    def config(self, site, toolType=None):
        """
        配置信息
        :param site: 工厂信息
        :param toolType: 工具类型
        :return:
        """
        self.pathConfig={
            'JM2':{
                'tgz': '\\\\jm2file\\JMFILE\\Product\\08-ENG\\tgz',
                'org': '\\\\10.3.100.251\\Product\\02-MI\\MI_data\\MI-project-已审核',
                'net_step':'net',
                'output_ipc_path_network': '\\\\10.3.100.235\\jmfile\\Product\\04-TEST\\飞针资料\\盛鑫自动化',
                'output_tgz_path_network': '\\\\10.3.100.235\\jmfile\\Product\\04-TEST\\飞针资料\\盛鑫自动化',
                'output_ipc_path': 'D:\\data',
                'output_tgz_path': 'D:\\data',
            },
            'JM1':{
                'tgz': '\\\\jm2file\\jmfile1\\Product\\08-ENG\\cam\\tgz',
                'org': '\\\\192.168.16.251\\Product\\06-MI\\00new',
                'net_step': 'net',
                'output_ipc_path_network': '\\\\192.168.16.251\\Product\\02-TEST\\盛鑫自动化',
                'output_tgz_path_network': '\\\\192.168.16.251\\Product\\02-TEST\\盛鑫自动化',
                'output_ipc_path': 'D:\\data',
                'output_tgz_path': 'D:\\data',
            },
            'ZH1':{
                'tgz': '\\\\zhfile\\zhfile01\\Product\\08-ENG\\cam\\tgz',
                'org': '\\\\zhfile01\\Product\\06-MI',
                'net_step': 'net',
                'output_ipc_path_network': 'D:\\data',
                'output_tgz_path_network': 'D:\\data',
                'output_ipc_path': 'D:\\data',
                'output_tgz_path': 'D:\\data',
            },
            'ZH2':{
                'tgz': '\\\\zh2eng\\zh2eng\\08-ENG\\cam\\tgz',
                'org': 'd:\\',
                'net_step': 'net',
                'output_ipc_path_network': 'D:\\data',
                'output_tgz_path_network': 'D:\\data',
                'output_ipc_path': 'D:\\data',
                'output_tgz_path': 'D:\\data',
            }
        }

        # --返回信息
        if toolType:
            return self.pathConfig[site][toolType]
        else:
            return self.pathConfig[site]

    def mailConfig(self, site):
        """
        邮箱配置参数
        :param site:工厂代码
        :return: 相关信息
        """
        self.E_Mail={
            'SJ'    : {
                'smtpSdrver': 'smtphz.qiye.163.com',
                'MailUsr'   : 'suntak_engineer@suntakpcb.com',
                'MailPwd'   : 'chuang_FS',
                'toAddr'    : ['ncbgj@suntakpcb.com', 'yhbgj@suntakpcb.com', 'wcbgj@suntakpcb.com',
                               'zhbgj@suntakpcb.com', 'zfbgj@suntakpcb.com', 'ldgjhs@suntakpcb.com',
                               'zdgjhs@suntakpcb.com', 'rybgjhs@suntakpcb.com','ncwcf@suntakpcb.com',
                               'film@suntakpcb.com', 'sfxue@suntakpcb.com', 'bjzhang@suntakpcb.com',
                               'wcwcf@suntakpcb.com', 'zhwcf@suntakpcb.com', 'zhwf@suntakpcb.com',
                               'gxchengxing@suntakpcb.com', 'gxchengxing2@suntakpcb.com', 'yhzhu1@suntakpcb.com'],
                'ccAddr'    : ['xmzhang@suntakpcb.com',  'smhuang@suntakpcb.com','skmo@suntakpcb.com','jwtang@suntakpcb.com'],
                'bccAddr'   : ['suntak_engineer@suntakpcb.com','gliu@suntakpcb.com'],
                'toAddrAdmin'   : ['suntak_engineer@suntakpcb.com','gliu@suntakpcb.com'],
                'ccAddrAdmin'   : ['suntak_engineer@suntakpcb.com','gliu@suntakpcb.com'],
                'bccAddrAdmin'  : ['suntak_engineer@suntakpcb.com','gliu@suntakpcb.com'],
            },
            'JM2': {
                'smtpSdrver': 'smtphz.qiye.163.com',
                'MailUsr'   : 'suntak_engineer@suntakpcb.com',
                'MailPwd'   : 'chuang_FS',
                'toAddr'    : ['gliu@suntakpcb.com', 'csong1@suntakpcb.com', 'rphe@suntakpcb.com'],# jm2gczl@suntakpcb.com 陈晓君通知：陆工，帮忙把江门二厂工程资料 和任主管的邮箱从这几个自动触发的邮箱里取消掉，我们不需要收这些邮件，太多了，一天几百封把真正要关注的邮件都顶不见了
                'ccAddr'    : ['gliu@suntakpcb.com', 'qxu@suntakpcb.com', 'yhe2@suntakpcb.com', 'hzhou1@suntakpcb.com'],# wlren@suntakpcb.com
                'bccAddr'   : ['suntak_engineer@suntakpcb.com','gliu@suntakpcb.com'],
                'toAddrAdmin'   : ['suntak_engineer@suntakpcb.com','gliu@suntakpcb.com', 'csong1@suntakpcb.com', 'rphe@suntakpcb.com','jm2gczl@suntakpcb.com'],
                'ccAddrAdmin'   : ['suntak_engineer@suntakpcb.com','gliu@suntakpcb.com', 'csong1@suntakpcb.com', 'rphe@suntakpcb.com'],
                'bccAddrAdmin'  : ['suntak_engineer@suntakpcb.com','gliu@suntakpcb.com', 'csong1@suntakpcb.com', 'rphe@suntakpcb.com'],
            }
        }

        # --返回备份地址
        return self.E_Mail[site]


# --程序入口
if __name__ == '__main__':
    REC=toolsMain()
    print (REC.config('SJ'))

