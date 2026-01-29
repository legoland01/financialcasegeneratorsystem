#!/usr/bin/env python3
import os
import sys

"""测试LLM配置"""
# 添加当前目录到路径
sys.path.append('.')

print("LLM配置测试:")
print(f"OPENAI_API_KEY: {'已设置' if os.getenv('OPENAI_API_KEY') else '未设置'}")
print(f"OPENAI_MODEL: {os.getenv('OPENAI_MODEL', '未设置')}")
print(f"OPENAI_API_BASE: {os.getenv('OPENAI_API_BASE', '未设置')}")

# 检查文件是否存在
print(f"\n文件检查:")
print(f".env: {'存在' if os.path.exists('.env') else '不存在'}")