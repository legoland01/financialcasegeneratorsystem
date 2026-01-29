#!/usr/bin/env python3
"""
测试报告生成器
分析 CI/CD 测试结果，生成测试报告
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import subprocess

OUTPUTS_DIR = Path("outputs")
OUTPUTS_COMPLETE_DIR = Path("outputs_complete")
TEST_DATA_DIR = Path("test_data")

class TestReporter:
    def __init__(self):
        self.results = []
        self.issues = []
        self.recommendations = []
    
    def check_judgment_file(self):
        """检查判决书文件"""
        print("=" * 60)
        print("1. 判决书文件检查")
        print("=" * 60)
        
        pdf_files = list(TEST_DATA_DIR.glob("*.pdf"))
        if not pdf_files:
            self.issues.append({
                "type": "critical",
                "category": "文件缺失",
                "description": "test_data/ 目录中没有 PDF 判决书文件",
                "impact": "无法进行任何测试"
            })
            print("❌ 未找到判决书文件")
            return False
        
        for pdf in pdf_files:
            size = pdf.stat().st_size
            print(f"✅ {pdf.name}: {size:,} bytes")
        
        self.results.append({"判决书文件": len(pdf_files)})
        return True
    
    def check_stage0_outputs(self):
        """检查 Stage 0 输出"""
        print("\n" + "=" * 60)
        print("2. Stage 0 产物检查")
        print("=" * 60)
        
        stage0_dir = OUTPUTS_DIR / "stage0"
        required_files = [
            "0.1_structured_extraction.json",
            "0.2_anonymization_plan.json", 
            "0.3_transaction_reconstruction.json",
            "0.4_key_numbers.json",
            "0.5_evidence_planning.json"
        ]
        
        missing = []
        for filename in required_files:
            filepath = stage0_dir / filename
            if filepath.exists():
                size = filepath.stat().st_size
                print(f"✅ {filename}: {size:,} bytes")
            else:
                print(f"❌ {filename}: 不存在")
                missing.append(filename)
        
        if missing:
            self.issues.append({
                "type": "critical",
                "category": "Stage 0 产物缺失",
                "description": f"缺少文件: {', '.join(missing)}",
                "impact": "无法进行后续阶段",
                "solution": "检查 LLM API 调用是否成功，或增加超时时间"
            })
        
        self.results.append({"Stage0产物": len(required_files) - len(missing)})
        return len(missing) == 0
    
    def check_stage1_outputs(self):
        """检查 Stage 1 输出"""
        print("\n" + "=" * 60)
        print("3. Stage 1 产物检查")
        print("=" * 60)
        
        stage1_dir = OUTPUTS_DIR / "stage1"
        if not stage1_dir.exists():
            self.issues.append({
                "type": "critical",
                "category": "Stage 1 未运行",
                "description": "outputs/stage1/ 目录不存在",
                "impact": "无法生成证据文件和 PDF",
                "solution": "检查 run_stage1() 是否执行，或增加超时时间"
            })
            print("❌ stage1/ 目录不存在")
            return False
        
        files = list(stage1_dir.glob("*.txt")) + list(stage1_dir.glob("*.json"))
        print(f"找到 {len(files)} 个文件:")
        for f in files:
            print(f"  ✅ {f.name}")
        
        # 检查关键文件
        key_files = ["plaintiff_package.json", "民事起诉状.txt"]
        missing = [f for f in key_files if not (stage1_dir / f).exists()]
        
        if missing:
            self.issues.append({
                "type": "warning",
                "category": "Stage 1 文件缺失",
                "description": f"缺少关键文件: {', '.join(missing)}",
                "impact": "PDF 生成可能不完整",
                "solution": "检查 Stage 1 服务是否正确生成所有文件"
            })
        
        self.results.append({"Stage1产物": len(files)})
        return len(missing) == 0
    
    def check_outputs_complete(self):
        """检查 outputs_complete 目录"""
        print("\n" + "=" * 60)
        print("4. outputs_complete 检查")
        print("=" * 60)
        
        if not OUTPUTS_COMPLETE_DIR.exists():
            self.issues.append({
                "type": "critical",
                "category": "outputs_complete 未生成",
                "description": "outputs_complete/ 目录不存在",
                "impact": "无法生成最终证据 PDF",
                "solution": "检查 run_pdf_generation() 是否执行"
            })
            print("❌ outputs_complete/ 目录不存在")
            return False
        
        files = list(OUTPUTS_COMPLETE_DIR.glob("*.pdf"))
        if not files:
            self.issues.append({
                "type": "critical",
                "category": "PDF 未生成",
                "description": "outputs_complete/ 目录中没有 PDF 文件",
                "impact": "无法提供最终证据材料",
                "solution": "检查 run_pdf_generation() 是否正确执行"
            })
            print("❌ 未找到 PDF 文件")
            return False
        
        for pdf in files:
            size = pdf.stat().st_size
            print(f"✅ {pdf.name}: {size:,} bytes ({size/1024:.1f} KB)")
        
        self.results.append({"PDF文件": len(files)})
        return True
    
    def check_data_consistency(self):
        """检查数据一致性"""
        print("\n" + "=" * 60)
        print("5. 数据一致性检查")
        print("=" * 60)
        
        key_numbers_file = OUTPUTS_DIR / "stage0" / "0.4_key_numbers.json"
        if not key_numbers_file.exists():
            print("⚠️ 无法检查数据一致性 (文件不存在)")
            return None
        
        data = json.loads(key_numbers_file.read_text())
        
        # 检查设备金额
        equipment_list = data.get("租赁物清单", [])
        total_equipment = sum(
            eq.get("评估价值", 0) or 0 
            for eq in equipment_list 
            if eq.get("评估价值")
        )
        
        contract_base = data.get("合同基础金额", {})
        if isinstance(contract_base, dict):
            contract_amount = contract_base.get("调整后合同金额", {}).get("数值",
                     contract_base.get("原合同金额", {}).get("数值", 0))
        else:
            contract_amount = contract_base
        
        print(f"设备总金额: {total_equipment:,} 元")
        print(f"合同金额: {contract_amount:,} 元")
        
        if total_equipment == contract_amount:
            print("✅ 金额一致")
            self.results.append({"数据一致性": "通过"})
            return True
        else:
            diff = abs(total_equipment - contract_amount)
            self.issues.append({
                "type": "warning",
                "category": "数据不一致",
                "description": f"设备金额 ({total_equipment:,}) != 合同金额 ({contract_amount:,})",
                "impact": "数据质量问题",
                "solution": "修复 fix_key_numbers() 函数确保金额一致"
            })
            print(f"❌ 金额不一致，差额: {diff:,} 元")
            self.results.append({"数据一致性": "失败"})
            return False
    
    def generate_report(self) -> str:
        """生成测试报告"""
        report = []
        report.append("# 测试报告")
        report.append(f"\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**测试目录**: {Path.cwd()}")
        
        report.append("\n## 测试结果汇总")
        for result in self.results:
            for key, value in result.items():
                report.append(f"- {key}: {value}")
        
        report.append("\n## 发现的问题")
        if self.issues:
            for i, issue in enumerate(self.issues, 1):
                report.append(f"\n### 问题 {i}: {issue['type'].upper()} - {issue['category']}")
                report.append(f"**描述**: {issue['description']}")
                report.append(f"**影响**: {issue['impact']}")
                report.append(f"**解决方案**: {issue['solution']}")
        else:
            report.append("未发现任何问题！")
        
        report.append("\n## 建议")
        for rec in self.recommendations:
            report.append(f"- {rec}")
        
        report.append("\n---\n")
        report.append(f"**报告版本**: 1.0")
        
        return "\n".join(report)
    
    def run_full_analysis(self) -> str:
        """运行完整分析"""
        print("\n" + "#" * 60)
        print("# 测试报告生成器")
        print("#" * 60)
        
        self.check_judgment_file()
        self.check_stage0_outputs()
        self.check_stage1_outputs()
        self.check_outputs_complete()
        self.check_data_consistency()
        
        report = self.generate_report()
        print("\n" + "=" * 60)
        print("测试报告")
        print("=" * 60)
        print(report)
        
        return report

def main():
    reporter = TestReporter()
    report = reporter.run_full_analysis()
    
    # 保存报告
    report_path = Path("test_report.md")
    report_path.write_text(report, encoding='utf-8')
    print(f"\n报告已保存到: {report_path}")
    
    # 保存问题清单
    if reporter.issues:
        issues_path = Path("test_issues.json")
        issues_data = {
            "timestamp": datetime.now().isoformat(),
            "issues": reporter.issues
        }
        issues_path.write_text(json.dumps(issues_data, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"问题清单已保存到: {issues_path}")
    
    # 返回退出码
    if any(issue['type'] == 'critical' for issue in reporter.issues):
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
