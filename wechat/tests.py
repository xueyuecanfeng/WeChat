from django.test import TestCase
from django.core.urlresolvers import resolve
from django.http import HttpRequest
from django.test import TestCase
import userpage.urls
import re
from unittest.mock import Mock,patch
from codex.baseerror import InputError, ValidateError
from userpage.views import UserBind
import json
import datetime
from wechat.models import  User,Activity,Ticket
from django.utils import timezone
from wechat.handlers import *
from wechat.wrapper import WeChatHandler
from WeChatTicket import settings
# Create your tests here.
class RegularExpHandlerTest(TestCase):
    def test_check_right_input(self):
        found = RegularExpHandler.check
        handler = Mock(wraps=RegularExpHandler(None, "123", None))
        handler.is_msg_type.return_value = True
        input = {"Content":"123"}
        handler.input = input
        self.assertTrue(found(handler))

    def test_check_wrong_input(self):
        found = RegularExpHandler.check
        handler = Mock(wraps=RegularExpHandler(None, "123", None))
        handler.is_msg_type.return_value = True
        input = {"Content": "123@"}
        handler.input = input
        self.assertFalse(found(handler))

    def test_handle_without_input(self):
        found = RegularExpHandler.handle
        handler = Mock(wraps=RegularExpHandler(None, "123", None))
        input = {"Content":""}
        handler.input = input
        handler.reply_text = Mock(side_effect=lambda x: x)
        self.assertEqual(found(handler), str('表达式有误，请重新输入!'))

    def test_handle_with_error_input(self):
        found = RegularExpHandler.handle
        handler = Mock(wraps=RegularExpHandler(None, "123", None))
        input = {"Content":"1+"}
        handler.input = input
        handler.reply_text = Mock(side_effect=lambda x: x)
        self.assertEqual(found(handler), str('表达式有误，请重新输入!'))

    def test_handle_with_right_input(self):
        found = RegularExpHandler.handle
        handler = Mock(wraps=RegularExpHandler(None, "123", None))
        input = {"Content":"1+1"}
        handler.input = input
        handler.reply_text = Mock(side_effect=lambda x: x)
        self.assertEqual(found(handler), 2)

