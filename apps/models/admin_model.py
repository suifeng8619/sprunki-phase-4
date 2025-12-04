import os

from flask import redirect, url_for, current_app
from flask_admin import AdminIndexView
from flask_login import UserMixin, current_user

from get_app import db

"""管理后台的用户表"""


class adminUser(UserMixin, db.Document):
    meta = {'collection': 'users'}
    username = db.StringField(max_length=150, unique=True, required=True)
    password = db.StringField(max_length=150, required=True)
    roles = db.ListField(db.StringField(), default=[])


class MyAdminIndexView(AdminIndexView):
    # 注入自定义深色主题CSS
    extra_css = ['/css/admin-theme.css']

    def is_accessible(self):

        print(os.environ['TESTING'])
        if os.environ['TESTING'] == '1':
            return True
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        # Redirect to the login view if the user is not authenticated
        return redirect(url_for('admin_url.admin_login'))

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return self.inaccessible_callback(name, **kwargs)
