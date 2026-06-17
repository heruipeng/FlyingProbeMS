#!/bin/python
# -*- coding: utf-8 -*-
"""
______________________________
Author      : rphe
Email       : 502614708@qq.com
CreateTime  : 2025-4-1 19:49
ProjectNmae : Automatic_monitoring_hard_disk
File        : wechat_robot.py
Software    : PyCharm
Use_For     :
______________________________
"""
# -*- coding: utf-8 -*-
# 文件结构：
# wechat_robot/
# ├── __init__.py
# ├── sender.py
# └── data_fetcher.py

# sender.py
import json
import requests
import logging


class WechatRobotSender(object):
    """企业微信机器人消息发送器（Python 2.7版本）"""

    def __init__(self, webhook_url):
        """
        初始化机器人
        :param webhook_url: 企业微信机器人Webhook地址
        """
        self.webhook_url = webhook_url
        self.logger = logging.getLogger(__name__)

    def send_text(
            self,
            content,
            mentioned_mobiles=None,
            mentioned_userids=None
    ):
        """
        发送文本消息
        :param content: 消息内容
        :param mentioned_mobiles: 需要@的手机号列表
        :param mentioned_userids: 需要@的用户ID列表
        :return: 是否发送成功
        """
        payload = {
            "msgtype": "text",
            "text": {
                "content": content,
                "mentioned_mobile_list": mentioned_mobiles or [],
                "mentioned_list": mentioned_userids or []
            }
        }
        return self._send(payload)

    def send_markdown(
            self,
            content,
            mentioned_mobiles=None
    ):
        """
        发送Markdown格式消息
        :param content: Markdown内容
        :param mentioned_mobiles: 需要@的手机号列表
        """
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": content,
                "mentioned_mobile_list": mentioned_mobiles or [],
            }
        }
        return self._send(payload)

    def _send(self, payload):
        """执行发送请求"""
        try:
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
                headers=headers,
                timeout=5,
                verify=False # ssl证书可能失效,发送不了,需要添加此参数
            )
            result = response.json()

            if response.status_code == 200 and result.get('errcode') == 0:
                self.logger.info("消息发送成功")
                return True

            self.logger.error("消息发送失败: %s", result.get('errmsg'))
            return False

        except Exception as e:
            self.logger.exception("消息发送异常: %s", str(e))
            return False

if __name__ == '__main__':
    # # 示例1：发送消息
    # from wechat_robot import WechatRobotSender
    # # 初始化机器人（替换为你的真实webhook）
    webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=cdfac7dc-04fe-4954-b0f7-7b01a6e23921"
    robot = WechatRobotSender(webhook_url)
    # 发送文本消息并@指定人
    robot.send_text(
        content=u"测试信息！",
        mentioned_mobiles=["024864"]
    )