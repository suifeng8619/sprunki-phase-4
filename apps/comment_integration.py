"""
评论系统集成模块
用于将评论系统集成到Flask应用中
"""

from flask import Flask
from flask_admin import Admin
from apps.views.comment_api import comment_api
from apps.models.comment_admin import CommentAdminView, CommentStatsView, CommentBatchView
from apps.models.comment_model import 评论db, 评论统计db


def init_comment_system(app: Flask, admin: Admin = None):
    """
    初始化评论系统
    
    Args:
        app: Flask应用实例
        admin: Flask-Admin实例（可选）
    """
    
    # 注册API蓝图
    app.register_blueprint(comment_api)
    
    # 如果提供了admin实例，注册管理后台视图
    if admin:
        # 注册评论管理视图
        admin.add_view(CommentAdminView(
            评论db, 
            name='评论管理', 
            category='评论系统',
            endpoint='comments'
        ))
        
        # 注册评论统计视图
        admin.add_view(CommentStatsView(
            name='评论统计', 
            category='评论系统',
            endpoint='comment_stats'
        ))
        
        # 注册批量操作视图
        admin.add_view(CommentBatchView(
            name='批量操作', 
            category='评论系统',
            endpoint='comment_batch'
        ))
    
    print("✅ 评论系统已成功集成到应用中")
    print("📊 API端点:")
    print("   GET  /api/comments/<article_url> - 获取评论列表")
    print("   POST /api/comments/<article_url> - 创建新评论")
    print("   POST /api/comments/<comment_id>/like - 点赞评论")
    print("   POST /api/comments/<comment_id>/reply - 回复评论")
    print("   GET  /api/comments/<article_url>/stats - 获取评论统计")
    print("   PUT  /api/comments/admin/<comment_id> - 管理员审核评论")
    print("   GET  /api/comments/admin/pending - 获取待审核评论")
    
    if admin:
        print("🔧 管理后台视图已注册:")
        print("   评论管理 - 查看和管理所有评论")
        print("   评论统计 - 查看评论数据统计")
        print("   批量操作 - 批量审核和管理评论") 