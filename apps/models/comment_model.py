import uuid
from datetime import datetime
import pytz
from mongoengine import (Document, EmbeddedDocument, StringField, IntField,
                         ListField, DateTimeField, BooleanField, FloatField,
                         EmbeddedDocumentField, DictField)


class 回复(EmbeddedDocument):
    """回复嵌入文档"""
    reply_id = StringField(required=True, default=lambda: str(uuid.uuid4()))
    username = StringField(required=True, max_length=50)
    content = StringField(required=True, max_length=2000)
    created_at = DateTimeField(default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    likes = IntField(default=0)
    user_ip = StringField()  # 回复者IP地址
    user_agent = StringField()  # 浏览器信息
    parent_reply_id = StringField()  # 被回复的回复ID，如果为空则是直接回复主评论
    reply_to_username = StringField(max_length=50)  # 被回复的用户名，用于显示@提及


class 评论db(Document):
    """评论主表"""
    meta = {
        'collection': 'comments',
        'indexes': [
            'article_id',
            'article_url',
            'status',
            'created_at',
            'username'
        ]
    }
    
    # 基本信息
    comment_id = StringField(required=True, unique=True, default=lambda: str(uuid.uuid4()))
    article_id = StringField(required=True)  # 关联的文章ID
    article_url = StringField(required=True)  # 文章URL
    
    # 用户信息
    username = StringField(required=True, max_length=50)
    email = StringField(max_length=100)  # 可选邮箱
    user_ip = StringField()  # 用户IP地址
    user_agent = StringField()  # 浏览器信息
    
    # 评论内容
    content = StringField(required=True, max_length=2000)
    rating = IntField(min_value=1, max_value=5, required=True)
    
    # 状态管理
    status = StringField(choices=['pending', 'approved', 'rejected'], default='pending')
    lang = StringField()  # 语言标识，可选字段，用于记录但不影响查询
    
    # 互动数据
    likes = IntField(default=0)
    replies = ListField(EmbeddedDocumentField(回复))  # 回复列表
    
    # 时间戳
    created_at = DateTimeField(default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    updated_at = DateTimeField(default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))
    
    # 审核信息
    moderated_by = StringField()  # 审核员
    moderated_at = DateTimeField()

    def __str__(self):
        return f'{self.username} - {self.content[:50]}'

    def save(self, *args, **kwargs):
        """保存时更新修改时间"""
        self.updated_at = datetime.now(pytz.timezone('Asia/Shanghai'))
        super(评论db, self).save(*args, **kwargs)


class 评论统计db(Document):
    """评论统计表"""
    meta = {
        'collection': 'comment_stats',
        'indexes': ['article_id', 'article_url']
    }
    
    article_id = StringField(required=True, unique=True)
    article_url = StringField(required=True)
    total_comments = IntField(default=0)
    average_rating = FloatField(default=0.0)
    rating_distribution = DictField(default={
        '1': 0, '2': 0, '3': 0, '4': 0, '5': 0
    })  # 评分分布
    last_updated = DateTimeField(default=lambda: datetime.now(pytz.timezone('Asia/Shanghai')))

    def __str__(self):
        return f'{self.article_url} - {self.total_comments} comments' 