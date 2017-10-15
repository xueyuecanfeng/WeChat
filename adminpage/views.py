from codex.baseerror import *
from codex.baseview import APIView
from django.contrib import auth
from django.contrib.auth.models import User
from django.utils import timezone

import uuid
from wechat.models import User,Activity,Ticket
from wechat.views import CustomWeChatView
import os
import requests
import WeChatTicket.settings

class Login(APIView):

    def get(self):
        if not self.request.user.is_authenticated():
            raise LogicError('not authenticate')

    def post(self):
        self.check_input('username', 'password')
        user =  auth.authenticate(requests=self.request, username = self.input['username'], password = self.input['password'])
        if not user:
           raise LogicError('username or password not right')
        auth.login(self.request, user)
class Logout(APIView):

    def post(self):
        auth.logout(self.request)
        if self.request.user.is_authenticated():
            raise LogicError('authenticate')

class ActivityList(APIView):
    def get(self):
        if not self.request.user.is_authenticated():
            raise LogicError('not authenticate')
        activities = Activity.objects.filter(status__gte = 0)
        if not activities:
            raise LogicError("activityList is empty")
        ret_activities = []
        for activity in activities:
            ret_activities.append({
                "id": activity.id,
                "name" : activity.name,
                "description" : activity.description,
                "startTime" : activity.start_time.timestamp(),
                "endTime" : activity.end_time.timestamp(),
                "place" : activity.place,
                "bookStart" : activity.book_start.timestamp(),
                "bookEnd" : activity.book_end.timestamp(),
                "currentTime" : timezone.now().timestamp(),
                "status" : activity.status,
            })
        return ret_activities

class ActivityDelete(APIView):
    def post(self):
        self.check_input('id')
        try:
            activity = Activity.objects.get(id = self.input['id'])
        except Activity.DoesNotExist:
            raise LogicError('activity not exist')
        activity.status = Activity.STATUS_DELETED
        activity.save()

class ActivityCreate(APIView):
    def post(self):
        if not self.request.user.is_authenticated():
            raise LogicError('not authenticate')
        self.check_input('name','key','place','description',
                         'picUrl','startTime','endTime','bookStart',
                         'bookEnd', 'totalTickets','status')
        activity = Activity.objects.create(
            name = self.input['name'],
            key = self.input['key'],
            description = self.input['description'],
            start_time = self.input['startTime'],
            end_time = self.input['endTime'],
            place = self.input['place'],
            book_start = self.input['bookStart'],
            book_end = self.input['bookEnd'],
            total_tickets = self.input['totalTickets'],
            status = self.input['status'],
            pic_url = self.input['picUrl'],
            remain_tickets = self.input['totalTickets']
        )
        if not activity:
            raise LogicError('activity not successfully created')
        return activity.id

class ImageUpload(APIView):
    def post(self):
        if not self.request.user.is_authenticated():
            raise LogicError('not authenticate')
        self.check_input('image')
        phototime = str(uuid.uuid1()) + self.input['image'][0].name
        dest = 'media/' + phototime
        try:
            destination = open('static/'+dest, 'wb+')
            for chunk in self.input['image'][0].chunks():
                destination.write(chunk)
            destination.close()
            return WeChatTicket.settings.get_url(dest)
        except:
            raise LogicError('files not open right')
        #return 'http://118.89.241.172/' + dest
