#!/usr/bin/env python3
"""
缓存监控和控制路由
提供缓存状态查看和控制接口
"""

from flask import Blueprint, jsonify, render_template_string
from cache_system import get_cache_status, article_cache, page_cache, language_cache
from datetime import datetime

cache_bp = Blueprint('cache_control', __name__)

@cache_bp.route('/cache/status')
def cache_status():
    """获取缓存状态"""
    try:
        status = get_cache_status()
        return jsonify({
            'success': True,
            'data': status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@cache_bp.route('/cache/dashboard')
def cache_dashboard():
    """缓存监控仪表板"""
    status = get_cache_status()
    
    dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>缓存监控仪表板</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-title { font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 15px; }
        .stat-item { display: flex; justify-content: space-between; margin: 8px 0; padding: 8px 0; border-bottom: 1px solid #eee; }
        .stat-label { font-weight: 500; }
        .stat-value { color: #27ae60; font-weight: bold; }
        .hit-rate { font-size: 24px; color: #e74c3c; }
        .refresh-btn { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        .refresh-btn:hover { background: #2980b9; }
        .timestamp { color: #7f8c8d; font-size: 12px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Sprunki Phase 4 缓存监控</h1>
            <p>实时监控应用缓存性能和状态</p>
            <button class="refresh-btn" onclick="location.reload()">刷新数据</button>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-title">📄 文章缓存 (Article Cache)</div>
                <div class="stat-item">
                    <span class="stat-label">缓存项数量:</span>
                    <span class="stat-value">{{ status.article_cache.items }} / {{ status.article_cache.max_items }}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">命中次数:</span>
                    <span class="stat-value">{{ status.article_cache.hits }}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">未命中次数:</span>
                    <span class="stat-value">{{ status.article_cache.misses }}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">命中率:</span>
                    <span class="stat-value hit-rate">{{ status.article_cache.hit_rate }}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">设置次数:</span>
                    <span class="stat-value">{{ status.article_cache.sets }}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">清理次数:</span>
                    <span class="stat-value">{{ status.article_cache.cleanups }}</span>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">📋 页面缓存 (Page Cache)</div>
                <div class="stat-item">
                    <span class="stat-label">缓存项数量:</span>
                    <span class="stat-value">{{ status.page_cache.items }} / {{ status.page_cache.max_items }}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">命中次数:</span>
                    <span class="stat-value">{{ status.page_cache.hits }}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">未命中次数:</span>
                    <span class="stat-value">{{ status.page_cache.misses }}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">命中率:</span>
                    <span class="stat-value hit-rate">{{ status.page_cache.hit_rate }}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">设置次数:</span>
                    <span class="stat-value">{{ status.page_cache.sets }}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">清理次数:</span>
                    <span class="stat-value">{{ status.page_cache.cleanups }}</span>
                </div>
            </div>
            
            <div class="stat-card">
                <div class="stat-title">🌐 语言缓存 (Language Cache)</div>
                <div class="stat-item">
                    <span class="stat-label">缓存项数量:</span>
                    <span class="stat-value">{{ status.language_cache.items }} / {{ status.language_cache.max_items }}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">命中次数:</span>
                    <span class="stat-value">{{ status.language_cache.hits }}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">未命中次数:</span>
                    <span class="stat-value">{{ status.language_cache.misses }}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">命中率:</span>
                    <span class="stat-value hit-rate">{{ status.language_cache.hit_rate }}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">设置次数:</span>
                    <span class="stat-value">{{ status.language_cache.sets }}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">清理次数:</span>
                    <span class="stat-value">{{ status.language_cache.cleanups }}</span>
                </div>
            </div>
        </div>
        
        <div class="timestamp">
            最后更新: {{ status.timestamp }}
        </div>
    </div>
    
    <script>
        // 自动刷新
        setInterval(() => {
            location.reload();
        }, 30000); // 30秒刷新一次
    </script>
</body>
</html>
    """
    
    return render_template_string(dashboard_html, status=status)

@cache_bp.route('/cache/clear')
def clear_cache():
    """清空所有缓存"""
    try:
        article_cache.clear()
        page_cache.clear()
        language_cache.clear()
        
        return jsonify({
            'success': True,
            'message': '所有缓存已清空',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@cache_bp.route('/cache/clear/<cache_type>')
def clear_specific_cache(cache_type):
    """清空特定缓存"""
    try:
        cache_map = {
            'article': article_cache,
            'page': page_cache,
            'language': language_cache
        }
        
        if cache_type not in cache_map:
            return jsonify({
                'success': False,
                'error': f'无效的缓存类型: {cache_type}'
            }), 400
        
        cache_map[cache_type].clear()
        
        return jsonify({
            'success': True,
            'message': f'{cache_type} 缓存已清空',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500