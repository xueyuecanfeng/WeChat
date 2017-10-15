# coding = utf-8

from django.test import LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import os


# Create your tests here.

class UserPageTest(StaticLiveServerTestCase):
    fixtures = ['users.json', 'activity.json', 'ticket.json']
    browser = None

    @classmethod
    def setUpClass(cls):
        super(UserPageTest, cls).setUpClass()
        cls.browser = webdriver.PhantomJS()
        cls.username = os.environ.get('username', '')
        cls.password = os.environ.get('password', '')

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super(UserPageTest, cls).tearDownClass()

    def test_bind_user_wrong(self):
        self.browser.get('%s%s' % (self.live_server_url, '/u/bind?openid=1'))

        name_box = WebDriverWait(self.browser, 10).until(
            expected_conditions.presence_of_element_located((By.ID, 'inputUsername')))
        name_box.send_keys(self.username+str(1))

        password_box = self.browser.find_element_by_id('inputPassword')
        password_box.send_keys(self.password)

        submit_button = self.browser.find_element_by_css_selector('#validationHolder button')
        submit_button.click()

        WebDriverWait(self.browser, 10).until(
            expected_conditions.text_to_be_present_in_element((By.ID, 'helpPassword'),'学号或密码错误！请输入登录info的学号和密码' ))

    def test_bind_user_right(self):
        self.browser.get('%s%s' % (self.live_server_url, '/u/bind?openid=1'))

        name_box = WebDriverWait(self.browser, 10).until(
            expected_conditions.presence_of_element_located((By.ID, 'inputUsername')))
        name_box.send_keys(self.username)

        password_box =self.browser.find_element_by_id('inputPassword')
        password_box.send_keys(self.password)

        submit_button = self.browser.find_element_by_css_selector('#validationHolder button')
        submit_button.click()

        success_holder =  WebDriverWait(self.browser, 10).until(
            expected_conditions.presence_of_element_located((By.ID, 'successHolder')))
        self.assertIn('认证成功', success_holder.text)

    def test_activity_detail_no_such_activity(self):
        self.browser.get('%s%s' % (self.live_server_url, '/u/activity?id=6'))

        details_text = WebDriverWait(self.browser, 10).until(
            expected_conditions.presence_of_element_located((By.ID, 'theme'))
        )
        print(not self.browser.find_element_by_id('theme'))
        self.assertIn("正在加载", self.browser.find_element_by_id('theme').text)

    def test_activity_detail_with_such_activity(self):
        self.browser.get('%s%s' % (self.live_server_url, '/u/activity?id=1'))

        details_text = WebDriverWait(self.browser, 10).until(
            expected_conditions.presence_of_element_located((By.ID, 'theme'))
        )
        self.assertNotIn("正在加载", self.browser.find_element_by_id('theme').text)
        
    def test_ticket_detail_no_such_ticket(self):
        self.browser.get('%s%s' % (self.live_server_url, '/u/ticket?ticket=6&openid=1'))
        details_text = WebDriverWait(self.browser, 10).until(
            expected_conditions.presence_of_element_located((By.ID, 'mainbody'))
        )
        print(self.browser.find_element_by_id('mainbody').text)
        self.assertNotIn("活动地点", self.browser.find_element_by_id('mainbody').text)

    def test_ticket_detail_with_ticket(self):
        self.browser.get('%s%s' % (self.live_server_url, '/u/ticket?ticket=1&openid=1'))
        details_text = WebDriverWait(self.browser, 10).until(
            expected_conditions.presence_of_element_located((By.ID, 'mainbody'))
        )
        self.assertIn("活动地点", self.browser.find_element_by_id('mainbody').text)

