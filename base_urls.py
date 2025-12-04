import re

import loguru
from flask import render_template, request, session, make_response, Blueprint, redirect, url_for, jsonify, send_from_directory
from loguru import logger
from werkzeug.routing import BaseConverter

from apps.models.article_model import *
from flask_babel import _
from apps.models.article_model import 文章db
from apps.views.util import redirect_if_en
from get_app import create_app
# from openai import OpenAI

from setting import ALLOWED_LANGUAGES

# 导入优化查询函数
from optimized_queries import get_article_optimized

"""
项目通用的url链接,后期需要根据实际情况简单修改
"""

app = create_app()
base_bp = Blueprint('base_url', import_name=__name__, url_prefix='')

# 优化路由正则表达式生成（缓存结果）
@lru_cache(maxsize=1)
def get_non_english_languages():
    """获取非英语语言列表（缓存）"""
    return [lang for lang in ALLOWED_LANGUAGES if lang != 'en']

@lru_cache(maxsize=1)
def get_language_regex():
    """获取语言路由正则表达式（缓存）"""
    no_ne = get_non_english_languages()
    return f'<regex("{"|".join(no_ne)}"):lang>'

# 使用缓存的正则表达式
regex_lang = get_language_regex()

# ===================== 静态文件路由映射 =====================
# 优先级最高 - 必须在其他路由之前，避免被通用路由捕获

@base_bp.route('/style/<path:filename>')
def style_files(filename):
    """CSS文件根目录访问"""
    return send_from_directory('static/style', filename)

@base_bp.route('/js/<path:filename>')
def js_files(filename):
    """JS文件根目录访问"""
    return send_from_directory('static/js', filename)

@base_bp.route('/css/<path:filename>')
def css_files(filename):
    """CSS文件根目录访问"""
    return send_from_directory('static/css', filename)

@base_bp.route('/images/<path:filename>')
def images_files(filename):
    """图片文件根目录访问"""
    return send_from_directory('static/images', filename)

@base_bp.route('/favicon.ico')
def favicon():
    """网站图标"""
    return send_from_directory('static', 'favicon.ico')

@base_bp.route('/manifest.json')
def manifest():
    """PWA清单文件"""
    return send_from_directory('static', 'manifest.json')

@base_bp.route('/robots.txt')
def robots():
    """搜索引擎爬虫文件"""
    return send_from_directory('static', 'robots.txt')

@base_bp.route('/sitemap.xml')
def sitemap():
    """网站地图"""
    return send_from_directory('static', 'sitemap.xml')

# ===================== 其他路由 =====================

@base_bp.route(f'{regex_lang}/<int:ids>.html', methods=['GET'])
@base_bp.route(f'<int:ids>.html', methods=['GET'])
@redirect_if_en('base_url')
def article_info(lang=None, ids=None):
    logger.info(f"当前语言{lang}")
    """文章详情页面 - 已优化查询性能"""
    # 使用优化的查询函数，显著提升性能
    article_data = get_article_optimized(ids, '发布')
    
    if article_data:
        web_title = ""
        web_content = ""
        
        # 使用优化后的数据结构（已经是字典格式）
        info = {
            'web_title': web_title,
            'web_content': web_content,
            "article": article_data,  # 直接使用优化的数据
        }

        return render_template("web/content.html", info=info)
    else:
        return render_template("base/404.html"), 404


# shouye

@base_bp.route(f'/')
@base_bp.route(f'/{regex_lang}')
@redirect_if_en("base_url")
def index_lang(lang=None):
    try:
        # 网站标题和网站内容,后期单独设置
        web_title = "sprunki phase 4 | Free Play sprunki phase 4 Online"
        web_content = "Sprunki Phase 4 is the latest update in the music rhythm game, offering new beats, characters, and challenges."
        # 最新文章
        # 最热文章

        new_articles = []
        hot_articles = []
        random_article = []
        
        # 暂时跳过数据库查询，直接使用默认数据
        try:

            dbs = 文章db.objects.filter(lang=lang).order_by('-发布时间').limit(30).all()
           # 要获取的文章
            for db in dbs:
                article_temp = {
                    'url': db.article_url,
                    'title': db.标题,
                    'image': db.image_url,
                    'desc': db.简介,
                }
                new_articles.append(article_temp)

            # 临时禁用数据库查询，避免超时
            # raise Exception("暂时跳过数据库查询")
        except Exception as e:
            logger.error(f"数据库查询失败: {e}")
            # 使用默认的测试数据
            new_articles = [
                {
                    'url': 'sprunki-phase-3',
                    'title': 'Sprunki Phase 3',
                    'image': 'https://img.sprunki.net/image/sprunki-phase-3.webp',
                    'desc': 'Play Sprunki Phase 3 online for free',
                },
                {
                    'url': 'sprunki-incredibox',
                    'title': 'Sprunki Incredibox',
                    'image': 'https://img.sprunki.net/image/sprunki-phase-4.webp',
                    'desc': 'Original Sprunki Incredibox game',
                }
            ]

        # 查询随机文章

        info = {
            "web_title": web_title,
            "web_content": web_content,
            # "latest_articles": hot_articles,
            # "new_articles": new_articles,
            # "random_article": random_article,
            # "user_data": {"name": "test"}
        }

        return render_template('web/index.html', datas_list=new_articles, info=info)
    except Exception as e:
        logger.error(f"首页路由错误: {e}")
        return f'<h1>首页加载中...</h1><p>错误: {str(e)}</p><a href="/test">测试页面</a>', 500


