import base64
import re
from datetime import datetime
import pytz
from flask_admin.contrib.mongoengine import ModelView

from mongoengine import (Document, StringField, IntField,
                         ListField, ReferenceField, DateTimeField,
                         FileField, BooleanField, DictField)

import os

from wtforms.widgets.core import TextArea

from tool.mpuscript import upload_files


class Counter(Document):
    name = StringField(required=True, unique=True)
    sequence_value = IntField(default=0)


def get_next_id(name):
    counter = Counter.objects(name=name).first()
    if not counter:
        counter = Counter(name=name, sequence_value=0).save()
    counter.update(inc__sequence_value=1)
    return counter.sequence_value


# 普通用户表
class User(Document):
    user_id = StringField(required=True, unique=True,
                          default=str(get_next_id("user")))  # 数据库生成的用户id
    google_id = StringField()  # 使用 Google ID 作为主键
    email = StringField(max_length=500)  # Google 邮箱
    name = StringField(max_length=500)  # 谷歌名称
    picture = StringField(max_length=500, required=True, unique=True)  # 头像
    score = IntField(nullable=True)  # 积分
    pictures = ListField(ReferenceField('Picture'))

    def __str__(self):
        return f'{self.name}'


# 图片表
class Picture(Document):
    id = IntField(primary_key=True, default=get_next_id("pictures"))
    picture = ListField(StringField())
    user = ReferenceField(User)  # 外键关联用户，必需


class 标签db(Document):
    标签名称 = StringField(max_length=500, required=True, unique=True)
    标签介绍 = StringField(max_length=5000, required=True, unique=True)

    def __str__(self):
        return f'{self.标签名称}'


class 分类db(Document):
    分类名称 = StringField(max_length=500, required=True, unique=True)
    分类介绍 = StringField(max_length=5000, required=True, unique=True)

    def __str__(self):
        return f'{self.分类名称}'


class 模板db(Document):
    模板名称 = StringField(max_length=500, required=True, unique=True)
    模板介绍 = StringField(max_length=5000, required=True, unique=True)
    模板路径 = StringField(max_length=500, required=True, unique=True)

    def __str__(self):
        return f'{self.模板名称}'


class 状态db(Document):
    状态名称 = StringField(max_length=500, required=True, unique=True)
    状态介绍 = StringField(max_length=5000, required=True, unique=True)

    def __str__(self):
        return f'{self.状态名称}'


class 文章db(Document):
    标题 = StringField(max_length=500, required=True)
    标签 = ListField(StringField())
    正文内容 = StringField()
    简介 = StringField(max_length=2000)
    分类_id = ReferenceField(分类db)
    分类 = StringField(max_length=500)
    发布时间 = DateTimeField(default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    模板路径_id = ReferenceField(模板db)
    模板路径 = StringField(max_length=500)
    状态_id = ReferenceField(状态db)
    iframe = StringField()
    状态 = StringField(max_length=500)
    ids = IntField(unique=True)
    image_url = StringField(max_length=500)
    image_title = StringField(max_length=500)
    article_url = StringField(max_length=500, required=True)  # 文章自定义url
    lang = StringField(max_length=500, required=True)  # 文章按语言分类
    is_update = BooleanField(default=False)

    game_auth = StringField(max_length=500)  # 游戏作者
    game_date_published = DateTimeField(default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))  # 游戏发布时间
    game_name = StringField(max_length=500)
    game_character = ListField(DictField())  # 游戏角色
    game_aggregateRating = DictField(max_length=500)
    meta = {
        'indexes': [
            {'fields': ['article_url', 'lang'], 'unique': True}  # 设置联合唯一索引
        ]
    }

    def __str__(self):
        return f'{self.标题}'


class Comment(Document):
    meta = {'collection': 'comments'}  # 指定 MongoDB 集合名

    name = StringField(required=True, max_length=100)
    email = StringField(required=True, max_length=100)
    content = StringField(required=True, max_length=2000)
    created_at = DateTimeField(default=datetime.utcnow)
    upvotes = IntField(default=0)
    downvotes = IntField(default=0)
    parent_id = ReferenceField('self', null=True)  # 自引用外键
    replies = ListField(ReferenceField('self'))  # 回复列表
    is_approved = BooleanField(default=False)
    user_id = StringField(required=True, max_length=50)


class WebSetting(Document):
    title = StringField(max_length=500, required=True, unique=True)
    description = StringField(max_length=5000, required=True, unique=True)
    content = StringField(max_length=5000, required=True, unique=True)
    lang = StringField(max_length=10)
    type = StringField(max_length=50)  # 首页或者其他


if __name__ == '__main__':
    print(User.objects.count())
    # 数据库的操作可以直接是用model
    pass
