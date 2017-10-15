# -*- coding: utf-8 -*-
#
from wechat.wrapper import WeChatHandler
import re
from codex.baseerror import *
from wechat.models import Activity,User,Ticket
from WeChatTicket import settings
import uuid
from django.utils import timezone
from django.db import transaction
__author__ = "Epsirom"


class ErrorHandler(WeChatHandler):

    def check(self):
        return True

    def handle(self):
        return self.reply_text('对不起，服务器现在有点忙，暂时不能给您答复 T T')


class DefaultHandler(WeChatHandler):

    def check(self):
        return True

    def handle(self):
        return self.reply_text('对不起，没有找到您需要的信息:(')


class HelpOrSubscribeHandler(WeChatHandler):

    def check(self):
        return self.is_text('帮助', 'help') or self.is_event('scan', 'subscribe') or \
               self.is_event_click(self.view.event_keys['help'])

    def handle(self):
        return self.reply_single_news({
            'Title': self.get_message('help_title'),
            'Description': self.get_message('help_description'),
            'Url': self.url_help(),
        })


class UnbindOrUnsubscribeHandler(WeChatHandler):

    def check(self):
        return self.is_text('解绑') or self.is_event('unsubscribe')

    def handle(self):
        self.user.student_id = None
        self.user.save()
        return self.reply_text(self.get_message('unbind_account'))


class BindAccountHandler(WeChatHandler):

    def check(self):
        return self.is_text('绑定') or self.is_event_click(self.view.event_keys['account_bind'])

    def handle(self):
        return self.reply_text(self.get_message('bind_account'))


class BookEmptyHandler(WeChatHandler):

    def check(self):
        return self.is_event_click(self.view.event_keys['book_empty'])

    def handle(self):
        return self.reply_text(self.get_message('book_empty'))

class RegularExpHandler(WeChatHandler):

    def check(self):
        return self.is_msg_type('text') and re.match(r'^[\s0123456789+*/()-]*$', self.input['Content'])

    def handle(self):
        try:
            content = self.input['Content']
            result = eval(content)
        except:
            return self.reply_text(str('表达式有误，请重新输入!'))
        else:
            return self.reply_text(result)

class ActivityBookingHandler(WeChatHandler):
    myid = 0
    def check(self):
        activities = Activity.objects.filter(status = Activity.STATUS_PUBLISHED)
        if not activities:
            raise LogicError('no activity')
        for act in activities:
            if self.is_event_click(self.view.event_keys['book_header'] + str(act.id)):
                self.myid = act.id
                return True
        self.myid = 0
        return False

    def handle(cls):
        if not cls.user.student_id:
            return cls.reply_text("请先绑定")
        with transaction.atomic():
            try:
                act = Activity.objects.select_for_update().get(id = cls.myid)
            except Activity.DoesNotExist:
                raise LogicError('act not exist')
            try:
                user = User.objects.get(open_id=cls.input['FromUserName'])
            except User.DoesNotExist:
                raise LogicError('user not exist')
            if timezone.now() < act.book_start:
                return cls.reply_single_news({
                    'Title': act.name,
                    "PicUrl": act.pic_url,
                    'Description':act.description,
                     'Url':  settings.get_url('u/activity', {'id' : cls.myid})
                })

            if timezone.now() >= act.book_start and timezone.now() < act.book_end:
                if act.remain_tickets > 0:
                    tickets = Ticket.objects.filter(student_id=user.student_id)
                    if tickets:
                        for ticket in tickets:
                            if ticket.activity.id == act.id and (ticket.status == Ticket.STATUS_VALID or ticket.status == Ticket.STATUS_USED):
                                return cls.reply_text(str('您已拥有') + act.key + str('活动的票！'))
                    act.remain_tickets -= 1
                    act.save()
                    _ticket = Ticket.objects.create(
                        student_id = user.student_id,
                        unique_id = str(uuid.uuid1()),
                        activity = act,
                        status = Ticket.STATUS_VALID
                    )
                    return cls.reply_text(str('您已成功抢到') + act.key + str('活动的票！'))
            if timezone.now() >= act.book_end:
                tickets = Ticket.objects.filter(student_id=user.student_id)
                if not tickets:
                    return cls.reply_text(str('抢票已结束，您还没有') + act.key + str('活动的票！'))
                for ticket in tickets:
                    if ticket.activity.id == act.id:
                        if ticket.status == Ticket.STATUS_VALID:
                            return cls.reply_single_news({
                                'Title': act.name,
                                'PicUrl': act.pic_url,
                                'Description': act.description,
                                'Url': settings.get_url('u/ticket',
                                                        {'openid': cls.input['FromUserName'], 'ticket': ticket.unique_id})
                            })
                return cls.reply_text(str('抢票已结束，您还没有') + act.key + str('活动的票！'))

