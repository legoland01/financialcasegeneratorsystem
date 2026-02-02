"""
test_evidence_list_creator.py - EvidenceListCreator单元测试

测试F2.5证据列表创建器的核心功能。
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import os

from src.core.evidence_list_creator import EvidenceListCreator
from src.core.data_models import (
    CaseData,
    Party,
    ContractInfo,
    BreachInfo,
    ClaimList,
    Claim,
    CaseType,
    EvidenceCollection,
    EvidenceItem,
    EvidenceType,
    EvidenceRequirements,
    EvidenceRequirement,
    EvidenceList,
    EvidenceListItem,
    AttachmentInfo,
    AttachmentForm
)


@pytest.fixture
def sample_case_data():
    """提供测试用的CaseData"""
    plaintiff = Party(
        name="上海融资租赁有限公司",
        credit_code="91310000123456789A",
        address="上海市浦东新区陆家嘴环路1000号",
        legal_representative="张三",
        bank_account="6222021001067890"
    )
    
    defendant = Party(
        name="北京设备有限公司",
        credit_code="91110108123456789B",
        address="北京市朝阳区建国路100号",
        legal_representative="李四",
        bank_account="6222021001067891"
    )
    
    contract = ContractInfo(
        type=CaseType.FINANCING_LEASE,
        subject="数控机床设备5台",
        amount=5000000.00,
        signing_date=datetime(2022, 3, 15),
        term_months=36
    )
    
    breach = BreachInfo(
        breach_date=datetime(2023, 6, 1),
        breach_amount=3500000.00,
        breach_description="被告自2023年6月起未按合同约定支付租金"
    )
    
    return CaseData(
        plaintiff=plaintiff,
        defendant=defendant,
        contract=contract,
        breach=breach,
        paid_amount=1500000.00,
        remaining_amount=3500000.00,
        attachments={
            "租赁物清单": [{"名称": "数控机床设备5台", "型号": "XK-500"}],
            "还款计划": [{"期数": "36期", "金额": "约138,889元"}]
        },
        extracted_at=datetime(2024, 1, 15)
    )


@pytest.fixture
def sample_evidence_collection():
    """提供测试用的EvidenceCollection"""
    items = [
        EvidenceItem(
            name="融资租赁合同",
            type=EvidenceType.CONTRACT,
            source="当事人提供",
            fabricated=False
        ),
        EvidenceItem(
            name="租赁物交接确认书",
            type=EvidenceType.VOUCHER,
            source="当事人提供",
            fabricated=False
        ),
        EvidenceItem(
            name="租金支付凭证",
            type=EvidenceType.VOUCHER,
            source="银行出具",
            fabricated=False
        ),
        EvidenceItem(
            name="催款函",
            type=EvidenceType.DOCUMENT,
            source="当事人提供",
            fabricated=False
        ),
        EvidenceItem(
            name="租赁物清单",
            type=EvidenceType.ATTACHMENT,
            source="当事人提供",
            fabricated=False
        )
    ]
    
    return EvidenceCollection(items=items)


@pytest.fixture
def sample_evidence_requirements():
    """提供测试用的EvidenceRequirements"""
    requirements = [
        EvidenceRequirement(
            name="融资租赁合同",
            type=EvidenceType.CONTRACT,
            facts_to_prove=["合同关系成立", "合同内容"],
            claims_supported=["本金", "利息"],
            attachment=None
        ),
        EvidenceRequirement(
            name="租赁物交接确认书",
            type=EvidenceType.VOUCHER,
            facts_to_prove=["租赁物交付"],
            claims_supported=["本金"],
            attachment=None
        ),
        EvidenceRequirement(
            name="租金支付凭证",
            type=EvidenceType.VOUCHER,
            facts_to_prove=["付款情况"],
            claims_supported=["本金", "利息"],
            attachment=None
        ),
        EvidenceRequirement(
            name="催款函",
            type=EvidenceType.DOCUMENT,
            facts_to_prove=["催款事实"],
            claims_supported=["违约金"],
            attachment=None
        ),
        EvidenceRequirement(
            name="租赁物清单",
            type=EvidenceType.ATTACHMENT,
            facts_to_prove=["租赁物详情"],
            claims_supported=["本金"],
            attachment=None
        )
    ]
    
    return EvidenceRequirements(requirements=requirements, case_type=CaseType.FINANCING_LEASE)


class TestEvidenceListCreator:
    """EvidenceListCreator测试类"""
    
    def test_init(self):
        """测试初始化"""
        creator = EvidenceListCreator()
        assert creator is not None
    
    def test_create_basic(self, sample_case_data, sample_evidence_collection, sample_evidence_requirements):
        """测试创建证据列表基本功能"""
        creator = EvidenceListCreator()
        result = creator.create(sample_case_data, sample_evidence_collection, sample_evidence_requirements)
        
        assert isinstance(result, EvidenceList)
        assert len(result.items) == 5
        assert result.case_type == CaseType.FINANCING_LEASE
    
    def test_create_contract_key_info(self, sample_case_data, sample_evidence_collection, sample_evidence_requirements):
        """测试合同类证据的关键信息提取"""
        creator = EvidenceListCreator()
        result = creator.create(sample_case_data, sample_evidence_collection, sample_evidence_requirements)
        
        contract_item = next((item for item in result.items if item.name == "融资租赁合同"), None)
        assert contract_item is not None
        assert "出租人" in contract_item.key_info
        assert "承租人" in contract_item.key_info
        assert "标的物" in contract_item.key_info
        assert contract_item.key_info["出租人"] == "上海融资租赁有限公司"
        assert contract_item.key_info["承租人"] == "北京设备有限公司"
        assert contract_item.key_info["标的物"] == "数控机床设备5台"
    
    def test_create_voucher_key_info(self, sample_case_data, sample_evidence_collection, sample_evidence_requirements):
        """测试凭证类证据的关键信息提取"""
        creator = EvidenceListCreator()
        result = creator.create(sample_case_data, sample_evidence_collection, sample_evidence_requirements)
        
        receipt_item = next((item for item in result.items if item.name == "租金支付凭证"), None)
        assert receipt_item is not None
        assert "付款方" in receipt_item.key_info
        assert "收款方" in receipt_item.key_info
        assert "金额" in receipt_item.key_info
        assert "1,500,000元" in receipt_item.key_info["金额"]
    
    def test_create_document_key_info(self, sample_case_data, sample_evidence_collection, sample_evidence_requirements):
        """测试文书类证据的关键信息提取"""
        creator = EvidenceListCreator()
        result = creator.create(sample_case_data, sample_evidence_collection, sample_evidence_requirements)
        
        doc_item = next((item for item in result.items if item.name == "催款函"), None)
        assert doc_item is not None
        assert "文书类型" in doc_item.key_info
        assert doc_item.key_info["文书类型"] == "催款函"
        assert "发证机关" in doc_item.key_info
    
    def test_create_attachment_key_info(self, sample_case_data, sample_evidence_collection, sample_evidence_requirements):
        """测试附件类证据的关键信息提取"""
        creator = EvidenceListCreator()
        result = creator.create(sample_case_data, sample_evidence_collection, sample_evidence_requirements)
        
        attachment_item = next((item for item in result.items if item.name == "租赁物清单"), None)
        assert attachment_item is not None
        assert "租赁物清单" in attachment_item.key_info
        assert "数控机床设备5台" in attachment_item.key_info["租赁物清单"][0]["名称"]
    
    def test_claims_supported(self, sample_case_data, sample_evidence_collection, sample_evidence_requirements):
        """测试证据支撑的诉求"""
        creator = EvidenceListCreator()
        result = creator.create(sample_case_data, sample_evidence_collection, sample_evidence_requirements)
        
        contract_item = next((item for item in result.items if item.name == "融资租赁合同"), None)
        assert "本金" in contract_item.claims_supported
        assert "利息" in contract_item.claims_supported
        
        receipt_item = next((item for item in result.items if item.name == "租金支付凭证"), None)
        assert "本金" in receipt_item.claims_supported
        assert "利息" in receipt_item.claims_supported
        
        demand_item = next((item for item in result.items if item.name == "催款函"), None)
        assert "违约金" in demand_item.claims_supported
    
    def test_attachment_info(self, sample_case_data, sample_evidence_collection):
        """测试附件信息"""
        creator = EvidenceListCreator()
        
        requirements_with_attachment = EvidenceRequirements(requirements=[
            EvidenceRequirement(
                name="融资租赁合同",
                type=EvidenceType.CONTRACT,
                facts_to_prove=["合同关系"],
                claims_supported=["本金"],
                attachment=None
            ),
            EvidenceRequirement(
                name="租赁物清单",
                type=EvidenceType.ATTACHMENT,
                facts_to_prove=["租赁物"],
                claims_supported=["本金"],
                attachment=None
            )
        ], case_type=CaseType.FINANCING_LEASE)
        
        result = creator.create(sample_case_data, sample_evidence_collection, requirements_with_attachment)
        
        contract_item = next((item for item in result.items if item.name == "融资租赁合同"), None)
        assert contract_item.attachment is None
    
    def test_validate_no_deanonymization(self, sample_case_data, sample_evidence_collection, sample_evidence_requirements):
        """测试脱敏标记验证"""
        creator = EvidenceListCreator()
        result = creator.create(sample_case_data, sample_evidence_collection, sample_evidence_requirements)
        
        issues = creator.validate_no_deanonymization(result)
        assert len(issues) == 0
    
    def test_validate_with_deanonymization(self):
        """测试发现脱敏标记"""
        creator = EvidenceListCreator()
        
        item = EvidenceListItem(
            name="测试证据",
            type=EvidenceType.CONTRACT,
            key_info={"出租人": "某某公司", "日期": "某年某月某日"},
            claims_supported=["本金"],
            attachment=None
        )
        
        evidence_list = EvidenceList(items=[item], case_type=CaseType.FINANCING_LEASE)
        
        issues = creator.validate_no_deanonymization(evidence_list)
        assert len(issues) == 2
        assert any("某某" in issue for issue in issues)
        assert any("某年某月某日" in issue for issue in issues)
    
    def test_empty_collection(self, sample_case_data, sample_evidence_requirements):
        """测试空证据集合"""
        creator = EvidenceListCreator()
        
        empty_collection = EvidenceCollection(items=[])
        result = creator.create(sample_case_data, empty_collection, sample_evidence_requirements)
        
        assert isinstance(result, EvidenceList)
        assert len(result.items) == 0
    
    def test_empty_requirements(self, sample_case_data, sample_evidence_collection):
        """测试空需求清单"""
        creator = EvidenceListCreator()
        
        empty_requirements = EvidenceRequirements(requirements=[], case_type=CaseType.FINANCING_LEASE)
        result = creator.create(sample_case_data, sample_evidence_collection, empty_requirements)
        
        assert isinstance(result, EvidenceList)
        assert len(result.items) == 5
        for item in result.items:
            assert len(item.claims_supported) == 0
    
    def test_case_type_preserved(self, sample_case_data, sample_evidence_collection, sample_evidence_requirements):
        """测试案件类型保持"""
        creator = EvidenceListCreator()
        result = creator.create(sample_case_data, sample_evidence_collection, sample_evidence_requirements)
        
        assert result.case_type == CaseType.FINANCING_LEASE
    
    def test_extract_key_info_with_none_paid_amount(self):
        """测试paid_amount为None时的处理"""
        plaintiff = Party(
            name="上海融资租赁有限公司",
            credit_code="91310000123456789A",
            address="上海市浦东新区",
            legal_representative="张三"
        )
        
        defendant = Party(
            name="北京设备有限公司",
            credit_code="91110108123456789B",
            address="北京市朝阳区",
            legal_representative="李四"
        )
        
        contract = ContractInfo(
            type=CaseType.FINANCING_LEASE,
            subject="设备",
            amount=1000000.00,
            signing_date=datetime(2022, 1, 1),
            term_months=12
        )
        
        case_data = CaseData(
            plaintiff=plaintiff,
            defendant=defendant,
            contract=contract,
            paid_amount=None
        )
        
        evidence_collection = EvidenceCollection(items=[
            EvidenceItem(name="租金支付凭证", type=EvidenceType.VOUCHER, source="银行出具")
        ])
        
        evidence_requirements = EvidenceRequirements(
            requirements=[
                EvidenceRequirement(
                    name="租金支付凭证",
                    type=EvidenceType.VOUCHER,
                    facts_to_prove=["付款"],
                    claims_supported=["本金"]
                )
            ],
            case_type=CaseType.FINANCING_LEASE
        )
        
        creator = EvidenceListCreator()
        result = creator.create(case_data, evidence_collection, evidence_requirements)
        
        receipt_item = result.items[0]
        assert "1,000,000元" in receipt_item.key_info["金额"]
    
    def test_extract_key_info_with_none_term_months(self):
        """测试term_months为None时的处理"""
        plaintiff = Party(name="原告公司", credit_code="91310000123456789A", address="地址", legal_representative="甲")
        defendant = Party(name="被告公司", credit_code="91110108123456789B", address="地址", legal_representative="乙")
        
        contract = ContractInfo(
            type=CaseType.FINANCING_LEASE,
            subject="设备",
            amount=1000000.00,
            signing_date=datetime(2022, 1, 1),
            term_months=None
        )
        
        case_data = CaseData(
            plaintiff=plaintiff,
            defendant=defendant,
            contract=contract
        )
        
        evidence_collection = EvidenceCollection(items=[
            EvidenceItem(name="融资租赁合同", type=EvidenceType.CONTRACT, source="当事人提供")
        ])
        
        evidence_requirements = EvidenceRequirements(
            requirements=[
                EvidenceRequirement(
                    name="融资租赁合同",
                    type=EvidenceType.CONTRACT,
                    facts_to_prove=["合同"],
                    claims_supported=["本金"]
                )
            ],
            case_type=CaseType.FINANCING_LEASE
        )
        
        creator = EvidenceListCreator()
        result = creator.create(case_data, evidence_collection, evidence_requirements)
        
        contract_item = result.items[0]
        assert contract_item.key_info["租期"] is None
    
    def test_get_attachment_data_unknown_attachment(self, sample_case_data):
        """测试未知附件类型"""
        unknown_collection = EvidenceCollection(items=[
            EvidenceItem(name="未知附件", type=EvidenceType.ATTACHMENT, source="当事人提供")
        ])
        
        unknown_requirements = EvidenceRequirements(
            requirements=[
                EvidenceRequirement(
                    name="未知附件",
                    type=EvidenceType.ATTACHMENT,
                    facts_to_prove=["未知"],
                    claims_supported=[]
                )
            ],
            case_type=CaseType.FINANCING_LEASE
        )
        
        creator = EvidenceListCreator()
        result = creator.create(sample_case_data, unknown_collection, unknown_requirements)
        
        unknown_item = result.items[0]
        assert unknown_item.key_info == {}
    
    def test_date_format(self, sample_case_data, sample_evidence_collection, sample_evidence_requirements):
        """测试日期格式"""
        creator = EvidenceListCreator()
        result = creator.create(sample_case_data, sample_evidence_collection, sample_evidence_requirements)
        
        contract_item = next((item for item in result.items if item.name == "融资租赁合同"), None)
        assert "2022年03月15日" in contract_item.key_info["签订日期"]
    
    def test_amount_format(self, sample_case_data, sample_evidence_collection, sample_evidence_requirements):
        """测试金额格式"""
        creator = EvidenceListCreator()
        result = creator.create(sample_case_data, sample_evidence_collection, sample_evidence_requirements)
        
        contract_item = next((item for item in result.items if item.name == "融资租赁合同"), None)
        assert "5,000,000元" in contract_item.key_info["合同金额"]
    
    def test_term_months_format(self, sample_case_data, sample_evidence_collection, sample_evidence_requirements):
        """测试租期格式"""
        creator = EvidenceListCreator()
        result = creator.create(sample_case_data, sample_evidence_collection, sample_evidence_requirements)
        
        contract_item = next((item for item in result.items if item.name == "融资租赁合同"), None)
        assert "36个月" in contract_item.key_info["租期"]
