# coding = utf-8

from django.test import LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
import uuid
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import os
import urllib
from wechat.views import CustomWeChatView
from wechat.wrapper import WeChatHandler
from wechat.wrapper import WeChatLib

def get_message_text(data, openid="1"):
    result = b'''<xml><ToUserName><![CDATA[gh_ae02bb978885]]></ToUserName>
        <FromUserName><![CDATA['''+ openid.encode() + b''']]></FromUserName> 
        <CreateTime>1508031926</CreateTime>
        <MsgType><![CDATA[text]]></MsgType>
        <Content><![CDATA[''' + data.encode() + b''']]></Content>
        <MsgId>6476947803910477524</MsgId>
        </xml>'''

    return result

def get_message_event_click(event_key, openid="1"):
    result = b'''<xml><ToUserName><![CDATA[gh_ae02bb978885]]></ToUserName>
        <FromUserName><![CDATA['''+openid.encode() + b''']]></FromUserName> 
        <CreateTime>1508031926</CreateTime>
        <MsgType><![CDATA[event]]></MsgType>
        <Event><![CDATA[CLICK]]></Event>
        <EventKey><![CDATA[''' + event_key.encode() + b''']]></EventKey>
        <MsgId>6476947803910477524</MsgId>
        </xml>'''

    return result

def send_message(url_local, data):
    lib = CustomWeChatView.lib
    url = url_local+('/wechat?access_token=%s' % (
        lib.get_wechat_access_token()
    ))
    req = urllib.request.Request(
        url=url, data=data, headers={'Content-Type': 'text/xml'}
    )
    res_data = urllib.request.urlopen(req)
    res = res_data.read().decode()
    return res

class AlmostTest(StaticLiveServerTestCase):
    fixtures = ['users.json', 'activity.json', 'ticket.json']
    browser = None

    @classmethod
    def setUpClass(cls):
        super(AlmostTest, cls).setUpClass()
        cls.browser = webdriver.PhantomJS()

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super(AlmostTest, cls).tearDownClass()

    def test_express_error(self):
        result = send_message(self.live_server_url, get_message_text("2+", "1"))
        self.assertIn('表达式有误，请重新输入!', result)

    def test_express_right(self):
        result = send_message(self.live_server_url, get_message_text("2+2", "1"))
        self.assertIn('4', result)

    def test_user_bind(self):
        result = send_message(self.live_server_url, get_message_text("绑定", "1"))
        self.assertIn("点此绑定学号", result)

    def test_user_unbind(self):
        result = send_message(self.live_server_url, get_message_text("解绑", "2"))
        self.assertIn("学号绑定已经解除", result)
    def test_user_book_ticket_success(self):
        result = send_message(self.live_server_url,get_message_text("抢票 1", "2"))
        self.assertIn("成功抢到", result)

    def test_user_book_ticket_failed_with_ticket(self):
        result = send_message(self.live_server_url, get_message_text("抢票 1", "3"))
        self.assertIn("已拥有", result)

    def test_user_book_ticket_success_by_button(self):
        result = send_message(self.live_server_url, get_message_event_click("BOOKING_ACTIVITY_1", "2"))
        self.assertIn("成功抢到", result)

    def test_user_book_ticket_failed_without_ticket(self):
        result = send_message(self.live_server_url, get_message_text("抢票 2", "3"))
        self.assertIn('您未抢到', result)
        
    def test_user_cancel_ticket_without_ticket(self):
        result = send_message(self.live_server_url, get_message_text("退票 2", "2"))
        self.assertIn('您还没有', result)

    def test_user_cancel_ticket_with_wrong_ticket(self):
        result = send_message(self.live_server_url, get_message_text("退票 2", "3"))
        self.assertIn('您还没有', result)

    def test_user_cancel_ticket_right(self):
        result = send_message(self.live_server_url, get_message_text("退票 1", "3"))
        self.assertIn('您已成功退掉', result)
        
    def test_user_activity_detail(self):
        result = send_message(self.live_server_url,  get_message_event_click("BOOKING_ACTIVITY_3", "2"))
        self.assertIn('/u/activity?id=3', result)

    def test_user_ticket_detail(self):
        result = send_message(self.live_server_url, get_message_event_click("BOOKING_ACTIVITY_4", "3"))
        self.assertIn('/u/ticket?', result)

    def test_user_cancel_ticket_without_ticket(self):
        result = send_message(self.live_server_url, get_message_text("取票 2", "2"))
        self.assertIn('您还没有', result)

    def test_user_cancel_ticket_with_wrong_ticket(self):
        result = send_message(self.live_server_url, get_message_text("取票 2", "3"))
        self.assertIn('您还没有', result)

    def test_user_cancel_ticket_right(self):
        result = send_message(self.live_server_url, get_message_text("取票 4", "3"))
        self.assertIn('/u/ticket?', result)
        
    def test_user_book_what_success(self):
        result = send_message(self.live_server_url, get_message_event_click("SERVICE_BOOK_WHAT", "3"))
        self.assertIn('/u/activity', result)

    def test_user_get_ticket_success(self):
        result = send_message(self.live_server_url, get_message_event_click("SERVICE_GET_TICKET", "3"))
        self.assertIn('/u/ticket', result)

class RemainTest(StaticLiveServerTestCase):
    fixtures = ['users.json', 'activity2.json', 'ticket2.json']
    browser = None

    @classmethod
    def setUpClass(cls):
        super( RemainTest, cls).setUpClass()
        cls.browser = webdriver.PhantomJS()

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super( RemainTest, cls).tearDownClass()

    def test_book_what_not_success(self):
        result = send_message(self.live_server_url, get_message_event_click("SERVICE_BOOK_WHAT", "3"))
        self.assertIn('目前没有可以抢票的活动', result)

    def test_user_get_ticket_success(self):
        result = send_message(self.live_server_url, get_message_event_click("SERVICE_GET_TICKET", "1"))
        self.assertIn('目前没有票', result)
