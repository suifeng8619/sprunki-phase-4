import re
import time

import loguru
from flask import render_template, request, session, make_response, Blueprint, redirect, url_for, jsonify, send_from_directory
from loguru import logger
from werkzeug.routing import BaseConverter
from cachetools import TTLCache

from apps.models.article_model import *
from flask_babel import _
from apps.models.article_model import 文章db
from apps.views.util import redirect_if_en
from get_app import create_app
# from openai import OpenAI

from setting import ALLOWED_LANGUAGES

# ==================== 缓存配置 ====================
# 文章列表缓存 - 按语言缓存，5分钟过期，最多缓存50个语言版本
_article_list_cache = TTLCache(maxsize=50, ttl=300)

# 单篇文章缓存 - 10分钟过期，最多缓存200篇
_article_cache = TTLCache(maxsize=200, ttl=600)

def get_cached_article_list(lang, limit=30):
    """获取缓存的文章列表"""
    cache_key = f"list_{lang}_{limit}"

    if cache_key in _article_list_cache:
        logger.debug(f"缓存命中: {cache_key}")
        return _article_list_cache[cache_key]

    logger.info(f"缓存未命中，查询数据库: {cache_key}")
    start_time = time.time()

    try:
        dbs = 文章db.objects.filter(lang=lang).order_by('-发布时间').limit(limit).all()
        articles = []
        for db in dbs:
            articles.append({
                'url': db.article_url,
                'title': db.标题,
                'image': db.image_url,
                'desc': db.简介,
            })

        _article_list_cache[cache_key] = articles
        logger.info(f"数据库查询耗时: {time.time() - start_time:.3f}s")
        return articles
    except Exception as e:
        logger.error(f"数据库查询失败: {e}")
        return []

def get_cached_article(article_url, lang):
    """获取缓存的单篇文章"""
    cache_key = f"article_{article_url}_{lang}"

    if cache_key in _article_cache:
        logger.debug(f"文章缓存命中: {cache_key}")
        return _article_cache[cache_key]

    logger.info(f"文章缓存未命中，查询数据库: {cache_key}")
    start_time = time.time()

    try:
        article = 文章db.objects(article_url=article_url, lang=lang).first()
        if article:
            article_data = {
                'ids': article_url,
                'title': article.标题,
                'content': article.正文内容,
                'jianjie': article.简介,
                'iframe': article.iframe,
                'image_url': article.image_url
            }
            _article_cache[cache_key] = article_data
            logger.info(f"文章查询耗时: {time.time() - start_time:.3f}s")
            return article_data
    except Exception as e:
        logger.error(f"文章查询失败: {e}")

    return None

"""
项目通用的url链接,后期需要根据实际情况简单修改
"""

app = create_app()
base_bp = Blueprint('base_url', import_name=__name__, url_prefix='')

no_ne = []
for i in ALLOWED_LANGUAGES:
    if i == 'en':
        continue
    no_ne.append(i)

regex_lang = f'<regex("{"|".join(no_ne)}"):lang>'

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
    """文章详情页面"""
    article = 文章db.objects(ids=ids, 状态='发布').first()
    if article:
        web_title = ""
        web_content = ""
        article = {
            'ids': ids,
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

        return render_template("web/content.html", info=info)
    else:
        return render_template("base/404.html"), 404


# shouye

@base_bp.route(f'/')
@base_bp.route(f'/{regex_lang}')
@redirect_if_en("base_url")
def index_lang(lang=None):
    try:
        # 网站标题和网站内容
        web_title = "sprunki phase 4 | Free Play sprunki phase 4 Online"
        web_content = "Sprunki Phase 4 is the latest update in the music rhythm game, offering new beats, characters, and challenges."

        # 使用缓存获取文章列表
        new_articles = get_cached_article_list(lang, limit=30)

        # 如果缓存为空，使用默认数据
        if not new_articles:
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

        info = {
            "web_title": web_title,
            "web_content": web_content,
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

    # 使用缓存获取文章
    article = get_cached_article(article_url, lang)

    if article:
        # 使用缓存获取推荐文章列表
        datas = get_cached_article_list(lang, limit=30)

        info = {
            'web_title': '',
            'web_content': '',
            "article": article,
        }

        return render_template('web/content.html', article=article, info=info, datas=datas)

    else:
        return render_template('base/404.html'), 404


# 分类缓存
_category_cache = TTLCache(maxsize=100, ttl=300)

def warmup_cache():
    """缓存预热 - 服务启动时预加载热门数据"""
    import threading

    def _warmup():
        logger.info("🔥 开始缓存预热...")
        start_time = time.time()

        # 预热主要语言的文章列表
        priority_langs = ['en', None, 'zh', 'ja', 'ko', 'es', 'fr', 'de']
        warmed_count = 0

        for lang in priority_langs:
            try:
                articles = get_cached_article_list(lang, limit=30)
                if articles:
                    warmed_count += 1
                    logger.debug(f"已预热语言 {lang}: {len(articles)} 篇文章")
            except Exception as e:
                logger.error(f"预热语言 {lang} 失败: {e}")

        # 预热热门文章
        hot_articles = ['sprunki-phase-4', 'sprunki-phase-3', 'sprunki', 'sprunki-incredibox']
        for article_url in hot_articles:
            for lang in ['en', None]:
                try:
                    article = get_cached_article(article_url, lang)
                    if article:
                        warmed_count += 1
                        logger.debug(f"已预热文章: {article_url} ({lang})")
                except Exception as e:
                    logger.error(f"预热文章 {article_url} 失败: {e}")

        elapsed = time.time() - start_time
        logger.info(f"✅ 缓存预热完成! 预热 {warmed_count} 项，耗时 {elapsed:.2f}s")

    # 在后台线程中运行，不阻塞服务器启动
    thread = threading.Thread(target=_warmup, daemon=True)
    thread.start()
    return thread

def get_cached_category_list(category, lang, limit=100):
    """获取缓存的分类文章列表"""
    cache_key = f"cat_{category}_{lang}_{limit}"

    if cache_key in _category_cache:
        logger.debug(f"分类缓存命中: {cache_key}")
        return _category_cache[cache_key]

    logger.info(f"分类缓存未命中，查询数据库: {cache_key}")
    start_time = time.time()

    try:
        dbs = 文章db.objects.filter(分类=category, lang=lang).order_by('-发布时间').limit(limit).all()
        articles = []
        for db in dbs:
            articles.append({
                'url': db.article_url,
                'title': db.标题,
                'image': db.image_url,
                'desc': db.简介,
            })

        _category_cache[cache_key] = articles
        logger.info(f"分类查询耗时: {time.time() - start_time:.3f}s")
        return articles
    except Exception as e:
        logger.error(f"分类查询失败: {e}")
        return []

# fenlei
@base_bp.route('/<string:category>_game.html', methods=['GET'])
@base_bp.route(f'{regex_lang}/<string:category>_game.html', methods=['GET'])
@redirect_if_en("base_url")
def article_list_demo(category=None, lang=None):
    header_foot_info = {
        "article": {
            "title": "Sprunki Incredibox mod",
            "jianjie": "Sprunki Incredibox mod collection list",
        }
    }
    logger.info(category)

    # 使用缓存获取分类文章列表
    article_list = get_cached_category_list(category, lang, limit=100)

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
