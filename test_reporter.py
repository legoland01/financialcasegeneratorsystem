#!/usr/bin/env python3
"""
测试报告生成器 - 简化版
分析 CI/CD 测试结果，生成测试报告
"""

import sys
import json
from pathlib import Path
from datetime import datetime

OUTPUTS_DIR = Path("outputs")
OUTPUTS_COMPLETE_DIR = Path("outputs_complete")
TEST_DATA_DIR = Path("test_data")

def check_file_exists(filepath, description):
    """检查文件是否存在"""
    if filepath.exists():
        size = filepath.stat().st_size
        print(f"✅ {description}: {filepath.name} ({size:,} bytes)")
        return True
    else:
        print(f"❌ {description}: {filepath.name} 不存在")
        return False

def main():
    print("\n" + "=" * 60)
    print("测试报告生成器")
    print("=" * 60)
    print(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    issues = []
    checks_passed = 0
    checks_total = 0
    
    # 1. 检查判决书文件
    print("1. 判决书文件检查")
    checks_total += 1
    pdf_files = list(TEST_DATA_DIR.glob("*.pdf"))
    if pdf_files:
        for pdf in pdf_files:
            size = pdf.stat().st_size
            print(f"   ✅ {pdf.name}: {size:,} bytes")
        checks_passed += 1
    else:
        print("   ❌ 未找到判决书文件")
        issues.append({"type": "critical", "description": "判决书文件不存在"})
    
    # 2. 检查 Stage 0 产物
    print("\n2. Stage 0 产物检查")
    checks_total += 1
    stage0_dir = OUTPUTS_DIR / "stage0"
    required_files = [
        "0.1_structured_extraction.json",
        "0.2_anonymization_plan.json", 
        "0.3_transaction_reconstruction.json",
        "0.4_key_numbers.json",
        "0.5_evidence_planning.json"
    ]
    stage0_files = [f for f in required_files if (stage0_dir / f).exists()]
    if len(stage0_files) == len(required_files):
        print(f"   ✅ Stage 0 产物完整 ({len(stage0_files)}/{len(required_files)})")
        checks_passed += 1
    else:
        print(f"   ❌ Stage 0 产物不完整 ({len(stage0_files)}/{len(required_files)})")
        issues.append({"type": "warning", "description": f"Stage 0 产物缺失: {', '.join([f for f in required_files if not (stage0_dir / f).exists()])}"})
    
    # 3. 检查 outputs_complete
    print("\n3. outputs_complete 检查")
    checks_total += 1
    if OUTPUTS_COMPLETE_DIR.exists():
        pdf_files = list(OUTPUTS_COMPLETE_DIR.glob("*.pdf"))
        if pdf_files:
            for pdf in pdf_files:
                size = pdf.stat().st_size
                print(f"   ✅ {pdf.name}: {size:,} bytes")
            checks_passed += 1
        else:
            print("   ⚠️ outputs_complete 存在但无 PDF 文件")
    else:
        print("   ❌ outputs_complete 目录不存在")
        issues.append({"type": "critical", "description": "outputs_complete 目录不存在"})
    
    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"检查通过: {checks_passed}/{checks_total}")
    
    if issues:
        print(f"\n发现 {len(issues)} 个问题:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. [{issue['type'].upper()}] {issue['description']}")
    
    # 保存报告
    report = f"""# 测试报告

**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**检查**: {checks_passed}/{checks_total} 通过

## 问题列表
"""
    if issues:
        for i, issue in enumerate(issues, 1):
            report += f"{i}. [{issue['type'].upper()}] {issue['description']}\n"
    else:
        report += "未发现任何问题\n"
    
    report_path = Path("test_report.md")
    report_path.write_text(report, encoding='utf-8')
    print(f"\n报告已保存: {report_path}")
    
    # 保存问题清单
    if issues:
        issues_path = Path("test_issues.json")
        issues_data = {
            "timestamp": datetime.now().isoformat(),
            "issues": issues
        }
        issues_path.write_text(json.dumps(issues_data, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"问题清单已保存: {issues_path}")
    
    # 退出码
    if any(issue['type'] == 'critical' for issue in issues):
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
