from flask_admin.contrib.mongoengine import ModelView
from flask_admin import BaseView, expose
from flask import request, redirect, url_for, flash, jsonify
from flask_login import current_user
from wtforms import SelectField, TextAreaField
from wtforms.validators import DataRequired
from apps.models.comment_model import 评论db, 评论统计db
from apps.services.comment_service import CommentService
from datetime import datetime, timedelta
import pytz


class CommentAdminView(ModelView):
    """评论管理视图"""
    
    # 权限检查
    def is_accessible(self):
        return current_user.is_authenticated and 'admin_user' in current_user.roles

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login'))
    
    # 列表视图配置
    column_list = [
        'username', 'article_url', 'content', 'rating', 
        'status', 'lang', 'created_at', 'likes'
    ]
    
    column_searchable_list = ['username', 'content', 'article_url', 'email']
    
    column_filters = [
        'status', 'lang', 'rating', 'created_at', 
        'article_url', 'username'
    ]
    
    column_sortable_list = [
        'username', 'created_at', 'rating', 'likes', 'status'
    ]
    
    # 分页设置
    page_size = 20
    
    # 列显示格式
    column_formatters = {
        'content': lambda v, c, m, p: (m.content[:50] + '...') if len(m.content) > 50 else m.content,
        'created_at': lambda v, c, m, p: m.created_at.strftime('%Y-%m-%d %H:%M') if m.created_at else '',
        'article_url': lambda v, c, m, p: (m.article_url[:30] + '...') if len(m.article_url) > 30 else m.article_url
    }
    
    # 列标签
    column_labels = {
        'username': '用户名',
        'article_url': '文章URL',
        'content': '评论内容',
        'rating': '评分',
        'status': '状态',
        'lang': '语言',
        'created_at': '创建时间',
        'likes': '点赞数',
        'email': '邮箱',
        'user_ip': 'IP地址',
        'moderated_by': '审核员',
        'moderated_at': '审核时间'
    }
    
    # 状态选择
    form_choices = {
        'status': [
            ('pending', '待审核'),
            ('approved', '已通过'),
            ('rejected', '已拒绝')
        ]
    }
    
    # 表单字段
    form_excluded_columns = ['comment_id', 'user_agent', 'replies', 'updated_at']
    
    # 详情视图字段
    column_details_list = [
        'comment_id', 'username', 'email', 'article_url', 
        'content', 'rating', 'status', 'lang', 'likes',
        'user_ip', 'user_agent', 'created_at', 'updated_at',
        'moderated_by', 'moderated_at', 'replies'
    ]
    
    # 批量操作
    column_default_sort = ('created_at', True)  # 默认按创建时间倒序
    
    def on_model_change(self, form, model, is_created):
        """模型变更时的钩子 - 更新统计信息"""
        if not is_created:
            # 如果状态发生变化，更新统计信息
            CommentService.update_statistics(model.article_url, model.article_id)
            
            # 记录审核信息
            if hasattr(current_user, 'name'):
                model.moderated_by = current_user.name
                model.moderated_at = datetime.now(pytz.timezone('Asia/Shanghai'))
    
    def delete_model(self, model):
        """删除模型后更新统计"""
        article_url = model.article_url
        article_id = model.article_id
        result = super().delete_model(model)
        
        # 更新统计信息
        CommentService.update_statistics(article_url, article_id)
        return result


