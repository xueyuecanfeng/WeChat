from codex.baseerror import *
from codex.baseview import APIView

from wechat.models import User

import requests

class UserBind(APIView):

    def validate_user(self):

        #input: self.input['student_id'] and self.input['password']
        #raise: ValidateError when validating failed
        posturl= 'https://id.tsinghua.edu.cn/security_check'

        values = {"username": self.input['student_id'], "password": self.input['password']}

        res = requests.post(posturl, values)
        if res.url != "https://id.tsinghua.edu.cn/f/account/settings":
            raise ValidateError(res.url)

    def get(self):
        self.check_input('openid')
        return User.get_by_openid(self.input['openid']).student_id

    def post(self):
        self.check_input('openid', 'student_id', 'password')
        user = User.get_by_openid(self.input['openid'])
        self.validate_user()
        user.student_id = self.input['student_id']
        user.save()
