# 新的网站地图
from datetime import timedelta, datetime

from loguru import logger
import pytz
from setting import mongo_uri
from mongoengine import connect

connect(host=mongo_uri)
from urllib.parse import urljoin
from apps.models.article_model import 文章db
from setting import languages

"""
主页
详情页
    读取文章数据库
"""
urls = []

host = "https://sprunkiphase4.net/"

for lang in languages:
    if lang == "en":
        lang = ""
    else:
        pass
    url = urljoin(host, lang)
    urls.append({
        "url": url,
        "lastmod": "2024-11-29T04:29:24.610000+00:00",
        'priority': 1,
    })
for i in 文章db.objects(状态="已发布").only("lang", "article_url", "发布时间"):
    lang = i.lang
    if lang == "en":
        lang = ""
    article = i.article_url + ".html"
    url = urljoin(host, lang)
    url = urljoin(url + '/', article)
    发布时间 = i.发布时间
    logger.info(发布时间)
    now = datetime.now()
    three_days_ago = now - timedelta(days=3)

    # 判断目标时间是否在近三天内
    if three_days_ago <= 发布时间 <= now:
        print("目标时间是近三天的时间")
        priority = 1
    else:
        print("目标时间不是近三天的时间")
        priority = 0.8

    utc_time = 发布时间.astimezone(pytz.utc)
    utc_str = utc_time.isoformat()
    logger.info(utc_time)
    urls.append({
        "url": url,
        "lastmod": utc_str,
        'priority': 1,
    })

print(len(urls))
for url in urls:
    print(url)
with open('static/sitemap.xml', 'wb') as f:
    f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write(b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    for url in urls:
        f.write(b'  <url>\n')
        f.write(f'    <loc>{url["url"]}</loc>\n'.encode('utf-8'))
        f.write(f'    <lastmod>{url["lastmod"]}</lastmod>\n'.encode('utf-8'))
        f.write(f'    <priority>{url["priority"]}</priority>\n'.encode('utf-8'))
        f.write(b'  </url>\n')
    f.write(b'</urlset>\n')