class ActivityBookingHandlerTest(TestCase):
    @patch.object(Activity.objects, "filter")
    def test_check_without_activity_published(self, Activity_objects_filter):
        found = ActivityBookingHandler.check
        handler = Mock(wraps=ActivityBookingHandler(None, "123", None))
        Activity.objects.filter.return_value = []
        self.assertRaises(LogicError, found, handler)

    @patch.object(Activity.objects, "filter")
    def test_check_without_activity_check_succeed(self, Activity_objects_filter):
        found = ActivityBookingHandler.check
        handler = Mock(wraps=ActivityBookingHandler(None, "123", None))
        act = Mock()
        act.id = "2"
        Activity.objects.filter.return_value = [act]
        handler.view.event_keys = {"book_header": ""}
        handler.is_event_click = Mock(side_effect= lambda x: x == "1")
        self.assertEqual(found(handler), False)

    @patch.object(Activity.objects, "filter")
    def test_check_with_activity_check_succeed(self, Activity_objects_filter):
        found = ActivityBookingHandler.check
        handler = Mock(wraps=ActivityBookingHandler(None, "123", None))
        act = Mock()
        act.id = "1"
        Activity.objects.filter.return_value = [act]
        handler.view.event_keys = {"book_header": ""}
        handler.is_event_click = Mock(side_effect=lambda x: x == "1")
        self.assertEqual(found(handler), True)

    @patch.object(Activity.objects, "select_for_update")
    def test_check_without_activity(self, Activity_objects_get):
        found = ActivityBookingHandler.handle
        handler = Mock(wraps=ActivityBookingHandler(None, "123", None))
        temp = Mock()
        Activity.objects.select_for_update.return_value = temp
        temp.get.side_effect = Activity.DoesNotExist
        self.assertRaises(LogicError, found, handler)

    @patch.object(Activity.objects, "select_for_update")
    @patch.object(User.objects, "get")
    def test_check_without_user(self, Activity_objects_get, User_ojects_get):
        found = ActivityBookingHandler.handle
        handler = Mock(wraps=ActivityBookingHandler(None, "123", None))
        handler.input = {"FromUserName":"1"}
        act = Mock()
        act.book_start = 1
        act.name = "1"
        act.pic_url =""
        act.description = "1"
        act.book_end = 2
        act.remain_tickets = 1
        act.key = "1"
        temp = Mock()
        Activity.objects.select_for_update.return_value = temp
        temp.get.return_value = act
        User.objects.get.side_effect = User.DoesNotExist
        self.assertRaises(LogicError, found, handler)

    @patch.object(Activity.objects, "select_for_update")
    @patch.object(User.objects, "get")
    @patch.object(timezone, "now")
    @patch.object(settings, "get_url")
    def test_check_before_book(self, Activity_objects_get, User_ojects_get, timezone_now, setting_get_url):
        found = ActivityBookingHandler.handle
        handler = Mock(wraps=ActivityBookingHandler(None, "123", None))
        handler.input = {"FromUserName": "1"}
        handler.myid = 1
        timezone.now.return_value = 1

        act = Mock()
        act.book_start = 2
        act.name = "1"
        act.pic_url = ""
        act.description = "1"
        act.book_end = 4
        act.remain_tickets = 1
        act.key = "1"
        temp = Mock()
        Activity.objects.select_for_update.return_value = temp
        temp.get.return_value = act
        user =Mock()
        user.student_id ="1"
        User.objects.get.return_value = user
        settings.get_url.return_value="1"
        handler.reply_single_news= Mock(side_effect=lambda x: x)
        self.assertEqual(found(handler), {
            'Title': "1",
            'PicUrl' : "",
            'Description' : "1",
            'Url': "1"
        })

    @patch.object(Activity.objects, "select_for_update")
    @patch.object(User.objects, "get")
    @patch.object(timezone, "now")
    @patch.object(settings, "get_url")
    @patch.object(Ticket.objects, "filter")
    @patch.object(Ticket.objects, "create")
    def test_check_now_book_without_ticket(self, Activity_objects_get, User_ojects_get, timezone_now, setting_get_url, Ticket_objects_filter,Ticket_objects_create):
        found = ActivityBookingHandler.handle
        handler = Mock(wraps=ActivityBookingHandler(None, "123", None))
        handler.input = {"FromUserName": "1"}
        handler.myid = 1
        timezone.now.return_value = 3

        act = Mock()
        act.book_start = 2
        act.name = "1"
        act.pic_url = ""
        act.description = "1"
        act.book_end = 4
        act.remain_tickets = 1
        act.key = "1"
        act.save.return_value = True
        temp = Mock()
        Activity.objects.select_for_update.return_value = temp
        temp.get.return_value = act

        user = Mock()
        user.student_id = "1"
        User.objects.get.return_value = user
        settings.get_url.return_value = "1"

        Ticket.objects.filter.return_value = []
        Ticket.objects.create.return_value = True
        handler.reply_single_news = Mock(side_effect=lambda x: x)
        handler.reply_text = Mock(side_effect=lambda x: x)
        self.assertEqual(found(handler), str('您已成功抢到') + act.key + str('活动的票！'))

    @patch.object(Activity.objects, "select_for_update")
    @patch.object(User.objects, "get")
    @patch.object(timezone, "now")
    @patch.object(settings, "get_url")
    @patch.object(Ticket.objects, "filter")
    @patch.object(Ticket.objects, "create")
    def test_check_now_book_with_ticket_but_not_match(self, Activity_objects_get, User_ojects_get, timezone_now, setting_get_url,
                                           Ticket_objects_filter, Ticket_objects_create):
        found = ActivityBookingHandler.handle
        handler = Mock(wraps=ActivityBookingHandler(None, "123", None))
        handler.input = {"FromUserName": "1"}
        handler.myid = 1
        timezone.now.return_value = 3

        act = Mock()
        act.book_start = 2
        act.name = "1"
        act.pic_url = ""
        act.description = "1"
        act.book_end = 4
        act.remain_tickets = 1
        act.key = "1"
        act.save.return_value = True
        temp = Mock()
        Activity.objects.select_for_update.return_value = temp
        temp.get.return_value = act

        user = Mock()
        user.student_id = "1"
        User.objects.get.return_value = user
        settings.get_url.return_value = "1"

        ticket = Mock()
        ticket.status = Ticket.STATUS_VALID
        acti = Mock()
        acti.id = "2"
        ticket.activity = acti
        Ticket.objects.filter.return_value = [ticket]
        Ticket.objects.create.return_value = True
        handler.reply_single_news = Mock(side_effect=lambda x: x)
        handler.reply_text = Mock(side_effect=lambda x: x)
        self.assertEqual(found(handler), str('您已成功抢到') + act.key + str('活动的票！'))

    @patch.object(Activity.objects, "select_for_update")
    @patch.object(User.objects, "get")
    @patch.object(timezone, "now")
    @patch.object(settings, "get_url")
    @patch.object(Ticket.objects, "filter")
    @patch.object(Ticket.objects, "create")
    def test_check_now_book_with_ticket_and_match(self, Activity_objects_get, User_ojects_get, timezone_now,
                                                      setting_get_url,
                                                      Ticket_objects_filter, Ticket_objects_create):
        found = ActivityBookingHandler.handle
        handler = Mock(wraps=ActivityBookingHandler(None, "123", None))
        handler.input = {"FromUserName": "1"}
        handler.myid = 1
        timezone.now.return_value = 3

        act = Mock()
        act.book_start = 2
        act.name = "1"
        act.pic_url = ""
        act.description = "1"
        act.book_end = 4
        act.remain_tickets = 1
        act.key = "1"
        act.id = "1"
        act.save.return_value = True
        temp = Mock()
        Activity.objects.select_for_update.return_value = temp
        temp.get.return_value = act

        user = Mock()
        user.student_id = "1"
        User.objects.get.return_value = user
        settings.get_url.return_value = "1"

        ticket = Mock()
        ticket.status = Ticket.STATUS_VALID
        acti = Mock()
        acti.id = "1"
        ticket.activity = acti
        Ticket.objects.filter.return_value = [ticket]
        Ticket.objects.create.return_value = True
        handler.reply_single_news = Mock(side_effect=lambda x: x)
        handler.reply_text = Mock(side_effect=lambda x: x)
        self.assertEqual(found(handler), str('您已拥有') + act.key + str('活动的票！'))

    @patch.object(Activity.objects, "select_for_update")
    @patch.object(User.objects, "get")
    @patch.object(timezone, "now")
    @patch.object(settings, "get_url")
    @patch.object(Ticket.objects, "filter")
    @patch.object(Ticket.objects, "create")
    def test_check_after_book_without_ticket(self, Activity_objects_get, User_ojects_get, timezone_now,
                                                      setting_get_url,
                                                      Ticket_objects_filter, Ticket_objects_create):
        found = ActivityBookingHandler.handle
        handler = Mock(wraps=ActivityBookingHandler(None, "123", None))
        handler.input = {"FromUserName": "1"}
        handler.myid = 1
        timezone.now.return_value = 5

        act = Mock()
        act.book_start = 2
        act.name = "1"
        act.pic_url = ""
        act.description = "1"
        act.book_end = 4
        act.remain_tickets = 1
        act.key = "1"
        act.id = "1"
        act.save.return_value = True
        temp = Mock()
        Activity.objects.select_for_update.return_value = temp
        temp.get.return_value = act
        user = Mock()
        user.student_id = "1"
        User.objects.get.return_value = user
        settings.get_url.return_value = "1"

        ticket = Mock()
        ticket.status = Ticket.STATUS_VALID
        acti = Mock()
        acti.id = "1"
        ticket.activity = acti
        Ticket.objects.filter.return_value = []
        Ticket.objects.create.return_value = True
        handler.reply_single_news = Mock(side_effect=lambda x: x)
        handler.reply_text = Mock(side_effect=lambda x: x)
        self.assertEqual(found(handler), str('抢票已结束，您还没有') + act.key + str('活动的票！'))

    @patch.object(Activity.objects, "select_for_update")
    @patch.object(User.objects, "get")
    @patch.object(timezone, "now")
    @patch.object(settings, "get_url")
    @patch.object(Ticket.objects, "filter")
    @patch.object(Ticket.objects, "create")
    def test_check_after_book_with_ticket_but_not_match(self, Activity_objects_get, User_ojects_get, timezone_now,
                                             setting_get_url,
                                             Ticket_objects_filter, Ticket_objects_create):
        found = ActivityBookingHandler.handle
        handler = Mock(wraps=ActivityBookingHandler(None, "123", None))
        handler.input = {"FromUserName": "1"}
        handler.myid = 1
        timezone.now.return_value = 5

        act = Mock()
        act.book_start = 2
        act.name = "1"
        act.pic_url = ""
        act.description = "1"
        act.book_end = 4
        act.remain_tickets = 1
        act.key = "1"
        act.id = "1"
        act.save.return_value = True
        temp = Mock()
        Activity.objects.select_for_update.return_value = temp
        temp.get.return_value = act

        user = Mock()
        user.student_id = "1"
        User.objects.get.return_value = user
        settings.get_url.return_value = "1"

        ticket = Mock()
        ticket.status = Ticket.STATUS_VALID
        acti = Mock()
        acti.id = "2"
        ticket.activity = acti
        Ticket.objects.filter.return_value = [ticket]
        Ticket.objects.create.return_value = True
        handler.reply_single_news = Mock(side_effect=lambda x: x)
        handler.reply_text = Mock(side_effect=lambda x: x)
        self.assertEqual(found(handler), str('您还没有') + act.key + str('活动的票！'))

    @patch.object(Activity.objects, "select_for_update")
    @patch.object(User.objects, "get")
    @patch.object(timezone, "now")
    @patch.object(settings, "get_url")
    @patch.object(Ticket.objects, "filter")
    @patch.object(Ticket.objects, "create")
    def test_check_after_book_with_ticket_but_not_match(self, Activity_objects_get, User_ojects_get, timezone_now,
                                                        setting_get_url,
                                                        Ticket_objects_filter, Ticket_objects_create):
        found = ActivityBookingHandler.handle
        handler = Mock(wraps=ActivityBookingHandler(None, "123", None))
        handler.input = {"FromUserName": "1"}
        handler.myid = 1
        timezone.now.return_value = 5

        act = Mock()
        act.book_start = 2
        act.name = "1"
        act.pic_url = ""
        act.description = "1"
        act.book_end = 4
        act.remain_tickets = 1
        act.key = "1"
        act.id = "1"
        act.save.return_value = True
        temp = Mock()
        Activity.objects.select_for_update.return_value = temp
        temp.get.return_value = act

        user = Mock()
        user.student_id = "1"
        User.objects.get.return_value = user
        settings.get_url.return_value = "1"

        ticket = Mock()
        ticket.status = Ticket.STATUS_VALID
        acti = Mock()
        acti.id = "1"
        ticket.activity = acti
        Ticket.objects.filter.return_value = [ticket]
        Ticket.objects.create.return_value = True
        handler.reply_single_news = Mock(side_effect=lambda x: x)
        handler.reply_text = Mock(side_effect=lambda x: x)
        self.assertEqual(found(handler), {
            'Title':"1",
            'PicUrl':"",
            'Description':"1",
            'Url':"1"
        })

