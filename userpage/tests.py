from django.core.urlresolvers import resolve
from django.http import HttpRequest
from django.test import TestCase
import userpage.urls
from unittest.mock import Mock,patch
from codex.baseerror import InputError, ValidateError
from userpage.views import UserBind
import json
import datetime
from wechat.models import  User,Activity,Ticket
from django.utils import timezone

# Create your tests here.
class URLTest(TestCase):
    def test_u_bind(self):
        response = self.client.get('/u/bind')
        self.assertContains(response, 'inputUsername')

class UserBindTest(TestCase):
    def test_get_without_openid(self):
        found = resolve('/user/bind/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 1)

    def test_get_with_openid(self):
        found = resolve('/user/bind/', urlconf = userpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"openid" : "1"}')
        with patch.object(User, 'get_by_openid',return_value=Mock(student_id=1)) as MockUser:
            response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 0)

    def test_validate_user_raise_error_without_input(self):
        user_bind_view = UserBind()
        with self.assertRaises(ValidateError):
            user_bind_view.validate_user()

    def test_validate_user_with_wrong_username_password(self):
        user_bind_view = UserBind()
        user_bind_view.input = {'student_id':1, 'password':'x'}
        with self.assertRaises(ValidateError):
            user_bind_view.validate_user()

    def test_post_without_input(self):
        found = resolve('/user/bind/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 1)

    @patch.object(UserBind, "validate_user")
    def test_post_with_all_input_but_wrong(self, UserBind_validate_user):
        found = resolve('/user/bind/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"openid" : "1", "student_id":"1", "password":"x"}')
        UserBind.validate_user = Mock(side_effect=ValidateError('msg='))
        with patch.object(User, 'get_by_openid',return_value=Mock(student_id="1")) as MockUser:
            response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 3)

    @patch.object(UserBind, "validate_user")
    def test_post_with_all_input_right(self, UserBind_validate_user):
        found = resolve('/user/bind/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        UserBind.validate_user.return_value = True
        request.body.decode = Mock(return_value='{"openid" : "1", "student_id":"1", "password":"x"}')
        with patch.object(User, 'get_by_openid',return_value=Mock(student_id="1")) as MockUser:
            response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 0)

class ActivityDetailTest(TestCase):
    def test_get_without_id(self):
        found = resolve('/activity/detail/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 1)

    def test_get_with_error_id(self):
        found = resolve('/activity/detail/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"id" : "100"}')
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    def test_get_with_error_activity_status(self):
        found = resolve('/activity/detail/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"id" : "1"}')
        with patch.object(Activity.objects, 'get', return_value=Mock(status = 0)) as MockActivity:
            response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    @patch.object(Activity.objects, "get")
    def test_get_with_error_input(self, Activity_objects_get):
        found = resolve('/activity/detail/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"id" : "1"}')
        Activity.objects.get.side_effect = Activity.DoesNotExist
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    @patch.object(timezone, "now")
    @patch.object(Activity.objects, 'get')
    def test_get_with_right_id(self, timezone_now, Activity_objects_get):
        found = resolve('/activity/detail/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"id" : "1"}')
        time = Mock()
        time.timestamp = Mock(return_value='1')
        timezone.now.return_value = time
        activity = Mock()
        activity.name = "1"
        activity.key = "1"
        activity.description = "1"
        activity.start_time=time
        activity.end_time = time
        activity.place = "1"
        activity.book_start = time
        activity.book_end = time
        activity.total_tickets = "10"
        activity.status = 1
        activity.pic_url = ""
        activity.remain_tickets = "10"
        Activity.objects.get.return_value = activity
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['data'], {
            "name": "1",
            "key": "1",
            "description": "1",
            "startTime": "1",
            "endTime": "1",
            "place": "1",
            "bookStart": "1",
            "bookEnd": "1",
            "totalTickets": "10",
            "picUrl": "",
            "remainTickets": "10",
            "currentTime": "1"
        })

class TicketDetailTest(TestCase):
    def test_get_without_input(self):
        found = resolve('/ticket/detail/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 1)

    @patch.object(Ticket.objects, "get")
    def test_get_without_error_ticket(self, Ticket_objects_get):
        found = resolve('/ticket/detail/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"openid":"1", "ticket":"1"}')
        Ticket.objects.get.side_effect = Ticket.DoesNotExist
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    @patch.object(timezone, "now")
    @patch.object(Ticket.objects, 'get')
    def test_get_with_right_input(self, timezone_now, Ticket_objects_get):
        found = resolve('/ticket/detail/', urlconf=userpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"openid":"1", "ticket":"1"}')
        time = Mock()
        time.timestamp = Mock(return_value='1')
        timezone.now.return_value = time
        act = Mock()
        act.name = "1"
        act.place = "1"
        act.key = "1"
        act.start_time = time
        act.end_time = time
        ticket = Mock()
        ticket.student_id="1"
        ticket.unique_id="1"
        ticket.activity = act
        ticket.status=1
        Ticket.objects.get.return_value = ticket
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response["data"], {
            "activityName": "1",
            "place": "1",
            "activityKey": "1",
            "uniqueId": "1",
            "startTime": "1",
            "endTime": "1",
            "currentTime": "1",
            "status": 1
        })

