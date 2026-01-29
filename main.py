"""主入口文件"""
import sys
from pathlib import Path

# 添加src到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.api import app

if __name__ == "__main__":
    import uvicorn
    from loguru import logger
    
    logger.info("启动金融案件测试数据生成系统")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
