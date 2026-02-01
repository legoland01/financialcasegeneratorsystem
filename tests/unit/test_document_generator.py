"""
Unit tests for document_generator.py
"""

import pytest
from datetime import datetime
from src.core.data_models import (
    CaseType,
    EvidenceType,
    Party,
    ContractInfo,
    BreachInfo,
    CaseData,
    Claim,
    ClaimList,
    EvidenceListItem,
    EvidenceList,
    GeneratedEvidence
)
from src.core.document_generator import DocumentGenerator


@pytest.fixture
def sample_case_data():
    """创建测试用的CaseData"""
    plaintiff = Party(
        name="测试原告融资租赁公司",
        credit_code="91110000123456789X",
        address="北京市朝阳区金融大街1号",
        legal_representative="张三",
        bank_account="123456789012"
    )
    defendant = Party(
        name="测试被告制造有限公司",
        credit_code="91110000987654321Y",
        address="北京市海淀区科技园路88号",
        legal_representative="李四",
        bank_account="987654321098"
    )
    contract = ContractInfo(
        type=CaseType.FINANCING_LEASE,
        subject="数控机床设备",
        amount=1500000.00,
        signing_date=datetime(2023, 1, 15),
        performance_date=datetime(2023, 1, 20),
        term_months=24
    )
    return CaseData(
        plaintiff=plaintiff,
        defendant=defendant,
        contract=contract,
        paid_amount=300000.00,
        remaining_amount=1200000.00,
        breach=BreachInfo(
            breach_date=datetime(2023, 6, 1),
            breach_amount=1200000.00,
            breach_description="被告自2023年6月起未按约定支付租金"
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
                "合同类型": "融资租赁合同"
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
                "文书类型": "催款函",
                "事由": "关于催收租金的函件"
            },
            claims_supported=["违约金"]
        ),
        EvidenceListItem(
            name="租赁物清单",
            type=EvidenceType.ATTACHMENT,
            key_info={
                "附件类型": "租赁物清单",
                "物品列表": [
                    {"名称": "数控机床", "规格": "VMC-850", "数量": 1, "单价": 800000.00, "金额": 800000.00},
                    {"名称": "加工中心", "规格": "MCV-1260", "数量": 1, "单价": 700000.00, "金额": 700000.00}
                ]
            },
            claims_supported=["本金"]
        )
    ]
    return EvidenceList(items=items, case_type=CaseType.FINANCING_LEASE)


class TestDocumentGenerator:
    """Test DocumentGenerator class"""

    def test_generate_creates_evidence(self, sample_evidence_list, sample_case_data, sample_claim_list):
        """测试生成证据"""
        generator = DocumentGenerator()
        result = generator.generate(sample_evidence_list, sample_case_data, sample_claim_list)

        assert len(result) == 4
        for evidence in result:
            assert evidence is not None
            assert evidence.filename is not None
            assert evidence.content is not None
            assert evidence.evidence_type is not None

    def test_generate_contracts(self, sample_evidence_list, sample_case_data, sample_claim_list):
        """测试生成合同类证据"""
        generator = DocumentGenerator()
        result = generator.generate(sample_evidence_list, sample_case_data, sample_claim_list)

        contract_evidence = [e for e in result if e.evidence_type == EvidenceType.CONTRACT]
        assert len(contract_evidence) == 1
        assert "融资租赁合同" in contract_evidence[0].content

    def test_generate_vouchers(self, sample_evidence_list, sample_case_data, sample_claim_list):
        """测试生成凭证类证据"""
        generator = DocumentGenerator()
        result = generator.generate(sample_evidence_list, sample_case_data, sample_claim_list)

        voucher_evidence = [e for e in result if e.evidence_type == EvidenceType.VOUCHER]
        assert len(voucher_evidence) == 1
        assert "收据" in voucher_evidence[0].content or "金额" in voucher_evidence[0].content

    def test_generate_documents(self, sample_evidence_list, sample_case_data, sample_claim_list):
        """测试生成文书类证据"""
        generator = DocumentGenerator()
        result = generator.generate(sample_evidence_list, sample_case_data, sample_claim_list)

        document_evidence = [e for e in result if e.evidence_type == EvidenceType.DOCUMENT]
        assert len(document_evidence) == 1
        assert "催收" in document_evidence[0].content or "函" in document_evidence[0].content

    def test_generate_attachments(self, sample_evidence_list, sample_case_data, sample_claim_list):
        """测试生成附件类证据"""
        generator = DocumentGenerator()
        result = generator.generate(sample_evidence_list, sample_case_data, sample_claim_list)

        attachment_evidence = [e for e in result if e.evidence_type == EvidenceType.ATTACHMENT]
        assert len(attachment_evidence) == 1
        assert "清单" in attachment_evidence[0].content or "设备" in attachment_evidence[0].content

    def test_generate_filename_format(self, sample_evidence_list, sample_case_data, sample_claim_list):
        """测试生成文件名格式"""
        generator = DocumentGenerator()
        result = generator.generate(sample_evidence_list, sample_case_data, sample_claim_list)

        for evidence in result:
            assert evidence.filename.endswith('.txt')
            assert '_' in evidence.filename

    def test_generate_includes_party_info(self, sample_evidence_list, sample_case_data, sample_claim_list):
        """测试生成内容包含当事人信息"""
        generator = DocumentGenerator()
        result = generator.generate(sample_evidence_list, sample_case_data, sample_claim_list)

        for evidence in result:
            assert "测试原告" in evidence.content or "测试被告" in evidence.content

    def test_generate_includes_contract_info(self, sample_evidence_list, sample_case_data, sample_claim_list):
        """测试生成内容包含合同信息"""
        generator = DocumentGenerator()
        result = generator.generate(sample_evidence_list, sample_case_data, sample_claim_list)

        for evidence in result:
            assert "1500000" in evidence.content or "1500000.00" in evidence.content

    def test_generate_empty_list(self, sample_case_data, sample_claim_list):
        """测试生成空证据列表"""
        empty_list = EvidenceList(items=[], case_type=CaseType.FINANCING_LEASE)
        generator = DocumentGenerator()
        result = generator.generate(empty_list, sample_case_data, sample_claim_list)

        assert len(result) == 0

    def test_generate_single_evidence(self, sample_case_data, sample_claim_list):
        """测试生成单个证据"""
        single_list = EvidenceList(
            items=[
                EvidenceListItem(
                    name="融资租赁合同",
                    type=EvidenceType.CONTRACT,
                    key_info={"合同编号": "2023-001"},
                    claims_supported=["本金"]
                )
            ],
            case_type=CaseType.FINANCING_LEASE
        )
        generator = DocumentGenerator()
        result = generator.generate(single_list, sample_case_data, sample_claim_list)

        assert len(result) == 1
        assert result[0].evidence_type == EvidenceType.CONTRACT

    def test_number_to_chinese(self):
        """测试数字转中文大写"""
        generator = DocumentGenerator()

        assert generator._number_to_chinese(100) == "壹佰元整"
        assert generator._number_to_chinese(1234) == "壹仟贰佰叁拾肆元整"

    def test_generate_filename_special_chars(self):
        """测试生成带特殊字符的文件名"""
        generator = DocumentGenerator()
        filename = generator._generate_filename("测试文档/名称", "文档")
        assert '/' not in filename


