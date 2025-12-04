#!/usr/bin/env python3
# 性能测试脚本

import time
import requests
from statistics import mean

def test_performance(url, runs=5):
    print(f"\n测试: {url}")
    times = []
    
    for i in range(runs):
        start = time.time()
        try:
            response = requests.get(url, timeout=10)
            end = time.time()
            
            if response.status_code == 200:
                elapsed = (end - start) * 1000
                times.append(elapsed)
                
                # 检查压缩
                encoding = response.headers.get('Content-Encoding', 'none')
                size = len(response.content) / 1024
                
                print(f"  Run {i+1}: {elapsed:.0f}ms, {size:.1f}KB, 编码: {encoding}")
            else:
                print(f"  Run {i+1}: 状态码 {response.status_code}")
        except Exception as e:
            print(f"  Run {i+1}: 错误 - {e}")
    
    if times:
        print(f"  平均: {mean(times):.0f}ms, 最快: {min(times):.0f}ms, 最慢: {max(times):.0f}ms")

print("🔍 开始性能测试...")
print("=" * 50)

# 测试主要页面
test_performance('http://localhost:9028/')
test_performance('http://localhost:9028/static/style/style.css')
test_performance('http://localhost:9028/zh/')

print("\n✅ 测试完成")
