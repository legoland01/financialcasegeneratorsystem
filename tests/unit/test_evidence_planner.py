"""
Unit tests for evidence_planner.py - F2.3
"""

import pytest
from datetime import datetime
from src.core.evidence_planner import EvidencePlanner
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
        signing_date=datetime(2023, 1, 15)
    )
    return CaseData(
        plaintiff=plaintiff,
        defendant=defendant,
        contract=contract,
        breach=BreachInfo(
            breach_amount=1200000.00,
            breach_description="被告未按约定支付租金"
        )
    )


@pytest.fixture
def sample_claim_list():
    """创建测试用的ClaimList"""
    claims = [
        Claim(type="本金", amount=1500000.00),
        Claim(type="利息", amount=75000.00),
        Claim(type="违约金", amount=30000.00)
    ]
    return ClaimList(claims=claims)


class TestEvidencePlanner:
    """Test EvidencePlanner class"""

    def test_plan_returns_evidence_requirements(self, sample_case_data, sample_claim_list):
        """测试规划返回EvidenceRequirements"""
        planner = EvidencePlanner()
        result = planner.plan(sample_case_data, sample_claim_list)

        assert result is not None
        assert isinstance(result, EvidenceRequirements)

    def test_plan_has_requirements(self, sample_case_data, sample_claim_list):
        """测试规划包含证据需求"""
        planner = EvidencePlanner()
        result = planner.plan(sample_case_data, sample_claim_list)

        assert len(result.requirements) > 0

    def test_plan_case_type(self, sample_case_data, sample_claim_list):
        """测试规划包含案件类型"""
        planner = EvidencePlanner()
        result = planner.plan(sample_case_data, sample_claim_list)

        assert result.case_type == CaseType.FINANCING_LEASE

    def test_plan_includes_contract_evidence(self, sample_case_data, sample_claim_list):
        """测试规划包含合同类证据"""
        planner = EvidencePlanner()
        result = planner.plan(sample_case_data, sample_claim_list)

        has_contract = any(
            r.type == EvidenceType.CONTRACT for r in result.requirements
        )
        assert has_contract

    def test_plan_includes_voucher_evidence(self, sample_case_data, sample_claim_list):
        """测试规划包含凭证类证据"""
        planner = EvidencePlanner()
        result = planner.plan(sample_case_data, sample_claim_list)

        has_voucher = any(
            r.type == EvidenceType.VOUCHER for r in result.requirements
        )
        assert has_voucher


class TestEvidencePlannerRequirements:
    """Test evidence requirement details"""

    def test_requirement_has_facts_to_prove(self, sample_case_data, sample_claim_list):
        """测试证据需求包含待证事实"""
        planner = EvidencePlanner()
        result = planner.plan(sample_case_data, sample_claim_list)

        for req in result.requirements:
            assert len(req.facts_to_prove) > 0

    def test_requirement_has_claims_supported(self, sample_case_data, sample_claim_list):
        """测试证据需求包含支撑的诉求"""
        planner = EvidencePlanner()
        result = planner.plan(sample_case_data, sample_claim_list)

        for req in result.requirements:
            assert len(req.claims_supported) > 0


class TestEvidencePlannerEdgeCases:
    """Test edge cases"""

    def test_plan_empty_claims(self, sample_case_data):
        """测试空诉求列表"""
        empty_claims = ClaimList(claims=[])
        planner = EvidencePlanner()
        result = planner.plan(sample_case_data, empty_claims)

        assert result is not None

    def test_plan_single_claim(self, sample_case_data):
        """测试单个诉求"""
        single_claim = ClaimList(claims=[Claim(type="本金", amount=1000000)])
        planner = EvidencePlanner()
        result = planner.plan(sample_case_data, single_claim)

        assert result is not None
        assert len(result.requirements) > 0
