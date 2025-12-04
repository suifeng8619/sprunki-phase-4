#!/usr/bin/env python3
"""
性能监控脚本
实时监控网站性能指标，验证优化效果
"""

import time
import requests
import statistics
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os

class PerformanceMonitor:
    def __init__(self, base_url="http://localhost:9028"):
        self.base_url = base_url
        self.results = []
        self.session = requests.Session()
        
        # 设置合理的超时和重试
        self.session.timeout = 10
        
    def print_status(self, message, status="INFO"):
        """打印带时间戳的状态信息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_symbols = {
            "INFO": "ℹ️",
            "SUCCESS": "✅", 
            "WARNING": "⚠️",
            "ERROR": "❌",
            "MONITOR": "📊"
        }
        symbol = status_symbols.get(status, "ℹ️")
        print(f"[{timestamp}] {symbol} {message}")

    def test_single_request(self, url_path="/", test_name="首页"):
        """测试单个请求的性能"""
        url = f"{self.base_url}{url_path}"
        
        try:
            start_time = time.time()
            response = self.session.get(url, timeout=10)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # 转换为毫秒
            
            result = {
                'test_name': test_name,
                'url': url,
                'status_code': response.status_code,
                'response_time_ms': response_time,
                'content_length': len(response.content),
                'timestamp': datetime.now().isoformat(),
                'success': response.status_code == 200
            }
            
            # 检查响应内容
            if response.status_code == 200:
                if len(response.content) < 1000:
                    result['warning'] = "响应内容过短，可能有错误"
                
                # 检查是否包含关键内容
                content_text = response.text.lower()
                if 'error' in content_text or 'traceback' in content_text:
                    result['warning'] = "响应包含错误信息"
            
            return result
            
        except requests.exceptions.Timeout:
            return {
                'test_name': test_name,
                'url': url,
                'error': 'Timeout',
                'response_time_ms': 10000,  # 超时记为10秒
                'timestamp': datetime.now().isoformat(),
                'success': False
            }
        except Exception as e:
            return {
                'test_name': test_name,
                'url': url,
                'error': str(e),
                'response_time_ms': None,
                'timestamp': datetime.now().isoformat(),
                'success': False
            }

    def test_multiple_endpoints(self):
        """测试多个端点的性能"""
        test_cases = [
            ("/", "首页"),
            ("/test", "测试页面"),
            ("/1.html", "文章页面(ID=1)"),
            ("/ja/1.html", "日语文章页面"),
            ("/zh/1.html", "中文文章页面"),
        ]
        
        results = []
        
        self.print_status("开始多端点性能测试...", "MONITOR")
        
        for url_path, test_name in test_cases:
            result = self.test_single_request(url_path, test_name)
            results.append(result)
            
            if result['success']:
                status = "SUCCESS" if result['response_time_ms'] < 2000 else "WARNING"
                self.print_status(
                    f"{test_name}: {result['response_time_ms']:.0f}ms", 
                    status
                )
            else:
                self.print_status(
                    f"{test_name}: 失败 - {result.get('error', '未知错误')}", 
                    "ERROR"
                )
        
        return results

    def continuous_monitor(self, duration_minutes=5, interval_seconds=30):
        """持续监控性能"""
        self.print_status(f"开始持续监控 {duration_minutes} 分钟，间隔 {interval_seconds} 秒", "MONITOR")
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        all_results = []
        
        while datetime.now() < end_time:
            # 测试主要端点
            result = self.test_single_request("/", "首页监控")
            all_results.append(result)
            
            if result['success']:
                response_time = result['response_time_ms']
                if response_time < 1000:
                    status = "SUCCESS"
                elif response_time < 3000:
                    status = "WARNING"
                else:
                    status = "ERROR"
                
                self.print_status(
                    f"响应时间: {response_time:.0f}ms", 
                    status
                )
            else:
                self.print_status(f"请求失败: {result.get('error', '未知')}", "ERROR")
            
            time.sleep(interval_seconds)
        
        # 生成统计报告
        self.generate_report(all_results)
        
        return all_results

    def concurrent_load_test(self, concurrent_users=5, requests_per_user=10):
        """并发负载测试"""
        self.print_status(f"并发负载测试: {concurrent_users} 用户, 每用户 {requests_per_user} 请求", "MONITOR")
        
        def user_session(user_id):
            """模拟单个用户的请求会话"""
            user_results = []
            for i in range(requests_per_user):
                result = self.test_single_request("/", f"用户{user_id}-请求{i+1}")
                user_results.append(result)
                time.sleep(0.1)  # 短暂间隔
            return user_results
        
        all_results = []
        start_time = time.time()
        
        # 使用线程池进行并发测试
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = [executor.submit(user_session, i+1) for i in range(concurrent_users)]
            
            for future in as_completed(futures):
                try:
                    user_results = future.result()
                    all_results.extend(user_results)
                except Exception as e:
                    self.print_status(f"用户会话失败: {e}", "ERROR")
        
        total_time = time.time() - start_time
        
        # 分析结果
        successful_requests = [r for r in all_results if r['success']]
        failed_requests = [r for r in all_results if not r['success']]
        
        if successful_requests:
            response_times = [r['response_time_ms'] for r in successful_requests]
            avg_response = statistics.mean(response_times)
            median_response = statistics.median(response_times)
            max_response = max(response_times)
            min_response = min(response_times)
            
            self.print_status("=== 负载测试结果 ===", "MONITOR")
            self.print_status(f"总请求数: {len(all_results)}", "INFO")
            self.print_status(f"成功请求: {len(successful_requests)}", "SUCCESS")
            self.print_status(f"失败请求: {len(failed_requests)}", "ERROR" if failed_requests else "INFO")
            self.print_status(f"平均响应时间: {avg_response:.0f}ms", "INFO")
            self.print_status(f"中位数响应时间: {median_response:.0f}ms", "INFO")
            self.print_status(f"最大响应时间: {max_response:.0f}ms", "WARNING" if max_response > 5000 else "INFO")
            self.print_status(f"最小响应时间: {min_response:.0f}ms", "INFO")
            self.print_status(f"总测试时间: {total_time:.1f}秒", "INFO")
            
            # 计算QPS
            qps = len(successful_requests) / total_time
            self.print_status(f"每秒请求数 (QPS): {qps:.1f}", "SUCCESS" if qps > 1 else "WARNING")
        
        return all_results

    def generate_report(self, results):
        """生成性能报告"""
        if not results:
            self.print_status("没有测试结果，无法生成报告", "WARNING")
            return
        
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]
        
        if not successful_results:
            self.print_status("所有请求都失败了", "ERROR")
            return
        
        response_times = [r['response_time_ms'] for r in successful_results]
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_requests': len(results),
            'successful_requests': len(successful_results),
            'failed_requests': len(failed_results),
            'success_rate': len(successful_results) / len(results) * 100,
            'response_times': {
                'average': statistics.mean(response_times),
                'median': statistics.median(response_times),
                'min': min(response_times),
                'max': max(response_times),
                'std_dev': statistics.stdev(response_times) if len(response_times) > 1 else 0
            }
        }
        
        # 保存报告到文件
        report_filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.print_status("=== 性能报告 ===", "MONITOR")
        self.print_status(f"成功率: {report['success_rate']:.1f}%", "SUCCESS" if report['success_rate'] > 95 else "WARNING")
        self.print_status(f"平均响应时间: {report['response_times']['average']:.0f}ms", "INFO")
        self.print_status(f"报告已保存: {report_filename}", "SUCCESS")

def main():
    """主函数"""
    import sys
    
    monitor = PerformanceMonitor()
    
    print("🚀 Sprunki Phase 4 性能监控工具")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            # 快速测试
            monitor.test_multiple_endpoints()
        elif command == "monitor":
            # 持续监控
            duration = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            monitor.continuous_monitor(duration_minutes=duration)
        elif command == "load":
            # 负载测试
            users = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            requests = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            monitor.concurrent_load_test(concurrent_users=users, requests_per_user=requests)
        else:
            print("未知命令。可用命令: test, monitor, load")
    else:
        # 默认执行全面测试
        print("执行默认测试套件...")
        
        # 1. 多端点测试
        monitor.test_multiple_endpoints()
        
        print("\n" + "=" * 50)
        
        # 2. 简单负载测试
        monitor.concurrent_load_test(concurrent_users=3, requests_per_user=5)

if __name__ == "__main__":
    main()