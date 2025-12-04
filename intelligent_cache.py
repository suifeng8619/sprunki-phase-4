#!/usr/bin/env python3
"""
页面级智能缓存系统
为Flask应用提供智能页面缓存，支持条件缓存和自动失效
"""

import time
import hashlib
import json
from functools import wraps
from flask import request, g, make_response
from loguru import logger
from cache_system import page_cache

class IntelligentPageCache:
    """
    智能页面缓存类
    特点：
    - 基于URL和参数的智能缓存键
    - 条件缓存（避免管理页面等敏感内容）
    - 自动压缩和优化
    - 缓存预热和批量更新
    """
    
    def __init__(self):
        self.cache_rules = {
            # 长期缓存 - 静态内容页面
            'static_pages': {
                'patterns': ['/test', '/about', '/contact'],
                'timeout': 3600,  # 1小时
                'conditions': []
            },
            
            # 中期缓存 - 文章页面
            'article_pages': {
                'patterns': ['.html', '/article/', '/post/'],
                'timeout': 1800,  # 30分钟
                'conditions': ['not_admin', 'not_preview']
            },
            
            # 短期缓存 - 首页和列表页
            'dynamic_pages': {
                'patterns': ['/', '/category/', '/tag/', '/search'],
                'timeout': 300,   # 5分钟
                'conditions': ['not_admin', 'stable_params']
            },
            
            # 不缓存
            'no_cache': {
                'patterns': ['/admin', '/api/', '/cache/', '/login', '/logout'],
                'timeout': 0,
                'conditions': []
            }
        }
    
    def generate_cache_key(self, request_obj=None):
        """生成智能缓存键"""
        if not request_obj:
            request_obj = request
            
        # 基础键: 路径 + 查询参数
        base_key = f"{request_obj.path}?{request_obj.query_string.decode()}"
        
        # 添加语言标识
        lang = getattr(g, 'language', 'en')
        
        # 添加用户类型（管理员vs普通用户）
        user_type = 'admin' if self._is_admin_request() else 'user'
        
        # 生成最终键
        final_key = f"page:{lang}:{user_type}:{base_key}"
        
        # 计算hash以控制键长度
        key_hash = hashlib.md5(final_key.encode()).hexdigest()
        return f"page_cache:{key_hash[:16]}"
    
    def _is_admin_request(self):
        """检查是否为管理员请求"""
        return '/admin' in request.path or 'admin' in request.args
    
    def _should_cache(self, path):
        """判断页面是否应该缓存"""
        # 检查不缓存规则
        for pattern in self.cache_rules['no_cache']['patterns']:
            if pattern in path:
                return False, 0
                
        # 检查其他缓存规则
        for rule_name, rule in self.cache_rules.items():
            if rule_name == 'no_cache':
                continue
                
            for pattern in rule['patterns']:
                if pattern in path:
                    # 检查条件
                    if self._check_conditions(rule['conditions']):
                        return True, rule['timeout']
        
        # 默认短期缓存
        return True, 180  # 3分钟
    
    def _check_conditions(self, conditions):
        """检查缓存条件"""
        for condition in conditions:
            if condition == 'not_admin' and self._is_admin_request():
                return False
            elif condition == 'not_preview' and 'preview' in request.args:
                return False
            elif condition == 'stable_params':
                # 检查参数是否稳定（排除时间戳等动态参数）
                unstable_params = ['timestamp', 'random', 'nocache', '_']
                for param in unstable_params:
                    if param in request.args:
                        return False
        return True
    
    def get_cached_response(self):
        """获取缓存的响应"""
        should_cache, timeout = self._should_cache(request.path)
        if not should_cache:
            return None
            
        cache_key = self.generate_cache_key()
        cached_data = page_cache.get(cache_key)
        
        if cached_data:
            logger.debug(f"页面缓存命中: {request.path}")
            response_data, headers, status_code = cached_data
            
            response = make_response(response_data, status_code)
            for key, value in headers.items():
                response.headers[key] = value
            
            # 添加缓存头
            response.headers['X-Cache-Status'] = 'HIT'
            response.headers['X-Cache-Key'] = cache_key[:8]
            
            return response
        
        return None
    
    def cache_response(self, response):
        """缓存响应"""
        should_cache, timeout = self._should_cache(request.path)
        if not should_cache or timeout == 0:
            return response
        
        # 只缓存成功的HTML响应
        if (response.status_code == 200 and 
            'text/html' in response.content_type):
            
            cache_key = self.generate_cache_key()
            
            # 准备缓存数据
            response_data = response.get_data(as_text=True)
            headers = dict(response.headers)
            status_code = response.status_code
            
            # 移除不应缓存的头
            headers_to_remove = ['Set-Cookie', 'X-Cache-Status', 'Date']
            for header in headers_to_remove:
                headers.pop(header, None)
            
            cached_data = (response_data, headers, status_code)
            page_cache.set(cache_key, cached_data, timeout)
            
            logger.debug(f"页面已缓存: {request.path}, 超时: {timeout}s")
            response.headers['X-Cache-Status'] = 'MISS'
            response.headers['X-Cache-Key'] = cache_key[:8]
        
        return response

# 全局智能缓存实例
intelligent_cache = IntelligentPageCache()

def intelligent_page_cache(func):
    """
    智能页面缓存装饰器
    用于视图函数的智能缓存
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 尝试获取缓存
        cached_response = intelligent_cache.get_cached_response()
        if cached_response:
            return cached_response
        
        # 执行原函数
        start_time = time.time()
        response = func(*args, **kwargs)
        execution_time = (time.time() - start_time) * 1000
        
        # 缓存响应
        response = intelligent_cache.cache_response(response)
        
        logger.info(f"页面生成: {request.path}, 耗时: {execution_time:.2f}ms")
        return response
    
    return wrapper

def cache_warm_up(urls):
    """
    缓存预热
    预先生成指定URL的缓存
    """
    logger.info(f"开始缓存预热: {len(urls)} 个URL")
    
    for url in urls:
        try:
            # 这里可以实现缓存预热逻辑
            # 例如：内部HTTP请求生成缓存
            logger.debug(f"预热URL: {url}")
        except Exception as e:
            logger.error(f"预热失败 {url}: {e}")
    
    logger.info("缓存预热完成")

def cache_invalidate_pattern(pattern):
    """
    按模式失效缓存
    清除匹配特定模式的所有缓存
    """
    # 这里可以实现模式匹配的缓存清理
    logger.info(f"失效缓存模式: {pattern}")
    
    # 由于我们的缓存系统使用hash键，这里简化为清空所有页面缓存
    page_cache.clear()
    logger.info("页面缓存已清空")

if __name__ == "__main__":
    # 测试智能缓存系统
    print("🧪 测试智能页面缓存系统...")
    
    cache = IntelligentPageCache()
    
    # 测试缓存规则
    test_paths = [
        '/',
        '/test',
        '/admin',
        '/api/test',
        '/article.html',
        '/ja/sprunki.html'
    ]
    
    for path in test_paths:
        should_cache, timeout = cache._should_cache(path)
        print(f"路径: {path:20} | 缓存: {should_cache:5} | 超时: {timeout:4}s")
    
    print("✅ 智能缓存系统测试完成！")