class TicketsHandlerTest(TestCase):
    def test_check_with_input(self):
        found = TicketsHandler.check
        handler = Mock(wraps=TicketsHandler(None,"123",None))
        handler.is_text_command = Mock(side_effect= lambda x,y,z: x+y+z)
        self.assertEqual(found(handler), "抢票取票退票")

    @patch.object(Activity.objects, "select_for_update")
    @patch.object(User.objects, "get")
    @patch.object(timezone, "now")
    @patch.object(settings, "get_url")
    @patch.object(Ticket.objects, "filter")
    @patch.object(Ticket.objects, "create")
    def test_handle_without_activity(self, Activity_objects_get, User_ojects_get, timezone_now,
                                                        setting_get_url,
                                                        Ticket_objects_filter, Ticket_objects_create):
        act = Mock()
        act.book_start = 2
        act.name = "1"
        act.pic_url = ""
        act.description = "1"
        act.book_end = 4
        act.remain_tickets = 1
        act.key = "1"
        act.id = "1"
        act.save.return_value = True
        temp = Mock()
        Activity.objects.select_for_update.return_value = temp
        temp.get = Mock(side_effect=Activity.DoesNotExist)

        user = Mock()
        user.student_id = "1"
        User.objects.get.return_value = user
        settings.get_url.return_value = "1"

        ticket = Mock()
        ticket.status = Ticket.STATUS_VALID
        acti = Mock()
        acti.id = "1"
        ticket.activity = acti
        Ticket.objects.filter.return_value = [ticket]
        Ticket.objects.create.return_value = True

        found = TicketsHandler.handle
        handler = Mock(wraps=TicketsHandler(None, "123", None))
        handler.reply_single_news = Mock(side_effect=lambda x: x)
        handler.reply_text = Mock(side_effect=lambda x: x)
        timezone.now.return_value = 5

        handler.input = {"Content" : "1 1"}
        self.assertRaises(LogicError, found, handler)

    @patch.object(Activity.objects, "select_for_update")
    @patch.object(User.objects, "get")
    @patch.object(timezone, "now")
    @patch.object(settings, "get_url")
    @patch.object(Ticket.objects, "filter")
    @patch.object(Ticket.objects, "create")
    def test_handle_without_user(self, Activity_objects_get, User_ojects_get, timezone_now,
                                     setting_get_url,
                                     Ticket_objects_filter, Ticket_objects_create):
        act = Mock()
        act.book_start = 2
        act.name = "1"
        act.pic_url = ""
        act.description = "1"
        act.book_end = 4
        act.remain_tickets = 1
        act.key = "1"
        act.id = "1"
        act.save.return_value = True
        temp = Mock()
        Activity.objects.select_for_update.return_value = temp
        temp.get.return_value = act
        user = Mock()
        user.student_id = "1"
        User.objects.get = Mock(side_effect=User.DoesNotExist)
        settings.get_url.return_value = "1"

        ticket = Mock()
        ticket.status = Ticket.STATUS_VALID
        acti = Mock()
        acti.id = "1"
        ticket.activity = acti
        Ticket.objects.filter.return_value = [ticket]
        Ticket.objects.create.return_value = True

        found = TicketsHandler.handle
        handler = Mock(wraps=TicketsHandler(None, "123", None))
        handler.reply_single_news = Mock(side_effect=lambda x: x)
        handler.reply_text = Mock(side_effect=lambda x: x)
        timezone.now.return_value = 5

        handler.input = {"Content": "1 1", "FromUserName":"1"}
        self.assertRaises(LogicError, found, handler)

    @patch.object(Activity.objects, "select_for_update")
    @patch.object(User.objects, "get")
    @patch.object(timezone, "now")
    @patch.object(settings, "get_url")
    @patch.object(Ticket.objects, "filter")
    @patch.object(Ticket.objects, "create")
    def test_handle_with_book_without_ticket(self, Activity_objects_get, User_ojects_get, timezone_now,
                                 setting_get_url,
                                 Ticket_objects_filter, Ticket_objects_create):
        act = Mock()
        act.book_start = 2
        act.name = "1"
        act.pic_url = ""
        act.description = "1"
        act.book_end = 4
        act.remain_tickets = 0
        act.key = "1"
        act.id = "1"
        act.save.return_value = True
        temp = Mock()
        Activity.objects.select_for_update.return_value = temp
        temp.get.return_value = act
        user = Mock()
        user.student_id = "1"
        User.objects.get.return_value = user
        settings.get_url.return_value = "1"

        ticket = Mock()
        ticket.status = Ticket.STATUS_VALID
        acti = Mock()
        acti.id = "1"
        ticket.activity = acti
        Ticket.objects.filter.return_value = [ticket]
        Ticket.objects.create.return_value = True

        found = TicketsHandler.handle
        handler = Mock(wraps=TicketsHandler(None, "123", None))
        handler.reply_single_news = Mock(side_effect=lambda x: x)
        handler.reply_text = Mock(side_effect=lambda x: x)
        timezone.now.return_value = 5

        handler.input = {"Content": "1 1", "FromUserName": "1"}

        handler.is_text_command = Mock(side_effect= lambda x: x=="抢票")
        self.assertEqual(found(handler), str('您未抢到') + act.key + str('活动的票！'))

    @patch.object(Activity.objects, "select_for_update")
    @patch.object(User.objects, "get")
    @patch.object(timezone, "now")
    @patch.object(settings, "get_url")
    @patch.object(Ticket.objects, "filter")
    @patch.object(Ticket.objects, "create")
    def test_handle_with_book_with_ticket_but_haved(self, Activity_objects_get, User_ojects_get, timezone_now,
                                             setting_get_url,
                                             Ticket_objects_filter, Ticket_objects_create):
        act = Mock()
        act.book_start = 2
        act.name = "1"
        act.pic_url = ""
        act.description = "1"
        act.book_end = 4
        act.remain_tickets = 1
        act.key = "1"
        act.id = "1"
        act.save.return_value = True
        temp = Mock()
        Activity.objects.select_for_update.return_value = temp
        temp.get.return_value = act
        user = Mock()
        user.student_id = "1"
        User.objects.get.return_value = user
        settings.get_url.return_value = "1"

        ticket = Mock()
        ticket.status = Ticket.STATUS_VALID
        acti = Mock()
        acti.id = "1"
        ticket.activity = acti
        Ticket.objects.filter.return_value = [ticket]
        Ticket.objects.create.return_value = True

        found = TicketsHandler.handle
        handler = Mock(wraps=TicketsHandler(None, "123", None))
        handler.reply_single_news = Mock(side_effect=lambda x: x)
        handler.reply_text = Mock(side_effect=lambda x: x)
        timezone.now.return_value = 3

        handler.input = {"Content": "1 1", "FromUserName": "1"}

        handler.is_text_command = Mock(side_effect=lambda x: x == "抢票")
        self.assertEqual(found(handler), str('您已拥有') + act.key + str('活动的票！'))

    @patch.object(Activity.objects, "select_for_update")
    @patch.object(User.objects, "get")
    @patch.object(timezone, "now")
    @patch.object(settings, "get_url")
    @patch.object(Ticket.objects, "filter")
    @patch.object(Ticket.objects, "create")
    def test_handle_with_book_with_ticket_and_succeed(self, Activity_objects_get, User_ojects_get, timezone_now,
                                                    setting_get_url,
                                                    Ticket_objects_filter, Ticket_objects_create):
        act = Mock()
        act.book_start = 2
        act.name = "1"
        act.pic_url = ""
        act.description = "1"
        act.book_end = 4
        act.remain_tickets = 1
        act.key = "1"
        act.id = "1"
        act.save.return_value = True
        temp = Mock()
        Activity.objects.select_for_update.return_value = temp
        temp.get.return_value = act
        user = Mock()
        user.student_id = "1"
        User.objects.get.return_value = user
        settings.get_url.return_value = "1"

        ticket = Mock()
        ticket.status = Ticket.STATUS_VALID
        acti = Mock()
        acti.id = "2"
        ticket.activity = acti
        Ticket.objects.filter.return_value = [ticket]
        Ticket.objects.create.return_value = True

        found = TicketsHandler.handle
        handler = Mock(wraps=TicketsHandler(None, "123", None))
        handler.reply_single_news = Mock(side_effect=lambda x: x)
        handler.reply_text = Mock(side_effect=lambda x: x)
        timezone.now.return_value = 3

        handler.input = {"Content": "1 1", "FromUserName": "1"}

        handler.is_text_command = Mock(side_effect=lambda x: x == "抢票")
        self.assertEqual(found(handler), str('您已成功抢到') + act.key + str('活动的票！'))

    @patch.object(Activity.objects, "select_for_update")
    @patch.object(User.objects, "get")
    @patch.object(timezone, "now")
    @patch.object(settings, "get_url")
    @patch.object(Ticket.objects, "filter")
    @patch.object(Ticket.objects, "create")
    def test_handle_with_quit_without_ticket(self, Activity_objects_get, User_ojects_get, timezone_now,
                                                      setting_get_url,
                                                      Ticket_objects_filter, Ticket_objects_create):
        act = Mock()
        act.book_start = 2
        act.name = "1"
        act.pic_url = ""
        act.description = "1"
        act.book_end = 4
        act.remain_tickets = 1
        act.key = "1"
        act.id = "1"
        act.save.return_value = True
        temp = Mock()
        Activity.objects.select_for_update.return_value = temp
        temp.get.return_value = act
        user = Mock()
        user.student_id = "1"
        User.objects.get.return_value = user
        settings.get_url.return_value = "1"

        ticket = Mock()
        ticket.status = Ticket.STATUS_VALID
        acti = Mock()
        acti.id = "1"
        ticket.activity = acti
        Ticket.objects.filter.return_value = []
        Ticket.objects.create.return_value = True

        found = TicketsHandler.handle
        handler = Mock(wraps=TicketsHandler(None, "123", None))
        handler.reply_single_news = Mock(side_effect=lambda x: x)
        handler.reply_text = Mock(side_effect=lambda x: x)
        timezone.now.return_value = 5

        handler.input = {"Content": "1 1", "FromUserName": "1"}

        handler.is_text_command = Mock(side_effect=lambda x: x == "退票")
        self.assertEqual(found(handler), str('您还没有') + act.key + str('活动的票！'))

    @patch.object(Activity.objects, "select_for_update")
    @patch.object(User.objects, "get")
    @patch.object(timezone, "now")
    @patch.object(settings, "get_url")
    @patch.object(Ticket.objects, "filter")
    @patch.object(Ticket.objects, "create")
    def test_handle_with_quit_with_ticket_but_not_match(self, Activity_objects_get, User_ojects_get, timezone_now,
                                             setting_get_url,
                                             Ticket_objects_filter, Ticket_objects_create):
        act = Mock()
        act.book_start = 2
        act.name = "1"
        act.pic_url = ""
        act.description = "1"
        act.book_end = 4
        act.remain_tickets = 1
        act.key = "1"
        act.id = "1"
        act.save.return_value = True
        temp = Mock()
        Activity.objects.select_for_update.return_value = temp
        temp.get.return_value = act
        user = Mock()
        user.student_id = "1"
        User.objects.get.return_value = user
        settings.get_url.return_value = "1"

        ticket = Mock()
        ticket.status = Ticket.STATUS_VALID
        acti = Mock()
        acti.id = "2"
        ticket.activity = acti
        Ticket.objects.filter.return_value = [ticket]
        Ticket.objects.create.return_value = True

        found = TicketsHandler.handle
        handler = Mock(wraps=TicketsHandler(None, "123", None))
        handler.reply_single_news = Mock(side_effect=lambda x: x)
        handler.reply_text = Mock(side_effect=lambda x: x)
        timezone.now.return_value = 5

        handler.input = {"Content": "1 1", "FromUserName": "1"}

        handler.is_text_command = Mock(side_effect=lambda x: x == "退票")
        self.assertEqual(found(handler), str('您还没有') + act.key + str('活动的票！'))

    @patch.object(Activity.objects, "select_for_update")
    @patch.object(User.objects, "get")
    @patch.object(timezone, "now")
    @patch.object(settings, "get_url")
    @patch.object(Ticket.objects, "filter")
    @patch.object(Ticket.objects, "create")
    def test_handle_with_quit_succeed(self, Activity_objects_get, User_ojects_get, timezone_now,
                                                        setting_get_url,
                                                        Ticket_objects_filter, Ticket_objects_create):
        act = Mock()
        act.book_start = 2
        act.name = "1"
        act.pic_url = ""
        act.description = "1"
        act.book_end = 4
        act.remain_tickets = 1
        act.key = "1"
        act.id = "1"
        act.save.return_value = True
        temp = Mock()
        Activity.objects.select_for_update.return_value = temp
        temp.get.return_value = act
        user = Mock()
        user.student_id = "1"
        User.objects.get.return_value = user
        settings.get_url.return_value = "1"

        ticket = Mock()
        ticket.status = Ticket.STATUS_VALID
        acti = Mock()
        acti.id = "1"
        ticket.activity = acti
        Ticket.objects.filter.return_value = [ticket]
        Ticket.objects.create.return_value = True

        found = TicketsHandler.handle
        handler = Mock(wraps=TicketsHandler(None, "123", None))
        handler.reply_single_news = Mock(side_effect=lambda x: x)
        handler.reply_text = Mock(side_effect=lambda x: x)
        timezone.now.return_value = 5

        handler.input = {"Content": "1 1", "FromUserName": "1"}

        handler.is_text_command = Mock(side_effect=lambda x: x == "退票")
        self.assertEqual(found(handler), str('您已成功退掉') + act.key + str('活动的票！'))

    @patch.object(Activity.objects, "select_for_update")
    @patch.object(User.objects, "get")
    @patch.object(timezone, "now")
    @patch.object(settings, "get_url")
    @patch.object(Ticket.objects, "filter")
    @patch.object(Ticket.objects, "create")
    def test_handle_with_quit_succeed(self, Activity_objects_get, User_ojects_get, timezone_now,
                                      setting_get_url,
                                      Ticket_objects_filter, Ticket_objects_create):
        act = Mock()
        act.book_start = 2
        act.name = "1"
        act.pic_url = ""
        act.description = "1"
        act.book_end = 4
        act.remain_tickets = 1
        act.key = "1"
        act.id = "1"
        act.save.return_value = True
        temp = Mock()
        Activity.objects.select_for_update.return_value = temp
        temp.get.return_value = act
        user = Mock()
        user.student_id = "1"
        User.objects.get.return_value = user
        settings.get_url.return_value = "1"

        ticket = Mock()
        ticket.status = Ticket.STATUS_VALID
        acti = Mock()
        acti.id = "1"
        ticket.activity = acti
        Ticket.objects.filter.return_value = []
        Ticket.objects.create.return_value = True

        found = TicketsHandler.handle
        handler = Mock(wraps=TicketsHandler(None, "123", None))
        handler.reply_single_news = Mock(side_effect=lambda x: x)
        handler.reply_text = Mock(side_effect=lambda x: x)
        timezone.now.return_value = 5

        handler.input = {"Content": "1 1", "FromUserName": "1"}

        handler.is_text_command = Mock(side_effect=lambda x: x == "取票")
        self.assertEqual(found(handler), str('您还没有') + act.key + str('活动的票！'))

    @patch.object(Activity.objects, "select_for_update")
    @patch.object(User.objects, "get")
    @patch.object(timezone, "now")
    @patch.object(settings, "get_url")
    @patch.object(Ticket.objects, "filter")
    @patch.object(Ticket.objects, "create")
    def test_handle_with_quit_but_not_match(self, Activity_objects_get, User_ojects_get, timezone_now,
                                      setting_get_url,
                                      Ticket_objects_filter, Ticket_objects_create):
        act = Mock()
        act.book_start = 2
        act.name = "1"
        act.pic_url = ""
        act.description = "1"
        act.book_end = 4
        act.remain_tickets = 1
        act.key = "1"
        act.id = "1"
        act.save.return_value = True
        temp = Mock()
        Activity.objects.select_for_update.return_value = temp
        temp.get.return_value = act
        user = Mock()
        user.student_id = "1"
        User.objects.get.return_value = user
        settings.get_url.return_value = "1"

        ticket = Mock()
        ticket.status = Ticket.STATUS_VALID
        acti = Mock()
        acti.id = "2"
        ticket.activity = acti
        Ticket.objects.filter.return_value = [ticket]
        Ticket.objects.create.return_value = True

        found = TicketsHandler.handle
        handler = Mock(wraps=TicketsHandler(None, "123", None))
        handler.reply_single_news = Mock(side_effect=lambda x: x)
        handler.reply_text = Mock(side_effect=lambda x: x)
        timezone.now.return_value = 5

        handler.input = {"Content": "1 1", "FromUserName": "1"}

        handler.is_text_command = Mock(side_effect=lambda x: x == "取票")
        self.assertEqual(found(handler), str('您还没有') + act.key + str('活动的票！'))

    @patch.object(Activity.objects, "select_for_update")
    @patch.object(User.objects, "get")
    @patch.object(timezone, "now")
    @patch.object(settings, "get_url")
    @patch.object(Ticket.objects, "filter")
    @patch.object(Ticket.objects, "create")
    def test_handle_with_quit_succeed(self, Activity_objects_get, User_ojects_get, timezone_now,
                                            setting_get_url,
                                            Ticket_objects_filter, Ticket_objects_create):
        act = Mock()
        act.book_start = 2
        act.name = "1"
        act.pic_url = ""
        act.description = "1"
        act.book_end = 4
        act.remain_tickets = 1
        act.key = "1"
        act.id = "1"
        act.save.return_value = True
        temp = Mock()
        Activity.objects.select_for_update.return_value = temp
        temp.get.return_value = act
        user = Mock()
        user.student_id = "1"
        User.objects.get.return_value = user
        settings.get_url.return_value = "1"

        ticket = Mock()
        ticket.status = Ticket.STATUS_VALID
        acti = Mock()
        acti.id = "1"
        ticket.activity = acti
        Ticket.objects.filter.return_value = [ticket]
        Ticket.objects.create.return_value = True

        found = TicketsHandler.handle
        handler = Mock(wraps=TicketsHandler(None, "123", None))
        handler.reply_single_news = Mock(side_effect=lambda x: x)
        handler.reply_text = Mock(side_effect=lambda x: x)
        timezone.now.return_value = 5

        handler.input = {"Content": "1 1", "FromUserName": "1"}

        handler.is_text_command = Mock(side_effect=lambda x: x == "取票")
        self.assertEqual(found(handler), {
            'Title' : "1",
            "PicUrl" : "",
            "Description" : "1",
            "Url" : "1"
        })

