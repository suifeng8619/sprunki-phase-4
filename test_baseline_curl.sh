#!/bin/bash
# 使用curl测试基准性能

echo "🔍 测试优化前的基准性能"
echo "============================================================"

# 测试函数
test_page() {
    local url=$1
    local name=$2
    echo -e "\n测试 $name: $url"
    
    for i in {1..3}; do
        # 使用curl测试，包括时间统计
        curl -w "  Run $i: 总时间: %{time_total}s, 大小: %{size_download} bytes, 编码: %{content_type}\n" \
             -o /dev/null -s "$url"
    done
}

# 测试主要页面
test_page "http://localhost:9028/" "首页"
test_page "http://localhost:9028/static/style/style.css" "CSS文件"
test_page "http://localhost:9028/static/style/fullscreen.js" "JS文件"
test_page "http://localhost:9028/zh/" "中文页面"

echo -e "\n✅ 基准测试完成"