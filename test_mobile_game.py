#!/usr/bin/env python3
"""
移动端游戏加载测试
"""

import requests
import time

def test_mobile_game_elements():
    print("🔧 测试移动端游戏元素...")
    print("=" * 40)
    
    url = "http://localhost:9028/sprunki.html"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"❌ 页面加载失败: {response.status_code}")
            return False
            
        content = response.text
        
        # 检查关键元素
        checks = {
            "游戏iframe": 'id="game_iframe"' in content,
            "游戏介绍区": 'id="game_intro"' in content,
            "PLAY按钮": 'onclick="playGameWithAudio()"' in content,
            "临时修复": '临时playGame函数' in content,
            "playGameWithAudio函数": 'window.playGameWithAudio' in content,
            "动态脚本加载": 'fullscreen.js' in content
        }
        
        print("📋 关键元素检查:")
        all_good = True
        for name, found in checks.items():
            status = "✅" if found else "❌"
            print(f"  {status} {name}: {'存在' if found else '缺失'}")
            if not found:
                all_good = False
        
        # 检查iframe src
        if 'src="https://img.sprunki.net/game/index.html"' in content:
            print(f"  ✅ iframe源地址: 正确")
        else:
            print(f"  ❌ iframe源地址: 异常")
            all_good = False
            
        # 检查CSS类
        if 'class="hidden"' in content:
            print(f"  ✅ 隐藏类: 正确设置")
        else:
            print(f"  ❌ 隐藏类: 缺失")
            all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_mobile_scripts():
    print("\n📱 测试移动端脚本加载...")
    print("=" * 40)
    
    script_files = [
        "/style/fullscreen.js",
        "/style/native-fullscreen.js", 
        "/js/game-status-bar.js"
    ]
    
    base_url = "http://localhost:9028"
    all_scripts_ok = True
    
    for script_path in script_files:
        try:
            url = base_url + script_path
            response = requests.head(url, timeout=5)
            
            if response.status_code == 200:
                size = response.headers.get('Content-Length', '未知')
                print(f"  ✅ {script_path}: {response.status_code} ({size} bytes)")
            else:
                print(f"  ❌ {script_path}: {response.status_code}")
                all_scripts_ok = False
                
        except Exception as e:
            print(f"  ❌ {script_path}: 加载失败 - {e}")
            all_scripts_ok = False
    
    return all_scripts_ok

def main():
    print("🔧 移动端游戏问题诊断")
    print("=" * 50)
    
    # 测试页面元素
    elements_ok = test_mobile_game_elements()
    
    # 测试脚本文件
    scripts_ok = test_mobile_scripts()
    
    print(f"\n🎯 诊断结果:")
    print(f"  页面元素: {'✅ 正常' if elements_ok else '❌ 异常'}")
    print(f"  脚本文件: {'✅ 正常' if scripts_ok else '❌ 异常'}")
    
    if elements_ok and scripts_ok:
        print(f"\n💡 建议:")
        print(f"  - 临时修复已添加，移动端应该能正常启动游戏")
        print(f"  - 如果仍有问题，可能是iOS特定的兼容性问题")
        print(f"  - 请在移动设备上测试PLAY按钮功能")
    else:
        print(f"\n⚠️  发现问题，需要进一步修复")
    
    return elements_ok and scripts_ok

if __name__ == "__main__":
    main()