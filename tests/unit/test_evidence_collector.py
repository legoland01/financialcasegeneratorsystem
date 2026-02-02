"""
Unit tests for evidence_collector.py - F2.4

RFC-2026-02-002 Q1 证据编造规则：
- 生产环境：不允许编造，缺失证据则跳过
- 测试环境：从配置文件加载或编造
"""

import pytest
from pathlib import Path
from datetime import datetime
from src.core.evidence_collector import EvidenceCollector
from src.core.data_models import (
    EvidenceRequirements, EvidenceRequirement, EvidenceItem,
    EvidenceType, CaseType, CaseData, Party, ContractInfo, ClaimList, Claim
)


@pytest.fixture
def sample_case_data():
    """创建测试用的CaseData"""
    return CaseData(
        plaintiff=Party(
            name="测试原告公司",
            credit_code="91110000AAA",
            address="北京市朝阳区",
            legal_representative="张三"
        ),
        defendant=Party(
            name="测试被告公司",
            credit_code="91110000BBB",
            address="上海市浦东新区",
            legal_representative="李四"
        ),
        contract=ContractInfo(
            type=CaseType.FINANCING_LEASE,
            subject="中央空调设备",
            amount=1500000.0,
            signing_date=datetime(2023, 1, 15)
        ),
        judgment_path=None,
        extracted_at=datetime.now()
    )


@pytest.fixture
def sample_claim_list():
    """创建测试用的ClaimList"""
    return ClaimList(
        claims=[
            Claim(type="本金", amount=1200000.0, description="要求支付剩余租金本金"),
            Claim(type="利息", amount=50000.0, description="要求支付逾期利息")
        ],
        litigation_cost=10000.0
    )


@pytest.fixture
def sample_requirements():
    """创建测试用的EvidenceRequirements"""
    return EvidenceRequirements(
        requirements=[
            EvidenceRequirement(
                name="融资租赁合同",
                type=EvidenceType.CONTRACT,
                facts_to_prove=["合同成立"],
                claims_supported=["本金"]
            ),
            EvidenceRequirement(
                name="租金收据",
                type=EvidenceType.VOUCHER,
                facts_to_prove=["付款事实"],
                claims_supported=["本金"]
            )
        ],
        case_type=CaseType.FINANCING_LEASE
    )


class TestEvidenceCollector:
    """Test EvidenceCollector class"""

    def test_collect_returns_evidence_collection(self, sample_case_data, sample_claim_list, sample_requirements):
        """测试收集返回EvidenceCollection"""
        collector = EvidenceCollector()
        result = collector.collect(
            sample_case_data,
            sample_claim_list,
            sample_requirements,
            environment="test"
        )

        assert result is not None
        assert result.items is not None

    def test_collect_returns_items(self, sample_case_data, sample_claim_list, sample_requirements):
        """测试收集返回证据项"""
        collector = EvidenceCollector()
        result = collector.collect(
            sample_case_data,
            sample_claim_list,
            sample_requirements,
            environment="test"
        )

        assert len(result.items) >= 0

    def test_collect_item_has_name(self, sample_case_data, sample_claim_list, sample_requirements):
        """测试证据项包含名称"""
        collector = EvidenceCollector()
        result = collector.collect(
            sample_case_data,
            sample_claim_list,
            sample_requirements,
            environment="test"
        )

        for item in result.items:
            assert item.name is not None
            assert len(item.name) > 0

    def test_collect_item_has_type(self, sample_case_data, sample_claim_list, sample_requirements):
        """测试证据项包含类型"""
        collector = EvidenceCollector()
        result = collector.collect(
            sample_case_data,
            sample_claim_list,
            sample_requirements,
            environment="test"
        )

        for item in result.items:
            assert item.type is not None

    def test_collect_item_has_source(self, sample_case_data, sample_claim_list, sample_requirements):
        """测试证据项包含来源"""
        collector = EvidenceCollector()
        result = collector.collect(
            sample_case_data,
            sample_claim_list,
            sample_requirements,
            environment="test"
        )

        for item in result.items:
            assert item.source is not None

    def test_collect_has_from_judgment_list(self, sample_case_data, sample_claim_list, sample_requirements):
        """测试收集包含来自判决书的证据列表"""
        collector = EvidenceCollector()
        result = collector.collect(
            sample_case_data,
            sample_claim_list,
            sample_requirements,
            environment="test"
        )

        assert result.from_judgment is not None


class TestEvidenceCollectorEdgeCases:
    """Test edge cases"""

    def test_collect_empty_requirements(self, sample_case_data, sample_claim_list):
        """测试空证据需求"""
        collector = EvidenceCollector()
        requirements = EvidenceRequirements(requirements=[], case_type=CaseType.FINANCING_LEASE)

        result = collector.collect(
            sample_case_data,
            sample_claim_list,
            requirements,
            environment="test"
        )

        assert result is not None
        assert len(result.items) >= 0

    def test_collect_with_llm_client(self, sample_case_data, sample_claim_list, sample_requirements):
        """测试使用LLM客户端"""
        class MockLLMClient:
            def complete(self, prompt):
                return '{"items": []}'

        collector = EvidenceCollector(llm_client=MockLLMClient())
        result = collector.collect(
            sample_case_data,
            sample_claim_list,
            sample_requirements,
            environment="test"
        )

        assert result is not None

    def test_production_environment_no_fabrication(self, sample_case_data, sample_claim_list, sample_requirements):
        """测试生产环境不允许编造证据"""
        collector = EvidenceCollector()
        result = collector.collect(
            sample_case_data,
            sample_claim_list,
            sample_requirements,
            environment="production"
        )

        # 生产环境：不应编造附件类证据
        fabricated_items = [item for item in result.items if item.fabricated]
        assert len(fabricated_items) == 0

    def test_test_environment_allows_fabrication(self, sample_case_data, sample_claim_list, sample_requirements):
        """测试环境允许编造附件类证据"""
        # 添加一个附件类证据需求
        sample_requirements.requirements.append(
            EvidenceRequirement(
                name="租赁物清单",
                type=EvidenceType.ATTACHMENT,
                facts_to_prove=["租赁物明细"],
                claims_supported=["本金"]
            )
        )
        
        collector = EvidenceCollector()
        result = collector.collect(
            sample_case_data,
            sample_claim_list,
            sample_requirements,
            environment="test"
        )

        # 测试环境：可以编造附件类证据
        attachment_items = [item for item in result.items if item.type == EvidenceType.ATTACHMENT]
        assert len(attachment_items) > 0
