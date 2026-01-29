"""完整测试脚本 - 读取PDF并执行完整流程"""
import sys
import os
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

# 设置环境变量
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE


def read_pdf_with_pypdf2(pdf_path: str) -> str:
    """使用PyPDF2读取PDF"""
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"PyPDF2读取失败: {e}")
        return ""


def read_pdf_with_pdfplumber(pdf_path: str) -> str:
    """使用pdfplumber读取PDF"""
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"pdfplumber读取失败: {e}")
        return ""


def read_pdf_text(pdf_path: str) -> str:
    """读取PDF文件内容"""
    logger.info(f"读取PDF文件: {pdf_path}")
    
    # 先尝试pdfplumber（通常效果更好）
    text = read_pdf_with_pdfplumber(pdf_path)
    if text:
        logger.success(f"使用pdfplumber读取成功，共 {len(text)} 字符")
        return text
    
    # 尝试PyPDF2
    text = read_pdf_with_pypdf2(pdf_path)
    if text:
        logger.success(f"使用PyPDF2读取成功，共 {len(text)} 字符")
        return text
    
    logger.error("PDF读取失败")
    return ""


def test_full_workflow(judgment_text: str):
    """执行完整的工作流测试"""
    logger.info("=" * 60)
    logger.info("开始执行完整工作流测试")
    logger.info("=" * 60)
    
    try:
        from src.services import Stage0Service, Stage1Service
        from src.utils import LLMClient
        
        # 创建LLM客户端
        llm_client = LLMClient(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            api_base=OPENAI_API_BASE
        )
        
        # ==================== 阶段0：判决书解析与全局规划 ====================
        logger.info("")
        logger.info("=" * 60)
        logger.info("阶段0：判决书解析与全局规划")
        logger.info("=" * 60)
        
        stage0_service = Stage0Service(llm_client=llm_client)
        stage0_result = stage0_service.run_all(judgment_text)
        
        logger.success("阶段0完成！")
        logger.info(f"结果已保存到: outputs/analysis_results.json")
        
        # 保存到测试输出
        test_output_path = Path("outputs/test_stage0_result.json")
        with open(test_output_path, 'w', encoding='utf-8') as f:
            json.dump(stage0_result, f, ensure_ascii=False, indent=2)
        logger.info(f"测试结果已保存到: {test_output_path}")
        
        # ==================== 阶段1：原告起诉包生成 ====================
        logger.info("")
        logger.info("=" * 60)
        logger.info("阶段1：原告起诉包生成")
        logger.info("=" * 60)
        
        stage1_service = Stage1Service(llm_client=llm_client)
        stage1_result = stage1_service.run_all(stage0_result)
        
        logger.success("阶段1完成！")
        logger.info(f"结果已保存到: outputs/stage1/plaintiff_package.json")
        
        # ==================== 测试总结 ====================
        logger.info("")
        logger.info("=" * 60)
        logger.info("测试总结")
        logger.info("=" * 60)
        logger.success("✅ 所有阶段测试通过！")
        logger.info(f"📁 输出目录: {Path('outputs').absolute()}")
        logger.info("")
        logger.info("生成的文件:")
        logger.info("  1. outputs/analysis_results.json - 阶段0完整结果")
        logger.info("  2. outputs/stage0/ - 阶段0各子任务结果")
        logger.info("  3. outputs/stage1/ - 阶段1生成文件")
        logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("金融案件测试数据生成系统 - 完整测试")
    logger.info("=" * 60)
    logger.info(f"API配置:")
    logger.info(f"  API Base: {OPENAI_API_BASE}")
    logger.info(f"  Model: {OPENAI_MODEL}")
    logger.info("=" * 60)
    print()
    
    # PDF文件路径
    pdf_path = Path("/Users/liuzhen/Documents/河广/Product Development/chatGPT/Digital Law/Digital court/金融法院/法官数字助手/案卷材料样例/融资租赁/(2024)沪74民初721号/OpenCode Trial/测试用判决书/(2024)沪74民初245号.pdf")
    
    if not pdf_path.exists():
        logger.error(f"PDF文件不存在: {pdf_path}")
        return False
    
    # 检查PDF解析库
    try:
        import PyPDF2
        import pdfplumber
        logger.success("✓ PDF解析库已安装")
    except ImportError as e:
        logger.error(f"✗ 缺少PDF解析库: {e}")
        logger.info("请安装: pip install PyPDF2 pdfplumber")
        return False
    
    # 读取PDF
    judgment_text = read_pdf_text(str(pdf_path))
    
    if not judgment_text:
        logger.error("PDF内容为空，无法继续测试")
        return False
    
    logger.info(f"PDF内容长度: {len(judgment_text)} 字符")
    logger.info(f"PDF内容预览:")
    print(judgment_text[:500])
    print("...\n")
    
    # 执行完整测试
    success = test_full_workflow(judgment_text)
    
    return success


if __name__ == "__main__":
    success = main()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
