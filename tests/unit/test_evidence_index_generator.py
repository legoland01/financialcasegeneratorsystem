"""
Unit tests for evidence_index_generator.py
"""

import pytest
from datetime import datetime
from src.core.data_models import (
    CaseType,
    EvidenceType,
    AttachmentForm,
    Party,
    ContractInfo,
    BreachInfo,
    CaseData,
    Claim,
    ClaimList,
    EvidenceRequirement,
    EvidenceRequirements,
    EvidenceItem,
    EvidenceCollection,
    AttachmentInfo,
    EvidenceListItem,
    EvidenceList,
    EvidenceIndexItem,
    EvidenceIndex
)
from src.core.evidence_index_generator import EvidenceIndexGenerator


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
        address="北京市海淀区",
        legal_representative="李四"
    )
    contract = ContractInfo(
        type=CaseType.FINANCING_LEASE,
        subject="数控机床设备",
        amount=1500000.00,
        signing_date=datetime(2023, 1, 15),
        term_months=24
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
        Claim(type="本金", amount=1500000.00, description="请求判令被告支付欠款本金"),
        Claim(type="利息", amount=75000.00, description="请求判令被告支付欠款利息"),
        Claim(type="违约金", amount=30000.00, description="请求判令被告支付违约金")
    ]
    return ClaimList(
        claims=claims,
        litigation_cost=5000.00
    )


@pytest.fixture
def sample_evidence_list():
    """创建测试用的EvidenceList"""
    items = [
        EvidenceListItem(
            name="融资租赁合同",
            type=EvidenceType.CONTRACT,
            key_info={
                "合同编号": "2023-001",
                "金额": 1500000.00,
                "签订日期": "2023-01-15"
            },
            claims_supported=["本金", "利息"]
        ),
        EvidenceListItem(
            name="租金支付收据",
            type=EvidenceType.VOUCHER,
            key_info={
                "凭证类型": "收据",
                "金额": 300000.00
            },
            claims_supported=["本金"]
        ),
        EvidenceListItem(
            name="债务催收函",
            type=EvidenceType.DOCUMENT,
            key_info={
                "文书类型": "情况说明",
                "事由": "关于债务催收的情况说明"
            },
            claims_supported=["违约金"]
        ),
        EvidenceListItem(
            name="租赁物清单",
            type=EvidenceType.ATTACHMENT,
            key_info={
                "附件类型": "租赁物清单",
                "物品列表": [
                    {"名称": "设备1", "规格": "A型", "数量": 1, "单价": 800000.00, "金额": 800000.00},
                    {"名称": "设备2", "规格": "B型", "数量": 1, "单价": 700000.00, "金额": 700000.00}
                ]
            },
            claims_supported=["本金"]
        )
    ]
    return EvidenceList(
        items=items,
        case_type=CaseType.FINANCING_LEASE
    )


class TestEvidenceIndexGenerator:
    """Test EvidenceIndexGenerator class"""

    def test_generate_basic(self, sample_evidence_list, sample_claim_list):
        """测试基本生成功能"""
        generator = EvidenceIndexGenerator()
        index = generator.generate(sample_evidence_list, sample_claim_list)

        assert index is not None
        assert index.total_count == 4
        assert len(index.items) == 4

    def test_generate_contracts_have_purpose(self, sample_evidence_list, sample_claim_list):
        """测试合同类证据的证明目的"""
        generator = EvidenceIndexGenerator()
        index = generator.generate(sample_evidence_list, sample_claim_list)

        contract_items = [item for item in index.items if item.type == EvidenceType.CONTRACT]
        assert len(contract_items) == 1
        assert "合同关系" in contract_items[0].purpose

    def test_generate_voucher_have_purpose(self, sample_evidence_list, sample_claim_list):
        """测试凭证类证据的证明目的"""
        generator = EvidenceIndexGenerator()
        index = generator.generate(sample_evidence_list, sample_claim_list)

        voucher_items = [item for item in index.items if item.type == EvidenceType.VOUCHER]
        assert len(voucher_items) == 1
        assert "付款" in voucher_items[0].purpose or "履行" in voucher_items[0].purpose

    def test_generate_evidence_numbers_start_from_1(self, sample_evidence_list, sample_claim_list):
        """测试证据编号从1开始"""
        generator = EvidenceIndexGenerator()
        index = generator.generate(sample_evidence_list, sample_claim_list)

        for i, item in enumerate(index.items, 1):
            assert item.number == i

    def test_generate_to_text(self, sample_evidence_list, sample_claim_list):
        """测试生成文本格式"""
        generator = EvidenceIndexGenerator()
        text = generator.generate_to_text(sample_evidence_list, sample_claim_list)

        assert "证据清单" in text
        assert "证据总数" in text
        assert "证据1" in text

    def test_generate_to_dict(self, sample_evidence_list, sample_claim_list):
        """测试生成字典格式"""
        generator = EvidenceIndexGenerator()
        result = generator.generate_to_dict(sample_evidence_list, sample_claim_list)

        assert "items" in result
        assert "total_count" in result
        assert result["total_count"] == 4
        assert len(result["items"]) == 4

    def test_empty_evidence_list(self, sample_claim_list):
        """测试空证据列表"""
        empty_list = EvidenceList(items=[], case_type=CaseType.FINANCING_LEASE)
        generator = EvidenceIndexGenerator()
        index = generator.generate(empty_list, sample_claim_list)

        assert index.total_count == 0
        assert len(index.items) == 0

    def test_single_evidence(self, sample_claim_list):
        """测试单个证据"""
        single_list = EvidenceList(
            items=[
                EvidenceListItem(
                    name="融资租赁合同",
                    type=EvidenceType.CONTRACT,
                    key_info={},
                    claims_supported=["本金"]
                )
            ],
            case_type=CaseType.FINANCING_LEASE
        )
        generator = EvidenceIndexGenerator()
        index = generator.generate(single_list, sample_claim_list)

        assert index.total_count == 1
        assert index.items[0].number == 1

    def test_evidence_supports_multiple_claims(self, sample_evidence_list, sample_claim_list):
        """测试证据支撑多个诉求"""
        generator = EvidenceIndexGenerator()
        index = generator.generate(sample_evidence_list, sample_claim_list)

        contract_item = [item for item in index.items if item.name == "融资租赁合同"][0]
        assert len(contract_item.claims_supported) >= 1

    def test_all_evidence_types_have_purpose(self, sample_evidence_list, sample_claim_list):
        """测试所有证据类型都有证明目的"""
        generator = EvidenceIndexGenerator()
        index = generator.generate(sample_evidence_list, sample_claim_list)

        for item in index.items:
            assert item.purpose is not None
            assert len(item.purpose) > 0

    def test_index_item_dict_format(self, sample_evidence_list, sample_claim_list):
        """测试索引项字典格式"""
        generator = EvidenceIndexGenerator()
        index = generator.generate(sample_evidence_list, sample_claim_list)

        item_dict = index.items[0].to_dict()
        assert "number" in item_dict
        assert "name" in item_dict
        assert "type" in item_dict
        assert "purpose" in item_dict
        assert "claims_supported" in item_dict

    def test_index_json_serialization(self, sample_evidence_list, sample_claim_list):
        """测试索引JSON序列化"""
        generator = EvidenceIndexGenerator()
        index = generator.generate(sample_evidence_list, sample_claim_list)

        json_str = index.to_json()
        assert isinstance(json_str, str)
        assert "证据清单" in json_str or "融资租赁合同" in json_str
