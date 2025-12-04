#!/usr/bin/env python3
"""测试优化前的基准性能"""

import time
import requests
from statistics import mean

def test_performance(url, name, runs=5):
    print(f"\n测试 {name}: {url}")
    times = []
    sizes = []
    
    for i in range(runs):
        start = time.time()
        try:
            response = requests.get(url, timeout=10)
            end = time.time()
            
            if response.status_code == 200:
                elapsed = (end - start) * 1000
                times.append(elapsed)
                size = len(response.content) / 1024
                sizes.append(size)
                
                # 检查是否有压缩
                encoding = response.headers.get('Content-Encoding', 'none')
                cache = response.headers.get('Cache-Control', 'none')
                
                print(f"  Run {i+1}: {elapsed:.0f}ms, {size:.1f}KB, 编码: {encoding}")
            else:
                print(f"  Run {i+1}: 状态码 {response.status_code}")
        except Exception as e:
            print(f"  Run {i+1}: 错误 - {e}")
    
    if times:
        print(f"  平均响应: {mean(times):.0f}ms")
        print(f"  平均大小: {mean(sizes):.1f}KB")
        print(f"  最快/最慢: {min(times):.0f}ms / {max(times):.0f}ms")
        return {
            'avg_time': mean(times),
            'avg_size': mean(sizes),
            'min_time': min(times),
            'max_time': max(times)
        }
    return None

print("🔍 测试优化前的基准性能")
print("=" * 60)

# 保存基准数据
baseline = {}

# 测试主要页面
baseline['home'] = test_performance('http://localhost:9028/', '首页')
baseline['css'] = test_performance('http://localhost:9028/static/style/style.css', 'CSS文件')
baseline['js'] = test_performance('http://localhost:9028/static/style/fullscreen.js', 'JS文件')
baseline['chinese'] = test_performance('http://localhost:9028/zh/', '中文页面')

# 保存基准数据
import json
with open('performance_baseline.json', 'w') as f:
    json.dump(baseline, f, indent=2)

print("\n✅ 基准测试完成，数据已保存到 performance_baseline.json")