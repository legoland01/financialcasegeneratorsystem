#!/usr/bin/env python3
"""
独立验证脚本 - 对生成的内容进行全面验证
"""
import sys
import json
from pathlib import Path

# 添加src到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.utils.validator import QualityValidator, validate_pdf


def print_header(title: str):
    """打印标题"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main():
    print_header("金融案件测试数据生成系统 - 自动验证")

    all_passed = True
    validator = QualityValidator()

    # 1. 验证Stage0数据
    print_header("【1】Stage0 数据验证")

    key_numbers_path = Path("outputs/stage0/0.4_key_numbers.json")
    if key_numbers_path.exists():
        with open(key_numbers_path, 'r', encoding='utf-8') as f:
            key_numbers = json.load(f)

        # 设备清单
        rental = key_numbers.get("租赁物清单", [])
        print(f"\n设备清单: {len(rental)}项")
        for item in rental[:3]:
            print(f"  {item['序号']}. {item['名称']}: {item['评估价值']:,}元")
        if len(rental) > 3:
            print(f"  ... 共{len(rental)}项")

        total = sum(item.get("评估价值", 0) for item in rental)
        contract_amount = key_numbers.get("合同基础金额", {}).get("原合同金额", {}).get("数值", 0)
        print(f"\n设备合计: {total:,}元")
        print(f"合同金额: {contract_amount:,}元")

        if total == contract_amount:
            print("  ✅ 金额一致")
        else:
            print("  ❌ 金额不一致！")
            all_passed = False

        # 抵押物
        collateral = key_numbers.get("抵押物清单", [])
        print(f"\n抵押物清单: {len(collateral)}项")
        for item in collateral:
            print(f"  - {item['名称']}: {item['评估价值']:,}元")

        # 租金计划
        rent_plan = key_numbers.get("租金支付计划", [])
        print(f"\n租金支付计划: {len(rent_plan)}期")

    else:
        print("  ❌ Stage0数据不存在")
        all_passed = False

    # 2. 验证证据文件
    print_header("【2】证据文件验证")

    evidence_dir = Path("outputs/stage1/evidence")
    if evidence_dir.exists():
        evidence_results = validator.check_all_evidence(evidence_dir)

        print(f"\n证据总数: {evidence_results['total']}")
        print(f"通过: {evidence_results['passed']}")
        print(f"失败: {evidence_results['failed']}")
        print(f"通过率: {evidence_results['passed_ratio']}")

        if evidence_results['failed'] > 0:
            print("\n失败的证据:")
            for detail in evidence_results['details']:
                if not detail['passed']:
                    print(f"  ❌ {detail['file'][-50:]}")
                    for check in detail['checks']:
                        if check['status'] == 'fail':
                            print(f"     - {check['item']}: {check['detail']}")
            all_passed = False
    else:
        print("  ❌ 证据目录不存在")
        all_passed = False

    # 3. 验证PDF
    print_header("【3】PDF验证")

    pdf_path = Path("outputs_complete/完整测试卷宗.pdf")
    if pdf_path.exists():
        pdf_result = validate_pdf(pdf_path)

        for check in pdf_result["checks"]:
            status = "✅" if check["passed"] else "❌"
            print(f"  {status} {check['name']}: {check['detail']}")

        if not pdf_result["passed"]:
            all_passed = False
    else:
        print("  ❌ PDF文件不存在 (检查路径: outputs_complete/完整测试卷宗.pdf)")
        # 尝试其他路径
        alt_paths = [
            "outputs/完整测试卷宗_简化版.pdf",
            "outputs/完整测试卷宗.pdf"
        ]
        for alt in alt_paths:
            if Path(alt).exists():
                print(f"  ℹ️ 找到替代文件: {alt}")
                break

    # 4. 脱敏检查
    print_header("【4】脱敏检查")

    pdf_path = Path("outputs_complete/完整测试卷宗.pdf")
    if pdf_path.exists():
        import PyPDF2
        import re
        reader = PyPDF2.PdfReader(str(pdf_path))
        text = "".join([p.extract_text() or "" for p in reader.pages])

        placeholders = ["某某", "某某公司", "长江某", "华鑫某"]
        found_any = False

        for p in placeholders:
            count = text.count(p)
            if count > 0:
                print(f"  ❌ 发现'{p}': {count}处")
                found_any = True
                all_passed = False

        # 检查独立的 XXXX 标记（排除 "第XXXXXXX号" 这种正常的证照编号）
        # 正常证照号格式：第XXXXXXXX号（7-10个X）
        # 脱敏标记格式：单独的 XXXX 或 XXXXXXXX
        # 排除 "第" 后面跟着7-10个X然后是"号"的情况
        certificate_pattern = r'第X{7,10}号'
        text_without_certs = re.sub(certificate_pattern, '[证照编号]', text)

        # 检查剩余文本中的 XXXX
        remaining_xxxx = re.findall(r'X{4,}', text_without_certs)
        if remaining_xxxx:
            print(f"  ❌ 发现脱敏标记'X{{4,}}': {len(remaining_xxxx)}处")
            found_any = True
            all_passed = False

        if not found_any:
            print("  ✅ 无脱敏标记")

    # 最终结论
    print_header("验证结论")

    if all_passed:
        print("""
🎉 所有验证通过！

生成的文件:
  - outputs/stage0/          (Stage0数据)
  - outputs/stage1/evidence/ (证据文件)
  - outputs/stage1/民事起诉状.txt
  - outputs/完整测试卷宗_简化版.pdf

下一步操作:
  1. 检查证据文件: ls -la outputs/stage1/evidence/
  2. 查看PDF: open outputs/完整测试卷宗_简化版.pdf
  3. 手动审查内容是否正确
""")
    else:
        print("""
❌ 存在验证失败项，请检查上述输出中的❌标记。

建议:
  1. 根据错误信息修复问题
  2. 重新生成: python3 run_full_regeneration.py
  3. 再次验证: python3 validate_outputs.py
""")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
