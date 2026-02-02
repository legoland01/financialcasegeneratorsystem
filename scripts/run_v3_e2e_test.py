#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v3.0 端到端测试脚本
"""

import sys
from pathlib import Path
from datetime import datetime

# 切换到项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from core.main import FinancialCaseGenerator
from core.data_models import (
    CaseData, Party, ContractInfo, BreachInfo,
    ClaimList, Claim, CaseType
)


def create_test_case_data():
    return CaseData(
        plaintiff=Party(
            name="东方金融租赁有限公司",
            credit_code="91310000607878901A",
            address="上海市浦东新区陆家嘴环路1000号",
            legal_representative="张明远"
        ),
        defendant=Party(
            name="南昌宏昌商业零售有限公司",
            credit_code="91360100683456012B",
            address="江西省南昌市红谷滩新区凤凰中大道1000号",
            legal_representative="李建国"
        ),
        contract=ContractInfo(
            type=CaseType.FINANCING_LEASE,
            subject="中央空调设备一套",
            amount=15000000.0,
            signing_date=datetime(2023, 1, 15),
            term_months=36
        ),
        paid_amount=7500000.0,
        remaining_amount=7500000.0,
        breach=BreachInfo(
            breach_date=datetime(2023, 7, 15),
            breach_amount=7500000.0,
            breach_description="自2023年7月起未按约定支付租金"
        ),
        extracted_at=datetime.now()
    )


def create_test_claim_list():
    return ClaimList(
        claims=[
            Claim(type="本金", amount=7500000.0, description="要求支付剩余租金"),
            Claim(type="利息", amount=375000.0, description="要求支付逾期利息")
        ],
        litigation_cost=68688.0
    )


def check_no_deanonymization(text):
    patterns = ["某某", "XX", "XXX", "某公司", "某年某月", "人民币叁仟万元整", "人民币壹亿伍仟万元整", "若干", "若干台"]
    return [p for p in patterns if p in text]


def main():
    print("=" * 60)
    print("v3.0 端到端测试")
    print("=" * 60)

    case_data = create_test_case_data()
    claim_list = create_test_claim_list()

    print(f"\n原告: {case_data.plaintiff.name}")
    print(f"被告: {case_data.defendant.name}")
    print(f"合同金额: {case_data.contract.amount:,.0f}元")

    generator = FinancialCaseGenerator(output_dir=project_root / "output_v3_test")

    print("\n开始生成...")
    result = generator.generate_from_data(case_data, claim_list, "v3_test_output")

    if result.success:
        print(f"\n生成成功!")
        print(f"证据列表数量: {len(result.evidence_list.items)}")
        print(f"生成证据数量: {len(result.generated_evidence)}")
        print(f"质量评分: {result.validation_report.score}/100")
        
        all_pass = True
        for item in result.evidence_list.items:
            issues = check_no_deanonymization(str(item.key_info))
            if issues:
                print(f"❌ {item.name}包含脱敏标记: {issues}")
                all_pass = False
            else:
                print(f"✅ {item.name}")
        
        print("\n" + "=" * 60)
        if all_pass:
            print("✅ 端到端测试通过! v3.0架构正确实现脱敏标记隔离")
            return 0
        else:
            print("❌ 端到端测试失败!")
            return 1
    else:
        print(f"生成失败: {result.errors}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
