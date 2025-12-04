import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 环境设置
os.environ['TESTING'] = os.getenv('TESTING', "0")  # 1测试环境  正式要为0
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = os.getenv('OAUTHLIB_INSECURE_TRANSPORT', '1')  # 1允许http
from loguru import logger

# ==========静态地址配置>>>>>>>>>>
UPLOAD_FOLDER_ROOT = os.path.join('static', 'images')
# ==========静态地址配置<<<<<<<<<<

# ++++++++++图床设置>>>>>>>>>>
R2_ENDPOINT_URL = os.getenv('R2_ENDPOINT_URL', "")
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME', '')
R2_ACCESS_KEY = os.getenv('R2_ACCESS_KEY', '')
R2_SECRET_KEY = os.getenv('R2_SECRET_KEY', '')
二级域名 = os.getenv('DOMAIN', "")
# ++++++++++图床设置<<<<<<<<<<

# ++++++++++支付hook>>>>>>>>>>
endpoint_secret = os.getenv('STRIPE_ENDPOINT_SECRET', "")
# ++++++++++支付hook<<<<<<<<<<

# ==========数据库设置>>>>>>>>>>
# ==========数据库设置<<<<<<<<<<
# ==========语言设置>>>>>>>>>>

languages = {
    'zh': '中文',
    'en': '英语',
    'hi': '印地语',
    'es': '西班牙语',
    'fr': '法语',
    'de': '德语',
    'ru': '俄语',
    'ja': '日语',
    'pt': '葡萄牙语',
    'ar': '阿拉伯语',
    'bn': '孟加拉语',
    'id': '印度尼西亚语',
    'pa': '旁遮普语',
    'ko': '韩语',
    'vi': '越南语',
    'tr': '土耳其语',
    'it': '意大利语',
    'th': '泰语',
    'nl': '荷兰语',
    'sv': '瑞典语',
    'fi': '芬兰语',
    'el': '希腊语',
    'he': '希伯来语',
    'sw': '斯瓦希里语',
    'hu': '匈牙利语',
    'cs': '捷克语',
    'ro': '罗马尼亚语',
    'da': '丹麦语',
    'no': '挪威语',
    'sk': '斯洛伐克语',
    'sl': '斯洛文尼亚语',
}
LANGUAGES = [

    {'code': 'en', 'name': 'English'},
    {'code': 'es', 'name': 'Español'},
    {'code': 'fr', 'name': 'Français'},
    {'code': 'de', 'name': 'Deutsch'},
    {'code': 'hi', 'name': 'हिन्दी'},
    {'code': 'zh', 'name': '中文'},
    {'code': 'ru', 'name': 'Русский'},
    {'code': 'ja', 'name': '日本語'},
    {'code': 'pt', 'name': 'Português'},
    {'code': 'ar', 'name': 'العربية'},
    {'code': 'bn', 'name': 'বাংলা'},
    {'code': 'id', 'name': 'Bahasa Indonesia'},
    {'code': 'pa', 'name': 'ਪੰਜਾਬੀ'},
    {'code': 'ko', 'name': '한국어'},
    {'code': 'vi', 'name': 'Tiếng Việt'},
    {'code': 'tr', 'name': 'Türkçe'},
    {'code': 'it', 'name': 'Italiano'},
    {'code': 'th', 'name': 'ภาษาไทย'},
    {'code': 'nl', 'name': 'Nederlands'},
    {'code': 'sv', 'name': 'Svenska'},
    {'code': 'fi', 'name': 'Suomi'},
    {'code': 'el', 'name': 'Ελληνικά'},
    {'code': 'he', 'name': 'עברית'},
    {'code': 'sw', 'name': 'Kiswahili'},
    {'code': 'hu', 'name': 'Magyar'},
    {'code': 'cs', 'name': 'Čeština'},
    {'code': 'ro', 'name': 'Română'},
    {'code': 'da', 'name': 'Dansk'},
    {'code': 'no', 'name': 'Norsk'},
    {'code': 'sk', 'name': 'Slovenčina'},
    {'code': 'sl', 'name': 'Slovenščina'},
]
ALLOWED_LANGUAGES = []
for lang in LANGUAGES:
    ALLOWED_LANGUAGES.append(lang['code'])
    logger.info(f"语序的语言{ALLOWED_LANGUAGES}")
# ALLOWED_LANGUAGES = ["en", 'zh', 'ja']
# ==========语言设置<<<<<<<<<<
# 数据库配置 - 使用环境变量
mongo_uri = os.getenv('MONGO_URI', "mongodb://127.0.0.1:27017/sprunkiphase4_net")


# 测试环境覆盖
if os.environ['TESTING'] == '1':
    logger.info("测试数据库")
    mongo_uri = os.getenv('MONGO_URI_TEST', "mongodb://127.0.0.1:27017/webtest")

# 注意: 所有敏感配置已移至环境变量，请参考 .env.example



UPLOAD_FOLDER_ROOT = os.path.join('static', 'images')

# +++++++++++ 评论系统配置 >>>>>>>>>>
COMMENT_SETTINGS = {
    'PER_PAGE': 10,  # 每页评论数
    'MAX_CONTENT_LENGTH': 2000,  # 评论最大长度
    'REQUIRE_MODERATION': False,  # 是否需要审核 - 改为False直接显示评论
    'ENABLE_REPLIES': True,  # 是否允许回复
    'ENABLE_RATING': True,  # 是否启用评分
    'CACHE_TIMEOUT': 300,  # 缓存超时时间（秒）
    'RATE_LIMIT': '10/minute',  # 频率限制
    'ALLOWED_TAGS': [],  # 允许的HTML标签
    'SPAM_KEYWORDS': [  # 垃圾评论关键词
        'spam', 'casino', 'viagra', 'cheap', 'money', 'free', 'click here',
        '广告', '推广', '代理', '投资', '赚钱', '免费', '点击这里'
    ],
    'AUTO_APPROVE': True,  # 是否自动审核通过 - 改为True自动批准
    'NOTIFY_ADMIN': True,  # 是否通知管理员新评论
    'MIN_CONTENT_LENGTH': 10,  # 评论最小长度
    'MAX_USERNAME_LENGTH': 50,  # 用户名最大长度
    'MAX_REPLY_LENGTH': 2000,  # 回复最大长度
    'MAX_REPLIES_PER_COMMENT': 5,  # 每个评论最多显示的回复数（性能优化）
    # 垃圾检测配置
    'ENABLE_SPAM_DETECTION': False,  # 开发环境中暂时禁用垃圾检测
    'SPAM_CHAR_REPEAT_THRESHOLD': 0.2,  # 重复字符阈值（降低以便测试）
    'SPAM_KEYWORD_CHECK': False,  # 开发环境中暂时禁用关键词检查
}
# +++++++++++ 评论系统配置 <<<<<<<<<<

