"""完整重新运行脚本 - 修复证据包生成问题后重新生成所有材料

⚠️ DEPRECATED: 此脚本已废弃，请使用 run_complete.py 作为统一入口
⚠️ 运行方式: python3 run_complete.py
"""
import sys
import json
import argparse
from pathlib import Path
import warnings

# 打印废弃警告
warnings.warn(
    "⚠️ run_full_regeneration.py 已废弃，请使用 run_complete.py 作为统一入口\n"
    "   推荐: python3 run_complete.py (完整流程) 或 python3 run_complete.py --verify (仅验证)",
    DeprecationWarning,
    stacklevel=2
)

# 添加src到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from loguru import logger

# API配置
OPENAI_API_KEY = "sk-fjephnssumhgkxhakpxlfrqayiuckkyogvwkchqutqolqilk"
OPENAI_API_BASE = "https://api.siliconflow.cn/v1"
OPENAI_MODEL = "deepseek-ai/DeepSeek-V3.2"

# PDF文件路径
PDF_PATH = Path("/Users/liuzhen/Documents/河广/Product Development/chatGPT/Digital Law/Digital court/金融法院/法官数字助手/案卷材料样例/融资租赁/(2024)沪74民初721号/OpenCode Trial/测试用判决书/(2024)沪74民初245号.pdf")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='金融案件测试数据生成系统 - 全自动执行',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python run_full_regeneration.py                    # 执行所有阶段，生成所有PDF
  python run_full_regeneration.py --stages 0         # 只执行阶段0
  python run_full_regeneration.py --stages 0,1      # 执行阶段0和1
  python run_full_regeneration.py --no-pdf          # 不生成PDF文件
  python run_full_regeneration.py --no-answer-key  # 不生成标准答案集
  python run_full_regeneration.py --new-arch       # 使用新架构生成证据文件
        """
    )
    parser.add_argument(
        '--stages',
        type=str,
        default='0,1,2,3',
        help='要执行的阶段，用逗号分隔（如：0,1,2,3）'
    )
    parser.add_argument(
        '--no-pdf',
        action='store_true',
        help='不生成PDF文件'
    )
    parser.add_argument(
        '--no-answer-key',
        action='store_true',
        help='不生成标准答案集'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='outputs',
        help='输出目录（默认：outputs）'
    )
    parser.add_argument(
        '--new-arch',
        action='store_true',
        help='使用新架构生成证据文件（生成独立证据文件而非合并文件）'
    )
    parser.add_argument(
        '--use-simple-pdf',
        action='store_true',
        help='使用简化版PDF生成器（直接读取证据文件）'
    )
    return parser.parse_args()


def read_pdf_text(pdf_path: str) -> str:
    """读取PDF文件内容"""
    try:
        import PyPDF2

        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"

        return text
    except ImportError:
        logger.error("PyPDF2未安装，请运行: pip install PyPDF2")
        return ""


def run_full_regeneration():
    """完整重新运行所有阶段"""

    args = parse_args()

    stages_to_run = [int(s) for s in args.stages.split(',')]
    generate_pdf = not args.no_pdf
    generate_answer_key = not args.no_answer_key
    use_new_architecture = True  # 默认使用新架构
    use_simple_pdf = True       # 默认使用简化PDF生成器

    logger.info("=" * 60)
    logger.info("金融案件测试数据生成系统 - 完整重新运行")
    logger.info("=" * 60)
    logger.info(f"API配置:")
    logger.info(f"  API Base: {OPENAI_API_BASE}")
    logger.info(f"  Model: {OPENAI_MODEL}")
    logger.info(f"  Timeout: 600秒 (10分钟)")
    logger.info(f"执行配置:")
    logger.info(f"  执行阶段: {','.join(str(s) for s in stages_to_run)}")
    logger.info(f"  生成PDF: {'是' if generate_pdf else '否'}")
    logger.info(f"  生成标准答案集: {'是' if generate_answer_key else '否'}")
    logger.info(f"  使用新架构: {'是' if use_new_architecture else '否'}")
    logger.info(f"  使用简化PDF生成器: {'是' if use_simple_pdf else '否'}")
    logger.info("=" * 60)
    print()

    # 检查PDF文件
    if not PDF_PATH.exists():
        logger.error(f"PDF文件不存在: {PDF_PATH}")
        return False

    logger.info(f"读取PDF文件: {PDF_PATH}")

    try:
        # 读取PDF内容
        judgment_text = read_pdf_text(str(PDF_PATH))
        if not judgment_text:
            logger.error("PDF文件读取失败")
            return False

        logger.info(f"PDF内容长度: {len(judgment_text)} 字符")

        # 配置环境变量
        import os
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE

        # 导入服务
        from src.services import Stage0Service, Stage1Service, Stage2Service, Stage3Service
        from src.utils import LLMClient

        # 创建LLM客户端（增加超时时间到600秒=10分钟）
        llm_client = LLMClient(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            api_base=OPENAI_API_BASE,
            timeout=600.0
        )

        logger.success(f"LLM客户端初始化成功，超时时间: 600秒")

        # 存储各阶段结果
        stage0_result = None
        stage1_result = None
        stage2_result = None
        stage3_result = None

        # ========================================================================
        # 阶段0：判决书解析与全局规划
        # ========================================================================
        if 0 in stages_to_run:
            logger.info("")
            logger.info("=" * 60)
            logger.info("【阶段0】判决书解析与全局规划")
            logger.info("=" * 60)

            stage0_service = Stage0Service(llm_client=llm_client)
            stage0_result = stage0_service.run_all(judgment_text)

            logger.success("【阶段0】完成！")
            logger.info(f"结果已保存到: outputs/stage0/")

            # 显示证据组信息
            evidence_planning = stage0_result.get("0.5_证据归属规划", {})
            evidence_groups = evidence_planning.get("证据分组", {})
            plaintiff_groups = [k for k, v in evidence_groups.items() if v.get("归属方") == "原告"]
            defendant_groups = [k for k, v in evidence_groups.items() if v.get("归属方") == "被告"]

            logger.info(f"证据分组统计:")
            logger.info(f"  原告证据组: {len(plaintiff_groups)} 个")
            logger.info(f"  被告证据组: {len(defendant_groups)} 个")
        else:
            logger.info("跳过阶段0")
            # 尝试从文件加载之前的结果
            stage0_file = Path("outputs/stage0/0.1_结构化提取.json")
            if stage0_file.exists():
                logger.info("加载之前阶段0的结果...")
                stage0_result = {}
                for f in Path("outputs/stage0").glob("*.json"):
                    key = f.stem
                    with open(f, 'r', encoding='utf-8') as file:
                        stage0_result[key] = json.load(file)

        # ========================================================================
        # 阶段1：原告起诉包生成
        # ========================================================================
        if 1 in stages_to_run and stage0_result:
            logger.info("")
            logger.info("=" * 60)
            logger.info("【阶段1】原告起诉包生成")
            if use_new_architecture:
                logger.info("  [使用新架构：生成独立证据文件]")
            logger.info("=" * 60)

            stage1_service = Stage1Service(llm_client=llm_client)
            stage1_result = stage1_service.run_all(
                stage0_data=stage0_result,
                use_new_architecture=use_new_architecture
            )

            if use_new_architecture:
                evidence_index = stage1_result.get("证据包", {})
                evidence_count = evidence_index.get("证据总数", 0)
                logger.info(f"  生成证据数: {evidence_count}")

                evidence_dir = Path("outputs/stage1/evidence")
                if evidence_dir.exists():
                    evidence_files = list(evidence_dir.glob("**/*.txt"))
                    logger.info(f"  证据文件目录: {evidence_dir}")
                    logger.info(f"  证据文件数: {len(evidence_files)}")
            else:
                evidence_package = stage1_result.get("证据包", {})
                generated_groups = len(evidence_package)
                logger.info(f"  生成证据组数: {generated_groups}")

            logger.success("【阶段1】完成！")
            logger.info(f"  结果已保存到: outputs/stage1/")

            # 显示生成的文件
            stage1_dir = Path("outputs/stage1")
            evidence_files = list(stage1_dir.glob("原告证据包_*.txt"))
            logger.info(f"  证据文件: {len(evidence_files)} 个")
            for f in evidence_files:
                logger.info(f"    - {f.name}")
        elif 1 in stages_to_run:
            logger.warning("无法执行阶段1：缺少阶段0结果")

        # ========================================================================
        # 阶段2：被告答辩包生成
        # ========================================================================
        if 2 in stages_to_run and stage0_result:
            logger.info("")
            logger.info("=" * 60)
            logger.info("【阶段2】被告答辩包生成")
            if use_new_architecture:
                logger.info("  [使用新架构：生成独立证据文件]")
            logger.info("=" * 60)

            stage2_service = Stage2Service(llm_client=llm_client)
            stage2_result = stage2_service.run_all(
                stage0_data=stage0_result,
                use_new_architecture=use_new_architecture
            )

            if use_new_architecture:
                evidence_index = stage2_result.get("证据包", {})
                evidence_count = evidence_index.get("证据总数", 0)
                logger.info(f"  生成证据数: {evidence_count}")

                evidence_dir = Path("outputs/stage2/evidence")
                if evidence_dir.exists():
                    evidence_files = list(evidence_dir.glob("**/*.txt"))
                    logger.info(f"  证据文件目录: {evidence_dir}")
                    logger.info(f"  证据文件数: {len(evidence_files)}")
            else:
                evidence_package = stage2_result.get("证据包", {})
                generated_groups = len(evidence_package)
                logger.info(f"  生成证据组数: {generated_groups}")

            logger.success("【阶段2】完成！")
            logger.info(f"  结果已保存到: outputs/stage2/")

            # 显示生成的文件
            stage2_dir = Path("outputs/stage2")
            evidence_files = list(stage2_dir.glob("被告证据包_*.txt"))
            logger.info(f"  证据文件: {len(evidence_files)} 个")
            for f in evidence_files:
                logger.info(f"    - {f.name}")
        elif 2 in stages_to_run:
            logger.warning("无法执行阶段2：缺少阶段0结果")

        # ========================================================================
        # 阶段3：法院审理包生成
        # ========================================================================
        if 3 in stages_to_run and stage0_result:
            logger.info("")
            logger.info("=" * 60)
            logger.info("【阶段3】法院审理包生成")
            logger.info("=" * 60)

            stage3_service = Stage3Service(llm_client=llm_client)
            stage3_result = stage3_service.run_all(
                original_judgment=judgment_text,
                stage0_data=stage0_result
            )

            logger.success("【阶段3】完成！")
            logger.info(f"结果已保存到: outputs/stage3/")
        elif 3 in stages_to_run:
            logger.warning("无法执行阶段3：缺少阶段0结果")

        # ========================================================================
        # 生成PDF文档
        # ========================================================================
        if generate_pdf and stage0_result:
            try:
                if use_simple_pdf and use_new_architecture:
                    from src.utils.pdf_generator_simple import PDFGeneratorSimple
                    logger.info("")
                    logger.info("=" * 60)
                    logger.info("使用简化版PDF生成器生成完整卷宗...")
                    logger.info("=" * 60)

                    # 合并原告和被告的证据索引
                    combined_evidence_index = {
                        "证据列表": [],
                        "证据组列表": []
                    }

                    if stage1_result:
                        plaintiff_evidence = stage1_result.get("证据包", {})
                        if isinstance(plaintiff_evidence, dict) and "证据列表" in plaintiff_evidence:
                            combined_evidence_index["证据列表"].extend(plaintiff_evidence.get("证据列表", []))
                            combined_evidence_index["证据组列表"].extend(plaintiff_evidence.get("证据组列表", []))

                    if stage2_result:
                        defendant_evidence = stage2_result.get("证据包", {})
                        if isinstance(defendant_evidence, dict) and "证据列表" in defendant_evidence:
                            combined_evidence_index["证据列表"].extend(defendant_evidence.get("证据列表", []))
                            combined_evidence_index["证据组列表"].extend(defendant_evidence.get("证据组列表", []))

                    # 加载起诉状内容
                    complaint_text = ""
                    complaint_path = Path("outputs/stage1/民事起诉状.txt")
                    if complaint_path.exists():
                        complaint_text = complaint_path.read_text(encoding='utf-8')

                    # 加载程序性文件内容
                    procedural_text = ""
                    procedural_path = Path("outputs/stage1/原告程序性文件.txt")
                    if procedural_path.exists():
                        procedural_text = procedural_path.read_text(encoding='utf-8')

                    pdf_generator = PDFGeneratorSimple("outputs/完整测试卷宗_简化版.pdf", stage0_result)
                    pdf_generator.generate_complete_docket(
                        stage0_data=stage0_result,
                        evidence_index=combined_evidence_index,
                        complaint_text=complaint_text,
                        procedural_text=procedural_text
                    )

                    logger.success("简化版完整卷宗PDF已生成: outputs/完整测试卷宗_简化版.pdf")
                else:
                    from src.utils.pdf_generator import PDFGenerator
                    logger.info("")
                    logger.info("=" * 60)
                    logger.info("生成完整卷宗PDF...")
                    logger.info("=" * 60)

                    pdf_generator = PDFGenerator("outputs/完整测试卷宗.pdf")
                    pdf_generator.generate_complete_docket(
                        stage0_data=stage0_result,
                        stage1_data=stage1_result or {},
                        stage2_data=stage2_result or {},
                        stage3_data=stage3_result or {}
                    )

                    logger.success("完整卷宗PDF已生成: outputs/完整测试卷宗.pdf")
            except ImportError as e:
                logger.warning(f"PDF生成功能未启用: {e}")
            except Exception as e:
                logger.error(f"PDF生成失败: {e}")
                import traceback
                traceback.print_exc()

        # ========================================================================
        # 生成标准答案集
        # ========================================================================
        if generate_answer_key and stage0_result:
            try:
                from src.services.answer_key_generator import AnswerKeyGenerator
                logger.info("")
                logger.info("=" * 60)
                logger.info("生成标准答案集...")
                logger.info("=" * 60)

                answer_key_generator = AnswerKeyGenerator(llm_client, "outputs")
                answer_key = answer_key_generator.generate_answer_key(
                    stage0_data=stage0_result,
                    stage1_data=stage1_result or {},
                    stage2_data=stage2_result or {}
                )

                # 生成标准答案集PDF
                from src.utils.pdf_generator import PDFGenerator
                pdf_generator = PDFGenerator("outputs/标准答案集.pdf")
                pdf_generator.generate_answer_key_pdf(answer_key)

                logger.success("标准答案集PDF已生成: outputs/标准答案集.pdf")
            except ImportError:
                logger.warning("标准答案集生成功能未启用")
            except Exception as e:
                logger.error(f"标准答案集生成失败: {e}")

        # ========================================================================
        # 最终验证
        # ========================================================================
        logger.info("")
        logger.info("=" * 60)
        logger.info("自动验证")
        logger.info("=" * 60)

        try:
            from src.utils.validator import QualityValidator, validate_pdf

            validator = QualityValidator()

            # 验证Stage0数据
            key_numbers_path = Path("outputs/stage0/0.4_key_numbers.json")
            if key_numbers_path.exists():
                with open(key_numbers_path, 'r', encoding='utf-8') as f:
                    key_numbers = json.load(f)

                logger.info("\n【Stage0 数据验证】")
                if validator.validate_key_numbers(key_numbers):
                    logger.info("  ✅ 关键数据验证通过")
                else:
                    validator.print_report()

            # 验证证据文件
            evidence_dir = Path("outputs/stage1/evidence")
            if evidence_dir.exists():
                logger.info("\n【证据文件验证】")
                evidence_results = validator.check_all_evidence(evidence_dir)
                logger.info(f"  证据完整性: {evidence_results['passed_ratio']} 通过")
                if evidence_results['failed'] > 0:
                    logger.warning(f"  ⚠️ {evidence_results['failed']} 个证据未通过检查")

            # 验证PDF
            pdf_path = Path("outputs/完整测试卷宗_简化版.pdf")
            if pdf_path.exists():
                logger.info("\n【PDF验证】")
                pdf_result = validate_pdf(pdf_path)
                for check in pdf_result["checks"]:
                    status = "✅" if check["passed"] else "❌"
                    logger.info(f"  {status} {check['name']}: {check['detail']}")

        except ImportError as e:
            logger.warning(f"验证模块未加载: {e}")

        logger.info("")
        logger.info("=" * 60)
        logger.success("执行完成！")
        logger.info("=" * 60)

        # 统计所有生成的文件
        total_files = 0
        for stage in ["stage0", "stage1", "stage2", "stage3"]:
            stage_dir = Path(f"outputs/{stage}")
            if stage_dir.exists():
                files = list(stage_dir.glob("*"))
                total_files += len(files)
                logger.info(f"  {stage}: {len(files)} 个文件")

        logger.info(f"  总计: {total_files} 个文件")

        logger.success("=" * 60)
        logger.success("执行成功完成！")
        logger.success("=" * 60)

        logger.info("")
        logger.info("后续操作:")
        logger.info("1. 检查生成的文件: ls -la outputs/")
        if generate_pdf:
            logger.info("2. 查看完整卷宗PDF: open outputs/完整测试卷宗.pdf")
            if use_simple_pdf and use_new_architecture:
                logger.info("3. 查看简化版卷宗PDF: open outputs/完整测试卷宗_简化版.pdf")
        if generate_answer_key:
            logger.info("4. 查看标准答案集PDF: open outputs/标准答案集.pdf")
        if use_new_architecture:
            logger.info("5. 查看证据文件目录: ls -la outputs/stage1/evidence/")
            logger.info("6. 查看单个证据文件: cat outputs/stage1/evidence/证据组1/证据组1_E001_转让合同.txt")
        else:
            logger.info("5. 查看证据包: cat outputs/stage1/原告证据包_证据组1.txt")
        logger.info("6. 查看庭审记录: cat outputs/stage3/庭审笔录.txt")
        logger.info("7. 查看答辩状: cat outputs/stage2/民事答辩状.txt")

        return True

    except ImportError as e:
        logger.error(f"缺少依赖库: {e}")
        logger.info("请先安装依赖:")
        logger.info("pip install -r requirements.txt")
        logger.info("或者单独安装:")
        logger.info("pip install PyPDF2 pdfplumber")
        return False

    except Exception as e:
        logger.error(f"执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_full_regeneration()

    if success:
        sys.exit(0)
    else:
        sys.exit(1)
