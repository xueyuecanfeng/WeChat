from django.test import TestCase
from django.core.urlresolvers import resolve
from django.http import HttpRequest
from django.test import TestCase
from django.utils.datastructures import MultiValueDict
import adminpage.urls
import uuid
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib import auth
from unittest.mock import Mock,patch
from codex.baseerror import InputError, ValidateError
from userpage.views import UserBind
import json
import datetime
from wechat.views import CustomWeChatView
from wechat.models import  User,Activity,Ticket
from django.utils import timezone

class LoginTest(TestCase):
    def test_get_without_authenticated(self):
        found = resolve('/login/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value= False)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    def test_get_with_authenticated(self):
        found = resolve('/login/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 0)

    def test_post_without_input(self):
        found = resolve('/login/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 1)

    @patch.object(auth, "authenticate")
    def test_post_activity_not_exist(self, auth_authenticate):
        found = resolve('/login/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"username":"1", "password":"1"}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        auth.authenticate = Mock(return_value = False)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    @patch.object(auth, "authenticate")
    @patch.object(auth, "login")
    def test_post_user_exist(self, auth_authenticate, auth_login):
        found = resolve('/login/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"username":"1", "password":"1"}')
        auth.authenticate = Mock(return_value=True)
        auth.login = Mock(return_value=True)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 0)

class LogoutTest(TestCase):
    @patch.object(auth, "logout")
    def test_logout_failed(self, auth_logout):
        found = resolve('/logout/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        auth.authenticate = Mock(return_value=True)
        request.user.is_authenticated = Mock(return_value=True)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    @patch.object(auth, "logout")
    def test_logout_true(self, auth_logout):
        found = resolve('/logout/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        auth.authenticate = Mock(return_value=True)
        request.user.is_authenticated = Mock(return_value=False)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 0)

class ActivityListTest(TestCase):
    @patch.object(auth, "authenticate")
    def test_get_user_is_not_authenticate(self, auth_athenticate):
        found = resolve('/activity/list/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=False)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    @patch.object(auth, "authenticate")
    @patch.object(Activity.objects, "filter")
    @patch.object(timezone, "now")
    def test_get_activity_not_exist(self, auth_athenticate, Activity_objects_filter, timezone_now):
        found = resolve('/activity/list/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        time = Mock()
        time.timestamp = Mock(return_value='1')
        timezone.now.return_value = time
        act = []
        Activity.objects.filter = Mock(return_value=act)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    @patch.object(auth, "authenticate")
    @patch.object(Activity.objects, "filter")
    @patch.object(timezone, "now")
    def test_get_activity_right(self, auth_athenticate, Activity_objects_filter, timezone_now):
        found = resolve('/activity/list/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        time = Mock()
        time.timestamp = Mock(return_value='1')
        timezone.now.return_value = time
        act = Mock()
        act.id = "1"
        act.name = "1"
        act.description = "1"
        act.start_time = time
        act.end_time = time
        act.place = "1"
        act.book_start = time
        act.book_end = time
        act.status = 1

        Activity.objects.filter = Mock(return_value=[act, act])
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['data'], [
            {
                "id": "1",
                "name" : "1",
                "description" : "1",
                "startTime" : "1",
                "endTime" : "1",
                "place" : "1",
                "bookStart" : "1",
                "bookEnd" : "1",
                "currentTime" : "1",
                "status" : 1,
            },
            {
                "id": "1",
                "name": "1",
                "description": "1",
                "startTime": "1",
                "endTime": "1",
                "place": "1",
                "bookStart": "1",
                "bookEnd": "1",
                "currentTime": "1",
                "status": 1,
            }
            ])

class ActivityDeleteTest(TestCase):

    def test_post_without_input(self):
        found = resolve('/activity/delete/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 1)

    @patch.object(Activity.objects, "get")
    def test_post_activity_not_exist(self, Activity_objects_get):
        found = resolve('/activity/delete/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"id" : "1"}')
        Activity.objects.get.side_effect = Activity.DoesNotExist
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    @patch.object(Activity.objects, "get")
    def test_post_activity_delete_succeed(self,Activity_objects_get):
        found = resolve('/activity/delete/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"id" : "1"}')
        act = Mock()
        act.save = Mock(return_value=True)
        act.status = 1
        Activity.objects.get.return_value = act
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 0)

class ActivityCreateTest(TestCase):

    def test_post_without_authenticated(self):
        found = resolve('/activity/create/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value= False)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    def test_post_without_input(self):
        found = resolve('/activity/create/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 1)

    @patch.object(Activity.objects, "create")
    def test_post_activity_create_failed(self, activity_objects_create):
        found = resolve('/activity/create/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"name" : "1","key" : "1","place":"1", "description":"1","picUrl":"", "startTime":"1", "endTime":"1", "bookStart":"1", "bookEnd":"1", "totalTickets":"1", "status":1}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        Activity.objects.create.return_value ={}
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    @patch.object(Activity.objects, "create")
    def test_post_activity_create_success(self, activity_objects_create):
        found = resolve('/activity/create/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(
            return_value='{"name" : "1","key" : "1","place":"1", "description":"1","picUrl":"", "startTime":"1", "endTime":"1", "bookStart":"1", "bookEnd":"1", "totalTickets":"1", "status":1}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        act = Mock()
        act.id = "1"
        Activity.objects.create.return_value = act
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['data'], "1")

class ImageUploadTest(TestCase):

    def test_post_without_authenticated(self):
        found = resolve('/image/upload/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value= False)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    def test_post_without_input(self):
        found = resolve('/image/upload/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 1)

    @patch.object(uuid, "uuid1")
    def test_post_dest_not_open(self, uuid_uuid1):
        found = resolve('/image/upload/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        file = MultiValueDict()
        file['image'] = InMemoryUploadedFile(None, None, "1", 'image/jpg', None, 'utf-8')
        file['image'].chunks = Mock(return_value= ["1"])
        request.FILES = file
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        uuid.uuid1.return_value = 1
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    @patch.object(uuid, "uuid1")
    def test_post_upload_succeed(self, uuid_uuid1):
        found = resolve('/image/upload/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        file = MultiValueDict()
        file['image'] = InMemoryUploadedFile(None, None, "1", 'image/jpg', None, 'utf-8')
        file['image'].chunks = Mock(return_value=[b"1"])
        request.FILES = file
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        uuid.uuid1.return_value = 1
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 0)

class ActivityDetailTest(TestCase):

    def test_get_without_authenticated(self):
        found = resolve('/activity/detail/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=False)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    def test_get_without_input(self):
        found = resolve('/activity/detail/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 1)

    @patch.object(Activity.objects, "get")
    def test_get_with_activity_not_exist(self, Activity_objects_get):
        found = resolve('/activity/detail/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"id" : "1"}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        Activity.objects.get.side_effect = Activity.DoesNotExist
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    @patch.object(Activity.objects, "get")
    @patch.object(Ticket.objects, "filter")
    @patch.object(timezone, "now")
    def test_get_without_used_ticket(self, Activity_objects_get, Ticket_objects_filter, timezone_now):
        found = resolve('/activity/detail/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"id" : "1"}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        time = Mock()
        time.timestamp = Mock(return_value='1')
        timezone.now.return_value = time
        act = Mock()
        act.name = "1"
        act.key = "1"
        act.description = "1"
        act.start_time = time
        act.end_time = time
        act.place = "1"
        act.book_start = time
        act.book_end = time
        act.total_tickets = 10
        act.pic_url = ""
        act.remain_tickets = 5
        act.status = 1
        Ticket.objects.filter.return_value = []
        Activity.objects.get.return_value = act
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['data'],{
            "name": "1",
            "key": "1",
            "description": "1",
            "startTime": "1",
            "endTime": "1",
            "place": "1",
            "bookStart": "1",
            "bookEnd": "1",
            "totalTickets": 10,
            "picUrl": "",
            "bookedTickets": 5,
            "usedTickets": 0,
            "currentTime": "1",
            "status": 1
        })

    @patch.object(Activity.objects, "get")
    @patch.object(Ticket.objects, "filter")
    @patch.object(timezone, "now")
    def test_get_right_return(self, Activity_objects_get, Ticket_objects_filter, timezone_now):
        found = resolve('/activity/detail/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"id" : "1"}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        time = Mock()
        time.timestamp = Mock(return_value='1')
        timezone.now.return_value = time
        act = Mock()
        act.name = "1"
        act.key = "1"
        act.description = "1"
        act.start_time = time
        act.end_time = time
        act.place = "1"
        act.book_start = time
        act.book_end = time
        act.total_tickets = 10
        act.pic_url = ""
        act.remain_tickets = 5
        act.status = 1
        Ticket.objects.filter.return_value = ["1", "1"]
        Activity.objects.get.return_value = act
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
            "totalTickets": 10,
            "picUrl": "",
            "bookedTickets": 5,
            "usedTickets": 2,
            "currentTime": "1",
            "status": 1
        })

    def test_post_without_authenticated(self):
        found = resolve('/activity/detail/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=False)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    def test_post_without_input(self):
        found = resolve('/activity/detail/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 1)

    @patch.object(Activity.objects, "get")
    def test_post_with_activity_not_exist(self,Activity_objects_get):
        found = resolve('/activity/detail/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"id" : "1", "name" : "1", "place":"1", "description":"1", "picUrl":"1", "startTime":"1", "endTime":"1", "bookStart":"1", "bookEnd":"1", "totalTickets":"1", "status":1}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        Activity.objects.get.side_effect = Activity.DoesNotExist
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    @patch.object(Activity.objects, "get")
    @patch.object(timezone, "now")
    def test_post_with_right_input(self, Activity_objects_get, timezone_now):
        found = resolve('/activity/detail/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(
            return_value='{"id" : "1", "name" : "1", "place":"1", "description":"1", "picUrl":"1", "startTime":"1", "endTime":"1", "bookStart":"1", "bookEnd":"1", "totalTickets":"1", "status":1}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        time = Mock()
        time.timestamp = Mock(return_value='1')
        timezone.now.return_value = time
        act = Mock()
        act.name = "1"
        act.key = "1"
        act.description = "1"
        act.start_time = time
        act.end_time = time
        act.place = "1"
        act.book_start = time
        act.book_end = time
        act.total_tickets = 10
        act.pic_url = ""
        act.remain_tickets = 5
        act.status = 1
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 0)

class ActivityMenuTest(TestCase):
    def test_get_without_authenticated(self):
        found = resolve('/activity/menu/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=False)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    @patch.object(Activity.objects, "filter")
    def test_get_without_published_activity(self, Activity_objects_filter):
        found = resolve('/activity/menu/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        Activity.objects.filter.return_value = []
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    @patch.object(Activity.objects, "filter")
    @patch.object(CustomWeChatView.lib, "get_wechat_menu")
    def test_get_without_sub_button(self, Activity_objects_filter, CustomWeChatView_lib_get_wechat_menu):
        found = resolve('/activity/menu/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        act1 = Mock()
        act1.id = "1"
        act1.name = "1"
        act2 = Mock()
        act2.id = "2"
        act2.name = "2"
        Activity.objects.filter.return_value = [act1, act2]
        menu = {"sub_button" : []}
        CustomWeChatView.lib.get_wechat_menu.return_value = [menu, menu]
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['data'], [{ "id":"1", "name":"1", "menuIndex":0},{ "id":"2", "name":"2", "menuIndex":0}])

    @patch.object(Activity.objects, "filter")
    @patch.object(CustomWeChatView.lib, "get_wechat_menu")
    def test_get_with_sub_button_single_match_activity(self, Activity_objects_filter, CustomWeChatView_lib_get_wechat_menu):
        found = resolve('/activity/menu/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        act1 = Mock()
        act1.id = "1"
        act1.name = "1"
        act2 = Mock()
        act2.id = "2"
        act2.name = "2"
        Activity.objects.filter.return_value = [act1, act2]
        menu = {"sub_button": [{"name":"1"}, {"name":"3"}]}
        CustomWeChatView.lib.get_wechat_menu.return_value = [menu, menu]
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['data'],
                         [{"id": "1", "name": "1", "menuIndex": 1}, {"id": "2", "name": "2", "menuIndex": 0}])

    @patch.object(Activity.objects, "filter")
    @patch.object(CustomWeChatView.lib, "get_wechat_menu")
    def test_get_with_sub_button_multi_match_activity(self, Activity_objects_filter, CustomWeChatView_lib_get_wechat_menu):
        found = resolve('/activity/menu/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='GET')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        act1 = Mock()
        act1.id = "1"
        act1.name = "1"
        act2 = Mock()
        act2.id = "2"
        act2.name = "2"
        Activity.objects.filter.return_value = [act1, act2]
        menu = {"sub_button": [{"name": "1"}, {"name": "2"}]}
        CustomWeChatView.lib.get_wechat_menu.return_value = [menu, menu]
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['data'],
                         [{"id": "1", "name": "1", "menuIndex": 1}, {"id": "2", "name": "2", "menuIndex": 2}])

    def test_post_without_authenticated(self):
        found = resolve('/activity/menu/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=False)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    @patch.object(CustomWeChatView, "update_menu")
    def test_post_without_input(self, CustomWeChatView_update_menu):
        found = resolve('/activity/menu/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='[]')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        CustomWeChatView.update_menu.return_value = True
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 0)

    @patch.object(Activity.objects, "get")
    @patch.object(CustomWeChatView, "update_menu")
    def test_post_with_activity_not_exist(self, Activity_objects_get,CustomWeChatView_update_menu):
        found = resolve('/activity/menu/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='[1, 2]')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        CustomWeChatView.update_menu.return_value = True
        Activity.objects.get.side_effect = Activity.DoesNotExist
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    @patch.object(Activity.objects, "get")
    @patch.object(CustomWeChatView, "update_menu")
    def test_post_with_right_input(self, Activity_objects_get, CustomWeChatView_update_menu):
        found = resolve('/activity/menu/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='[1, 2]')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        CustomWeChatView.update_menu.return_value = True
        Activity.objects.get.return_value = {"1"}
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 0)

class ActivityCheckinTest(TestCase):
    def test_post_without_authenticated(self):
        found = resolve('/activity/checkin/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=False)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    def test_post_without_input(self):
        found = resolve('/activity/checkin/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 1)

    @patch.object(Ticket.objects, "get")
    def test_post_with_input_ticket_but_ticket_not_exist(self, Ticket_objects_get):
        found = resolve('/activity/checkin/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"actId":"1", "ticket":"1"}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        Ticket.objects.get.side_effect = Ticket.DoesNotExist
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    @patch.object(Ticket.objects, "get")
    def test_post_with_input_ticket_but_ticket_not_match(self, Ticket_objects_get):
        found = resolve('/activity/checkin/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"actId":"1", "ticket":"1"}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        ticket = Mock()
        ticket.activity = {"id" : "3"}
        ticket.status = 1
        ticket.student_id = "1"
        Ticket.objects.get.return_values = ticket
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    @patch.object(Ticket.objects, "get")
    def test_post_with_input_ticket_and_ticket_match(self, Ticket_objects_get):
        found = resolve('/activity/checkin/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"actId":"1", "ticket":"1"}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        act = Mock()
        act.id = "1"
        ticket = Mock()
        ticket.status = 1
        ticket.student_id = "1"
        ticket.activity = act
        ticket.save = Mock(return_value=True)
        Ticket.objects.get = Mock(return_value=ticket)
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['data'], {
            "ticket": "1",
            "studentId": "1"
        })

    @patch.object(Ticket.objects, "filter")
    def test_post_with_studentId_but_ticket_not_exist(self,Ticket_objects_filter):
        found = resolve('/activity/checkin/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"actId":"1", "studentId":"1"}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        Ticket.objects.filter.return_value = []
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    @patch.object(Ticket.objects, "filter")
    def test_post_with_studentId_but_ticket_not_match(self, Ticket_objects_filter):
        found = resolve('/activity/checkin/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"actId":"1", "studentId":"1"}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        act = Mock()
        act.id = "2"
        ticket = Mock()
        ticket.status = 1
        ticket.activity = act
        ticket.save = Mock(return_value=True)
        Ticket.objects.filter.return_value = [ticket]
        response = json.loads(found.func(request).content.decode())
        self.assertEqual(response['code'], 2)

    @patch.object(Ticket.objects, "filter")
    def test_post_with_studentId_and_ticket_match(self, Ticket_objects_filter):
        found = resolve('/activity/checkin/', urlconf=adminpage.urls)
        request = Mock(wraps=HttpRequest(), method='POST')
        request.body = Mock()
        request.body.decode = Mock(return_value='{"actId":"1", "studentId":"1"}')
        request.user = Mock()
        request.user.is_authenticated = Mock(return_value=True)
        act = Mock()
        act.id = "1"
        ticket = Mock()
        ticket.status = 1
        ticket.activity = act
        ticket.unique_id = "1"
        ticket.save = Mock(return_value=True)
        Ticket.objects.filter.return_value = [ticket]
        response = json.loads(found.func(request).content.decode())
        print(response)
        self.assertEqual(response['data'], {
            "ticket" : "1",
            "studentId" : "1"
        })