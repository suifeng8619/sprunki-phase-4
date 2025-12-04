import re
import uuid
from datetime import datetime, timedelta
import pytz
from flask import request
from mongoengine import Q
from apps.models.comment_model import 评论db, 评论统计db, 回复
from apps.models.article_model import 文章db
from setting import COMMENT_SETTINGS


class CommentService:
    """评论服务类"""
    
    # 从配置文件读取敏感词列表
    SPAM_KEYWORDS = COMMENT_SETTINGS.get('SPAM_KEYWORDS', [
        'spam', 'casino', 'viagra', 'cheap', 'money', 'free', 'click here',
        '广告', '推广', '代理', '投资', '赚钱', '免费', '点击这里'
    ])
    
    @staticmethod
    def create_comment(article_url, data, request_info=None):
        """
        创建新评论
        Args:
            article_url: 文章URL
            data: 评论数据字典
            request_info: 请求信息（IP、User-Agent等）
        Returns:
            dict: 操作结果
        """
        try:
            # 1. 数据验证
            validation_result = CommentService._validate_comment_data(data)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'message': validation_result['message'],
                    'errors': validation_result.get('errors', [])
                }
            
            # 2. 垃圾评论检测
            if CommentService._is_spam_comment(data['content'], data['username']):
                return {
                    'success': False,
                    'message': 'Comment detected as spam'
                }
            
            # 3. 频率限制检查
            if request_info:
                rate_limit_result = CommentService._check_rate_limit(request_info.get('ip'))
                if not rate_limit_result['allowed']:
                    return {
                        'success': False,
                        'message': 'Rate limit exceeded. Please try again later.'
                    }
            
            # 4. 获取文章信息（不再根据语言过滤）
            article = 文章db.objects(article_url=article_url).first()
            if not article:
                # 如果没有找到文章，创建一个虚拟的article_id
                article_id = str(uuid.uuid4())
            else:
                article_id = str(article.id)
            
            # 5. 内容清理
            cleaned_content = CommentService._sanitize_content(data['content'])
            
            # 6. 创建评论对象
            comment = 评论db(
                article_id=article_id,
                article_url=article_url,
                username=data['username'],
                email=data.get('email', ''),
                content=cleaned_content,
                rating=data['rating'],
                lang=data.get('lang', ''),  # 语言字段可选
                user_ip=request_info.get('ip', '') if request_info else '',
                user_agent=request_info.get('user_agent', '') if request_info else ''
            )
            
            # 7. 设置评论状态（根据配置决定是否需要审核）
            if COMMENT_SETTINGS.get('AUTO_APPROVE', False) or not COMMENT_SETTINGS.get('REQUIRE_MODERATION', True):
                comment.status = 'approved'  # 自动批准
            else:
                comment.status = 'pending'   # 需要审核
            
            # 8. 保存评论
            comment.save()
            
            # 9. 更新统计信息
            CommentService.update_statistics(article_url, article_id)
            
            return {
                'success': True,
                'message': 'Comment created successfully',
                'comment_id': comment.comment_id,
                'status': comment.status
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error creating comment: {str(e)}'
            }
    
    @staticmethod
    def get_comments(article_url, page=1, per_page=10, sort_by='created_at'):
        """
        获取评论列表（不再按语言过滤）
        Args:
            article_url: 文章URL
            page: 页码
            per_page: 每页数量
            sort_by: 排序字段
        Returns:
            dict: 评论列表和分页信息
        """
        try:
            # 构建查询条件（根据配置决定是否过滤状态）
            if COMMENT_SETTINGS.get('REQUIRE_MODERATION', True):
                # 需要审核时，只显示已批准的评论
                query = Q(article_url=article_url) & Q(status='approved')
            else:
                # 不需要审核时，显示所有评论（除了被拒绝的）
                query = Q(article_url=article_url) & Q(status__ne='rejected')
            
            # 排序
            sort_field = f'-{sort_by}' if sort_by in ['created_at', 'likes'] else '-created_at'
            
            # 分页查询
            offset = (page - 1) * per_page
            comments = 评论db.objects(query).order_by(sort_field).skip(offset).limit(per_page)
            total = 评论db.objects(query).count()
            
            # 转换为字典格式
            comment_list = []
            for comment in comments:
                comment_dict = {
                    'comment_id': comment.comment_id,
                    'username': comment.username,
                    'content': comment.content,
                    'rating': comment.rating,
                    'likes': comment.likes,
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'lang': comment.lang or '',  # 显示语言信息，但不影响查询
                    'replies': []
                }
                
                # 优化回复查询 - 只加载前几条回复，避免性能问题
                if comment.replies:
                    # 限制显示的回复数量
                    max_replies_to_show = COMMENT_SETTINGS.get('MAX_REPLIES_PER_COMMENT', 5)
                    
                    # 按时间排序，只取前几条
                    sorted_replies = sorted(comment.replies, key=lambda x: x.created_at)[:max_replies_to_show]
                    
                    raw_replies = []
                    for reply in sorted_replies:
                        reply_dict = {
                            'reply_id': reply.reply_id,
                            'username': reply.username,
                            'content': reply.content,
                            'likes': reply.likes,
                            'created_at': reply.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                            'parent_reply_id': reply.parent_reply_id or '',
                            'reply_to_username': reply.reply_to_username or ''
                        }
                        raw_replies.append(reply_dict)
                    
                    comment_dict['replies'] = raw_replies
                    comment_dict['total_replies'] = len(comment.replies)  # 总回复数
                    comment_dict['showing_replies'] = len(raw_replies)    # 当前显示数
                
                comment_list.append(comment_dict)
            
            return {
                'success': True,
                'comments': comment_list,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving comments: {str(e)}'
            }
    
    @staticmethod
    def add_reply(comment_id, reply_data, request_info=None):
        """
        添加回复
        Args:
            comment_id: 评论ID
            reply_data: 回复数据，可包含parent_reply_id和reply_to_username
            request_info: 请求信息
        Returns:
            dict: 操作结果
        """
        try:
            # 查找评论
            comment = 评论db.objects(comment_id=comment_id).first()
            if not comment:
                return {
                    'success': False,
                    'message': 'Comment not found'
                }
            
            # 验证回复数据 - 使用更严格的验证
            validation_result = CommentService._validate_reply_data(reply_data)
            if not validation_result['valid']:
                # 打印调试信息
                print(f"🔍 Validation failed for reply data: {reply_data}")
                print(f"🔍 Validation errors: {validation_result.get('errors', [])}")
                return {
                    'success': False,
                    'message': validation_result['message'] + ': ' + ', '.join(validation_result.get('errors', [])),
                    'errors': validation_result.get('errors', [])
                }
            
            # 垃圾检测（回复也需要检测）
            if CommentService._is_spam_comment(reply_data['content'], reply_data['username']):
                return {
                    'success': False,
                    'message': 'Reply detected as spam'
                }
            
            # 如果是回复其他回复，验证被回复的回复是否存在
            parent_reply_id = reply_data.get('parent_reply_id')
            reply_to_username = reply_data.get('reply_to_username')
            
            if parent_reply_id:
                # 验证被回复的回复是否存在
                parent_reply_exists = any(reply.reply_id == parent_reply_id for reply in comment.replies)
                if not parent_reply_exists:
                    return {
                        'success': False,
                        'message': 'Parent reply not found'
                    }
            
            # 创建回复对象
            reply = 回复(
                username=reply_data['username'],
                content=CommentService._sanitize_content(reply_data['content']),
                user_ip=request_info.get('ip', '') if request_info else '',
                user_agent=request_info.get('user_agent', '') if request_info else '',
                parent_reply_id=parent_reply_id,
                reply_to_username=reply_to_username
            )
            
            # 添加回复到评论
            comment.replies.append(reply)
            comment.save()
            
            return {
                'success': True,
                'message': 'Reply added successfully',
                'reply_id': reply.reply_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error adding reply: {str(e)}'
            }
    
    @staticmethod
    def like_comment(comment_id):
        """
        点赞评论
        Args:
            comment_id: 评论ID
        Returns:
            dict: 操作结果
        """
        try:
            comment = 评论db.objects(comment_id=comment_id).first()
            if not comment:
                return {
                    'success': False,
                    'message': 'Comment not found'
                }
            
            comment.update(inc__likes=1)
            
            return {
                'success': True,
                'message': 'Comment liked',
                'likes': comment.likes + 1
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error liking comment: {str(e)}'
            }
    
    @staticmethod
    def like_reply(comment_id, reply_id):
        """
        点赞回复
        Args:
            comment_id: 评论ID
            reply_id: 回复ID
        Returns:
            dict: 操作结果
        """
        try:
            comment = 评论db.objects(comment_id=comment_id).first()
            if not comment:
                return {
                    'success': False,
                    'message': 'Comment not found'
                }
            
            # 查找并更新回复
            for reply in comment.replies:
                if reply.reply_id == reply_id:
                    reply.likes += 1
                    comment.save()
                    return {
                        'success': True,
                        'message': 'Reply liked',
                        'likes': reply.likes
                    }
            
            return {
                'success': False,
                'message': 'Reply not found'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error liking reply: {str(e)}'
            }
    
    @staticmethod
    def get_comment_stats(article_url):
        """
        获取评论统计
        Args:
            article_url: 文章URL
        Returns:
            dict: 统计信息
        """
        try:
            stats = 评论统计db.objects(article_url=article_url).first()
            
            if not stats:
                return {
                    'success': True,
                    'stats': {
                        'total_comments': 0,
                        'average_rating': 0.0,
                        'rating_distribution': {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0}
                    }
                }
            
            return {
                'success': True,
                'stats': {
                    'total_comments': stats.total_comments,
                    'average_rating': round(stats.average_rating, 1),
                    'rating_distribution': stats.rating_distribution
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error retrieving stats: {str(e)}'
            }
    
    @staticmethod
    def moderate_comment(comment_id, status, moderator):
        """
        审核评论
        Args:
            comment_id: 评论ID
            status: 新状态 (approved/rejected)
            moderator: 审核员
        Returns:
            dict: 操作结果
        """
        try:
            comment = 评论db.objects(comment_id=comment_id).first()
            if not comment:
                return {
                    'success': False,
                    'message': 'Comment not found'
                }
            
            old_status = comment.status
            comment.status = status
            comment.moderated_by = moderator
            comment.moderated_at = datetime.now(pytz.timezone('Asia/Shanghai'))
            comment.save()
            
            # 如果状态发生变化，更新统计信息
            if old_status != status:
                CommentService.update_statistics(comment.article_url, comment.article_id)
            
            return {
                'success': True,
                'message': f'Comment {status} successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error moderating comment: {str(e)}'
            }
    
    @staticmethod
    def update_statistics(article_url, article_id):
        """
        更新评论统计（不再按语言区分）
        Args:
            article_url: 文章URL
            article_id: 文章ID
        """
        try:
            # 查询该文章的所有已审核评论（不再按语言过滤）
            comments = 评论db.objects(article_url=article_url, status='approved')
            
            total_comments = comments.count()
            
            if total_comments == 0:
                # 如果没有评论，删除统计记录或设置为0
                评论统计db.objects(article_url=article_url).delete()
                return
            
            # 计算平均评分
            total_rating = sum(comment.rating for comment in comments)
            average_rating = total_rating / total_comments
            
            # 计算评分分布
            rating_distribution = {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0}
            for comment in comments:
                rating_distribution[str(comment.rating)] += 1
            
            # 更新或创建统计记录
            评论统计db.objects(article_url=article_url).update_one(
                set__article_id=article_id,
                set__total_comments=total_comments,
                set__average_rating=average_rating,
                set__rating_distribution=rating_distribution,
                set__last_updated=datetime.now(pytz.timezone('Asia/Shanghai')),
                upsert=True
            )
            
        except Exception as e:
            print(f"Error updating statistics: {str(e)}")
    
    @staticmethod
    def _validate_comment_data(data):
        """验证评论数据（去掉语言必需验证）"""
        errors = []
        
        # 检查必需字段（添加email）
        required_fields = ['username', 'email', 'content', 'rating']
        for field in required_fields:
            if not data.get(field):
                errors.append(f'{field} is required')
        
        # 用户名长度检查
        if data.get('username') and len(data['username']) > 50:
            errors.append('Username too long (max 50 characters)')
        
        # 用户名格式检查
        if data.get('username') and not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5\u3040-\u309f\u30a0-\u30ff\s]+$', data['username']):
            errors.append('Username contains invalid characters')
        
        # 内容长度检查
        if data.get('content'):
            if len(data['content']) < 10:
                errors.append('Content too short (min 10 characters)')
            elif len(data['content']) > 1000:
                errors.append('Content too long (max 1000 characters)')
        
        # 评分检查
        if data.get('rating'):
            try:
                rating = int(data['rating'])
                if rating < 1 or rating > 5:
                    errors.append('Rating must be between 1 and 5')
            except (ValueError, TypeError):
                errors.append('Rating must be a number')
        
        # 邮箱格式检查（必填）
        if data.get('email'):
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, data['email']):
                errors.append('Invalid email format')
        
        return {
            'valid': len(errors) == 0,
            'message': 'Validation passed' if len(errors) == 0 else 'Validation failed',
            'errors': errors
        }
    
    @staticmethod
    def _validate_reply_data(data):
        """验证回复数据 - 更严格的验证"""
        errors = []
        
        # 检查必需字段
        required_fields = ['username', 'content']
        for field in required_fields:
            if not data.get(field):
                errors.append(f'{field} is required')
        
        # 用户名长度检查
        if data.get('username'):
            if len(data['username']) > COMMENT_SETTINGS.get('MAX_USERNAME_LENGTH', 50):
                errors.append(f'Username too long (max {COMMENT_SETTINGS.get("MAX_USERNAME_LENGTH", 50)} characters)')
            elif len(data['username']) < 2:
                errors.append('Username too short (min 2 characters)')
        
        # 用户名格式检查
        if data.get('username') and not re.match(r'^[a-zA-Z0-9_\u4e00-\u9fa5\u3040-\u309f\u30a0-\u30ff\s]+$', data['username']):
            errors.append('Username contains invalid characters')
        
        # 内容长度检查
        if data.get('content'):
            min_length = COMMENT_SETTINGS.get('MIN_CONTENT_LENGTH', 10)
            max_length = COMMENT_SETTINGS.get('MAX_REPLY_LENGTH', 500)
            if len(data['content']) < min_length:
                errors.append(f'Content too short (min {min_length} characters)')
            elif len(data['content']) > max_length:
                errors.append(f'Content too long (max {max_length} characters)')
        
        # 邮箱格式检查（可选，但如果提供了必须格式正确）
        if data.get('email'):
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, data['email']):
                errors.append('Invalid email format')
        
        return {
            'valid': len(errors) == 0,
            'message': 'Validation passed' if len(errors) == 0 else 'Validation failed',
            'errors': errors
        }
    
    @staticmethod
    def _is_spam_comment(content, username):
        """垃圾评论检测"""
        # 如果禁用了垃圾检测，直接返回False
        if not COMMENT_SETTINGS.get('ENABLE_SPAM_DETECTION', True):
            return False
            
        content_lower = content.lower()
        username_lower = username.lower()
        
        # 检查敏感词（如果启用）
        if COMMENT_SETTINGS.get('SPAM_KEYWORD_CHECK', True):
            for keyword in CommentService.SPAM_KEYWORDS:
                if keyword.lower() in content_lower or keyword.lower() in username_lower:
                    return True
        
        # 检查重复字符（使用配置的阈值）
        char_repeat_threshold = COMMENT_SETTINGS.get('SPAM_CHAR_REPEAT_THRESHOLD', 0.3)
        if len(content) > 0 and len(set(content)) / len(content) < char_repeat_threshold:
            return True
        
        return False
    
    @staticmethod
    def _check_rate_limit(ip_address):
        """频率限制检查"""
        if not ip_address:
            return {'allowed': True}
        
        # 简单的频率限制：每IP每分钟最多5条评论
        try:
            one_minute_ago = datetime.now(pytz.timezone('Asia/Shanghai')) - timedelta(minutes=1)
            recent_comments = 评论db.objects(
                user_ip=ip_address,
                created_at__gte=one_minute_ago
            ).count()
            
            return {
                'allowed': recent_comments < 5,
                'remaining': max(0, 5 - recent_comments)
            }
        except:
            return {'allowed': True}
    
    @staticmethod
    def _sanitize_content(content):
        """内容清理"""
        # 只转义危险的HTML字符，保留常用标点符号如单引号
        content = content.replace('&', '&amp;')  # 必须最先处理
        content = content.replace('<', '&lt;')
        content = content.replace('>', '&gt;')
        content = content.replace('"', '&quot;')
        # 注意：不转义单引号 (') 以保持用户输入的自然性
        
        # 移除多余空格
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content
    
    @staticmethod
    def _organize_replies_hierarchy(replies):
        """
        将回复组织为扁平结构，按时间排序
        Args:
            replies: 原始回复列表
        Returns:
            list: 扁平化的回复列表
        """
        # 直接按时间排序所有回复
        return sorted(replies, key=lambda x: x['created_at']) 