class BookWhatHandlerTest(TestCase):
    def test_check_book_what(self):
        found = BookWhatHandler.check
        handler = Mock(wraps=BookWhatHandler(None, "123", None))
        handler.view.event_keys = {"book_what": True}
        handler.is_event_click = Mock(side_effect=lambda x:x)
        self.assertEqual(found(handler), True)

    @patch.object(Activity.objects, "filter")
    def test_handle_without_activity(self, Activity_objects_filter):
        found = BookWhatHandler.handle
        handle = Mock(wraps=BookWhatHandler(None, "123", None))
        Activity.objects.filter.return_value = []
        handle.reply_text = Mock(side_effect=lambda x: x)
        self.assertEqual(found(handle), '目前没有可以抢票的活动')

    @patch.object(Activity.objects, "filter")
    @patch.object(settings, "get_url")
    def test_handle_with_activity_but_not_match(self, Activity_objects_filter, settings_get_url):
        found = BookWhatHandler.handle
        handle = Mock(wraps=BookWhatHandler(None, "123", None))
        act = Mock()
        act.status = Activity.STATUS_DELETED
        act.name ="1"
        act.pic_url = ""
        act.description = "1"
        act.id = "1"
        Activity.objects.filter.return_value = [act]
        settings.get_url.return_value = "1"
        handle.reply_text = Mock(side_effect=lambda x: x)
        self.assertEqual(found(handle), '目前没有可以抢票的活动')

    @patch.object(Activity.objects, "filter")
    @patch.object(settings, "get_url")
    def test_handle_with_activity_but_not_match(self, Activity_objects_filter, settings_get_url):
        found = BookWhatHandler.handle
        handle = Mock(wraps=BookWhatHandler(None, "123", None))
        act = Mock()
        act.status = Activity.STATUS_PUBLISHED
        act.name = "1"
        act.pic_url = ""
        act.description = "1"
        act.id = "1"
        Activity.objects.filter.return_value = [act]
        settings.get_url.return_value = "1"
        handle.reply_text = Mock(side_effect=lambda x: x)
        handle.reply_news = Mock(side_effect=lambda x: x)
        self.assertEqual(found(handle), [{
            'Title' : "1",
            'PicUrl' : "",
            'Description' : "1",
            'Url' : "1"
        }])

