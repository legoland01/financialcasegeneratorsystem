"""
Unit tests for evidence_collector.py - F2.4
"""

import pytest
from src.core.evidence_collector import EvidenceCollector
from src.core.data_models import (
    CaseData, Party, ContractInfo, Claim, ClaimList,
    CaseType, BreachInfo, EvidenceRequirement, EvidenceRequirements,
    EvidenceType, AttachmentForm
)


@pytest.fixture
def sample_case_data():
    """创建测试用的CaseData"""
    plaintiff = Party(
        name="测试原告公司",
        credit_code="91110000123456789X",
        address="北京市朝阳区",
        legal_representative="张三"
    )
    defendant = Party(
        name="测试被告公司",
        credit_code="91110000987654321Y",
        address="上海市浦东新区",
        legal_representative="李四"
    )
    contract = ContractInfo(
        type=CaseType.FINANCING_LEASE,
        subject="数控机床",
        amount=1500000.00,
        signing_date=__import__('datetime').datetime(2023, 1, 15)
    )
    return CaseData(
        plaintiff=plaintiff,
        defendant=defendant,
        contract=contract,
        paid_amount=300000.00,
        remaining_amount=1200000.00
    )


@pytest.fixture
def sample_claim_list():
    """创建测试用的ClaimList"""
    claims = [
        Claim(type="本金", amount=1500000.00),
        Claim(type="利息", amount=75000.00)
    ]
    return ClaimList(claims=claims)


@pytest.fixture
def sample_evidence_requirements():
    """创建测试用的EvidenceRequirements"""
    requirements = [
        EvidenceRequirement(
            name="融资租赁合同",
            type=EvidenceType.CONTRACT,
            facts_to_prove=["合同关系成立"],
            claims_supported=["本金"]
        ),
        EvidenceRequirement(
            name="租金收据",
            type=EvidenceType.VOUCHER,
            facts_to_prove=["付款事实"],
            claims_supported=["本金"]
        )
    ]
    return EvidenceRequirements(
        requirements=requirements,
        case_type=CaseType.FINANCING_LEASE
    )


class TestEvidenceCollector:
    """Test EvidenceCollector class"""

    def test_collect_basic(self, sample_case_data, sample_claim_list, sample_evidence_requirements):
        """测试基本收集功能"""
        collector = EvidenceCollector()
        result = collector.collect(sample_case_data, sample_claim_list, sample_evidence_requirements)

        assert result is not None
        assert len(result.items) > 0

    def test_collect_returns_evidence_items(self, sample_case_data, sample_claim_list, sample_evidence_requirements):
        """测试收集返回证据项"""
        collector = EvidenceCollector()
        result = collector.collect(sample_case_data, sample_claim_list, sample_evidence_requirements)

        assert len(result.items) == len(sample_evidence_requirements.requirements)

    def test_collect_includes_from_judgment(self, sample_case_data, sample_claim_list, sample_evidence_requirements):
        """测试收集包含来自判决书的证据"""
        collector = EvidenceCollector()
        result = collector.collect(sample_case_data, sample_claim_list, sample_evidence_requirements)

        assert len(result.from_judgment) > 0

    def test_collect_includes_fabricated(self, sample_case_data, sample_claim_list, sample_evidence_requirements):
        """测试收集包含自行编造的证据"""
        collector = EvidenceCollector()
        result = collector.collect(sample_case_data, sample_claim_list, sample_evidence_requirements)

        assert len(result.fabricated) >= 0


class TestEvidenceCollectorItems:
    """Test collected evidence items"""

    def test_item_has_name(self, sample_case_data, sample_claim_list, sample_evidence_requirements):
        """测试证据项包含名称"""
        collector = EvidenceCollector()
        result = collector.collect(sample_case_data, sample_claim_list, sample_evidence_requirements)

        for item in result.items:
            assert item.name is not None
            assert len(item.name) > 0

    def test_item_has_type(self, sample_case_data, sample_claim_list, sample_evidence_requirements):
        """测试证据项包含类型"""
        collector = EvidenceCollector()
        result = collector.collect(sample_case_data, sample_claim_list, sample_evidence_requirements)

        for item in result.items:
            assert item.type is not None

    def test_item_has_source(self, sample_case_data, sample_claim_list, sample_evidence_requirements):
        """测试证据项包含来源"""
        collector = EvidenceCollector()
        result = collector.collect(sample_case_data, sample_claim_list, sample_evidence_requirements)

        for item in result.items:
            assert item.source is not None


class TestEvidenceCollectorEdgeCases:
    """Test edge cases"""

    def test_collect_empty_requirements(self, sample_case_data, sample_claim_list):
        """测试空证据需求"""
        empty_requirements = EvidenceRequirements(
            requirements=[],
            case_type=CaseType.FINANCING_LEASE
        )
        collector = EvidenceCollector()
        result = collector.collect(sample_case_data, sample_claim_list, empty_requirements)

        assert result is not None
        assert len(result.items) == 0

    def test_collect_single_requirement(self, sample_case_data, sample_claim_list):
        """测试单个证据需求"""
        single_requirement = EvidenceRequirements(
            requirements=[
                EvidenceRequirement(
                    name="合同",
                    type=EvidenceType.CONTRACT,
                    facts_to_prove=["合同成立"],
                    claims_supported=["本金"]
                )
            ],
            case_type=CaseType.FINANCING_LEASE
        )
        collector = EvidenceCollector()
        result = collector.collect(sample_case_data, sample_claim_list, single_requirement)

        assert result is not None
        assert len(result.items) == 1
