#!/usr/bin/env python3
"""
高性能内存缓存系统
为Flask应用提供安全、高效的内存缓存
"""

import time
import threading
from functools import wraps
from datetime import datetime, timedelta
import hashlib
import json
from loguru import logger

class PerformanceCache:
    """
    高性能内存缓存类
    特点：
    - 线程安全
    - 自动过期清理
    - 内存控制
    - 性能监控
    """
    
    def __init__(self, max_items=500, default_timeout=600):
        self.max_items = max_items
        self.default_timeout = default_timeout
        self._cache = {}
        self._timestamps = {}
        self._access_count = {}
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'cleanups': 0
        }
        
        # 启动后台清理线程
        self._start_cleanup_thread()
    
    def _generate_key(self, key):
        """生成缓存键"""
        if isinstance(key, (list, tuple, dict)):
            key = json.dumps(key, sort_keys=True)
        return str(key)
    
    def _is_expired(self, key):
        """检查是否过期"""
        if key not in self._timestamps:
            return True
        
        timestamp, timeout = self._timestamps[key]
        return time.time() - timestamp > timeout
    
    def _cleanup_expired(self):
        """清理过期缓存"""
        with self._lock:
            current_time = time.time()
            expired_keys = []
            
            for key, (timestamp, timeout) in self._timestamps.items():
                if current_time - timestamp > timeout:
                    expired_keys.append(key)
            
            for key in expired_keys:
                self._remove_key(key)
            
            if expired_keys:
                self._stats['cleanups'] += len(expired_keys)
                logger.debug(f"缓存清理: 删除 {len(expired_keys)} 个过期项")
    
    def _remove_key(self, key):
        """删除缓存项"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
        self._access_count.pop(key, None)
    
    def _enforce_size_limit(self):
        """强制执行大小限制"""
        if len(self._cache) <= self.max_items:
            return
        
        # 按访问次数排序，删除最少使用的项
        items_by_access = sorted(
            self._access_count.items(), 
            key=lambda x: x[1]
        )
        
        # 删除最少使用的20%
        to_remove = len(self._cache) - int(self.max_items * 0.8)
        
        for key, _ in items_by_access[:to_remove]:
            self._remove_key(key)
        
        logger.debug(f"缓存大小控制: 删除 {to_remove} 个最少使用项")
    
    def _start_cleanup_thread(self):
        """启动后台清理线程"""
        def cleanup_worker():
            while True:
                time.sleep(60)  # 每分钟清理一次
                try:
                    self._cleanup_expired()
                    self._enforce_size_limit()
                except Exception as e:
                    logger.error(f"缓存清理失败: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        logger.info("缓存清理线程已启动")
    
    def get(self, key):
        """获取缓存"""
        key = self._generate_key(key)
        
        with self._lock:
            if key not in self._cache or self._is_expired(key):
                self._stats['misses'] += 1
                return None
            
            # 更新访问统计
            self._access_count[key] = self._access_count.get(key, 0) + 1
            self._stats['hits'] += 1
            
            return self._cache[key]
    
    def set(self, key, value, timeout=None):
        """设置缓存"""
        key = self._generate_key(key)
        timeout = timeout or self.default_timeout
        
        with self._lock:
            self._cache[key] = value
            self._timestamps[key] = (time.time(), timeout)
            self._access_count[key] = 0
            self._stats['sets'] += 1
            
            # 检查大小限制
            self._enforce_size_limit()
    
    def delete(self, key):
        """删除缓存"""
        key = self._generate_key(key)
        
        with self._lock:
            if key in self._cache:
                self._remove_key(key)
                self._stats['deletes'] += 1
                return True
            return False
    
    def clear(self):
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._access_count.clear()
            logger.info("缓存已清空")
    
    def get_stats(self):
        """获取缓存统计"""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'items': len(self._cache),
                'max_items': self.max_items,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': f"{hit_rate:.1f}%",
                'sets': self._stats['sets'],
                'deletes': self._stats['deletes'],
                'cleanups': self._stats['cleanups']
            }

# 全局缓存实例
article_cache = PerformanceCache(max_items=300, default_timeout=600)  # 10分钟
page_cache = PerformanceCache(max_items=100, default_timeout=300)     # 5分钟
language_cache = PerformanceCache(max_items=50, default_timeout=3600) # 1小时

def cached_function(cache_instance=None, timeout=None, key_func=None):
    """
    函数缓存装饰器
    
    Args:
        cache_instance: 缓存实例，默认使用article_cache
        timeout: 缓存超时时间
        key_func: 自定义键生成函数
    """
    if cache_instance is None:
        cache_instance = article_cache
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
            
            # 尝试从缓存获取
            cached_result = cache_instance.get(cache_key)
            if cached_result is not None:
                logger.debug(f"缓存命中: {func.__name__}")
                return cached_result
            
            # 执行函数
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            # 缓存结果
            cache_instance.set(cache_key, result, timeout)
            logger.debug(f"缓存设置: {func.__name__}, 耗时: {execution_time:.2f}ms")
            
            return result
        
        # 添加缓存控制方法
        wrapper.cache_clear = lambda: cache_instance.clear()
        wrapper.cache_stats = lambda: cache_instance.get_stats()
        
        return wrapper
    return decorator

def cache_with_key(cache_key, cache_instance=None, timeout=None):
    """
    基于固定键的缓存装饰器
    """
    if cache_instance is None:
        cache_instance = article_cache
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 使用固定键
            cached_result = cache_instance.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 执行并缓存
            result = func(*args, **kwargs)
            cache_instance.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator

# 性能监控装饰器
def monitor_performance(func):
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            if execution_time > 100:  # 超过100ms记录警告
                logger.warning(f"慢函数检测: {func.__name__} 耗时 {execution_time:.2f}ms")
            else:
                logger.debug(f"函数执行: {func.__name__} 耗时 {execution_time:.2f}ms")
            
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"函数执行失败: {func.__name__} 耗时 {execution_time:.2f}ms, 错误: {e}")
            raise
    return wrapper

def get_cache_status():
    """获取所有缓存状态"""
    return {
        'article_cache': article_cache.get_stats(),
        'page_cache': page_cache.get_stats(),
        'language_cache': language_cache.get_stats(),
        'timestamp': datetime.now().isoformat()
    }

if __name__ == "__main__":
    # 测试缓存系统
    print("🧪 测试缓存系统...")
    
    @cached_function(timeout=5)
    def test_function(x, y):
        time.sleep(0.1)  # 模拟耗时操作
        return x + y
    
    # 测试缓存命中
    print("第一次调用...")
    start = time.time()
    result1 = test_function(1, 2)
    time1 = (time.time() - start) * 1000
    
    print("第二次调用（应该命中缓存）...")
    start = time.time()
    result2 = test_function(1, 2)
    time2 = (time.time() - start) * 1000
    
    print(f"结果: {result1} = {result2}")
    print(f"第一次耗时: {time1:.2f}ms")
    print(f"第二次耗时: {time2:.2f}ms (缓存命中)")
    print(f"性能提升: {((time1 - time2) / time1 * 100):.1f}%")
    
    # 显示统计
    print("\n📊 缓存统计:")
    stats = test_function.cache_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")