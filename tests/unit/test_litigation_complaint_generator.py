"""
test_litigation_complaint_generator.py - LitigationComplaintGenerator单元测试

测试F2.6起诉状生成器的核心功能。
"""

import pytest
from datetime import datetime

from src.core.litigation_complaint_generator import LitigationComplaintGenerator
from src.core.data_models import (
    CaseData,
    Party,
    ContractInfo,
    BreachInfo,
    ClaimList,
    Claim,
    CaseType,
    EvidenceList,
    EvidenceListItem,
    EvidenceType
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
        extracted_at=datetime(2024, 1, 15)
    )


@pytest.fixture
def sample_claim_list():
    """提供测试用的ClaimList"""
    claims = [
        Claim(type="本金", amount=3500000.00, description="欠款本金"),
        Claim(type="利息", amount=350000.00, description="欠款利息"),
        Claim(type="违约金", amount=175000.00, description="违约金")
    ]
    
    return ClaimList(
        claims=claims,
        litigation_cost=50000.00
    )


@pytest.fixture
def sample_evidence_list():
    """提供测试用的EvidenceList"""
    items = [
        EvidenceListItem(
            name="融资租赁合同",
            type=EvidenceType.CONTRACT,
            key_info={"出租人": "上海融资租赁有限公司", "承租人": "北京设备有限公司"},
            claims_supported=["本金", "利息"]
        ),
        EvidenceListItem(
            name="租金支付凭证",
            type=EvidenceType.VOUCHER,
            key_info={"金额": "1500000元"},
            claims_supported=["本金"]
        ),
        EvidenceListItem(
            name="催款函",
            type=EvidenceType.DOCUMENT,
            key_info={"文书类型": "催款函"},
            claims_supported=["违约金"]
        )
    ]
    
    return EvidenceList(items=items, case_type=CaseType.FINANCING_LEASE)


