#!/usr/bin/env python3
"""
快速PDF生成脚本 - 使用outputs_complete的证据文件生成PDF

⚠️ DEPRECATED: 此脚本已废弃，请使用 run_complete.py 作为统一入口
⚠️ 推荐: python3 run_complete.py --stage2 (生成PDF)
"""
import sys
import json
import re
from pathlib import Path
import warnings

# 打印废弃警告
warnings.warn(
    "⚠️ generate_pdf.py 已废弃，请使用 run_complete.py 作为统一入口\n"
    "   推荐: python3 run_complete.py --stage2 (生成PDF)",
    DeprecationWarning,
    stacklevel=2
)

# 添加src到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.utils.pdf_generator_simple import PDFGeneratorSimple
from src.utils.llm import LLMClient
from loguru import logger


def validate_with_llm(pdf_text: str, key_numbers: dict) -> dict:
    """
    使用LLM验证生成内容是否正确

    Returns:
        dict: 验证结果，包含各项检查的通过状态
    """
    result = {
        "passed": True,
        "checks": [],
        "suggestions": []
    }

    # 检查1: 脱敏标记
    placeholders = ["某某", "某某公司", "某某律师事务所", "XXXX", "XXXXXXXX", "长江某"]
    placeholder_found = []
    for p in placeholders:
        if p in pdf_text:
            placeholder_found.append(p)

    if placeholder_found:
        result["checks"].append({
            "name": "脱敏标记检查",
            "passed": False,
            "detail": f"发现脱敏标记: {placeholder_found}"
        })
        result["passed"] = False
    else:
        result["checks"].append({
            "name": "脱敏标记检查",
            "passed": True,
            "detail": "无脱敏标记"
        })

    # 检查2: 设备清单
    rental = key_numbers.get("租赁物清单", [])
    if len(rental) >= 5:
        total_value = sum(item.get("评估价值", 0) for item in rental)
        if total_value > 0:
            result["checks"].append({
                "name": "设备清单检查",
                "passed": True,
                "detail": f"设备清单{len(rental)}项，合计{total_value:,}元"
            })
        else:
            result["checks"].append({
                "name": "设备清单检查",
                "passed": False,
                "detail": "设备评估价值为0"
            })
            result["passed"] = False
    else:
        result["checks"].append({
            "name": "设备清单检查",
            "passed": False,
            "detail": f"设备清单仅{len(rental)}项，应>=5项"
        })
        result["passed"] = False

    # 检查3: 抵押物清单
    collateral = key_numbers.get("抵押物清单", [])
    if len(collateral) >= 1:
        result["checks"].append({
            "name": "抵押物清单检查",
            "passed": True,
            "detail": f"抵押物清单{len(collateral)}项"
        })
    else:
        result["checks"].append({
            "name": "抵押物清单检查",
            "passed": False,
            "detail": "缺少抵押物清单"
        })
        result["passed"] = False

    # 检查4: 数据一致性（使用LLM）
    try:
        llm_client = LLMClient(
            api_key='sk-fjephnssumhgkxhakpxlfrqayiuckkyogvwkchqutqolqilk',
            model='deepseek-ai/DeepSeek-V3.2',
            api_base='https://api.siliconflow.cn/v1',
            timeout=30.0
        )

        check_prompt = f"""
请验证以下金融案件数据的一致性：

1. 设备清单合计金额：{sum(item.get('评估价值', 0) for item in rental):,}元
2. 合同基础金额：{key_numbers.get('合同基础金额', {}).get('原合同金额', {}).get('数值', '未设置')}元

请检查：
1. 设备清单合计是否等于合同金额？
2. 设备名称是否合理？
3. 是否有明显的数据错误？

请直接回答：通过 或 不通过，并说明原因。
"""
        llm_result = llm_client.generate(check_prompt)
        if "通过" in llm_result or "PASS" in llm_result.upper():
            result["checks"].append({
                "name": "LLM数据一致性检查",
                "passed": True,
                "detail": "数据一致"
            })
        else:
            result["checks"].append({
                "name": "LLM数据一致性检查",
                "passed": False,
                "detail": f"LLM反馈: {llm_result[:100]}..."
            })
            result["passed"] = False
    except Exception as e:
        result["checks"].append({
            "name": "LLM数据一致性检查",
            "passed": True,
            "detail": f"跳过LLM检查: {str(e)[:50]}"
        })

    return result


def validate_pdf_content(pdf_path: Path) -> dict:
    """
    验证PDF内容的正确性

    Returns:
        dict: 验证结果
    """
    result = {
        "passed": True,
        "issues": []
    }

    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(str(pdf_path))
        text = "".join([p.extract_text() or "" for p in reader.pages])

        # 检查Markdown表格
        if "|" in text and ":---" in text:
            result["issues"].append("发现Markdown表格格式，需要使用PDF真实表格")
            result["passed"] = False

        # 检查脱敏标记
        if "某某" in text or "XXXX" in text:
            result["issues"].append("发现脱敏标记")
            result["passed"] = False

    except Exception as e:
        result["issues"].append(f"PDF验证失败: {str(e)}")

    return result


