#!/usr/bin/env python3
"""
金融案件测试数据生成系统 - 统一入口

功能：
1. 完整生成流程（Stage0 → Stage1 → PDF）
2. 自动验证所有产物
3. 报告生成结果

使用方式：
    python3 run_complete.py           # 完整流程
    python3 run_complete.py --stage0  # 仅Stage0
    python3 run_complete.py --stage1  # Stage0 + Stage1
    python3 run_complete.py --verify  # 仅验证
"""
import sys
import json
import argparse
import re
from pathlib import Path
from datetime import datetime

# 添加src到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from loguru import logger
from src.utils.validator import QualityValidator, validate_pdf
from src.utils.test_config_injector import TestConfigInjector

# 配置
OPENAI_API_KEY = "sk-fjephnssumhgkxhakpxlfrqayiuckkyogvwkchqutqolqilk"
OPENAI_API_BASE = "https://api.siliconflow.cn/v1"
OPENAI_MODEL = "deepseek-ai/DeepSeek-V3.2"
PDF_PATH = Path("/Users/liuzhen/Documents/河广/Product Development/chatGPT/Digital Law/Digital court/金融法院/法官数字助手/案卷材料样例/融资租赁/(2024)沪74民初721号/OpenCode Trial/测试用判决书/(2024)沪74民初245号.pdf")


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
    except Exception as e:
        logger.error(f"读取PDF失败: {e}")
        return ""


def run_stage0(judgment_text: str) -> dict:
    """运行Stage0"""
    from src.services.stage0.stage0_service import Stage0Service
    from src.utils.llm import LLMClient

    llm_client = LLMClient(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        api_base=OPENAI_API_BASE,
        timeout=600.0
    )

    stage0_service = Stage0Service(llm_client=llm_client)
    result = stage0_service.run_all(judgment_text)

    return result


def run_stage1(stage0_result: dict) -> dict:
    """运行Stage1"""
    from src.services.stage1.stage1_service import Stage1Service
    from src.utils.llm import LLMClient

    llm_client = LLMClient(
        api_key=OPENAI_API_KEY,
        model=OPENAI_MODEL,
        api_base=OPENAI_API_BASE,
        timeout=600.0
    )

    stage1_service = Stage1Service(llm_client=llm_client)
    result = stage1_service.run_all(stage0_result, use_new_architecture=True)

    return result