class CommentStatsView(BaseView):
    """评论统计视图"""
    
    def is_accessible(self):
        return current_user.is_authenticated and 'admin_user' in current_user.roles

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login'))
    
    @expose('/')
    def index(self):
        """评论统计首页"""
        # 获取总体统计
        total_comments = 评论db.objects.count()
        pending_comments = 评论db.objects(status='pending').count()
        approved_comments = 评论db.objects(status='approved').count()
        rejected_comments = 评论db.objects(status='rejected').count()
        
        # 最近7天的评论趋势
        seven_days_ago = datetime.now(pytz.timezone('Asia/Shanghai')) - timedelta(days=7)
        recent_comments = 评论db.objects(created_at__gte=seven_days_ago).count()
        
        # 平均评分
        all_approved = 评论db.objects(status='approved')
        if all_approved.count() > 0:
            avg_rating = sum(c.rating for c in all_approved) / all_approved.count()
        else:
            avg_rating = 0
        
        # 热门文章（评论最多）
        from collections import Counter
        article_counts = Counter()
        for comment in 评论db.objects(status='approved'):
            article_counts[comment.article_url] += 1
        
        popular_articles = article_counts.most_common(10)
        
        # 语言分布
        lang_counts = Counter()
        for comment in 评论db.objects(status='approved'):
            lang_counts[comment.lang] += 1
        
        stats = {
            'total_comments': total_comments,
            'pending_comments': pending_comments,
            'approved_comments': approved_comments,
            'rejected_comments': rejected_comments,
            'recent_comments': recent_comments,
            'avg_rating': round(avg_rating, 2),
            'popular_articles': popular_articles,
            'lang_distribution': dict(lang_counts)
        }
        
        return self.render('admin/comment_stats.html', stats=stats)
    
    @expose('/pending')
    def pending_comments(self):
        """待审核评论"""
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        comments = 评论db.objects(status='pending').order_by('-created_at').paginate(
            page=page, per_page=per_page
        )
        
        return self.render('admin/pending_comments.html', comments=comments)
    
    @expose('/approve/<comment_id>')
    def approve_comment(self, comment_id):
        """批准评论"""
        moderator = current_user.name if hasattr(current_user, 'name') else 'admin'
        result = CommentService.moderate_comment(comment_id, 'approved', moderator)
        
        if result['success']:
            flash('评论已批准', 'success')
        else:
            flash(f'操作失败: {result["message"]}', 'error')
        
        return redirect(url_for('.pending_comments'))
    
    @expose('/reject/<comment_id>')
    def reject_comment(self, comment_id):
        """拒绝评论"""
        moderator = current_user.name if hasattr(current_user, 'name') else 'admin'
        result = CommentService.moderate_comment(comment_id, 'rejected', moderator)
        
        if result['success']:
            flash('评论已拒绝', 'success')
        else:
            flash(f'操作失败: {result["message"]}', 'error')
        
        return redirect(url_for('.pending_comments'))


class CommentBatchView(BaseView):
    """批量操作视图"""
    
    def is_accessible(self):
        return current_user.is_authenticated and 'admin_user' in current_user.roles

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin_login'))
    
    @expose('/')
    def index(self):
        """批量操作首页"""
        return self.render('admin/comment_batch.html')
    
    @expose('/batch-approve', methods=['POST'])
    def batch_approve(self):
        """批量批准评论"""
        comment_ids = request.form.getlist('comment_ids')
        moderator = current_user.name if hasattr(current_user, 'name') else 'admin'
        
        success_count = 0
        for comment_id in comment_ids:
            result = CommentService.moderate_comment(comment_id, 'approved', moderator)
            if result['success']:
                success_count += 1
        
        flash(f'成功批准 {success_count} 条评论', 'success')
        return redirect(url_for('commentstatsview.pending_comments'))
    
    @expose('/batch-reject', methods=['POST'])
    def batch_reject(self):
        """批量拒绝评论"""
        comment_ids = request.form.getlist('comment_ids')
        moderator = current_user.name if hasattr(current_user, 'name') else 'admin'
        
        success_count = 0
        for comment_id in comment_ids:
            result = CommentService.moderate_comment(comment_id, 'rejected', moderator)
            if result['success']:
                success_count += 1
        
        flash(f'成功拒绝 {success_count} 条评论', 'success')
        return redirect(url_for('commentstatsview.pending_comments'))
    
    @expose('/clean-spam', methods=['POST'])
    def clean_spam(self):
        """清理垃圾评论"""
        # 获取所有待审核的评论
        pending_comments = 评论db.objects(status='pending')
        spam_count = 0
        
        for comment in pending_comments:
            # 使用垃圾检测算法
            if CommentService._is_spam_comment(comment.content, comment.username):
                comment.status = 'rejected'
                comment.moderated_by = 'auto-spam-filter'
                comment.moderated_at = datetime.now(pytz.timezone('Asia/Shanghai'))
                comment.save()
                spam_count += 1
        
        flash(f'自动清理了 {spam_count} 条垃圾评论', 'success')
        return redirect(url_for('.index')) 