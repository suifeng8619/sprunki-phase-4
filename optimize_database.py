#!/usr/bin/env python3
"""
数据库索引优化脚本
安全地检查和创建性能优化索引
"""

import sys
import time
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import OperationFailure

# 导入项目配置
from setting import mongo_uri
from get_app import app

# 确保在导入模型前先建立数据库连接
with app.app_context():
    from apps.models.article_model import 文章db

def print_status(message, status="INFO"):
    """打印带时间戳的状态信息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_symbols = {
        "INFO": "ℹ️",
        "SUCCESS": "✅", 
        "WARNING": "⚠️",
        "ERROR": "❌"
    }
    symbol = status_symbols.get(status, "ℹ️")
    print(f"[{timestamp}] {symbol} {message}")

def check_existing_indexes():
    """检查现有索引"""
    print_status("检查现有数据库索引...")
    
    try:
        # 获取文章集合
        collection = 文章db._get_collection()
        
        # 列出所有现有索引
        indexes = list(collection.list_indexes())
        
        print_status("现有索引列表:")
        for idx in indexes:
            index_name = idx.get('name', 'unnamed')
            index_keys = idx.get('key', {})
            print(f"  📋 {index_name}: {dict(index_keys)}")
        
        return indexes
        
    except Exception as e:
        print_status(f"检查索引失败: {e}", "ERROR")
        return []

def check_index_exists(indexes, target_fields):
    """检查目标索引是否已存在"""
    target_set = set(target_fields)
    
    for idx in indexes:
        index_keys = idx.get('key', {})
        index_fields = [field for field, _ in index_keys.items()]
        
        if set(index_fields) == target_set:
            return True, idx.get('name', 'unnamed')
    
    return False, None

def create_optimized_indexes():
    """创建优化索引"""
    print_status("开始创建优化索引...")
    
    try:
        # 检查现有索引
        existing_indexes = check_existing_indexes()
        
        # 目标索引：(ids, 状态) 用于文章查询优化
        target_fields = ['ids', '状态']
        index_exists, existing_name = check_index_exists(existing_indexes, target_fields)
        
        if index_exists:
            print_status(f"索引已存在: {existing_name}，跳过创建", "WARNING")
            return True
        
        # 创建新索引
        collection = 文章db._get_collection()
        
        print_status("创建索引: (ids, 状态)...")
        
        # 后台创建索引，不阻塞应用
        result = collection.create_index(
            [("ids", 1), ("状态", 1)],
            background=True,  # 后台创建，关键！
            name="idx_ids_status_opt"
        )
        
        print_status(f"索引创建成功: {result}", "SUCCESS")
        
        # 验证索引创建
        time.sleep(2)  # 等待索引创建完成
        new_indexes = check_existing_indexes()
        
        # 确认新索引存在
        index_created, new_name = check_index_exists(new_indexes, target_fields)
        if index_created:
            print_status(f"索引验证成功: {new_name}", "SUCCESS")
            return True
        else:
            print_status("索引验证失败", "ERROR")
            return False
            
    except OperationFailure as e:
        print_status(f"索引创建失败: {e}", "ERROR")
        return False
    except Exception as e:
        print_status(f"未知错误: {e}", "ERROR")
        return False

def test_query_performance():
    """测试查询性能"""
    print_status("测试查询性能...")
    
    try:
        # 测试查询
        start_time = time.time()
        
        # 执行典型查询
        article = 文章db.objects(ids=1, 状态='发布').first()
        
        query_time = (time.time() - start_time) * 1000  # 转换为毫秒
        
        if article:
            print_status(f"查询测试成功，耗时: {query_time:.2f}ms", "SUCCESS")
        else:
            print_status(f"查询测试完成（无匹配数据），耗时: {query_time:.2f}ms", "INFO")
        
        return query_time
        
    except Exception as e:
        print_status(f"查询测试失败: {e}", "ERROR")
        return None

def main():
    """主函数"""
    print_status("=== 数据库优化开始 ===")
    print_status(f"连接数据库: {mongo_uri.split('@')[-1] if '@' in mongo_uri else mongo_uri}")
    
    # 检查数据库连接
    try:
        with app.app_context():
            # 测试连接
            文章db.objects().count()
            print_status("数据库连接成功", "SUCCESS")
    except Exception as e:
        print_status(f"数据库连接失败: {e}", "ERROR")
        return False
    
    # 性能基准测试
    print_status("=== 优化前性能基准 ===")
    before_time = test_query_performance()
    
    # 创建索引
    print_status("=== 创建优化索引 ===")
    success = create_optimized_indexes()
    
    if not success:
        print_status("索引创建失败，停止优化", "ERROR")
        return False
    
    # 优化后性能测试
    print_status("=== 优化后性能测试 ===")
    after_time = test_query_performance()
    
    # 性能对比
    if before_time and after_time:
        improvement = ((before_time - after_time) / before_time) * 100
        print_status(f"查询性能提升: {improvement:.1f}% ({before_time:.2f}ms → {after_time:.2f}ms)", "SUCCESS")
    
    print_status("=== 数据库优化完成 ===", "SUCCESS")
    print_status("下一步：运行 'python run.py' 测试应用性能")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_status("用户中断操作", "WARNING")
        sys.exit(1)
    except Exception as e:
        print_status(f"脚本执行失败: {e}", "ERROR")
        sys.exit(1)