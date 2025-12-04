import datetime

import pytz
from flask import redirect, url_for
from flask_mongoengine import MongoEngine
from flask_admin.contrib.mongoengine import ModelView
from flask_mongoengine import Document
from flask_login import UserMixin, current_user

"""admin 登录判断"""


class AdminModelView(ModelView):

    def is_accessible(self):
        return current_user.is_authenticated and 'admin_user' in current_user.roles

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login'))

    def get_query(self):
        if 'admin_user' in current_user.roles:
            return super().get_query()
        return super().get_query().filter(id=current_user.id)

    def get_count_query(self):
        if 'admin_user' in current_user.roles:
            return super().get_count_query()
        return super().get_count_query().filter(id=current_user.id)