class TestDocumentGeneratorWithLLM:
    """Test DocumentGenerator with LLM client"""

    def test_generate_with_llm_client(self, sample_evidence_list, sample_case_data, sample_claim_list):
        """测试使用LLM客户端生成"""
        class MockLLMClient:
            def complete(self, prompt):
                return "模拟生成的合同内容"

        generator = DocumentGenerator(llm_client=MockLLMClient())
        result = generator.generate(sample_evidence_list, sample_case_data, sample_claim_list)

        assert len(result) == 4


class TestContractContent:
    """Test contract content generation"""

    def test_contract_contains_parties(self, sample_case_data, sample_claim_list):
        """测试合同包含当事人信息"""
        from src.core.document_generator import DocumentGenerator

        generator = DocumentGenerator()
        contract_list = EvidenceList(
            items=[
                EvidenceListItem(
                    name="融资租赁合同",
                    type=EvidenceType.CONTRACT,
                    key_info={"合同编号": "2023-001"},
                    claims_supported=["本金"]
                )
            ],
            case_type=CaseType.FINANCING_LEASE
        )
        result = generator.generate(contract_list, sample_case_data, sample_claim_list)

        content = result[0].content
        assert "测试原告" in content
        assert "测试被告" in content

    def test_contract_contains_amount(self, sample_case_data, sample_claim_list):
        """测试合同包含金额"""
        from src.core.document_generator import DocumentGenerator

        generator = DocumentGenerator()
        contract_list = EvidenceList(
            items=[
                EvidenceListItem(
                    name="融资租赁合同",
                    type=EvidenceType.CONTRACT,
                    key_info={"合同编号": "2023-001"},
                    claims_supported=["本金"]
                )
            ],
            case_type=CaseType.FINANCING_LEASE
        )
        result = generator.generate(contract_list, sample_case_data, sample_claim_list)

        content = result[0].content
        assert "1500000" in content

    def test_contract_contains_date(self, sample_case_data, sample_claim_list):
        """测试合同包含日期"""
        from src.core.document_generator import DocumentGenerator

        generator = DocumentGenerator()
        contract_list = EvidenceList(
            items=[
                EvidenceListItem(
                    name="融资租赁合同",
                    type=EvidenceType.CONTRACT,
                    key_info={"合同编号": "2023-001"},
                    claims_supported=["本金"]
                )
            ],
            case_type=CaseType.FINANCING_LEASE
        )
        result = generator.generate(contract_list, sample_case_data, sample_claim_list)

        content = result[0].content
        assert "2023年" in content or "01月" in content or "15日" in content
