from codex.baseerror import *
from codex.baseview import APIView

from wechat.models import User,Activity,Ticket
from urllib import parse, request
from django.utils import timezone
class UserBind(APIView):

    def validate_user(self):

        #input: self.input['student_id'] and self.input['password']
        #raise: ValidateError when validating failed

        try:
            username = self.input['student_id']
            password = self.input['password']
        except:
            raise ValidateError('msg=1')
        posturl = 'https://learn.tsinghua.edu.cn/MultiLanguage/lesson/teacher/loginteacher.jsp'
        login = parse.urlencode({'userid':username, 'userpass':password}).encode('utf-8')
        req = request.Request(posturl,login)
        act = str(request.urlopen(req).read())
        if act.find("loginteacher_action.jsp") < 0:
            raise ValidateError('msg=')

    def get(self):
        self.check_input('openid')
        return User.get_by_openid(self.input['openid']).student_id

    def post(self):
        self.check_input('openid', 'student_id', 'password')
        user = User.get_by_openid(self.input['openid'])
        self.validate_user()
        user.student_id = self.input['student_id']
        user.save()

class ActivityDetail(APIView):

    def get(self):
        self.check_input('id')
        try:
             activity = Activity.objects.get(id = self.input['id'])
        except Activity.DoesNotExist:
            raise LogicError('activity not exist')
        if activity.status == 1:
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
                "remainTickets" : activity.remain_tickets,
                "currentTime" : timezone.now().timestamp()
            }
        else:
            raise LogicError('status not right')

class TicketDetail(APIView):
    def get(self):
        self.check_input('openid', 'ticket')
        try:
            ticket = Ticket.objects.get(unique_id = self.input['ticket'])
        except Ticket.DoesNotExist:
            raise LogicError('this ticket not exist')
        return {
            "activityName" : ticket.activity.name,
            "place" : ticket.activity.place,
            "activityKey" : ticket.activity.key,
            "uniqueId" : ticket.unique_id,
            "startTime" : ticket.activity.start_time.timestamp(),
            "endTime" : ticket.activity.end_time.timestamp(),
            "currentTime" : timezone.now().timestamp(),
            "status" : ticket.status
        }