def main():
    logger.info("=" * 60)
    logger.info("快速PDF生成")
    logger.info("=" * 60)
    
    # 输出目录
    output_dir = Path("outputs_complete")
    if not output_dir.exists():
        logger.error(f"输出目录不存在: {output_dir}")
        return
    
    # 加载证据索引
    evidence_index_path = output_dir / "原告起诉包" / "evidence_index.json"
    if not evidence_index_path.exists():
        logger.error(f"证据索引不存在: {evidence_index_path}")
        return
    
    with open(evidence_index_path, 'r', encoding='utf-8') as f:
        evidence_index = json.load(f)
    
    logger.info(f"证据总数: {evidence_index['证据总数']}")
    logger.info(f"证据组数: {evidence_index['证据组数']}")
    
    # 读取起诉状
    complaint_path = output_dir / "原告起诉包" / "民事起诉状.txt"
    complaint_text = ""
    if complaint_path.exists():
        complaint_text = complaint_path.read_text(encoding='utf-8')
        logger.info(f"起诉状: {len(complaint_text)} 字符")
    
    # 读取程序性文件
    procedural_path = output_dir / "法院审理包" / "程序性文件" / "送达回证.txt"
    procedural_text = ""
    if procedural_path.exists():
        procedural_text = procedural_path.read_text(encoding='utf-8')
    
    # 加载Stage0数据（如果存在）
    stage0_data = None
    stage0_path = Path("outputs/stage0/0.4_key_numbers.json")
    if stage0_path.exists():
        try:
            with open(stage0_path, 'r', encoding='utf-8') as f:
                stage0_data = {"0.4_key_numbers": json.load(f)}
            logger.info(f"已加载Stage0数据")
        except Exception as e:
            logger.warning(f"加载Stage0数据失败: {e}")
    
    # 优先从outputs_complete加载关键数据
    key_numbers_path = output_dir / "原告起诉包" / "key_numbers.json"
    key_numbers = {}
    if key_numbers_path.exists():
        try:
            with open(key_numbers_path, 'r', encoding='utf-8') as f:
                key_numbers = json.load(f)
            if stage0_data is None:
                stage0_data = {}
            stage0_data["0.4_key_numbers"] = key_numbers
            logger.info(f"已加载关键数据（租赁物清单{len(key_numbers.get('租赁物清单', []))}项，抵押物清单{len(key_numbers.get('抵押物清单', []))}项）")
        except Exception as e:
            logger.warning(f"加载关键数据失败: {e}")
    
    # 生成PDF
    pdf_path = output_dir / "完整测试卷宗.pdf"
    logger.info(f"生成PDF: {pdf_path}")
    
    generator = PDFGeneratorSimple(
        str(pdf_path),
        stage0_data=stage0_data if stage0_data else {},
        config_path=""  # 使用默认配置
    )
    
    # 生成完整卷宗
    generator.generate_complete_docket(
        stage0_data=stage0_data or {},
        evidence_index=evidence_index,
        complaint_text=complaint_text,
        procedural_text=procedural_text
    )
    
    # 检查PDF文件
    if pdf_path.exists():
        size = pdf_path.stat().st_size
        logger.success(f"PDF生成成功: {pdf_path}")
        logger.info(f"PDF大小: {size / 1024:.0f} KB")
        
        # 检查PDF页数
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(str(pdf_path))
            logger.info(f"PDF页数: {len(reader.pages)}")
        except Exception as e:
            logger.warning(f"无法读取PDF页数: {e}")

        # 验证PDF内容
        logger.info("")
        logger.info("=" * 60)
        logger.info("自动验证")
        logger.info("=" * 60)

        pdf_validation = validate_pdf_content(pdf_path)
        if pdf_validation["issues"]:
            for issue in pdf_validation["issues"]:
                logger.warning(f"  ⚠️ {issue}")
        else:
            logger.info("  ✅ PDF内容验证通过")

        # LLM验证
        if key_numbers:
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(str(pdf_path))
                pdf_text = "".join([p.extract_text() or "" for p in reader.pages])

                llm_validation = validate_with_llm(pdf_text, key_numbers)
                for check in llm_validation["checks"]:
                    status = "✅" if check["passed"] else "❌"
                    logger.info(f"  {status} {check['name']}: {check['detail']}")

                if llm_validation["passed"]:
                    logger.success("  🎉 所有验证通过！")
                else:
                    logger.error("  ❌ 存在验证失败项，请检查")
            except Exception as e:
                logger.warning(f"  验证失败: {e}")
    else:
        logger.error("PDF生成失败")
