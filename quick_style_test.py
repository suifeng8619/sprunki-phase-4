#!/usr/bin/env python3
"""
快速样式测试 - 验证修复后的CSS加载
"""

import requests
import time

def quick_test():
    print("🔥 紧急样式修复验证")
    print("=" * 40)
    
    # 测试关键页面
    pages = [
        ("首页", "http://localhost:9028/"),
        ("内页1", "http://localhost:9028/sprunki.html"),
        ("内页2", "http://localhost:9028/sprunki-is-but-everyone-alive-v0.html")
    ]
    
    for name, url in pages:
        try:
            response = requests.get(url, timeout=5)
            content = response.text
            
            # 检查关键CSS文件
            css_checks = {
                "Tailwind": "/css/tailwind.min.css" in content,
                "Style.css": "/style/style.css" in content,
                "Language": "/style/language-selector.css" in content
            }
            
            print(f"\n📄 {name}:")
            print(f"  状态: {response.status_code}")
            for css_name, found in css_checks.items():
                print(f"  {css_name}: {'✅' if found else '❌'}")
                
        except Exception as e:
            print(f"❌ {name}: {e}")
    
    # 测试CSS文件是否可访问
    print(f"\n🎨 CSS文件可访问性:")
    css_files = [
        "/css/tailwind.min.css",
        "/style/style.css", 
        "/style/language-selector.css"
    ]
    
    for css_file in css_files:
        try:
            url = f"http://localhost:9028{css_file}"
            response = requests.head(url, timeout=3)
            size = response.headers.get('Content-Length', '未知')
            print(f"  {css_file}: {response.status_code} ({size} bytes)")
        except Exception as e:
            print(f"  {css_file}: ❌ {e}")

if __name__ == "__main__":
    quick_test()