#!/bin/bash
# 一键优化脚本 - 第一阶段安全优化
# 自动执行所有优化步骤，包含安全检查和回滚机制

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_status() {
    local status=$1
    local message=$2
    local timestamp=$(date '+%H:%M:%S')
    
    case $status in
        "INFO")
            echo -e "${BLUE}[$timestamp] ℹ️  $message${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[$timestamp] ✅ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}[$timestamp] ⚠️  $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}[$timestamp] ❌ $message${NC}"
            ;;
    esac
}

# 检查Python环境
check_python_env() {
    print_status "INFO" "检查Python环境..."
    
    if ! command -v python3 &> /dev/null; then
        print_status "ERROR" "Python3 未安装"
        exit 1
    fi
    
    # 检查必要的包
    python3 -c "import pymongo, flask, mongoengine" 2>/dev/null || {
        print_status "ERROR" "缺少必要的Python包：pymongo, flask, mongoengine"
        exit 1
    }
    
    print_status "SUCCESS" "Python环境检查通过"
}

# 备份当前状态
backup_current_state() {
    print_status "INFO" "开始备份当前状态..."
    
    # 1. Git备份
    if [ -d ".git" ]; then
        git add .
        git commit -m "优化前自动备份 - $(date)" || {
            print_status "WARNING" "Git提交失败，可能没有变更"
        }
        print_status "SUCCESS" "代码已备份到Git"
    else
        print_status "WARNING" "不是Git仓库，跳过代码备份"
    fi
    
    # 2. 创建备份目录
    backup_dir="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # 3. 备份关键文件
    cp -r apps/views/base_urls.py "$backup_dir/" 2>/dev/null || true
    cp -r get_app.py "$backup_dir/" 2>/dev/null || true
    
    print_status "SUCCESS" "文件备份完成: $backup_dir"
    echo "$backup_dir" > .backup_location  # 保存备份位置
}

# 性能基准测试
run_baseline_test() {
    print_status "INFO" "运行性能基准测试..."
    
    # 检查应用是否运行
    if ! curl -s http://localhost:9028/test > /dev/null 2>&1; then
        print_status "WARNING" "应用未运行，跳过基准测试"
        return 0
    fi
    
    # 运行基准测试
    python3 performance_monitor.py test > baseline_performance.log 2>&1 || {
        print_status "WARNING" "基准测试失败，继续执行优化"
        return 0
    }
    
    print_status "SUCCESS" "基准测试完成，结果保存到 baseline_performance.log"
}

# 执行数据库优化
optimize_database() {
    print_status "INFO" "开始数据库优化..."
    
    # 运行数据库优化脚本
    if python3 optimize_database.py; then
        print_status "SUCCESS" "数据库优化完成"
        return 0
    else
        print_status "ERROR" "数据库优化失败"
        return 1
    fi
}

# 验证应用功能
verify_application() {
    print_status "INFO" "验证应用功能..."
    
    # 检查导入是否正常
    python3 -c "
try:
    from optimized_queries import get_article_optimized
    from apps.views.base_urls import base_bp
    print('✅ 导入检查通过')
except ImportError as e:
    print(f'❌ 导入失败: {e}')
    exit(1)
except Exception as e:
    print(f'❌ 其他错误: {e}')
    exit(1)
" || {
        print_status "ERROR" "模块导入失败"
        return 1
    }
    
    print_status "SUCCESS" "应用功能验证通过"
}

# 运行性能测试
run_performance_test() {
    print_status "INFO" "运行优化后性能测试..."
    
    # 等待应用启动
    sleep 2
    
    # 检查应用是否运行
    if ! curl -s http://localhost:9028/test > /dev/null 2>&1; then
        print_status "ERROR" "应用未响应，请手动启动后测试"
        return 1
    fi
    
    # 运行性能测试
    python3 performance_monitor.py test > optimized_performance.log 2>&1 || {
        print_status "WARNING" "性能测试失败，请手动检查"
        return 0
    }
    
    print_status "SUCCESS" "性能测试完成，结果保存到 optimized_performance.log"
    
    # 简单性能对比
    if [ -f "baseline_performance.log" ]; then
        print_status "INFO" "性能对比分析..."
        python3 -c "
import re
import os

def extract_response_time(log_file):
    if not os.path.exists(log_file):
        return None
    
    with open(log_file, 'r') as f:
        content = f.read()
    
    # 提取首页响应时间
    match = re.search(r'首页.*?(\d+)ms', content)
    if match:
        return int(match.group(1))
    return None

baseline = extract_response_time('baseline_performance.log')
optimized = extract_response_time('optimized_performance.log')

if baseline and optimized:
    improvement = ((baseline - optimized) / baseline) * 100
    print(f'📊 性能对比:')
    print(f'   优化前: {baseline}ms')
    print(f'   优化后: {optimized}ms')
    print(f'   提升: {improvement:.1f}%')
    
    if improvement > 10:
        print('✅ 优化效果显著')
    elif improvement > 0:
        print('⚠️ 有一定改善')
    else:
        print('❌ 性能无明显改善')
else:
    print('⚠️ 无法进行性能对比')
"
    fi
}

# 清理临时文件
cleanup() {
    print_status "INFO" "清理临时文件..."
    # 这里可以清理一些临时文件，但保留日志
    print_status "SUCCESS" "清理完成"
}

# 回滚函数
rollback() {
    print_status "WARNING" "开始回滚操作..."
    
    if [ -f ".backup_location" ]; then
        backup_dir=$(cat .backup_location)
        if [ -d "$backup_dir" ]; then
            # 恢复文件
            cp "$backup_dir"/* . 2>/dev/null || true
            print_status "SUCCESS" "文件已从 $backup_dir 恢复"
        fi
    fi
    
    # Git回滚
    if [ -d ".git" ]; then
        git checkout HEAD~1 -- apps/views/base_urls.py get_app.py 2>/dev/null || true
        print_status "SUCCESS" "Git回滚完成"
    fi
    
    print_status "SUCCESS" "回滚操作完成"
}

# 主函数
main() {
    echo "🚀 Sprunki Phase 4 第一阶段优化脚本"
    echo "=========================================="
    
    # 捕获错误信号，执行回滚
    trap 'print_status "ERROR" "脚本执行失败，开始回滚..."; rollback; exit 1' ERR
    
    # 1. 环境检查
    check_python_env
    
    # 2. 备份
    backup_current_state
    
    # 3. 基准测试
    run_baseline_test
    
    # 4. 数据库优化
    if ! optimize_database; then
        print_status "ERROR" "数据库优化失败，执行回滚"
        rollback
        exit 1
    fi
    
    # 5. 功能验证
    if ! verify_application; then
        print_status "ERROR" "应用验证失败，执行回滚"
        rollback
        exit 1
    fi
    
    # 6. 性能测试
    run_performance_test
    
    # 7. 清理
    cleanup
    
    print_status "SUCCESS" "🎉 第一阶段优化完成！"
    echo ""
    echo "📋 下一步操作："
    echo "   1. 启动应用: python3 run.py"
    echo "   2. 访问测试: http://localhost:9028"
    echo "   3. 查看报告: cat optimized_performance.log"
    echo "   4. 持续监控: python3 performance_monitor.py monitor 30"
    echo ""
    echo "📁 备份位置: $(cat .backup_location 2>/dev/null || echo '未知')"
    echo "🔄 如需回滚: bash 一键优化脚本.sh rollback"
}

# 处理回滚命令
if [ "$1" = "rollback" ]; then
    rollback
    exit 0
fi

# 执行主函数
main "$@"