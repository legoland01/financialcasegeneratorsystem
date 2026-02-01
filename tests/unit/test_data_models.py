"""
Unit tests for data_models.py
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
    AttachmentPlan,
    EvidenceRequirement,
    EvidenceRequirements,
    EvidenceItem,
    EvidenceCollection,
    AttachmentInfo,
    EvidenceListItem,
    EvidenceList,
    GeneratedEvidence,
    EvidenceIndexItem,
    EvidenceIndex
)


class TestCaseType:
    """Test CaseType enum"""

    def test_case_type_values(self):
        assert CaseType.FINANCING_LEASE.value == "融资租赁"
        assert CaseType.LOAN.value == "金融借款"
        assert CaseType.FACTORING.value == "保理"
        assert CaseType.GUARANTEE.value == "担保"


class TestEvidenceType:
    """Test EvidenceType enum"""

    def test_evidence_type_values(self):
        assert EvidenceType.CONTRACT.value == "合同类"
        assert EvidenceType.VOUCHER.value == "凭证类"
        assert EvidenceType.DOCUMENT.value == "文书类"
        assert EvidenceType.ATTACHMENT.value == "附件类"


class TestAttachmentForm:
    """Test AttachmentForm enum"""

    def test_attachment_form_values(self):
        assert AttachmentForm.INDEPENDENT_FILE.value == "独立文件"
        assert AttachmentForm.IN_BODY.value == "正文包含"
        assert AttachmentForm.NO_ATTACHMENT.value == "不需附件"


class TestParty:
    """Test Party dataclass"""

    def test_party_creation(self):
        party = Party(
            name="测试公司",
            credit_code="91110000123456789X",
            address="北京市朝阳区测试路100号",
            legal_representative="张三",
            bank_account="123456789012"
        )
        assert party.name == "测试公司"
        assert party.credit_code == "91110000123456789X"
        assert party.address == "北京市朝阳区测试路100号"
        assert party.legal_representative == "张三"
        assert party.bank_account == "123456789012"

    def test_party_to_dict(self):
        party = Party(
            name="测试公司",
            credit_code="91110000123456789X",
            address="北京市朝阳区测试路100号",
            legal_representative="张三"
        )
        result = party.to_dict()
        assert result["name"] == "测试公司"
        assert result["credit_code"] == "91110000123456789X"
        assert result["address"] == "北京市朝阳区测试路100号"
        assert result["legal_representative"] == "张三"
        assert result["bank_account"] is None

    def test_party_optional_bank_account(self):
        party = Party(
            name="测试公司",
            credit_code="91110000123456789X",
            address="北京市朝阳区测试路100号",
            legal_representative="张三"
        )
        assert party.bank_account is None


class TestContractInfo:
    """Test ContractInfo dataclass"""

    def test_contract_info_creation(self):
        contract = ContractInfo(
            type=CaseType.FINANCING_LEASE,
            subject="数控机床设备",
            amount=1500000.00,
            signing_date=datetime(2023, 1, 15),
            term_months=24
        )
        assert contract.type == CaseType.FINANCING_LEASE
        assert contract.subject == "数控机床设备"
        assert contract.amount == 1500000.00
        assert contract.signing_date == datetime(2023, 1, 15)
        assert contract.term_months == 24

    def test_contract_info_to_dict(self):
        contract = ContractInfo(
            type=CaseType.FINANCING_LEASE,
            subject="数控机床设备",
            amount=1500000.00,
            signing_date=datetime(2023, 1, 15)
        )
        result = contract.to_dict()
        assert result["type"] == "融资租赁"
        assert result["subject"] == "数控机床设备"
        assert result["amount"] == 1500000.00
        assert result["signing_date"] == "2023-01-15T00:00:00"


class TestBreachInfo:
    """Test BreachInfo dataclass"""

    def test_breach_info_creation(self):
        breach = BreachInfo(
            breach_date=datetime(2023, 6, 1),
            breach_amount=500000.00,
            breach_description="被告自2023年6月起未按约定支付租金"
        )
        assert breach.breach_date == datetime(2023, 6, 1)
        assert breach.breach_amount == 500000.00
        assert breach.breach_description == "被告自2023年6月起未按约定支付租金"


class TestCaseData:
    """Test CaseData dataclass"""

    def test_case_data_creation(self):
        plaintiff = Party(
            name="原告公司",
            credit_code="91110000123456789X",
            address="北京市朝阳区",
            legal_representative="张三"
        )
        defendant = Party(
            name="被告公司",
            credit_code="91110000987654321Y",
            address="北京市海淀区",
            legal_representative="李四"
        )
        contract = ContractInfo(
            type=CaseType.FINANCING_LEASE,
            subject="设备",
            amount=1000000.00,
            signing_date=datetime(2023, 1, 1)
        )

        case_data = CaseData(
            plaintiff=plaintiff,
            defendant=defendant,
            contract=contract,
            paid_amount=300000.00,
            remaining_amount=700000.00
        )

        assert case_data.plaintiff.name == "原告公司"
        assert case_data.defendant.name == "被告公司"
        assert case_data.contract.amount == 1000000.00
        assert case_data.paid_amount == 300000.00
        assert case_data.remaining_amount == 700000.00

    def test_case_data_to_json(self):
        plaintiff = Party(
            name="原告公司",
            credit_code="91110000123456789X",
            address="北京市朝阳区",
            legal_representative="张三"
        )
        defendant = Party(
            name="被告公司",
            credit_code="91110000987654321Y",
            address="北京市海淀区",
            legal_representative="李四"
        )
        contract = ContractInfo(
            type=CaseType.FINANCING_LEASE,
            subject="设备",
            amount=1000000.00,
            signing_date=datetime(2023, 1, 1)
        )

        case_data = CaseData(
            plaintiff=plaintiff,
            defendant=defendant,
            contract=contract
        )

        json_str = case_data.to_json()
        assert "原告公司" in json_str
        assert "被告公司" in json_str


class TestClaim:
    """Test Claim dataclass"""

    def test_claim_creation(self):
        claim = Claim(
            type="本金",
            amount=1000000.00,
            description="请求判令被告支付欠款本金"
        )
        assert claim.type == "本金"
        assert claim.amount == 1000000.00
        assert claim.description == "请求判令被告支付欠款本金"

    def test_claim_to_dict(self):
        claim = Claim(
            type="利息",
            amount=50000.00
        )
        result = claim.to_dict()
        assert result["type"] == "利息"
        assert result["amount"] == 50000.00
        assert result["description"] is None


class TestClaimList:
    """Test ClaimList dataclass"""

    def test_claim_list_creation(self):
        claims = [
            Claim(type="本金", amount=1000000.00),
            Claim(type="利息", amount=50000.00),
            Claim(type="违约金", amount=20000.00)
        ]
        claim_list = ClaimList(
            claims=claims,
            litigation_cost=5000.00,
            attorney_fee=10000.00
        )
        assert len(claim_list.claims) == 3
        assert claim_list.litigation_cost == 5000.00
        assert claim_list.attorney_fee == 10000.00

    def test_claim_list_to_json(self):
        claims = [Claim(type="本金", amount=1000000.00)]
        claim_list = ClaimList(claims=claims)
        json_str = claim_list.to_json()
        assert "本金" in json_str
        assert "1000000" in json_str


class TestAttachmentPlan:
    """Test AttachmentPlan dataclass"""

    def test_attachment_plan_creation(self):
        plan = AttachmentPlan(
            type="租赁物清单",
            form=AttachmentForm.INDEPENDENT_FILE,
            source="案情数据"
        )
        assert plan.type == "租赁物清单"
        assert plan.form == AttachmentForm.INDEPENDENT_FILE
        assert plan.source == "案情数据"


class TestEvidenceRequirement:
    """Test EvidenceRequirement dataclass"""

    def test_evidence_requirement_creation(self):
        requirement = EvidenceRequirement(
            name="融资租赁合同",
            type=EvidenceType.CONTRACT,
            facts_to_prove=["合同关系成立", "合同金额"],
            claims_supported=["本金"],
            attachment=AttachmentPlan(
                type="租赁物清单",
                form=AttachmentForm.INDEPENDENT_FILE,
                source="编造"
            )
        )
        assert requirement.name == "融资租赁合同"
        assert requirement.type == EvidenceType.CONTRACT
        assert len(requirement.facts_to_prove) == 2
        assert len(requirement.claims_supported) == 1


class TestEvidenceRequirements:
    """Test EvidenceRequirements dataclass"""

    def test_evidence_requirements_creation(self):
        requirements = [
            EvidenceRequirement(
                name="合同",
                type=EvidenceType.CONTRACT,
                facts_to_prove=["合同成立"],
                claims_supported=["本金"]
            )
        ]
        evidence_requirements = EvidenceRequirements(
            requirements=requirements,
            case_type=CaseType.FINANCING_LEASE
        )
        assert len(evidence_requirements.requirements) == 1
        assert evidence_requirements.case_type == CaseType.FINANCING_LEASE


class TestEvidenceItem:
    """Test EvidenceItem dataclass"""

    def test_evidence_item_creation(self):
        item = EvidenceItem(
            name="融资租赁合同",
            type=EvidenceType.CONTRACT,
            source="判决书提取",
            fabricated=False
        )
        assert item.name == "融资租赁合同"
        assert item.type == EvidenceType.CONTRACT
        assert item.source == "判决书提取"
        assert item.fabricated is False


class TestEvidenceCollection:
    """Test EvidenceCollection dataclass"""

    def test_evidence_collection_creation(self):
        items = [
            EvidenceItem(name="合同", type=EvidenceType.CONTRACT, source="判决书"),
            EvidenceItem(name="收据", type=EvidenceType.VOUCHER, source="判决书")
        ]
        collection = EvidenceCollection(
            items=items,
            from_judgment=["合同", "收据"],
            fabricated=[]
        )
        assert len(collection.items) == 2
        assert len(collection.from_judgment) == 2


class TestAttachmentInfo:
    """Test AttachmentInfo dataclass"""

    def test_attachment_info_creation(self):
        info = AttachmentInfo(
            type="租赁物清单",
            source="案情数据",
            form=AttachmentForm.INDEPENDENT_FILE,
            data={"物品": ["设备1", "设备2"]}
        )
        assert info.type == "租赁物清单"
        assert info.form == AttachmentForm.INDEPENDENT_FILE


class TestEvidenceListItem:
    """Test EvidenceListItem dataclass"""

    def test_evidence_list_item_creation(self):
        item = EvidenceListItem(
            name="融资租赁合同",
            type=EvidenceType.CONTRACT,
            key_info={
                "合同编号": "2023-001",
                "金额": 1000000.00
            },
            claims_supported=["本金"],
            attachment=AttachmentInfo(
                type="租赁物清单",
                source="编造",
                form=AttachmentForm.INDEPENDENT_FILE
            )
        )
        assert item.name == "融资租赁合同"
        assert item.key_info["合同编号"] == "2023-001"

    def test_evidence_list_item_to_prompt_context(self):
        item = EvidenceListItem(
            name="合同",
            type=EvidenceType.CONTRACT,
            key_info={"金额": 1000000.00},
            claims_supported=["本金"]
        )
        context = item.to_prompt_context()
        assert "合同" in context
        assert "1000000.0" in context


class TestEvidenceList:
    """Test EvidenceList dataclass"""

    def test_evidence_list_creation(self):
        items = [
            EvidenceListItem(
                name="合同",
                type=EvidenceType.CONTRACT,
                key_info={},
                claims_supported=["本金"]
            )
        ]
        evidence_list = EvidenceList(
            items=items,
            case_type=CaseType.FINANCING_LEASE
        )
        assert len(evidence_list.items) == 1
        assert evidence_list.case_type == CaseType.FINANCING_LEASE

    def test_evidence_list_to_llm_prompt(self):
        items = [
            EvidenceListItem(
                name="合同",
                type=EvidenceType.CONTRACT,
                key_info={"金额": 1000000.00},
                claims_supported=["本金"]
            )
        ]
        evidence_list = EvidenceList(items=items, case_type=CaseType.FINANCING_LEASE)
        prompt = evidence_list.to_llm_prompt()
        assert "证据列表" in prompt
        assert "合同" in prompt


class TestGeneratedEvidence:
    """Test GeneratedEvidence dataclass"""

    def test_generated_evidence_creation(self):
        evidence = GeneratedEvidence(
            filename="001_融资租赁合同.txt",
            content="合同内容...",
            evidence_type=EvidenceType.CONTRACT
        )
        assert evidence.filename == "001_融资租赁合同.txt"
        assert evidence.evidence_type == EvidenceType.CONTRACT


class TestEvidenceIndexItem:
    """Test EvidenceIndexItem dataclass"""

    def test_evidence_index_item_creation(self):
        item = EvidenceIndexItem(
            number=1,
            name="融资租赁合同",
            type=EvidenceType.CONTRACT,
            purpose="证明合同关系",
            claims_supported=["本金"]
        )
        assert item.number == 1
        assert item.name == "融资租赁合同"
        assert item.purpose == "证明合同关系"


class TestEvidenceIndex:
    """Test EvidenceIndex dataclass"""

    def test_evidence_index_creation(self):
        items = [
            EvidenceIndexItem(
                number=1,
                name="合同",
                type=EvidenceType.CONTRACT,
                purpose="证明合同关系",
                claims_supported=["本金"]
            ),
            EvidenceIndexItem(
                number=2,
                name="收据",
                type=EvidenceType.VOUCHER,
                purpose="证明付款事实",
                claims_supported=["本金"]
            )
        ]
        index = EvidenceIndex(items=items, total_count=2)
        assert len(index.items) == 2
        assert index.total_count == 2

    def test_evidence_index_to_text(self):
        items = [
            EvidenceIndexItem(
                number=1,
                name="合同",
                type=EvidenceType.CONTRACT,
                purpose="证明合同关系",
                claims_supported=["本金"]
            )
        ]
        index = EvidenceIndex(items=items, total_count=1)
        text = index.to_text()
        assert "证据清单" in text
        assert "证据1：合同" in text

    def test_evidence_index_to_json(self):
        items = [
            EvidenceIndexItem(
                number=1,
                name="合同",
                type=EvidenceType.CONTRACT,
                purpose="证明合同关系",
                claims_supported=["本金"]
            )
        ]
        index = EvidenceIndex(items=items, total_count=1)
        json_str = index.to_json()
        assert "合同" in json_str
