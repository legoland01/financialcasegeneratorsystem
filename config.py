"""配置文件"""
import os
from pathlib import Path
from loguru import logger
import sys


# 项目根目录
BASE_DIR = Path(__file__).parent

# 日志配置
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
logger.add(
    LOG_DIR / "app_{time:YYYY-MM-DD}.log",
    level="DEBUG",
    rotation="1 day",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)

# API配置
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# 大模型配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

# 路径配置
PROMPT_DIR = BASE_DIR / "prompts"
SCHEMA_DIR = BASE_DIR / "schemas"
OUTPUT_DIR = BASE_DIR / "outputs"
INPUT_DIR = BASE_DIR / "inputs"

# 确保目录存在
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
INPUT_DIR.mkdir(parents=True, exist_ok=True)

logger.info(f"项目根目录: {BASE_DIR}")
logger.info(f"日志目录: {LOG_DIR}")
logger.info(f"提示词目录: {PROMPT_DIR}")
logger.info(f"Schema目录: {SCHEMA_DIR}")
logger.info(f"输出目录: {OUTPUT_DIR}")
logger.info(f"输入目录: {INPUT_DIR}")