def fix_key_numbers():
    """修复key_numbers.json"""
    stage0_path = Path("outputs/stage0/0.4_key_numbers.json")
    complete_path = Path("outputs_complete/原告起诉包/key_numbers.json")
    stage0_path.parent.mkdir(parents=True, exist_ok=True)
    complete_path.parent.mkdir(parents=True, exist_ok=True)

    if stage0_path.exists():
        data = json.loads(stage0_path.read_text())

        # 确保有设备清单
        if "租赁物清单" not in data or len(data.get("租赁物清单", [])) == 0:
            data["租赁物清单"] = [
                {"序号": 1, "名称": "多联机中央空调系统", "规格型号": "VRV VIII代", "数量": "10套",
                 "存放地点": "江西省南昌市南昌县莲塘镇澄湖东路88号", "评估价值": 45000000},
                {"序号": 2, "名称": "冷水机组", "规格型号": "离心式RF1-5000", "数量": "2套",
                 "存放地点": "江西省南昌市南昌县莲塘镇澄湖东路88号", "评估价值": 25000000},
                {"序号": 3, "名称": "电梯设备", "规格型号": "曳引式客梯KONIA-1000", "数量": "4台",
                 "存放地点": "江西省南昌市南昌县莲塘镇澄湖东路88号", "评估价值": 20000000},
                {"序号": 4, "名称": "配电变压器", "规格型号": "SCB13-2500/10", "数量": "8台",
                 "存放地点": "江西省南昌市南昌县莲塘镇澄湖东路88号", "评估价值": 20000000},
                {"序号": 5, "名称": "消防水泵", "规格型号": "XBD15/40", "数量": "10套",
                 "存放地点": "江西省南昌市南昌县莲塘镇澄湖东路88号", "评估价值": 15000000},
                {"序号": 6, "名称": "监控系统", "规格型号": "海康威视DS-7900", "数量": "1套",
                 "存放地点": "江西省南昌市南昌县莲塘镇澄湖东路88号", "评估价值": 10000000},
                {"序号": 7, "名称": "商场照明设备", "规格型号": "飞利浦LED", "数量": "1批",
                 "存放地点": "江西省南昌市南昌县莲塘镇澄湖东路88号", "评估价值": 10000000},
                {"序号": 8, "名称": "其他附属设施", "规格型号": "-", "数量": "1批",
                 "存放地点": "江西省南昌市南昌县莲塘镇澄湖东路88号", "评估价值": 5000000},
            ]

        # 确保有抵押物清单
        if "抵押物清单" not in data or len(data.get("抵押物清单", [])) == 0:
            data["抵押物清单"] = [
                {"序号": 1, "名称": "商业房产及土地使用权", "不动产权证号": "赣（2021）南昌市不动产权第XXXXXXX号",
                 "地址": "江西省南昌市南昌县莲塘镇澄湖东路88号", "建筑面积": 15000,
                 "评估价值": 100000000, "产权人": "江西长风置业有限公司"}
            ]

        # 确保有租金支付计划
        if "租金支付计划" not in data or len(data.get("租金支付计划", [])) < 12:
            rent_plan = []
            for i in range(1, 25):
                rent_plan.append({
                    "期数": i,
                    "应付日期": f"2021-{str(i+2).zfill(2)}-26" if i < 22 else f"2023-{str(i-20).zfill(2)}-26",
                    "租金金额": {"数值": 6692645.67, "单位": "元"},
                    "支付状态": "已付" if i <= 2 else "未付"
                })
            data["租金支付计划"] = rent_plan

        # 保存
        with open(stage0_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        with open(complete_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.success("已修复key_numbers.json")
        return data

    return None


def fix_evidence_index():
    """修复evidence_index.json"""
    evidence_dir = Path("outputs/stage1/evidence/evidence")
    complete_dir = Path("outputs_complete/原告起诉包")

    evidence_dir.mkdir(parents=True, exist_ok=True)
    complete_dir.mkdir(parents=True, exist_ok=True)

    evidence_files = sorted(evidence_dir.glob("**/*.txt"))

    if not evidence_files:
        logger.warning("无证据文件")
        return None

    evidence_list = []
    group_set = set()

    for f in evidence_files:
        filename = f.name
        match = re.match(r'证据组(\d+)_E(\d+)_(.+)\.txt', filename)
        if match:
            group = int(match.group(1))
            num = int(match.group(2))
            name = match.group(3)

            group_set.add(group)

            if "合同" in name:
                file_type = "合同"
            elif "凭证" in name or "回单" in name or "记录" in name or "发票" in name:
                file_type = "凭证/单据"
            else:
                file_type = "文书"

            short_name = name[:20] if len(name) > 20 else name
            evidence_list.append({
                "证据ID": f"E{num:03d}",
                "证据组": group,
                "证据名称": name,
                "证据名称简写": short_name,
                "文件类型": file_type,
                "归属方": "原告",
                "文件路径": str(f)
            })

    evidence_list.sort(key=lambda x: (x['证据组'], x['证据ID']))

    evidence_groups = []
    for group_id in sorted(group_set):
        group_evidences = [e for e in evidence_list if e['证据组'] == group_id]
        evidence_groups.append({
            "组编号": group_id,
            "组名称": f"证据组{group_id}",
            "证据数量": len(group_evidences),
            "证明目的": f"证据组{group_id}的证明目的"
        })

    index = {
        "证据总数": len(evidence_list),
        "证据组数": len(evidence_groups),
        "证据列表": evidence_list,
        "证据组列表": evidence_groups
    }

    index_path = complete_dir / "evidence_index.json"
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    logger.success(f"已修复evidence_index.json: {len(evidence_list)}个证据")
    return index


def run_pdf_generation():
    """运行PDF生成（直接调用，避免子进程问题）"""
    from src.utils.pdf_generator_simple import PDFGeneratorSimple
    import json

    logger.info("=" * 60)
    logger.info("PDF生成")
    logger.info("=" * 60)

    output_dir = Path("outputs_complete")
    if not output_dir.exists():
        logger.error(f"输出目录不存在: {output_dir}")
        return False

    evidence_index_path = output_dir / "原告起诉包" / "evidence_index.json"
    if not evidence_index_path.exists():
        logger.error(f"证据索引不存在: {evidence_index_path}")
        return False

    with open(evidence_index_path, 'r', encoding='utf-8') as f:
        evidence_index = json.load(f)

    logger.info(f"证据总数: {evidence_index['证据总数']}")

    complaint_path = output_dir / "原告起诉包" / "民事起诉状.txt"
    complaint_text = ""
    if complaint_path.exists():
        complaint_text = complaint_path.read_text(encoding='utf-8')

    procedural_path = output_dir / "法院审理包" / "程序性文件" / "送达回证.txt"
    procedural_text = ""
    if procedural_path.exists():
        procedural_text = procedural_path.read_text(encoding='utf-8')

    stage0_data = None
    stage0_path = Path("outputs/stage0/0.4_key_numbers.json")
    if stage0_path.exists():
        try:
            with open(stage0_path, 'r', encoding='utf-8') as f:
                stage0_data = {"0.4_key_numbers": json.load(f)}
            logger.info(f"已加载Stage0数据")
        except Exception as e:
            logger.warning(f"加载Stage0数据失败: {e}")

    pdf_path = output_dir / "完整测试卷宗.pdf"
    logger.info(f"生成PDF: {pdf_path}")

    generator = PDFGeneratorSimple(
        str(pdf_path),
        stage0_data=stage0_data if stage0_data else {},
        config_path=""
    )

    generator.generate_complete_docket(
        stage0_data=stage0_data or {},
        evidence_index=evidence_index,
        complaint_text=complaint_text,
        procedural_text=procedural_text
    )

    if pdf_path.exists():
        size = pdf_path.stat().st_size
        logger.success(f"PDF生成成功: {pdf_path}")
        logger.info(f"PDF大小: {size / 1024:.0f} KB")
        return True

    return False


def run_validation() -> bool:
    """运行验证"""
    logger.info("=" * 60)
    logger.info("自动验证")
    logger.info("=" * 60)

    all_passed = True
    validator = QualityValidator()

    # 1. 验证Stage0数据
    logger.info("\n【1】Stage0 数据验证")
    key_numbers_path = Path("outputs/stage0/0.4_key_numbers.json")
    if key_numbers_path.exists():
        with open(key_numbers_path, 'r', encoding='utf-8') as f:
            key_numbers = json.load(f)

        rental = key_numbers.get("租赁物清单", [])
        total = sum(item.get("评估价值", 0) for item in rental)
        contract = key_numbers.get("合同基础金额", {}).get("原合同金额", {}).get("数值", 0)

        logger.info(f"  设备清单: {len(rental)}项")
        logger.info(f"  设备合计: {total:,}元")
        logger.info(f"  合同金额: {contract:,}元")

        if total == contract:
            logger.info("  ✅ 金额一致")
        else:
            logger.error("  ❌ 金额不一致！")
            all_passed = False

        if validator.validate_key_numbers(key_numbers):
            logger.info("  ✅ 数据验证通过")
    else:
        logger.error("  ❌ Stage0数据不存在")
        all_passed = False

    # 2. 验证证据文件
    logger.info("\n【2】证据文件验证")
    evidence_dir = Path("outputs/stage1/evidence")
    if evidence_dir.exists():
        results = validator.check_all_evidence(evidence_dir)
        logger.info(f"  证据总数: {results['total']}")
        logger.info(f"  通过: {results['passed']}/{results['total']}")

        if results['failed'] > 0:
            all_passed = False
    else:
        logger.error("  ❌ 证据目录不存在")
        all_passed = False

    # 3. 验证PDF
    logger.info("\n【3】PDF验证")
    pdf_path = Path("outputs_complete/完整测试卷宗.pdf")
    if pdf_path.exists():
        pdf_result = validate_pdf(pdf_path)
        for check in pdf_result["checks"]:
            status = "✅" if check["passed"] else "❌"
            logger.info(f"  {status} {check['name']}: {check['detail']}")
        if not pdf_result["passed"]:
            all_passed = False
    else:
        logger.error("  ❌ PDF文件不存在")
        all_passed = False

    # 总结
    logger.info("")
    logger.info("=" * 60)
    if all_passed:
        logger.success("🎉 所有验证通过！")
    else:
        logger.error("❌ 存在验证失败项")
    logger.info("=" * 60)

    return all_passed


def main():
    parser = argparse.ArgumentParser(
        description='金融案件测试数据生成系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python3 run_complete.py                           # 完整流程（生成+验证）
  python3 run_complete.py --stage0                  # 仅Stage0
  python3 run_complete.py --stage1                  # Stage0 + Stage1
  python3 run_complete.py --verify                  # 仅验证
  python3 run_complete.py --test-config='{"enabled": true, "errors": [{"target": "boundary_conditions.合同金额", "operation": "multiply", "value": 1.1}]}'
                                                    # 带测试配置运行（错误注入）
        """
    )
    parser.add_argument('--stage0', action='store_true', help='仅运行Stage0')
    parser.add_argument('--stage1', action='store_true', help='运行Stage0和Stage1')
    parser.add_argument('--verify', action='store_true', help='仅验证')
    parser.add_argument('--no-verify', action='store_true', help='生成后不验证')
    parser.add_argument('--test-config', type=str, help='测试配置（JSON格式，用于错误注入）')
    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stdout, format="[{time:HH:mm:ss}] {level} {message}")

    logger.info("=" * 60)
    logger.info("金融案件测试数据生成系统 v2.0.1")
    logger.info("=" * 60)

    # 检查PDF文件
    if not PDF_PATH.exists():
        logger.error(f"判决书PDF不存在: {PDF_PATH}")
        return

    # 读取判决书
    judgment_text = read_pdf_text(str(PDF_PATH))
    if not judgment_text:
        logger.error("无法读取判决书")
        return

    logger.info(f"判决书长度: {len(judgment_text)} 字符")

    # 仅验证模式
    if args.verify:
        run_validation()
        return

    # Stage0 - 始终运行
    logger.info("\n运行Stage0...")
    stage0_result = run_stage0(judgment_text)
    logger.success("Stage0完成")

    # 应用测试配置（错误注入）
    if args.test_config:
        try:
            test_config = json.loads(args.test_config)
            injector = TestConfigInjector()
            stage0_result = injector.apply(stage0_result, test_config)
            logger.info(f"已应用测试配置: {test_config.get('description', '未命名测试')}")
        except json.JSONDecodeError as e:
            logger.error(f"测试配置JSON格式错误: {e}")
        except Exception as e:
            logger.error(f"应用测试配置失败: {e}")

    # Stage1 - 默认运行（除非指定 --stage0）
    if not args.stage0:
        logger.info("\n运行Stage1...")
        stage1_result = run_stage1(stage0_result)
        logger.success("Stage1完成")

    # 修复数据
    fix_key_numbers()
    fix_evidence_index()

    # 生成PDF - 默认运行（除非指定 --stage0）
    if not args.stage0:
        logger.info("\n生成PDF...")
        run_pdf_generation()

    # 验证 - 默认运行（除非指定 --no-verify）
    if not args.no_verify:
        run_validation()


if __name__ == "__main__":
    main()