class TestLitigationComplaintGenerator:
    """LitigationComplaintGenerator测试类"""
    
    def test_init(self):
        """测试初始化"""
        generator = LitigationComplaintGenerator()
        assert generator is not None
    
    def test_generate_basic(self, sample_case_data, sample_claim_list, sample_evidence_list):
        """测试生成起诉状基本功能"""
        generator = LitigationComplaintGenerator()
        result = generator.generate(sample_case_data, sample_claim_list, sample_evidence_list)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_header(self):
        """测试标题生成"""
        generator = LitigationComplaintGenerator()
        header = generator._generate_header()
        
        assert header == "民事起诉状"
    
    def test_parties(self, sample_case_data):
        """测试当事人信息生成"""
        generator = LitigationComplaintGenerator()
        parties = generator._generate_parties(sample_case_data)
        
        assert "原告：" in parties
        assert "上海融资租赁有限公司" in parties
        assert "上海市浦东新区陆家嘴环路1000号" in parties
        assert "张三" in parties
        assert "被告：" in parties
        assert "北京设备有限公司" in parties
        assert "北京市朝阳区建国路100号" in parties
        assert "李四" in parties
    
    def test_parties_with_bank_account(self, sample_case_data):
        """测试带银行账户的当事人信息"""
        generator = LitigationComplaintGenerator()
        parties = generator._generate_parties(sample_case_data)
        
        assert "6222021001067890" in parties
        assert "6222021001067891" in parties
    
    def test_parties_with_guarantor(self):
        """测试带担保人的当事人信息"""
        plaintiff = Party(
            name="原告公司",
            credit_code="91310000123456789A",
            address="地址1",
            legal_representative="甲"
        )
        
        defendant = Party(
            name="被告公司",
            credit_code="91110108123456789B",
            address="地址2",
            legal_representative="乙"
        )
        
        guarantor = Party(
            name="担保人公司",
            credit_code="91110108123456789C",
            address="地址3",
            legal_representative="丙"
        )
        
        contract = ContractInfo(
            type=CaseType.FINANCING_LEASE,
            subject="设备",
            amount=1000000.00,
            signing_date=datetime(2022, 1, 1)
        )
        
        case_data = CaseData(
            plaintiff=plaintiff,
            defendant=defendant,
            contract=contract,
            guarantor=guarantor
        )
        
        generator = LitigationComplaintGenerator()
        parties = generator._generate_parties(case_data)
        
        assert "担保人：" in parties
        assert "担保人公司" in parties
    
    def test_claims_principal(self, sample_claim_list):
        """测试本金诉求生成"""
        generator = LitigationComplaintGenerator()
        claims = generator._generate_claims(sample_claim_list)
        
        assert "请求判令被告向原告支付欠款本金人民币3,500,000元" in claims
    
    def test_claims_interest(self, sample_claim_list):
        """测试利息诉求生成"""
        generator = LitigationComplaintGenerator()
        claims = generator._generate_claims(sample_claim_list)
        
        assert "请求判令被告向原告支付欠款利息人民币350,000元" in claims
    
    def test_claims_penalty(self, sample_claim_list):
        """测试违约金诉求生成"""
        generator = LitigationComplaintGenerator()
        claims = generator._generate_claims(sample_claim_list)
        
        assert "请求判令被告向原告支付违约金人民币175,000元" in claims
    
    def test_litigation_cost(self, sample_claim_list):
        """测试诉讼费用诉求"""
        generator = LitigationComplaintGenerator()
        claims = generator._generate_claims(sample_claim_list)
        
        assert "请求判令被告承担本案诉讼费用人民币50,000元" in claims
    
    def test_facts_contract(self, sample_case_data):
        """测试合同签订情况生成"""
        generator = LitigationComplaintGenerator()
        facts = generator._generate_facts(sample_case_data)
        
        assert "合同签订情况" in facts
        assert "2022年03月15日" in facts
        assert "融资租赁" in facts
        assert "数控机床设备5台" in facts
        assert "5,000,000元" in facts
        assert "36个月" in facts
    
    def test_facts_performance(self, sample_case_data):
        """测试合同履行情况生成"""
        generator = LitigationComplaintGenerator()
        facts = generator._generate_facts(sample_case_data)
        
        assert "合同履行情况" in facts
        assert "1,500,000元" in facts
        assert "3,500,000元" in facts
    
    def test_facts_breach(self, sample_case_data):
        """测试违约情况生成"""
        generator = LitigationComplaintGenerator()
        facts = generator._generate_facts(sample_case_data)
        
        assert "被告违约事实" in facts
        assert "2023年06月01日" in facts
        assert "3,500,000元" in facts
        assert "被告自2023年6月起未按合同约定支付租金" in facts
    
    def test_evidence_list(self, sample_evidence_list):
        """测试证据清单生成"""
        generator = LitigationComplaintGenerator()
        evidence = generator._generate_evidence_list(sample_evidence_list)
        
        assert "证据清单：" in evidence
        assert "1. 融资租赁合同（合同类）" in evidence
        assert "2. 租金支付凭证（凭证类）" in evidence
        assert "3. 催款函（文书类）" in evidence
    
    def test_footer_court(self, sample_case_data):
        """测试落款法院"""
        generator = LitigationComplaintGenerator()
        footer = generator._generate_footer(sample_case_data)
        
        assert "此致" in footer
        assert "上海市浦东新区人民法院" in footer
    
    def test_footer_signature(self, sample_case_data):
        """测试落款签名"""
        generator = LitigationComplaintGenerator()
        footer = generator._generate_footer(sample_case_data)
        
        assert "起诉人（盖章）：" in footer
        assert "日期：" in footer
    
    def test_footer_with_date(self, sample_case_data):
        """测试落款日期"""
        generator = LitigationComplaintGenerator()
        footer = generator._generate_footer(sample_case_data)
        
        assert "2024年01月15日" in footer
    
    def test_footer_without_date(self):
        """测试落款无日期"""
        generator = LitigationComplaintGenerator()
        plaintiff = Party(name="原告", credit_code="91310000123456789A", address="地址", legal_representative="甲")
        defendant = Party(name="被告", credit_code="91110108123456789B", address="地址", legal_representative="乙")
        contract = ContractInfo(type=CaseType.FINANCING_LEASE, subject="设备", amount=1000000.00, signing_date=datetime(2022, 1, 1))
        case_data = CaseData(plaintiff=plaintiff, defendant=defendant, contract=contract, extracted_at=None)
        footer = generator._generate_footer(case_data)
        
        assert "____年__月__日" in footer
    
    def test_generate_full_complaint(self, sample_case_data, sample_claim_list, sample_evidence_list):
        """测试完整起诉状生成"""
        generator = LitigationComplaintGenerator()
        complaint = generator.generate(sample_case_data, sample_claim_list, sample_evidence_list)
        
        assert "民事起诉状" in complaint
        assert "原告：" in complaint
        assert "被告：" in complaint
        assert "诉讼请求：" in complaint
        assert "事实与理由：" in complaint
        assert "证据清单：" in complaint
        assert "此致" in complaint
    
    def test_complaint_ends_with_proper_formatting(self, sample_case_data, sample_claim_list, sample_evidence_list):
        """测试起诉状格式"""
        generator = LitigationComplaintGenerator()
        complaint = generator.generate(sample_case_data, sample_claim_list, sample_evidence_list)
        
        lines = complaint.split("\n")
        assert lines[0] == "民事起诉状"
        assert "起诉人（盖章）：" in complaint
        assert "上海市浦东新区人民法院" in complaint
    
    def test_claim_numbering(self, sample_claim_list):
        """测试诉求编号"""
        generator = LitigationComplaintGenerator()
        claims = generator._generate_claims(sample_claim_list)
        
        assert "1. 请求判令被告向原告支付欠款本金" in claims
        assert "2. 请求判令被告向原告支付欠款利息" in claims
        assert "3. 请求判令被告向原告支付违约金" in claims
        assert "4. 请求判令被告承担本案诉讼费用" in claims
    
    def test_no_guarantor_section(self):
        """测试无担保人时不显示担保人"""
        plaintiff = Party(
            name="原告公司",
            credit_code="91310000123456789A",
            address="地址1",
            legal_representative="甲"
        )
        
        defendant = Party(
            name="被告公司",
            credit_code="91110108123456789B",
            address="地址2",
            legal_representative="乙"
        )
        
        contract = ContractInfo(
            type=CaseType.FINANCING_LEASE,
            subject="设备",
            amount=1000000.00,
            signing_date=datetime(2022, 1, 1)
        )
        
        case_data = CaseData(
            plaintiff=plaintiff,
            defendant=defendant,
            contract=contract
        )
        
        generator = LitigationComplaintGenerator()
        parties = generator._generate_parties(case_data)
        
        assert "担保人：" not in parties
    
    def test_no_term_months_in_facts(self):
        """测试无租期时的处理"""
        plaintiff = Party(name="原告", credit_code="91310000123456789A", address="地址", legal_representative="甲")
        defendant = Party(name="被告", credit_code="91110108123456789B", address="地址", legal_representative="乙")
        
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
        
        generator = LitigationComplaintGenerator()
        facts = generator._generate_facts(case_data)
        
        assert "租赁期限为" not in facts
    
    def test_no_paid_amount_in_facts(self):
        """测试无已付金额时的处理"""
        plaintiff = Party(name="原告", credit_code="91310000123456789A", address="地址", legal_representative="甲")
        defendant = Party(name="被告", credit_code="91110108123456789B", address="地址", legal_representative="乙")
        
        contract = ContractInfo(
            type=CaseType.FINANCING_LEASE,
            subject="设备",
            amount=1000000.00,
            signing_date=datetime(2022, 1, 1)
        )
        
        case_data = CaseData(
            plaintiff=plaintiff,
            defendant=defendant,
            contract=contract,
            paid_amount=None
        )
        
        generator = LitigationComplaintGenerator()
        facts = generator._generate_facts(case_data)
        
        assert "合同履行情况" not in facts
    
    def test_no_breach_in_facts(self):
        """测试无违约信息时的处理"""
        plaintiff = Party(name="原告", credit_code="91310000123456789A", address="地址", legal_representative="甲")
        defendant = Party(name="被告", credit_code="91110108123456789B", address="地址", legal_representative="乙")
        
        contract = ContractInfo(
            type=CaseType.FINANCING_LEASE,
            subject="设备",
            amount=1000000.00,
            signing_date=datetime(2022, 1, 1)
        )
        
        case_data = CaseData(
            plaintiff=plaintiff,
            defendant=defendant,
            contract=contract,
            paid_amount=1000000.00,
            breach=None
        )
        
        generator = LitigationComplaintGenerator()
        facts = generator._generate_facts(case_data)
        
        assert "被告违约事实" not in facts
    
    def test_empty_evidence_list(self, sample_case_data, sample_claim_list):
        """测试空证据清单"""
        generator = LitigationComplaintGenerator()
        
        empty_evidence_list = EvidenceList(items=[], case_type=CaseType.FINANCING_LEASE)
        evidence = generator._generate_evidence_list(empty_evidence_list)
        
        assert "证据清单：" in evidence
    
    def test_evidence_order_preserved(self, sample_evidence_list):
        """测试证据顺序保持"""
        generator = LitigationComplaintGenerator()
        evidence = generator._generate_evidence_list(sample_evidence_list)
        
        lines = evidence.split("\n")
        contract_idx = next(i for i, line in enumerate(lines) if "融资租赁合同" in line)
        receipt_idx = next(i for i, line in enumerate(lines) if "租金支付凭证" in line)
        demand_idx = next(i for i, line in enumerate(lines) if "催款函" in line)
        
        assert contract_idx < receipt_idx < demand_idx
