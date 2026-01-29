#!/bin/bash

# 安装和测试脚本

echo "========================================"
echo "金融案件测试数据生成系统 - 安装和测试"
echo "========================================"
echo ""

# 检查Python版本
echo "检查Python版本..."
python3 --version

# 安装依赖
echo ""
echo "安装依赖包..."
python3 -m pip install --user fastapi uvicorn pydantic loguru openai pandas numpy python-multipart python-dotenv

echo ""
echo "========================================"
echo "依赖安装完成！"
echo "========================================"
echo ""
echo "现在可以运行测试脚本："
echo "  python3 test_quick.py"
echo ""