class TicketsHandler(WeChatHandler):
    def check(self):
        return self.is_text_command("抢票","取票","退票")

    def handle(cls):
        if not cls.user.student_id:
            return cls.reply_text("请先绑定")
        act_key = (cls.input['Content'].split() or [None])[1]
        with transaction.atomic():
            try:
                act = Activity.objects.select_for_update().get(key=act_key)
            except Activity.DoesNotExist:
                raise LogicError('activity is not existed')
            try:
                user = User.objects.get(open_id = cls.input['FromUserName'])
            except User.DoesNotExist:
                raise LogicError('user is not exist')
            if cls.is_text_command("抢票"):
                if act.remain_tickets > 0 and timezone.now() >= act.book_start and timezone.now() < act.book_end:
                    tickets = Ticket.objects.filter(student_id=user.student_id)
                    if tickets:
                        for ticket in tickets:
                            if ticket.activity.id == act.id and (ticket.status == Ticket.STATUS_VALID or ticket.status == Ticket.STATUS_USED):
                                return cls.reply_text(str('您已拥有') + act_key + str('活动的票！'))
                    act.remain_tickets -= 1
                    act.save()
                    _ticket = Ticket.objects.create(
                        student_id = user.student_id,
                        unique_id = str(uuid.uuid1()),
                        activity = act,
                        status = Ticket.STATUS_VALID
                    )
                    return cls.reply_text(str('您已成功抢到') + act_key + str('活动的票！'))
                else:
                    return cls.reply_text(str('您未抢到') + act_key + str('活动的票！'))

            if cls.is_text_command("退票"):
                tickets = Ticket.objects.filter(student_id=user.student_id)
                if not tickets:
                    return cls.reply_text(str('您还没有') + act_key + str('活动的票！'))
                for ticket in tickets:
                    if ticket.activity.id == act.id:
                        if ticket.status == Ticket.STATUS_VALID:
                            ticket.status = Ticket.STATUS_CANCELLED
                            ticket.save()
                            act.remain_tickets += 1
                            act.save()
                            return cls.reply_text(str('您已成功退掉') + act_key + str('活动的票！'))
                return cls.reply_text(str('您还没有') + act_key + str('活动的票！'))

            if cls.is_text_command("取票"):
                tickets = Ticket.objects.filter(student_id=user.student_id)
                if not tickets:
                    return cls.reply_text(str('您还没有') + act_key + str('活动的票！'))
                for ticket in tickets:
                    if ticket.activity.id == act.id:
                        if ticket.status == Ticket.STATUS_VALID:
                            return cls.reply_single_news({
                                 'Title': act.name,
                                 'PicUrl': act.pic_url,
                                 'Description':act.description,
                                 'Url':  settings.get_url('u/ticket', {'openid' : cls.input['FromUserName'], 'ticket': ticket.unique_id})
                                })
                return cls.reply_text(str('您还没有') + act_key + str('活动的票！'))

class BookWhatHandler(WeChatHandler):
    def check(self):
        return self.is_event_click(self.view.event_keys['book_what'])

    def handle(self):
        if not self.user.student_id:
            return self.reply_text("请先绑定")
        activities = Activity.objects.filter(book_end__gte=timezone.now())
        if not activities:
            return self.reply_text('目前没有可以抢票的活动')
        ret_message = []
        for activity in activities:
            if activity.status == Activity.STATUS_PUBLISHED:
                 ret_message.append({
                     'Title': activity.name,
                     "PicUrl": activity.pic_url,
                     'Description': activity.description,
                     'Url': settings.get_url('u/activity', {'id': activity.id})
                 })
        if not ret_message:
            return self.reply_text('目前没有可以抢票的活动')
        return self.reply_news(ret_message)

class GetTicketHandler(WeChatHandler):
    def check(self):
        return self.is_event_click(self.view.event_keys['get_ticket'])

    def handle(self):
        if not self.user.student_id:
            return self.reply_text("请先绑定")
        try:
            user = User.objects.get(open_id=self.input['FromUserName'])
        except User.DoesNotExist:
            raise LogicError('user not exist')
        tickets = Ticket.objects.filter(student_id=user.student_id)
        if not tickets:
            return self.reply_text('目前没有票')
        ret_tickets = []
        for ticket in tickets:
            if ticket.status == Ticket.STATUS_VALID:
                ret_tickets.append({
                    'Title': ticket.activity.name,
                    'PicUrl': ticket.activity.pic_url,
                    'Description': ticket.activity.description,
                    'Url': settings.get_url('u/ticket',
                                            {'openid': self.input['FromUserName'], 'ticket': ticket.unique_id})
                })
        if not ret_tickets:
            return self.reply_text('目前没有票')
        return self.reply_news(ret_tickets)