class ActivityDetail(APIView):
    def get(self):
        if not self.request.user.is_authenticated():
            raise LogicError('not authenticate')
        self.check_input('id')
        try:
            activity = Activity.objects.get(id = self.input['id'])
        except Activity.DoesNotExist:
            raise LogicError('activity not exist')
        ticket = Ticket.objects.filter(activity = activity, status = Ticket.STATUS_USED)
        return {
            "name" : activity.name,
            "key" : activity.key,
            "description" : activity.description,
            "startTime" : activity.start_time.timestamp(),
            "endTime" : activity.end_time.timestamp(),
            "place" : activity.place,
            "bookStart" : activity.book_start.timestamp(),
            "bookEnd" : activity.book_end.timestamp(),
            "totalTickets" : activity.total_tickets,
            "picUrl" : activity.pic_url,
            "bookedTickets" : activity.total_tickets - activity.remain_tickets,
            "usedTickets" : len(ticket),
            "currentTime" : timezone.now().timestamp(),
            "status" : activity.status
        }

    def post(self):
        if not self.request.user.is_authenticated():
            raise LogicError('not authenticate')
        self.check_input('id', 'name', 'place', 'description', 'picUrl', 'startTime', 'endTime', 'bookStart', 'bookEnd', 'totalTickets', 'status')
        try:
            activity = Activity.objects.get(id = self.input['id'])
        except Activity.DoesNotExist:
            raise LogicError('this activity not exist')
        activity.name = self.input['name']
        activity.place = self.input['place']
        activity.description = self.input['description']
        activity.pic_url = self.input['picUrl']
        activity.start_time = self.input['startTime']
        activity.end_time = self.input['endTime']
        activity.book_start = self.input['bookStart']
        activity.book_end = self.input['bookEnd']
        activity.total_tickets = self.input['totalTickets']
        activity.status = self.input['status']
        activity.save()

class  ActivityMenu(APIView):
    def get(self):
        if not self.request.user.is_authenticated():
            raise LogicError('not authenticate')
        activities = Activity.objects.filter(status = Activity.STATUS_PUBLISHED)
        if not activities:
            raise LogicError("activities is empty")
        ret_activities = []
        menu_list = CustomWeChatView.lib.get_wechat_menu()
        index = 1
        exist_flag = 0
        if not menu_list[1]['sub_button']:
            for activity in activities:
                ret_activities.append({
                    "id": activity.id,
                    "name": activity.name,
                    "menuIndex": 0
                })
            return ret_activities
        for activity in activities:
            exist_flag = 0
            for sub_button in  menu_list[1]['sub_button']:
                if sub_button['name'] == activity.name:
                    ret_activities.append({
                        "id" : activity.id,
                        "name" : activity.name,
                        "menuIndex" : index
                    })
                    index += 1
                    exist_flag = 1
            if exist_flag == 0:
                ret_activities.append({
                    "id": activity.id,
                    "name": activity.name,
                    "menuIndex": 0
                })
        return ret_activities

    def post(self):
        if not self.request.user.is_authenticated():
            raise LogicError('not authenticate')
        ret_activities = []
        if not self.input:
            CustomWeChatView.update_menu(ret_activities)
        for _id in self.input:
            try:
                activity = Activity.objects.get(id = _id)
            except Activity.DoesNotExist:
                raise LogicError('activity not exist')
            ret_activities.append(activity)

        CustomWeChatView.update_menu(ret_activities)

class ActivityCheckin(APIView):
    def post(self):
        if not self.request.user.is_authenticated():
            raise LogicError('not authenticate')
        try:
            self.check_input('actId', 'ticket')
            try:
                ticket = Ticket.objects.get(unique_id=self.input['ticket'])
            except Ticket.DoesNotExist:
                raise LogicError('ticket not exist')
            if str(ticket.activity.id) == str(self.input['actId']):
                if ticket.status == Ticket.STATUS_VALID:
                    ticket.status = Ticket.STATUS_USED
                    ticket.save()
                    return {
                        "ticket" : self.input['ticket'],
                        "studentId" : ticket.student_id
                    }
            raise LogicError('ticket not match')
        except InputError:
            self.check_input('actId', 'studentId')
            tickets2 = Ticket.objects.filter(student_id= self.input['studentId'])
            if not tickets2:
                raise LogicError('ticket no exist')
            for tic in tickets2:
                if str(tic.activity.id) == str(self.input['actId']):
                    if tic.status == Ticket.STATUS_VALID:
                        tic.status = Ticket.STATUS_USED
                        tic.save()
                        return {
                            "ticket" : tic.unique_id,
                            "studentId" : self.input['studentId']
                        }
            raise LogicError('ticket not exist')


