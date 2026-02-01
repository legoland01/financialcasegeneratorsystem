"""
Unit tests for quality_validator.py
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
from src.core.quality_validator import (
    ValidationIssue,
    ValidationReport,
    QualityValidator,
    EvidenceQualityChecker
)


@pytest.fixture
def valid_case_data():
    """创建有效的测试CaseData"""
    plaintiff = Party(
        name="测试原告公司",
        credit_code="91110000123456789X",
        address="北京市朝阳区",
        legal_representative="张三",
        bank_account="123456789012"
    )
    defendant = Party(
        name="测试被告公司",
        credit_code="91110000987654321Y",
        address="北京市海淀区",
        legal_representative="李四",
        bank_account="987654321098"
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
        remaining_amount=1200000.00,
        breach=BreachInfo(
            breach_date=datetime(2023, 6, 1),
            breach_amount=1200000.00,
            breach_description="被告自2023年6月起未按约定支付租金"
        )
    )


@pytest.fixture
def valid_claim_list():
    """创建有效的测试ClaimList"""
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
def valid_evidence_list():
    """创建有效的测试EvidenceList（至少3个以避免警告）"""
    items = [
        EvidenceListItem(
            name="融资租赁合同",
            type=EvidenceType.CONTRACT,
            key_info={"合同编号": "2023-001"},
            claims_supported=["本金"]
        ),
        EvidenceListItem(
            name="租金支付收据",
            type=EvidenceType.VOUCHER,
            key_info={"金额": 300000.00},
            claims_supported=["本金"]
        ),
        EvidenceListItem(
            name="债务催收函",
            type=EvidenceType.DOCUMENT,
            key_info={"文书类型": "催款函"},
            claims_supported=["违约金"]
        )
    ]
    return EvidenceList(items=items, case_type=CaseType.FINANCING_LEASE)


@pytest.fixture
def valid_generated_evidence():
    """创建有效的测试GeneratedEvidence列表"""
    return [
        GeneratedEvidence(
            filename="001_融资租赁合同.txt",
            content="合同内容" * 100,
            evidence_type=EvidenceType.CONTRACT
        ),
        GeneratedEvidence(
            filename="002_收据.txt",
            content="收据内容" * 100,
            evidence_type=EvidenceType.VOUCHER
        )
    ]


class TestValidationIssue:
    """Test ValidationIssue dataclass"""

    def test_validation_issue_creation(self):
        issue = ValidationIssue(
            severity="error",
            category="test",
            message="测试问题",
            suggestion="测试建议"
        )
        assert issue.severity == "error"
        assert issue.category == "test"
        assert issue.message == "测试问题"
        assert issue.suggestion == "测试建议"

    def test_validation_issue_optional_suggestion(self):
        issue = ValidationIssue(
            severity="warning",
            category="test",
            message="测试问题"
        )
        assert issue.suggestion is None


class TestValidationReport:
    """Test ValidationReport dataclass"""

    def test_empty_report_is_valid(self):
        report = ValidationReport(is_valid=True)
        assert report.is_valid is True
        assert len(report.issues) == 0

    def test_add_issue_updates_status(self):
        report = ValidationReport(is_valid=True)
        issue = ValidationIssue(severity="warning", category="test", message="测试问题")
        report.add_issue(issue)
        assert report.is_valid is True
        assert report.score < 100

    def test_critical_issue_marks_invalid(self):
        report = ValidationReport(is_valid=True)
        issue = ValidationIssue(severity="critical", category="test", message="严重问题")
        report.add_issue(issue)
        assert report.is_valid is False

    def test_error_issue_marks_invalid(self):
        report = ValidationReport(is_valid=True)
        issue = ValidationIssue(severity="error", category="test", message="错误")
        report.add_issue(issue)
        assert report.is_valid is False

    def test_multiple_issues_accumulate(self):
        report = ValidationReport(is_valid=True)
        report.add_issue(ValidationIssue(severity="error", category="test", message="错误1"))
        report.add_issue(ValidationIssue(severity="warning", category="test", message="警告1"))
        report.add_issue(ValidationIssue(severity="warning", category="test", message="警告2"))
        assert report.is_valid is False
        assert len(report.issues) == 3

    def test_details_contain_counts(self):
        report = ValidationReport(is_valid=True)
        report.add_issue(ValidationIssue(severity="error", category="test", message="错误"))
        report.add_issue(ValidationIssue(severity="warning", category="test", message="警告"))
        assert report.details["total_issues"] == 2
        assert report.details["errors"] == 1
        assert report.details["warnings"] == 1


class TestQualityValidator:
    """Test QualityValidator class"""

    def test_validate_valid_data(self, valid_case_data, valid_claim_list, valid_evidence_list, valid_generated_evidence):
        """测试验证有效数据"""
        validator = QualityValidator()
        report = validator.validate(
            valid_case_data,
            valid_claim_list,
            valid_evidence_list,
            valid_generated_evidence
        )
        assert report.is_valid is True

    def test_validate_missing_plaintiff(self, valid_claim_list, valid_evidence_list, valid_generated_evidence):
        """测试验证缺失原告数据"""
        invalid_data = CaseData(
            plaintiff=None,
            defendant=Party(name="被告", credit_code="123", address="地址", legal_representative="李四"),
            contract=ContractInfo(type=CaseType.FINANCING_LEASE, subject="设备", amount=100000, signing_date=datetime.now())
        )
        validator = QualityValidator()
        report = validator.validate(
            invalid_data,
            valid_claim_list,
            valid_evidence_list,
            valid_generated_evidence
        )
        assert not report.is_valid
        assert len(report.issues) > 0

    def test_validate_missing_defendant(self, valid_claim_list, valid_evidence_list, valid_generated_evidence):
        """测试验证缺失被告数据"""
        invalid_data = CaseData(
            plaintiff=Party(name="原告", credit_code="123", address="地址", legal_representative="张三"),
            defendant=None,
            contract=ContractInfo(type=CaseType.FINANCING_LEASE, subject="设备", amount=100000, signing_date=datetime.now())
        )
        validator = QualityValidator()
        report = validator.validate(
            invalid_data,
            valid_claim_list,
            valid_evidence_list,
            valid_generated_evidence
        )
        assert not report.is_valid

    def test_validate_empty_claims(self, valid_case_data, valid_evidence_list, valid_generated_evidence):
        """测试验证空诉求列表"""
        empty_claims = ClaimList(claims=[])
        validator = QualityValidator()
        report = validator.validate(
            valid_case_data,
            empty_claims,
            valid_evidence_list,
            valid_generated_evidence
        )
        assert not report.is_valid

    def test_validate_empty_evidence(self, valid_case_data, valid_claim_list, valid_generated_evidence):
        """测试验证空证据列表"""
        empty_evidence = EvidenceList(items=[], case_type=CaseType.FINANCING_LEASE)
        validator = QualityValidator()
        report = validator.validate(
            valid_case_data,
            valid_claim_list,
            empty_evidence,
            valid_generated_evidence
        )
        assert not report.is_valid

    def test_validate_inconsistent_amounts(self, valid_claim_list, valid_evidence_list, valid_generated_evidence):
        """测试验证金额不一致"""
        inconsistent_data = CaseData(
            plaintiff=Party(name="原告", credit_code="123", address="地址", legal_representative="张三"),
            defendant=Party(name="被告", credit_code="456", address="地址", legal_representative="李四"),
            contract=ContractInfo(type=CaseType.FINANCING_LEASE, subject="设备", amount=100000, signing_date=datetime.now()),
            paid_amount=200000
        )
        validator = QualityValidator()
        report = validator.validate(
            inconsistent_data,
            valid_claim_list,
            valid_evidence_list,
            valid_generated_evidence
        )
        has_amount_warning = any(
            issue.category == "amount" for issue in report.issues
        )
        assert has_amount_warning

    def test_validate_future_date(self, valid_claim_list, valid_evidence_list, valid_generated_evidence):
        """测试验证未来日期"""
        future_date = datetime(2099, 1, 1)
        invalid_data = CaseData(
            plaintiff=Party(name="原告", credit_code="123", address="地址", legal_representative="张三"),
            defendant=Party(name="被告", credit_code="456", address="地址", legal_representative="李四"),
            contract=ContractInfo(type=CaseType.FINANCING_LEASE, subject="设备", amount=100000, signing_date=future_date)
        )
        validator = QualityValidator()
        report = validator.validate(
            invalid_data,
            valid_claim_list,
            valid_evidence_list,
            valid_generated_evidence
        )
        has_date_issue = any(
            issue.category == "date" for issue in report.issues
        )

    def test_quick_validate_valid_data(self, valid_case_data, valid_claim_list, valid_evidence_list):
        """测试快速验证有效数据"""
        validator = QualityValidator()
        result = validator.quick_validate(valid_case_data, valid_claim_list, valid_evidence_list)
        assert result is True

    def test_quick_validate_missing_data(self, valid_claim_list, valid_evidence_list):
        """测试快速验证缺失数据"""
        validator = QualityValidator()
        incomplete_data = CaseData(
            plaintiff=Party(name="原告", credit_code="123", address="地址", legal_representative="张三"),
            defendant=Party(name="被告", credit_code="456", address="地址", legal_representative="李四"),
            contract=None
        )
        result = validator.quick_validate(incomplete_data, valid_claim_list, valid_evidence_list)
        assert result is False


class TestEvidenceQualityChecker:
    """Test EvidenceQualityChecker class"""

    def test_check_short_content(self, valid_case_data):
        """测试检查短内容"""
        checker = EvidenceQualityChecker()
        short_evidence = GeneratedEvidence(
            filename="test.txt",
            content="短内容",
            evidence_type=EvidenceType.CONTRACT
        )
        issues = checker.check(short_evidence, valid_case_data)
        has_length_issue = any(
            issue.category == "evidence_quality" and "过短" in issue.message
            for issue in issues
        )
        assert has_length_issue

    def test_check_valid_content(self, valid_case_data):
        """测试检查有效内容"""
        checker = EvidenceQualityChecker()
        valid_evidence = GeneratedEvidence(
            filename="test.txt",
            content="内容" * 200,
            evidence_type=EvidenceType.CONTRACT
        )
        issues = checker.check(valid_evidence, valid_case_data)
        assert len(issues) == 0

    def test_check_missing_filename(self, valid_case_data):
        """测试检查缺失文件名"""
        checker = EvidenceQualityChecker()
        evidence = GeneratedEvidence(
            filename="",
            content="内容" * 200,
            evidence_type=EvidenceType.CONTRACT
        )
        issues = checker.check(evidence, valid_case_data)
        has_filename_issue = any(
            issue.category == "evidence_quality" and "文件名" in issue.message
            for issue in issues
        )
        assert has_filename_issue

    def test_check_missing_type(self, valid_case_data):
        """测试检查缺失证据类型"""
        checker = EvidenceQualityChecker()
        evidence = GeneratedEvidence(
            filename="test.txt",
            content="内容" * 200,
            evidence_type=None
        )
        issues = checker.check(evidence, valid_case_data)
        has_type_issue = any(
            issue.category == "evidence_quality" and "类型" in issue.message
            for issue in issues
        )
        assert has_type_issue
