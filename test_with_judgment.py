"""测试脚本 - 读取PDF并调用API"""
import sys
import json
from pathlib import Path

# 添加src到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from loguru import logger

# API配置
OPENAI_API_KEY = "sk-fjephnssumhgkxhakpxlfrqayiuckkyogvwkchqutqolqilk"
OPENAI_API_BASE = "https://api.siliconflow.cn/v1"
OPENAI_MODEL = "deepseek-ai/DeepSeek-V3.2"


def read_pdf_text(pdf_path: str) -> str:
    """读取PDF文件内容"""
    import PyPDF2
    
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
    
    return text


def test_with_judgment():
    """使用判决书文件测试系统"""
    logger.info("开始测试金融案件测试数据生成系统")
    
    # PDF文件路径
    pdf_path = Path("/Users/liuzhen/Documents/河广/Product Development/chatGPT/Digital Law/Digital court/金融法院/法官数字助手/案卷材料样例/融资租赁/(2024)沪74民初721号/OpenCode Trial/测试用判决书/(2024)沪74民初245号.pdf")
    
    if not pdf_path.exists():
        logger.error(f"PDF文件不存在: {pdf_path}")
        return False
    
    logger.info(f"读取PDF文件: {pdf_path}")
    
    try:
        # 读取PDF内容
        judgment_text = read_pdf_text(str(pdf_path))
        logger.info(f"PDF内容长度: {len(judgment_text)} 字符")
        
        # 导入服务
        from src.services import Stage0Service
        from src.utils import LLMClient
        
        # 配置LLM客户端
        import os
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE
        
        llm_client = LLMClient(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            api_base=OPENAI_API_BASE
        )
        
        # 执行阶段0测试
        logger.info("=" * 50)
        logger.info("开始执行阶段0：判决书解析与全局规划")
        logger.info("=" * 50)
        
        stage0_service = Stage0Service(llm_client=llm_client)
        stage0_result = stage0_service.run_all(judgment_text)
        
        logger.success("阶段0完成！")
        logger.info(f"结果已保存到: outputs/analysis_results.json")
        
        # 执行阶段1测试
        logger.info("=" * 50)
        logger.info("开始执行阶段1：原告起诉包生成")
        logger.info("=" * 50)
        
        stage1_service = Stage0Service = Stage0Service(llm_client=llm_client)
        from src.services import Stage1Service
        stage1_service = Stage1Service(llm_client=llm_client)
        stage1_result = stage1_service.run_all(stage0_result)
        
        logger.success("阶段1完成！")
        logger.info(f"结果已保存到: outputs/stage1/plaintiff_package.json")
        
        logger.success("=" * 50)
        logger.success("测试完成！")
        logger.success("=" * 50)
        
        return True
        
    except ImportError as e:
        logger.error(f"缺少依赖库: {e}")
        logger.info("请先安装依赖: pip install PyPDF2 pdfplumber")
        return False
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("金融案件测试数据生成系统 - 完整测试")
    logger.info("=" * 50)
    logger.info(f"API配置:")
    logger.info(f"  API Base: {OPENAI_API_BASE}")
    logger.info(f"  Model: {OPENAI_MODEL}")
    logger.info("=" * 50)
    print()
    
    success = test_with_judgment()
    
    if success:
        logger.success("测试成功完成！")
        sys.exit(0)
    else:
        logger.error("测试失败！")
        sys.exit(1)
