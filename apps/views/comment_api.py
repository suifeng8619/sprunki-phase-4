from flask import Blueprint, request, jsonify, g
from apps.services.comment_service import CommentService
from apps.models.comment_model import 评论db, 回复
from datetime import datetime
import pytz

# 创建蓝图
comment_api = Blueprint('comment_api', __name__, url_prefix='/api/comments')


def get_request_info():
    """获取请求信息"""
    return {
        'ip': request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR')),
        'user_agent': request.environ.get('HTTP_USER_AGENT', '')
    }


@comment_api.route('/<path:article_url>', methods=['GET'])
def get_comments(article_url):
    """获取评论列表"""
    try:
        # 获取查询参数（去掉lang参数）
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)  # 限制最大50条
        sort_by = request.args.get('sort_by', 'created_at')
        
        # 调用服务获取评论（去掉lang参数）
        result = CommentService.get_comments(
            article_url=article_url,
            page=page,
            per_page=per_page,
            sort_by=sort_by
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['comments'],
                'pagination': result['pagination']
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500


@comment_api.route('/<path:article_url>', methods=['POST'])
def create_comment(article_url):
    """创建新评论"""
    try:
        # 检查请求内容类型
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        
        # 获取请求信息
        request_info = get_request_info()
        
        # 调用服务创建评论
        result = CommentService.create_comment(
            article_url=article_url,
            data=data,
            request_info=request_info
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': {
                    'comment_id': result['comment_id'],
                    'status': result['status']
                }
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': result['message'],
                'errors': result.get('errors', [])
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500


@comment_api.route('/<comment_id>/like', methods=['POST'])
def like_comment(comment_id):
    """点赞评论"""
    try:
        # 调用服务点赞评论
        result = CommentService.like_comment(comment_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': {
                    'likes': result['likes']
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500


@comment_api.route('/<comment_id>/reply', methods=['POST'])
def add_reply(comment_id):
    """添加回复"""
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        
        # 验证必需字段（现在更严格）
        if not data.get('username') or not data.get('content'):
            return jsonify({
                'success': False,
                'message': 'Username and content are required'
            }), 400
        
        # 获取请求信息
        request_info = get_request_info()
        
        # 调用服务添加回复
        result = CommentService.add_reply(
            comment_id=comment_id,
            reply_data=data,
            request_info=request_info
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': {
                    'reply_id': result['reply_id']
                }
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500


@comment_api.route('/<comment_id>/reply/<reply_id>/like', methods=['POST'])
def like_reply(comment_id, reply_id):
    """点赞回复"""
    try:
        # 调用服务点赞回复
        result = CommentService.like_reply(comment_id, reply_id)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': {
                    'likes': result['likes']
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500


@comment_api.route('/<path:article_url>/stats', methods=['GET'])
def get_comment_stats(article_url):
    """获取评论统计"""
    try:
        # 调用服务获取统计信息
        result = CommentService.get_comment_stats(article_url)
        
        if result['success']:
            return jsonify({
                'success': True,
                'data': result['stats']
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500


# 管理员API端点
@comment_api.route('/admin/<comment_id>', methods=['PUT'])
def moderate_comment(comment_id):
    """管理员审核评论"""
    try:
        # 这里应该添加管理员权限检查
        # if not current_user.is_authenticated or 'admin_user' not in current_user.roles:
        #     return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        
        # 验证状态值
        status = data.get('status')
        if status not in ['approved', 'rejected']:
            return jsonify({
                'success': False,
                'message': 'Status must be "approved" or "rejected"'
            }), 400
        
        moderator = data.get('moderated_by', 'admin')  # 实际项目中应该从用户session获取
        
        # 调用服务审核评论
        result = CommentService.moderate_comment(comment_id, status, moderator)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message']
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500


@comment_api.route('/admin/pending', methods=['GET'])
def get_pending_comments():
    """获取待审核评论列表"""
    try:
        # 这里应该添加管理员权限检查
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # 查询待审核评论
        offset = (page - 1) * per_page
        comments = 评论db.objects(status='pending').order_by('-created_at').skip(offset).limit(per_page)
        total = 评论db.objects(status='pending').count()
        
        # 转换为字典格式
        comment_list = []
        for comment in comments:
            comment_dict = {
                'comment_id': comment.comment_id,
                'article_url': comment.article_url,
                'username': comment.username,
                'email': comment.email,
                'content': comment.content,
                'rating': comment.rating,
                'lang': comment.lang or '',  # 显示语言但不强制
                'user_ip': comment.user_ip,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'status': comment.status
            }
            comment_list.append(comment_dict)
        
        return jsonify({
            'success': True,
            'data': comment_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500


# 错误处理
@comment_api.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Endpoint not found'
    }), 404


@comment_api.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'message': 'Method not allowed'
    }), 405 