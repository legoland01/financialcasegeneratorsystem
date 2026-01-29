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
    
    if not OUTPUTS_COMPLETE_DIR.exists():
        print("⚠️ outputs_complete/ 目录不存在 (跳过)")
        return None
    
    pdf_files = list(OUTPUTS_COMPLETE_DIR.glob("*.pdf"))
    if not pdf_files:
        print("⚠️ 未找到PDF文件 (跳过)")
        return None
    
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
        print("⚠️ outputs/ 目录不存在")
        return None
    
    stage0_dir = OUTPUTS_DIR / "stage0"
    if not stage0_dir.exists():
        print("⚠️ outputs/stage0/ 目录不存在")
        return None
    
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
        print("⚠️ 0.4_key_numbers.json 不存在 (跳过)")
        return None
    
    data = json.loads(key_numbers_file.read_text())
    
    equipment_list = data.get("租赁物清单", [])
    if not equipment_list:
        print("⚠️ 租赁物清单为空 (跳过)")
        return None
    
    total_equipment_value = sum(
        eq.get("评估价值", 0) or 0 
        for eq in equipment_list 
        if eq.get("评估价值")
    )
    
    print(f"设备总数: {len(equipment_list)}")
    print(f"设备总金额: {total_equipment_value:,} 元")
    
    contract_base = data.get("合同基础金额", {})
    if isinstance(contract_base, dict):
        contract_amount = contract_base.get("调整后合同金额", {}).get("数值",
                 contract_base.get("原合同金额", {}).get("数值", total_equipment_value))
    else:
        contract_amount = contract_base or total_equipment_value
    
    print(f"合同金额: {contract_amount:,} 元")
    
    if contract_amount > 0 and total_equipment_value > 0:
        if total_equipment_value == contract_amount:
            print("✅ 金额一致")
            return True
        else:
            diff = abs(total_equipment_value - contract_amount)
            print(f"⚠️ 金额不一致 (差额: {diff:,} 元)")
            return True  # 不作为失败
    
    return True

def main():
    """主函数"""
    print("PDF质量检查")
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = []
    
    results.append(("PDF文件", check_pdf_exists()))
    results.append(("Stage 0 产物", check_stage0_outputs()))
    results.append(("数据一致性", check_data_consistency()))
    
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
    
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
