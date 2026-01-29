#!/bin/bash

# 停止脚本

echo "正在停止金融案件测试数据生成系统..."

# 查找并停止进程
pkill -f "python main.py"

echo "服务已停止"
