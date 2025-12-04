from loguru import logger

from flask import redirect, url_for
from flask_admin.contrib.mongoengine import ModelView
from flask_admin import form
from flask_login import current_user
from flask_wtf.file import FileField, MultipleFileField
from wtforms.fields.list import FieldList
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm
import os
from apps.models.article_model import get_next_id, 分类db, 模板db, 状态db, 文章db
from setting import UPLOAD_FOLDER_ROOT
from tool.mpuscript import upload_file


class AuthView(ModelView):
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


base_select = [(None, "")]


# 后台文章添加id自增视图
class ArticleView(AuthView):
    form_extra_fields = {
        'image_load': form.ImageUploadField('Upload Images', base_path=UPLOAD_FOLDER_ROOT, )
    }
    column_list = ('标题', '发布时间', "lang", '状态_id', "分类_id", '模板路径_id')
    column_editable_list = ['状态_id', "分类_id", '模板路径_id']
    form_columns = (
        '标题', 'lang', "article_url", '标签', '正文内容', '简介', '分类_id', '发布时间', '状态_id', 'ids',
        '模板路径_id', "image_url",
        "iframe", 'image_load')
    # 自定义标签名称
    form_args = {
        '分类_id': {'label': '分类'},
        '状态_id': {'label': '状态'},
        '模板路径_id': {'label': '模板路径'},
        'lang': {'label': '语言'},
        'article_url': {'label': '自定义链接'}
    }

    form_excluded_columns = ['状态', 'ids']

    # ++++++++++ck使用>>>>>>>>>>
    # form_overrides = {
    #     '正文内容': CKEditorField,
    #     'iframe': CKEditorField
    # }
    create_template = 'edit.html'
    edit_template = 'edit.html'

    # ++++++++++ck使用<<<<<<<<<<

    def on_model_change(self, form, model, is_created):

        # ==============================
        if is_created:
            # 当创建新记录时，自动设置 ID
            model.ids = int(get_next_id('article_id'))
        # ====================

        # 判断是否为列表页面
        image_load = getattr(form, 'image_load', None)
        if image_load:
            file = form.image_load.data
            if file:
                logger.info(file)
                new_url = upload_file(file)
                model.image_url = new_url
            # 保存文件到指定目录

            # upload_folder = 'uploads'
            # if not os.path.exists(upload_folder):
            #     os.makedirs(upload_folder)
            # file_path = os.path.join(upload_folder, file.filename)
            # file.save(file_path)  # 保存文件
            # model.image_url = file_path  # 将文件路径保存到模型中

            # 处理引用字段

            # model.发布时间 = form.发布时间.data
            # model.标题 = form.标题.data
            # model.正文内容 = form.正文内容.data
            # model.简介 = form.简介.data

        分类id = form.分类_id
        if 分类id and 分类id.data:
            分类obj = 分类db.objects.get(id=form.分类_id.data.id)
            # model.分类_id = 分类obj
            model.分类 = 分类obj.分类名称
        模板路径_id = form.模板路径_id
        if 模板路径_id and 模板路径_id.data:
            模板obj = 模板db.objects.get(id=form.模板路径_id.data.id)
            # model.模板路径_id = 模板obj
            model.模板名称 = 模板obj.模板名称

        状态_id = form.状态_id
        if 状态_id and 状态_id.data:
            状态obj = 状态db.objects.get(id=form.状态_id.data.id)
            # model.状态_id = 状态obj
            model.状态 = 状态obj.状态名称

        return super(ArticleView, self).on_model_change(form, model, is_created)


# 标签动态跟随
# 分类动态跟随
# 状态动态跟随


class CategoryView(AuthView):
    # 如何分类名称改变 对应的所有文章的名称也改变
    def on_model_change(self, form, model, is_created):
        文章db.objects(分类_id=model.id).update(set__分类=model.分类名称)
        return super().on_model_change(form, model, is_created)

    # 如果分类删除，对应的文章分类也删除
    def on_model_delete(self, model):
        文章db.objects(分类_id=model.id).update(set__分类=None, set__分类_id=None)  # 或者其他处理逻辑
        return super().on_model_delete(model)


# class TagView(AuthView):
#
#     def on_model_change(self, form, model, is_created):
#         文章db.objects(标签_id=model.id).update(set__分类=model.分类名称)
#         return super().on_model_change(form, model, is_created)
#
#     # 如果分类删除，对应的文章分类也删除
#     def on_model_delete(self, model):
#         文章db.objects(分类_id=model.id).update(set__分类=None, set__分类_id=None)  # 或者其他处理逻辑
#         return super().on_model_delete(model)

class PictureForm(FlaskForm):
    uploaded_image = FileField('Upload Image', validators=[DataRequired()])
    picture = FieldList(StringField('Picture Link'), min_entries=1)


class PictureModelView(AuthView):
    form_extra_fields = {
        'images': MultipleFileField('Upload Images')
    }

    def on_model_change(self, form, model, is_created):

        # 处理文件上传(可以自己添加多个图片)
        if form.images.data:
            image_chars = []
            for uploaded_file in form.images.data:
                # 这里可以添加你的逻辑来处理图片并返回字符
                image_char = f"processed_{uploaded_file.filename}"  # 示例字符表示
                image_chars.append(image_char)
            k = list(model.picture)
            k.extend(image_chars)

            model.picture = k  # 将处理后的图片字符存储到模型中
