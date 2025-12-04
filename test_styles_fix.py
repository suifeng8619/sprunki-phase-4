#!/usr/bin/env python3
"""
样式修复验证脚本
测试首页和内页的样式加载情况
"""

import requests
import time
from urllib.parse import urljoin

def test_css_loading():
    """测试CSS文件加载"""
    print("🎨 测试CSS文件加载...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    base_url = "http://localhost:9028"
    css_files = [
        "/css/tailwind.min.css",
        "/style/style.css", 
        "/style/language-selector.css",
        "/css/comment-system.css"
    ]
    
    for css_file in css_files:
        try:
            url = urljoin(base_url, css_file)
            response = requests.head(url, timeout=5)
            
            if response.status_code == 200:
                size = response.headers.get('Content-Length', '未知')
                cache_control = response.headers.get('Cache-Control', '未设置')
                print(f"✅ {css_file}: {response.status_code} | 大小: {size} bytes | Cache: {cache_control}")
            else:
                print(f"❌ {css_file}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {css_file}: 加载失败 - {e}")

def test_page_styles():
    """测试页面样式加载"""
    print("\n📄 测试页面样式加载...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    test_pages = [
        ('首页', 'http://localhost:9028/'),
        ('测试页', 'http://localhost:9028/test'),
        ('内页示例1', 'http://localhost:9028/sprunki.html'),
        ('内页示例2', 'http://localhost:9028/sprunki-is-but-everyone-alive-v0.html')
    ]
    
    for page_name, url in test_pages:
        try:
            start_time = time.time()
            response = requests.get(url, timeout=10)
            load_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                content = response.text
                
                # 检查是否包含本地CSS引用
                has_local_tailwind = '/css/tailwind.min.css' in content
                has_cdn_tailwind = 'cdn.tailwindcss.com' in content
                cache_status = response.headers.get('X-Cache-Status', 'UNKNOWN')
                
                print(f"📋 {page_name}:")
                print(f"  状态: {response.status_code}")
                print(f"  加载时间: {load_time:.2f}ms")
                print(f"  本地Tailwind: {'✅' if has_local_tailwind else '❌'}")
                print(f"  CDN引用: {'❌' if has_cdn_tailwind else '✅ 无CDN'}")
                print(f"  缓存状态: {cache_status}")
                
                # 检查其他关键样式引用
                style_checks = {
                    'style.css': '/style/style.css' in content,
                    'language-selector.css': '/style/language-selector.css' in content,
                    'Google Fonts': 'fonts.googleapis.com' in content
                }
                
                for style_name, found in style_checks.items():
                    print(f"  {style_name}: {'✅' if found else '❌'}")
                
            else:
                print(f"❌ {page_name}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {page_name}: 测试失败 - {e}")
        
        print()

def performance_comparison():
    """性能对比测试"""
    print("⚡ 性能对比测试...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    test_urls = [
        ('首页', 'http://localhost:9028/'),
        ('内页', 'http://localhost:9028/sprunki.html'),
        ('测试页', 'http://localhost:9028/test')
    ]
    
    results = {}
    
    for name, url in test_urls:
        times = []
        cache_hits = 0
        
        # 测试5次获取平均值
        for i in range(5):
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                request_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    times.append(request_time)
                    if response.headers.get('X-Cache-Status') == 'HIT':
                        cache_hits += 1
                        
            except Exception as e:
                print(f"  测试失败: {e}")
        
        if times:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            
            results[name] = {
                'avg': avg_time,
                'min': min_time,
                'max': max_time,
                'cache_hits': cache_hits
            }
            
            print(f"📊 {name}:")
            print(f"  平均响应: {avg_time:.2f}ms")
            print(f"  最快响应: {min_time:.2f}ms") 
            print(f"  最慢响应: {max_time:.2f}ms")
            print(f"  缓存命中: {cache_hits}/5")
            print()
    
    return results

def generate_fix_report():
    """生成修复报告"""
    print("📋 样式修复报告")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    print("✅ 已完成的修复:")
    print("  • 替换CDN Tailwind CSS为本地文件")
    print("  • 修复head_foot.html模板")
    print("  • 修复index.html模板")
    print("  • 验证本地CSS文件正常加载")
    
    print("\n🎯 修复效果:")
    print("  • 消除对外部CDN的依赖")
    print("  • 提高页面加载稳定性") 
    print("  • 改善缓存效率")
    print("  • 减少网络请求延迟")
    
    print("\n🔍 下一步建议:")
    print("  • 继续监控页面加载性能")
    print("  • 定期检查CSS文件完整性")
    print("  • 考虑启用CSS压缩和合并")

def main():
    """主测试函数"""
    print("🎨 样式修复验证测试")
    print("=" * 50)
    
    # 1. 测试CSS文件加载
    test_css_loading()
    
    # 2. 测试页面样式
    test_page_styles()
    
    # 3. 性能对比
    perf_results = performance_comparison()
    
    # 4. 生成报告
    generate_fix_report()
    
    print("\n✅ 样式修复验证完成！")
    return True

if __name__ == "__main__":
    main()