class GetTicketHandlerTest(TestCase):
    def test_check_get_ticket(self):
        found = GetTicketHandler.check
        handler = Mock(wraps=GetTicketHandler(None, "123", None))
        handler.view.event_keys = {"get_ticket": True}
        handler.is_event_click = Mock(side_effect=lambda x:x)
        self.assertEqual(found(handler), True)

    @patch.object(User.objects, "get")
    def test_handle_without_user(self, User_objects_get):
        found = GetTicketHandler.handle
        handler = Mock(wraps=GetTicketHandler(None, "123", None))
        handler.input = {"Content":"1", "FromUserName":"1"}
        User.objects.get = Mock(side_effect = User.DoesNotExist)
        self.assertRaises(LogicError, found, handler)

    @patch.object(User.objects, "get")
    @patch.object(Ticket.objects, "filter")
    def test_handle_without_ticket(self, User_objects_get, Ticket_objects_filter):
        found = GetTicketHandler.handle
        handler = Mock(wraps=GetTicketHandler(None, "123", None))
        handler.input = {"Content": "1", "FromUserName": "1"}
        user =Mock()
        user.student_id = "1"
        User.objects.get.return_value = user
        Ticket.objects.filter.return_value = []
        handler.reply_text = Mock(side_effect=lambda x:x)
        self.assertEqual(found(handler), '目前没有票')

    @patch.object(User.objects, "get")
    @patch.object(Ticket.objects, "filter")
    @patch.object(settings, "get_url")
    def test_handle_with_ticket_but_status_not_valid(self, User_objects_get, Ticket_objects_filter, setting_get_url):
        found = GetTicketHandler.handle
        handler = Mock(wraps=GetTicketHandler(None, "123", None))
        handler.input = {"Content": "1", "FromUserName": "1"}
        user = Mock()
        user.student_id = "1"
        User.objects.get.return_value = user
        ticket = Mock()
        ticket.status = Ticket.STATUS_USED
        act = Mock()
        act.name = "1"
        act.pic_url = ""
        act.description = "1"
        ticket.activity = act
        Ticket.objects.filter.return_value = [ticket]
        settings.get_url.return_value = "1"
        handler.reply_text = Mock(side_effect=lambda x: x)
        self.assertEqual(found(handler), '目前没有票')

    @patch.object(User.objects, "get")
    @patch.object(Ticket.objects, "filter")
    @patch.object(settings, "get_url")
    def test_handle_with_ticket_and_status_valid(self, User_objects_get, Ticket_objects_filter, setting_get_url):
        found = GetTicketHandler.handle
        handler = Mock(wraps=GetTicketHandler(None, "123", None))
        handler.input = {"Content": "1", "FromUserName": "1"}
        user = Mock()
        user.student_id = "1"
        User.objects.get.return_value = user
        ticket = Mock()
        ticket.status = Ticket.STATUS_VALID
        act = Mock()
        act.name = "1"
        act.pic_url = ""
        act.description = "1"
        ticket.activity = act
        Ticket.objects.filter.return_value = [ticket]
        settings.get_url.return_value = "1"
        handler.reply_text = Mock(side_effect=lambda x: x)
        handler.reply_news = Mock(side_effect=lambda x: x)
        self.assertEqual(found(handler), [{
            'Title':"1",
            'PicUrl':"",
            'Description':"1",
            "Url":"1"
        }])
