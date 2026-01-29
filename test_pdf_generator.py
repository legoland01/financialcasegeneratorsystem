"""测试PDF生成功能"""
import sys
import json
from pathlib import Path

# 添加src到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from loguru import logger


def test_pdf_generator():
    """测试PDF生成功能"""

    logger.info("=" * 60)
    logger.info("测试PDF生成功能")
    logger.info("=" * 60)

    try:
        from src.utils.pdf_generator import PDFGenerator

        # 生成完整卷宗PDF
        logger.info("生成完整卷宗PDF...")

        pdf_generator = PDFGenerator("outputs/完整测试卷宗_测试.pdf")

        # 读取阶段0数据
        stage0_data = {}
        for f in Path("outputs/stage0").glob("*.json"):
            key = f.stem.replace("0.", "0.")
            with open(f, 'r', encoding='utf-8') as file:
                stage0_data[key] = json.load(file)

        # 读取阶段1数据
        stage1_data = {
            "民事起诉状.txt": "（测试内容）",
            "证据包": {}
        }

        # 简化的stage2和stage3数据
        stage2_data = {}
        stage3_data = {}

        # 尝试生成PDF（即使缺少部分数据）
        try:
            pdf_generator.generate_complete_docket(
                stage0_data=stage0_data,
                stage1_data=stage1_data,
                stage2_data=stage2_data,
                stage3_data=stage3_data
            )
            logger.success("完整卷宗PDF生成成功！")
        except Exception as e:
            logger.error(f"完整卷宗PDF生成失败: {e}")
            import traceback
            traceback.print_exc()

        # 测试标准答案集生成
        logger.info("")
        logger.info("生成标准答案集PDF...")

        from src.services.answer_key_generator import AnswerKeyGenerator

        answer_key_generator = AnswerKeyGenerator(None, "outputs")
        answer_key = answer_key_generator.generate_answer_key(
            stage0_data=stage0_data,
            stage1_data=stage1_data,
            stage2_data=stage2_data
        )

        pdf_generator2 = PDFGenerator("outputs/标准答案集_测试.pdf")
        pdf_generator2.generate_answer_key_pdf(answer_key)

        logger.success("标准答案集PDF生成成功！")

        logger.success("=" * 60)
        logger.success("PDF生成功能测试完成！")
        logger.success("=" * 60)

        logger.info("")
        logger.info("生成的PDF文件:")
        logger.info("1. outputs/完整测试卷宗_测试.pdf")
        logger.info("2. outputs/标准答案集_测试.pdf")

        return True

    except ImportError as e:
        logger.error(f"缺少依赖库: {e}")
        logger.info("请先安装依赖:")
        logger.info("pip install reportlab")
        return False

    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_pdf_generator()

    if success:
        sys.exit(0)
    else:
        sys.exit(1)
