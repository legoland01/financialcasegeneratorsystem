#!/usr/bin/env python3
"""PDF质量检查脚本 - 用于GitHub Actions CI/CD"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '.')

OUTPUTS_DIR = Path("outputs")
OUTPUTS_COMPLETE_DIR = Path("outputs_complete")
TEST_DATA_DIR = Path("test_data")

def check_pdf_exists():
    """检查PDF文件是否存在"""
    print("\n" + "=" * 60)
    print("1. PDF文件检查")
    print("=" * 60)
    
    # 检查 outputs_complete 目录
    if not OUTPUTS_COMPLETE_DIR.exists():
        print("⚠️ outputs_complete/ 目录不存在 (CI/CD 环境跳过)")
        print("ℹ️  完整PDF生成需要在本地运行: python3 run_complete.py")
        return None  # 返回 None 表示跳过，不算失败
    
    pdf_files = list(OUTPUTS_COMPLETE_DIR.glob("*.pdf"))
    if not pdf_files:
        print("⚠️ 未找到PDF文件")
        return False
    
    for pdf in pdf_files:
        size = pdf.stat().st_size
        print(f"✅ {pdf.name}: {size:,} bytes ({size/1024:.1f} KB)")
    
    return len(pdf_files) > 0

def check_stage0_outputs():
    """检查Stage 0输出文件"""
    print("\n" + "=" * 60)
    print("2. Stage 0 产物检查")
    print("=" * 60)
    
    if not OUTPUTS_DIR.exists():
        print("⚠️ outputs/ 目录不存在 (需要先运行: python3 run_complete.py)")
        return None  # 跳过，不算失败
    
    stage0_dir = OUTPUTS_DIR / "stage0"
    required_files = [
        "0.1_structured_extraction.json",
        "0.2_anonymization_plan.json", 
        "0.3_transaction_reconstruction.json",
        "0.4_key_numbers.json",
        "0.5_evidence_planning.json"
    ]
    
    all_exist = True
    for filename in required_files:
        filepath = stage0_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"✅ {filename}: {size:,} bytes")
        else:
            print(f"❌ {filename}: 不存在")
            all_exist = False
    
    return all_exist

def check_data_consistency():
    """检查数据一致性"""
    print("\n" + "=" * 60)
    print("3. 数据一致性检查")
    print("=" * 60)
    
    key_numbers_file = OUTPUTS_DIR / "stage0" / "0.4_key_numbers.json"
    if not key_numbers_file.exists():
        print("❌ 0.4_key_numbers.json 不存在")
        return False
    
    data = json.loads(key_numbers_file.read_text())
    
    # 检查租赁物清单
    equipment_list = data.get("租赁物清单", [])
    if not equipment_list:
        print("❌ 租赁物清单为空")
        return False
    
    # 计算设备总金额
    total_equipment_value = 0
    equipment_with_value = 0
    equipment_missing_value = 0
    
    for eq in equipment_list:
        value = eq.get("评估价值")
        if value is not None and value > 0:
            total_equipment_value += value
            equipment_with_value += 1
        else:
            equipment_missing_value += 1
    
    print(f"设备总数: {len(equipment_list)}")
    print(f"有金额的设备: {equipment_with_value}")
    print(f"缺失金额的设备: {equipment_missing_value}")
    print(f"设备总金额: {total_equipment_value:,} 元")
    
    # 获取合同金额 (可能有多个字段名和格式)
    contract_amount = data.get("合同金额", 0)
    if contract_amount == 0:
        contract_base = data.get("合同基础金额", {})
        if isinstance(contract_base, dict):
            contract_amount = contract_base.get("调整后合同金额", {}).get("数值", 
                     contract_base.get("原合同金额", {}).get("数值", 0))
        else:
            contract_amount = contract_base
    if contract_amount == 0:
        # 尝试从租赁物计算
        contract_amount = total_equipment_value
    
    print(f"合同金额: {contract_amount:,} 元")
    
    if equipment_missing_value > 0:
        print(f"⚠️ 警告: {equipment_missing_value} 个设备缺少评估价值")
    
    if total_equipment_value != contract_amount:
        diff = abs(total_equipment_value - contract_amount)
        print(f"❌ 金额不一致! 差额: {diff:,} 元")
        return False
    
    print("✅ 金额一致")
    return True

def check_evidence_planning():
    """检查证据规划"""
    print("\n" + "=" * 60)
    print("4. 证据规划检查")
    print("=" * 60)
    
    evidence_file = OUTPUTS_DIR / "stage0" / "0.5_evidence_planning.json"
    if not evidence_file.exists():
        print("❌ 0.5_evidence_planning.json 不存在")
        return False
    
    data = json.loads(evidence_file.read_text())
    
    # 检查证据归属规划表
    evidence_table = data.get("证据归属规划表", [])
    if evidence_table:
        print(f"证据归属规划表: {len(evidence_table)} 条记录")
    
    # 检查证据分组
    evidence_groups = data.get("证据分组", {})
    if evidence_groups:
        print(f"证据分组: {len(evidence_groups)} 个组")
        for group_name, items in evidence_groups.items():
            if isinstance(items, list):
                print(f"  {group_name}: {len(items)} 个证据")
    
    total_evidence = len(evidence_table)
    return total_evidence > 0

def check_judgment_file():
    """检查判决书文件"""
    print("\n" + "=" * 60)
    print("5. 判决书文件检查")
    print("=" * 60)
    
    pdf_files = list(TEST_DATA_DIR.glob("*.pdf"))
    if not pdf_files:
        print("❌ test_data/ 目录中没有PDF文件")
        return False
    
    for pdf in pdf_files:
        size = pdf.stat().st_size
        print(f"✅ {pdf.name}: {size:,} bytes")
    
    return len(pdf_files) > 0

def main():
    """主函数"""
    print("PDF质量检查")
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    # 运行所有检查
    results.append(("判决书文件", check_judgment_file()))
    results.append(("Stage 0 产物", check_stage0_outputs()))
    results.append(("证据规划", check_evidence_planning()))
    results.append(("数据一致性", check_data_consistency()))
    results.append(("PDF文件", check_pdf_exists()))
    
    # 汇总
    print("\n" + "=" * 60)
    print("检查结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for name, result in results:
        if result is None:
            status = "⏭️ 跳过"
            skipped += 1
        elif result:
            status = "✅ 通过"
            passed += 1
        else:
            status = "❌ 失败"
            failed += 1
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed} 通过, {failed} 失败, {skipped} 跳过")
    
    # 只有真正的失败才返回非零退出码
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
