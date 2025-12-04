#!/usr/bin/env python3
"""
修复评论中的单引号转义问题

这个脚本会查找数据库中所有包含 &#x27; 的评论和回复，
并将其替换为正常的单引号 (')
"""

import sys
import os

# 添加应用路径到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from get_app import app
from apps.models.comment_model import 评论db


def fix_comment_quotes():
    """修复评论中的单引号转义问题"""
    try:
        # 获取应用实例以建立数据库连接
        
        with app.app_context():
            print("🔧 开始修复评论中的单引号转义问题...")
            
            # 查找所有包含 &#x27; 的评论
            comments_with_encoded_quotes = 评论db.objects(content__contains='&#x27;')
            comments_count = comments_with_encoded_quotes.count()
            
            print(f"📊 找到 {comments_count} 条包含转义单引号的评论")
            
            if comments_count == 0:
                print("✅ 没有需要修复的评论")
                return
            
            # 修复评论内容
            fixed_comments = 0
            for comment in comments_with_encoded_quotes:
                original_content = comment.content
                # 将 &#x27; 替换为 '
                fixed_content = original_content.replace('&#x27;', "'")
                
                if original_content != fixed_content:
                    comment.content = fixed_content
                    comment.save()
                    fixed_comments += 1
                    print(f"✅ 修复评论 {comment.comment_id}")
                    print(f"   原内容: {original_content[:50]}...")
                    print(f"   新内容: {fixed_content[:50]}...")
            
            # 查找并修复回复中的单引号
            all_comments = 评论db.objects()
            fixed_replies = 0
            
            for comment in all_comments:
                if comment.replies:
                    reply_updated = False
                    for reply in comment.replies:
                        if '&#x27;' in reply.content:
                            original_content = reply.content
                            reply.content = original_content.replace('&#x27;', "'")
                            reply_updated = True
                            fixed_replies += 1
                            print(f"✅ 修复回复 {reply.reply_id}")
                            print(f"   原内容: {original_content[:50]}...")
                            print(f"   新内容: {reply.content[:50]}...")
                    
                    if reply_updated:
                        comment.save()
            
            print(f"\n🎉 修复完成!")
            print(f"   修复评论: {fixed_comments} 条")
            print(f"   修复回复: {fixed_replies} 条")
            print(f"   总计修复: {fixed_comments + fixed_replies} 条")
            
    except Exception as e:
        print(f"❌ 修复过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()


def preview_fixes():
    """预览需要修复的内容（不实际修改）"""
    try:
        
        with app.app_context():
            print("👀 预览需要修复的评论...")
            
            # 查找所有包含 &#x27; 的评论
            comments_with_encoded_quotes = 评论db.objects(content__contains='&#x27;')
            comments_count = comments_with_encoded_quotes.count()
            
            print(f"📊 找到 {comments_count} 条包含转义单引号的评论")
            
            for i, comment in enumerate(comments_with_encoded_quotes[:10]):  # 只显示前10条
                print(f"\n📝 评论 {i+1} (ID: {comment.comment_id})")
                print(f"   用户: {comment.username}")
                print(f"   原内容: {comment.content}")
                fixed_preview = comment.content.replace('&#x27;', "'")
                print(f"   修复后: {fixed_preview}")
            
            if comments_count > 10:
                print(f"\n... 还有 {comments_count - 10} 条评论需要修复")
            
            # 检查回复
            all_comments = 评论db.objects()
            replies_to_fix = 0
            
            for comment in all_comments:
                if comment.replies:
                    for reply in comment.replies:
                        if '&#x27;' in reply.content:
                            replies_to_fix += 1
            
            print(f"\n📊 需要修复的回复: {replies_to_fix} 条")
            
    except Exception as e:
        print(f"❌ 预览过程中出现错误: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        preview_fixes()
    else:
        print("🚀 评论单引号修复工具")
        print("用法:")
        print("  python fix_comment_quotes.py --preview  # 预览需要修复的内容")
        print("  python fix_comment_quotes.py           # 执行修复")
        print()
        
        if len(sys.argv) == 1:
            response = input("确定要修复所有评论中的单引号转义问题吗? (y/N): ")
            if response.lower() in ['y', 'yes']:
                fix_comment_quotes()
            else:
                print("取消修复操作") 