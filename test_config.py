#!/usr/bin/env python3
"""测试LLM配置"""
from src.utils import get_llm_secrets
from src.utils.llm import LLMClient

# 获取环境变量
secrets = get_llm_secrets()
print("LLM配置测试:")
print(f"API Key: {'已设置' if secrets['api_key'] else '未设置'}")
print(f"Model: {secrets['model']}")
print(f"Base: {secrets['api_base']}")

# 创建客户端
client = LLMClient(
    api_key=secrets['api_key'],
    model=secrets['model'],
    api_base=secrets['api_base']
)

print(f"\nClient配置:")
print(f"Model: {client.model}")
print(f"API Base: {client.api_base}")

# 检查环境变量
import os
print(f"\n环境变量检查:")
print(f"OPENAI_API_KEY: {'已设置' if os.getenv('OPENAI_API_KEY') else '未设置'}")
print(f"OPENAI_MODEL: {os.getenv('OPENAI_MODEL', '未设置')}")
print(f"OPENAI_API_BASE: {os.getenv('OPENAI_API_BASE', '未设置')}")