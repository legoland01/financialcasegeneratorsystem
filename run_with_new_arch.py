#!/usr/bin/env python3
"""运行脚本 - 使用新架构和简化PDF生成器"""
import subprocess
import sys
import os

# 设置环境变量
os.environ["OPENAI_API_KEY"] = "sk-fjephnssumhgkxhakpxlfrqayiuckkyogvwkchqutqolqilk"
os.environ["OPENAI_API_BASE"] = "https://api.siliconflow.cn/v1"
os.environ["OPENAI_MODEL"] = "deepseek-ai/DeepSeek-V3.2"

print("=" * 60)
print("金融案件测试数据生成系统")
print("配置: 使用新架构 + 简化PDF生成器")
print("=" * 60)

# 运行主脚本
try:
    result = subprocess.run([
        sys.executable, 
        "run_full_regeneration.py",
        "--stages", "0,1,2,3",
        "--new-arch",
        "--use-simple-pdf"
    ], check=True, capture_output=True, text=True)
    
    print("执行成功！")
    print(result.stdout)
    
except subprocess.CalledProcessError as e:
    print(f"执行失败: {e}")
    print("错误输出:")
    print(e.stderr)
except Exception as e:
    print(f"运行错误: {e}")