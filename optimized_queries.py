#!/usr/bin/env python3
"""
优化的查询函数模块
提供高性能的数据库查询函数，用于替换现有的低效查询
"""

from apps.models.article_model import 文章db
from loguru import logger
import time

# 导入缓存系统
from cache_system import cached_function, monitor_performance, article_cache

@cached_function(cache_instance=article_cache, timeout=600)
@monitor_performance
def get_article_optimized(ids, status='发布'):
    """
    优化的文章查询函数
    
    Args:
        ids (int): 文章ID
        status (str): 文章状态，默认为'发布'
        
    Returns:
        dict or None: 优化后的文章数据，如果未找到返回None
    """
    start_time = time.time()
    
    try:
        # 使用 only() 只查询需要的字段，显著减少网络传输
        article = 文章db.objects(ids=ids, 状态=status).only(
            'ids',
            '标题',
            '简介', 
            'iframe',
            'image_url',
            'article_url',  # 可能需要的URL字段
            '正文内容'  # 保留原有字段，避免模板错误
        ).first()
        
        query_time = (time.time() - start_time) * 1000
        logger.info(f"文章查询优化: ID={ids}, 耗时={query_time:.2f}ms")
        
        if not article:
            logger.warning(f"文章未找到: ID={ids}, status={status}")
            return None
        
        # 返回优化的数据结构，保持与原有代码兼容
        optimized_data = {
            'ids': article.ids,
            'title': article.标题,
            'content': article.正文内容,
            'jianjie': article.简介,
            'iframe': article.iframe,
            'image_url': article.image_url,
            # 可选字段，如果存在的话
            'article_url': getattr(article, 'article_url', ''),
        }
        
        logger.debug(f"文章数据优化完成: {optimized_data['title'][:50]}...")
        return optimized_data
        
    except Exception as e:
        query_time = (time.time() - start_time) * 1000
        logger.error(f"文章查询失败: ID={ids}, 耗时={query_time:.2f}ms, 错误={e}")
        return None

@cached_function(cache_instance=article_cache, timeout=300)
@monitor_performance
def get_article_list_optimized(status='发布', limit=10, offset=0):
    """
    优化的文章列表查询
    
    Args:
        status (str): 文章状态
        limit (int): 查询数量限制
        offset (int): 查询偏移量
        
    Returns:
        list: 文章列表
    """
    start_time = time.time()
    
    try:
        articles = 文章db.objects(状态=status).only(
            'ids',
            '标题',
            '简介',
            'image_url',
            '发布时间'
        ).skip(offset).limit(limit).order_by('-发布时间')
        
        query_time = (time.time() - start_time) * 1000
        logger.info(f"文章列表查询: {len(articles)}条记录, 耗时={query_time:.2f}ms")
        
        # 转换为字典列表，减少模板处理时间
        result = []
        for article in articles:
            result.append({
                'ids': article.ids,
                'title': article.标题,
                'jianjie': article.简介,
                'image_url': article.image_url,
                'publish_time': article.发布时间
            })
        
        return result
        
    except Exception as e:
        query_time = (time.time() - start_time) * 1000
        logger.error(f"文章列表查询失败: 耗时={query_time:.2f}ms, 错误={e}")
        return []

@cached_function(cache_instance=article_cache, timeout=600)
@monitor_performance
def get_article_by_url_optimized(article_url, lang='en'):
    """
    根据URL优化查询文章
    
    Args:
        article_url (str): 文章URL
        lang (str): 语言代码
        
    Returns:
        dict or None: 文章数据
    """
    start_time = time.time()
    
    try:
        article = 文章db.objects(
            article_url=article_url, 
            lang=lang, 
            状态='发布'
        ).only(
            'ids',
            '标题',
            '简介',
            'iframe',
            'image_url',
            'article_url'
        ).first()
        
        query_time = (time.time() - start_time) * 1000
        logger.info(f"URL文章查询: {article_url}, 耗时={query_time:.2f}ms")
        
        if not article:
            return None
            
        return {
            'ids': article.ids,
            'title': article.标题,
            'jianjie': article.简介,
            'iframe': article.iframe,
            'image_url': article.image_url,
            'article_url': article.article_url
        }
        
    except Exception as e:
        query_time = (time.time() - start_time) * 1000
        logger.error(f"URL文章查询失败: {article_url}, 耗时={query_time:.2f}ms, 错误={e}")
        return None

# 兼容性包装函数，方便替换现有代码
def optimize_article_query(original_query_func):
    """
    装饰器：为现有查询函数添加性能优化
    
    Args:
        original_query_func: 原始查询函数
        
    Returns:
        function: 优化后的查询函数
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = original_query_func(*args, **kwargs)
            query_time = (time.time() - start_time) * 1000
            
            if query_time > 100:  # 查询时间超过100ms时记录警告
                logger.warning(f"慢查询检测: {original_query_func.__name__}, 耗时={query_time:.2f}ms")
            else:
                logger.debug(f"查询完成: {original_query_func.__name__}, 耗时={query_time:.2f}ms")
                
            return result
            
        except Exception as e:
            query_time = (time.time() - start_time) * 1000
            logger.error(f"查询错误: {original_query_func.__name__}, 耗时={query_time:.2f}ms, 错误={e}")
            raise
            
    return wrapper

if __name__ == "__main__":
    # 测试优化查询函数
    print("测试优化查询函数...")
    
    # 测试文章查询
    article = get_article_optimized(1)
    if article:
        print(f"✅ 文章查询成功: {article['title']}")
    else:
        print("⚠️ 未找到测试文章 (ID=1)")
    
    # 测试文章列表
    articles = get_article_list_optimized(limit=5)
    print(f"✅ 文章列表查询: 找到 {len(articles)} 篇文章")
    
    print("测试完成！")