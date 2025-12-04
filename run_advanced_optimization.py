#!/usr/bin/env python3
"""
在Flask应用内运行高级优化
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from get_app import app
from advanced_db_optimizer import optimize_database_advanced

def run_optimization():
    """在Flask应用上下文中运行优化"""
    with app.app_context():
        print("🚀 在Flask应用内执行高级数据库优化...")
        
        success = optimize_database_advanced()
        
        if success:
            print("✅ 高级优化在Flask应用内完成成功！")
        else:
            print("❌ 高级优化失败")

if __name__ == "__main__":
    run_optimization()