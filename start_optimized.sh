#!/bin/bash
# 生产环境启动脚本

echo "🚀 启动Sprunki Phase 4 (优化版)..."

# 检查端口是否被占用
if lsof -Pi :9028 -sTCP:LISTEN -t >/dev/null ; then
    echo "❌ 端口 9028 已被占用"
    echo "运行 'lsof -i :9028' 查看占用进程"
    exit 1
fi

# 使用Gunicorn启动
echo "✅ 使用Gunicorn启动应用..."
gunicorn run:app -c gunicorn_config.py

# 如果Gunicorn失败，回退到开发服务器
if [ $? -ne 0 ]; then
    echo "⚠️  Gunicorn启动失败，使用开发服务器..."
    python run.py
fi
