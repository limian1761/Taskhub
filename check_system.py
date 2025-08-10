#!/usr/bin/env python3
"""
Taskhub系统状态检查脚本
用于验证系统各组件是否正常运行
"""

import requests
import time
import sys
from typing import Dict, Any

def check_service(url: str, name: str) -> bool:
    """检查单个服务状态"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {name} 服务运行正常")
            return True
        else:
            print(f"❌ {name} 服务返回状态码: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {name} 服务连接失败: {e}")
        return False

def main():
    """主检查函数"""
    services = {
        "Taskhub API": "http://localhost:8000/health",
        "Outline API": "http://localhost:3000/api",
    }
    
    print("🔍 正在检查Taskhub系统状态...")
    print("=" * 50)
    
    all_healthy = True
    for name, url in services.items():
        if not check_service(url, name):
            all_healthy = False
    
    print("=" * 50)
    if all_healthy:
        print("🎉 所有服务运行正常！可以开始使用Taskhub了")
    else:
        print("⚠️  部分服务未启动，请运行 start_all.bat 启动所有服务")
        print("   或者使用以下命令分别启动：")
        print("   - Taskhub API: python -m taskhub.api_server")
        print("   - Outline: 需要单独启动Outline服务")

if __name__ == "__main__":
    main()