# 文章详情页
@base_bp.route('/<string:article_url>.html', methods=['GET'])
@base_bp.route(f'/{regex_lang}/<string:article_url>.html', methods=['GET'])
@redirect_if_en("base_url")
def article_info_demo(article_url, lang=None):
    logger.info(f"当前语言{lang}")

    article = 文章db.objects(article_url=article_url, lang=lang).first()
    if article:
        # 按发布时间降序排列，获取最新的30篇文章用于推荐
        dbs = 文章db.objects.filter(lang=lang).order_by('-发布时间').limit(30).all()
        datas = []  # 要获取的文章
        for db in dbs:
            article_temp = {
                'url': db.article_url,
                'title': db.标题,
                'image': db.image_url,
                'desc': db.简介,
            }
            datas.append(article_temp)
        web_title = ""
        web_content = ""
        article = {
            'ids': article_url,
            'title': article.标题,
            'content': article.正文内容,
            'jianjie': article.简介,
            "iframe": article.iframe,
            'image_url': article.image_url
        }
        info = {
            'web_title': web_title,
            'web_content': web_content,
            "article": article,
        }

        return render_template('web/content.html', article=article, info=info, datas=datas)

    else:
        return render_template('base/404.html'), 404


# fenlei
@base_bp.route('/<string:category>_game.html', methods=['GET'])
@base_bp.route(f'{regex_lang}/<string:category>_game.html', methods=['GET'])
@redirect_if_en("base_url")
def article_list_demo(category=None, lang=None):
    # ========根据实际情况组织参数==========
    # 参数必须要
    header_foot_info = {

        "article": {
            "title": "Sprunki Incredibox mod",
            "jianjie": "Sprunki Incredibox mod collection list",
        }
    }
    logger.info(category)
    # 按发布时间降序排列，获取该分类最新的100篇文章
    dbs = 文章db.objects.filter(分类=category,lang=lang).order_by('-发布时间').limit(100).all()
    article_list = []  # 要获取的文章
    for db in dbs:
        article_temp = {
            'url': db.article_url,
            'title': db.标题,
            'image': db.image_url,
            'desc': db.简介,
        }
        article_list.append(article_temp)
    # return True
    logger.info(article_list)
    return render_template('web/category.html', article_list=article_list, info=header_foot_info)


# New route for privacy policy
@base_bp.route('/privacy-policy.html', methods=['GET'])
@base_bp.route(f'/{regex_lang}/privacy-policy.html', methods=['GET'])
@redirect_if_en("base_url")
def privacy_policy(lang=None):
    """Privacy Policy page"""
    web_title = "Privacy Policy"
    web_content = "Privacy Policy"

    header_foot_info = {
        'web_title': web_title,
        'web_content': web_content,
    }

    return render_template("web/privacy_policy.html")

# New route for about page
@base_bp.route('/about.html', methods=['GET'])
@base_bp.route(f'/{regex_lang}/about.html', methods=['GET'])
@redirect_if_en("base_url")
def about(lang=None):
    """About page"""
    web_title = "About Sprunki Phase 4"
    web_content = "Learn more about Sprunki Phase 4"

    header_foot_info = {
        'web_title': web_title,
        'web_content': web_content,
    }

    return render_template("web/about.html", info=header_foot_info)

# 评论系统演示页面
@base_bp.route('/comment-demo', methods=['GET'])
def comment_demo():
    """评论系统演示页面"""
    return render_template("comment_demo.html")

# PWA测试页面
@base_bp.route('/pwa-test', methods=['GET'])
def pwa_test():
    """PWA配置测试页面"""
    return render_template("pwa_test.html")

# 游戏调试页面
@base_bp.route('/game-debug', methods=['GET'])
def game_debug():
    """游戏功能调试页面"""
    return send_from_directory('.', 'debug_game.html')

# 测试页面路由
@base_bp.route('/test', methods=['GET'])
def test_page():
    """简单测试页面"""
    return '<h1>测试页面</h1><p>Flask服务器运行正常！</p>' + \
           '<a href="/test-play-button.html">测试PLAY按钮</a><br>' + \
           '<a href="/function-test.html">测试函数可用性</a><br>' + \
           '<a href="/standalone-test.html">完整功能测试</a><br>' + \
           '<a href="/">主页（修复后的PLAY GAME）</a>'

# 函数测试页面
@base_bp.route('/function-test.html', methods=['GET'])
def function_test():
    """函数可用性测试页面"""
    try:
        import os
        file_path = os.path.join(os.getcwd(), 'function_test.html')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
        else:
            return '<h1>测试页面未找到</h1><p>function_test.html 文件不存在</p>', 404
    except Exception as e:
        return f'<h1>错误</h1><p>{str(e)}</p>', 500

# PLAY按钮测试页面
@base_bp.route('/test-play-button.html', methods=['GET'])
def test_play_button():
    """PLAY按钮测试页面"""
    try:
        import os
        file_path = os.path.join(os.getcwd(), 'test_play_button.html')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
        else:
            return '<h1>测试页面未找到</h1><p>test_play_button.html 文件不存在</p>', 404
    except Exception as e:
        return f'<h1>错误</h1><p>{str(e)}</p>', 500

# 独立测试页面
@base_bp.route('/standalone-test.html', methods=['GET'])
def standalone_test():
    """独立测试页面"""
    try:
        import os
        file_path = os.path.join(os.getcwd(), 'standalone_test.html')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
        else:
            return '<h1>测试页面未找到</h1><p>standalone_test.html 文件不存在</p>', 404
    except Exception as e:
        return f'<h1>错误</h1><p>{str(e)}</p>', 500
