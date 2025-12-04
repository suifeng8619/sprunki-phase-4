from loguru import logger
from flask import Flask, request
from flask_babel import Babel
try:
    from flask_compress import Compress
    HAS_COMPRESS = True
except ImportError:
    HAS_COMPRESS = False
from flask_mongoengine import MongoEngine
from werkzeug.routing import BaseConverter

from setting import mongo_uri, ALLOWED_LANGUAGES


def get_locale():
    # 获取语言
    path_parts = request.path.strip('/').split('/')
    lang = 'en'
    if path_parts and path_parts[0] in app.config['BABEL_SUPPORTED_LOCALES']:
        # 从路径中提取语言代码并设置到 session
        lang = path_parts[0]
    # loguru.logger.info(f"语言为{lang}")
    return lang


def no_en_get_locale():
    path_parts = request.path.strip('/').split('/')
    # 过滤掉空字符串
    path_parts = [part for part in path_parts if part]
    logger.info(path_parts)
    lang = 'en'
    if path_parts and path_parts[0] in app.config['BABEL_SUPPORTED_LOCALES']:
        # 从路径中提取语言代码并设置到 session
        lang = path_parts[0]
    logger.info(f"语言为{lang}")
    if lang == 'en':
        return None
    return lang


class RegexConverter(BaseConverter):
    """
    自定义URL匹配正则表达式
    """

    def __init__(self, map, regex):
        super(RegexConverter, self).__init__(map)
        self.regex = regex

    def to_python(self, value):
        """
        路由匹配时，匹配成功后传递给视图函数中参数的值
        :param value:
        :return:
        """
        logger.info(f"999999：{value}")
        return value

    def to_url(self, value):
        """
        使用url_for反向生成URL时，传递的参数经过该方法处理，返回的值用于生成URL中的参数
        :param value:
        :return:
        """
        val = super(RegexConverter, self).to_url(value)
        logger.info(f"888888:{value}")
        return val


def create_app():
    """flask 配置在这里"""
    # 静态文件目录
    app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path="/")

    # Register the custom converter
    app.url_map.converters['regex'] = RegexConverter
    app.url_map.strict_slashes = False  # 自动重定向尾部/问题
    babel = Babel(app)

    app.secret_key = 'eyJpc3MiOiJzdXBhwicm9sZSI6ImFub24iLCJpYXQiOjE3MjAwNjMyMjUsImV4cCI6MjAzNTYzOTIyNX0'  # 用于会话管理
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'
    # 语言设置
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.config['BABEL_SUPPORTED_LOCALES'] = ALLOWED_LANGUAGES

    app.config['MONGODB_SETTINGS'] = {
        'host': mongo_uri
    }
    app.config['SESSION_COOKIE_SECURE'] = True  # In production, this should be True if using HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True

    # 性能优化：静态文件缓存 (1年 for hashed files, 1天 for others)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 86400  # 1天

    # 性能优化：启用Gzip压缩
    if HAS_COMPRESS:
        compress = Compress()
        app.config['COMPRESS_ALGORITHM'] = 'gzip'
        app.config['COMPRESS_LEVEL'] = 6
        app.config['COMPRESS_MIN_SIZE'] = 500
        # 排除大CSS文件的压缩，避免截断问题
        app.config['COMPRESS_MIMETYPES'] = [
            'text/html',
            'text/xml',
            'application/json',
            'application/javascript',
        ]
        compress.init_app(app)
        logger.info("✅ Gzip压缩已启用（CSS文件除外）")
    else:
        logger.warning("⚠️ flask-compress未安装，压缩功能未启用")

    babel.init_app(app, locale_selector=get_locale)

    #  设置login验证
    return app


app = create_app()
db = MongoEngine(app)

# 静态文件缓存辅助函数
def add_cache_headers(response, max_age=86400):
    """添加缓存头"""
    response.headers['Cache-Control'] = f'public, max-age={max_age}'
    return response

# 临时解决方案：添加全局静态文件路由处理器
@app.route('/style/<path:filename>')
def global_style_files(filename):
    """全局CSS文件根目录访问 - 临时解决方案"""
    from flask import send_from_directory
    response = send_from_directory('static/style', filename)
    return add_cache_headers(response, 604800)  # 7天

@app.route('/js/<path:filename>')
def global_js_files(filename):
    """全局JS文件根目录访问 - 临时解决方案"""
    from flask import send_from_directory
    response = send_from_directory('static/js', filename)
    return add_cache_headers(response, 604800)  # 7天

@app.route('/css/<path:filename>')
def global_css_files(filename):
    """全局CSS文件根目录访问 - 临时解决方案"""
    from flask import send_from_directory
    response = send_from_directory('static/css', filename)
    return add_cache_headers(response, 604800)  # 7天

@app.route('/dist/<path:filename>')
def global_dist_files(filename):
    """构建后的静态文件 - 长期缓存"""
    from flask import send_from_directory
    response = send_from_directory('static/dist', filename)
    return add_cache_headers(response, 31536000)  # 1年

@app.route('/images/<path:filename>')
def global_images_files(filename):
    """全局图片文件根目录访问 - 临时解决方案"""
    from flask import send_from_directory
    response = send_from_directory('static/images', filename)
    return add_cache_headers(response, 2592000)  # 30天

@app.route('/favicon.ico')
def global_favicon():
    """全局网站图标 - 临时解决方案"""
    from flask import send_from_directory
    response = send_from_directory('static', 'favicon.ico')
    return add_cache_headers(response, 2592000)  # 30天

# 全局404错误处理器
@app.errorhandler(404)
def page_not_found(e):
    """全局404页面 - 品牌化设计"""
    from flask import render_template
    return render_template('base/404.html'), 404
