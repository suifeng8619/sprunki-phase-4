import os
from datetime import datetime
from urllib.parse import urljoin

from flask import request, redirect, url_for, g, session
from flask_admin import Admin, BaseView
from flask_babel import Babel, _
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash
from loguru import logger
from apps.models.admin_model import MyAdminIndexView, adminUser
from apps.views.web_url import web_bp
from get_app import app, get_locale, no_en_get_locale
from apps.views.admin_urls import admin_bp
from apps.views.base_urls import base_bp, warmup_cache
from apps.models.article_model import 分类db, 模板db, 标签db, 状态db, 文章db, User, Picture

from setting import LANGUAGES
from apps.models.article_view import ArticleView, CategoryView, AuthView, PictureModelView
# 导入评论系统集成模块
from apps.comment_integration import init_comment_system

def join_multiple_paths(base_url, *paths):
    for path in paths:
        path = path.lstrip('/')  # 左边的/去掉
        path = path.rstrip('/')  # 右边的/去掉

        base_url = base_url.rstrip('/') + '/'  # 右边一定有/
        base_url = urljoin(base_url, path)

    return base_url


# 多语言根据params参数来生成

# 初始化app函数
ckeditor = CKEditor(app)

# 注册蓝图

app.register_blueprint(admin_bp)
app.register_blueprint(base_bp)
app.register_blueprint(web_bp, url_prefix='/speech')

# 注册缓存监控路由
from cache_routes import cache_bp
app.register_blueprint(cache_bp)

# 导入智能页面缓存
from intelligent_cache import intelligent_cache


@app.route('/test')
def test_route():
    return "✅ 应用正常运行！这是一个测试页面。"

@app.before_request
def before_request():
    # 记录请求的时间和 URL
    # logger.info(f"请求前{request.url}")
    
    # 尝试获取智能页面缓存
    if request.method == 'GET' and 'text/html' in request.headers.get('Accept', ''):
        cached_response = intelligent_cache.get_cached_response()
        if cached_response:
            return cached_response





@app.context_processor
def inject_locale():
    path = request.path
    # 剔除第一个路径部分
    if get_locale() == 'en':
        no_lang_path = path
    else:
        no_lang_path = '/'.join(path.split('/')[2:])

    return dict(get_locale=get_locale, no_en_lang=no_en_get_locale, languages=LANGUAGES, no_lang_path=no_lang_path,
                urljoin=join_multiple_paths)


def create_super_admin():
    admin_username = os.getenv('ADMIN_USERNAME', 'superadmin')
    admin_password = os.getenv('ADMIN_PASSWORD', 'changeme123')  # 生产环境必须通过环境变量设置
    if not adminUser.objects(username=admin_username).first():
        super_admin = adminUser(username=admin_username, password=generate_password_hash(admin_password),
                                roles=['admin_user'])
        super_admin.save()
        print(f"Super admin '{admin_username}' created")


@app.after_request
def set_url(response):

    # 高级性能优化：静态资源缓存策略
    static_extensions = ('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.woff', '.woff2', '.ttf', '.svg', '.webp')
    if any(request.path.endswith(ext) for ext in static_extensions):
        if 'v=' in request.url or 'version=' in request.url:
            # 带版本号的资源，永久缓存
            response.cache_control.max_age = 31536000  # 1年
            response.cache_control.public = True
            response.cache_control.immutable = True  # 不可变资源
        else:
            # 普通静态资源，短期缓存
            response.cache_control.max_age = 86400  # 1天
            response.cache_control.public = True
        
        # 设置压缩和缓存头
        response.headers['Vary'] = 'Accept-Encoding'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        return response

    # 高级HTML页面缓存策略
    if 'text/html' in response.content_type and response.status_code == 200:
        # 根据页面类型设置不同的缓存策略
        if request.path == '/' or request.path.startswith('/en') or request.path.startswith('/zh'):
            # 首页和主要页面：短期缓存
            response.cache_control.max_age = 300  # 5分钟
            response.cache_control.public = True
        elif '.html' in request.path:
            # 文章页面：中期缓存
            response.cache_control.max_age = 1800  # 30分钟
            response.cache_control.public = True
        elif request.path.startswith('/admin'):
            # 管理页面：不缓存
            response.cache_control.no_cache = True
            response.cache_control.no_store = True
            response.cache_control.must_revalidate = True
        else:
            # 其他页面：短期缓存
            response.cache_control.max_age = 600  # 10分钟
        
        # 设置通用头
        response.headers['Vary'] = 'Accept-Language, Accept-Encoding'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
    # 智能页面缓存处理
    if request.method == 'GET' and response.status_code == 200:
        response = intelligent_cache.cache_response(response)
    
    # 原有的canonical链接处理（仅在模板未提供时注入）
    if 'text/html' in response.content_type:
        data = response.get_data(as_text=True)

        # 只在页面没有canonical标签时才注入
        if '</head>' in data and 'rel="canonical"' not in data:
            host = request.headers.get('X-Forwarded-Host', request.host)
            url = f"{request.scheme}://{host}{request.path}"
            if '/' == url[-1]:
                url = url[:-1]
            icon_url = f"{request.scheme}://{host}/favicon.ico"

            if url == "https://sprunkiphase4.net/ja/sprunki-phase-3.html":
                canonical_link = f'<link rel="canonical" href="https://sprunkiphase4.net/ja/sprunki.html">'
            else:
                canonical_link = f'<link rel="canonical" href="{url}">'
            canonical_link_2 = f'<link rel="icon" href="{icon_url}">'

            data = data.replace('</head>', f'{canonical_link}{canonical_link_2}</head>')
            response.set_data(data)

    return response


""" admin 视图"""
admin = Admin(app, name='Admin', template_mode='bootstrap3', index_view=MyAdminIndexView())

admin.add_view(ArticleView(文章db))
admin.add_view(AuthView(状态db))
admin.add_view(CategoryView(分类db))
admin.add_view(AuthView(标签db))
admin.add_view(AuthView(模板db))
admin.add_view(AuthView(User))
admin.add_view(PictureModelView(Picture))

# 集成评论系统
init_comment_system(app, admin)

# 注意：静态文件路由已在 get_app.py 中定义

if __name__ == '__main__':
    # 7-15-15-44
    create_super_admin()

    # 缓存预热 - 在后台线程中运行
    warmup_cache()

    # 检查是否有 SSL 证书文件
    import os
    if os.path.exists('cert.pem') and os.path.exists('key.pem'):
        # 使用 HTTPS
        print("🔒 启动 HTTPS 服务器...")
        app.run(debug=True, port=9028, host='0.0.0.0',
                ssl_context=('cert.pem', 'key.pem'))
    else:
        # 使用 HTTP
        print("⚠️  未找到 SSL 证书，使用 HTTP...")
        app.run(debug=True, port=9028, host='0.0.0.0')
