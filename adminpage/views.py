from codex.baseerror import *
from codex.baseview import APIView
from django.contrib import auth
from django.contrib.auth.models import User
from django.utils import timezone

from wechat.models import User,Activity
from wechat.views import CustomWeChatView
import os
import requests

class Login(APIView):

    def get(self):
        if not self.request.user.is_authenticated():
            raise ValidateError('not authenticate')

    def post(self):
        self.check_input('username', 'password')
        user =  auth.authenticate(requests=self.request, username = self.input['username'], password = self.input['password'])
        if not user:
           raise ValidateError('username or password not right')
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
        activity = Activity.objects.get(id = self.input['id'])
        if not activity:
            raise LogicError('activity not exist')
        activity.status = -1
        activity.save()

class ActivityCreate(APIView):
    def post(self):
        if not self.request.user.is_authenticated():
            raise LogicError('not authenticate')
        self.check_input('name','key','place','description','picUrl','startTime','endTime','bookStart', 'bookEnd', 'totalTickets','status')
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
        phototime = self.request.user.username + self.input['image'][0].name
        dest = 'media/' + phototime
        try:
            destination = open('static/'+dest, 'wb+')
        except:
            raise LogicError('files not open right')
        for chunk in self.input['image'][0].chunks():
            destination.write(chunk)
        destination.close()
        return 'http://118.89.241.172/' + dest

class ActivityDetail(APIView):
    def get(self):
        if not self.request.user.is_authenticated():
            raise LogicError('not authenticate')
        self.check_input('id')
        activity = Activity.objects.get(id = self.input['id'])
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
            "usedTickets" : activity.total_tickets - activity.remain_tickets,
            "currentTime" : timezone.now().timestamp(),
            "status" : activity.status
        }

    def post(self):
        self.check_input('id', 'name', 'place', 'description', 'picUrl', 'startTime', 'endTime', 'bookStart', 'bookEnd', 'totalTickets', 'status')
        activity = Activity.objects.get(id = self.input['id'])
        if not activity:
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
        activities = Activity.objects.filter(status = 1)
        ret_activities = []
        index = 1
        for activity in activities:
            ret_activities.append({
                "id" : activity.id,
                "name" : activity.name,
                "menuindex" : index
            })
            index += 1
        return ret_activities

    def post(self):
        if not self.request.user.is_authenticated():
            raise LogicError('not authenticate')
        ret_activities = []
        for _id in self.input:
            ret_activities.append(Activity.objects.get(id = _id))
        CustomWeChatView.update_menu(ret_activities)

class ActivityCheckin(APIView):
    def post(self):
        if not self.request.user.is_authenticated():
            raise LogicError('not authenticate')
       # self.check_input('actId', 'ticket', 'studentId')


