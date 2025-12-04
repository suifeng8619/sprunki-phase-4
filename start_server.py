#!/usr/bin/env python3
"""
简单的Flask服务器启动脚本
"""
import os
import sys

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 直接导入run模块来确保所有路由都被注册
import run

if __name__ == '__main__':
    print("🚀 正在启动Flask服务器...")
    print("📍 访问地址: http://127.0.0.1:9028")
    print("📍 中文页面: http://127.0.0.1:9028/zh/")
    print("📍 日文页面: http://127.0.0.1:9028/ja/")
    print("📍 管理后台: http://127.0.0.1:9028/admin/")
    print("⚠️  按 Ctrl+C 停止服务器")
    
    try:
        run.app.run(
            host='127.0.0.1',
            port=9028,
            debug=True,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")