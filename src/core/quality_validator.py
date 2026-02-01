"""
QualityValidator - 质量验证器

功能：验证生成证据的质量和完整性

输入：CaseData, ClaimList, EvidenceList, GeneratedEvidence列表
输出：验证报告

核心原则：
- P1 脱敏标记隔离：验证不使用脱敏标记
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from .data_models import (
    CaseData,
    ClaimList,
    EvidenceList,
    GeneratedEvidence,
    EvidenceIndex
)


@dataclass
class ValidationIssue:
    """验证问题"""
    severity: str
    category: str
    message: str
    suggestion: Optional[str] = None


@dataclass
class ValidationReport:
    """验证报告"""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    score: int = 0
    details: Dict[str, Any] = field(default_factory=dict)

    def add_issue(self, issue: ValidationIssue):
        self.issues.append(issue)
        self._update_status()

    def _update_status(self):
        critical_count = sum(1 for i in self.issues if i.severity == "critical")
        error_count = sum(1 for i in self.issues if i.severity == "error")
        warning_count = sum(1 for i in self.issues if i.severity == "warning")

        self.is_valid = critical_count == 0 and error_count == 0

        base_score = 100
        base_score -= critical_count * 20
        base_score -= error_count * 10
        base_score -= warning_count * 5
        self.score = max(0, base_score)

        self.details = {
            "total_issues": len(self.issues),
            "critical": critical_count,
            "errors": error_count,
            "warnings": warning_count,
            "score": self.score
        }


class QualityValidator:
    """
    质量验证器

    验证生成证据的质量和完整性。
    检查项包括：
    1. 数据完整性
    2. 金额一致性
    3. 日期逻辑
    4. 当事人信息完整性
    5. 证据覆盖完整性
    """

    def __init__(self):
        self.validators = [
            self._validate_case_data,
            self._validate_claim_list,
            self._validate_evidence_list,
            self._validate_amount_consistency,
            self._validate_date_logic,
            self._validate_party_info,
            self._validate_evidence_coverage,
        ]

    def validate(
        self,
        case_data: CaseData,
        claim_list: ClaimList,
        evidence_list: EvidenceList,
        generated_evidence: List[GeneratedEvidence],
        evidence_index: Optional[EvidenceIndex] = None
    ) -> ValidationReport:
        """
        执行完整验证

        Args:
            case_data: 案情基本数据
            claim_list: 诉求列表
            evidence_list: 证据列表
            generated_evidence: 生成的证据列表
            evidence_index: 证据索引（可选）
        Returns:
            ValidationReport: 验证报告
        """
        report = ValidationReport(is_valid=True)

        for validator in self.validators:
            validator(report, case_data, claim_list, evidence_list, generated_evidence)

        return report

    def _validate_case_data(
        self,
        report: ValidationReport,
        case_data: CaseData,
        claim_list: ClaimList,
        evidence_list: EvidenceList,
        generated_evidence: List[GeneratedEvidence]
    ):
        """验证案情数据完整性"""
        if not case_data.plaintiff:
            report.add_issue(ValidationIssue(
                severity="critical",
                category="case_data",
                message="原告信息缺失",
                suggestion="请提供完整的原告信息"
            ))

        if not case_data.defendant:
            report.add_issue(ValidationIssue(
                severity="critical",
                category="case_data",
                message="被告信息缺失",
                suggestion="请提供完整的被告信息"
            ))

        if not case_data.contract:
            report.add_issue(ValidationIssue(
                severity="critical",
                category="case_data",
                message="合同信息缺失",
                suggestion="请提供完整的合同信息"
            ))

    def _validate_claim_list(
        self,
        report: ValidationReport,
        case_data: CaseData,
        claim_list: ClaimList,
        evidence_list: EvidenceList,
        generated_evidence: List[GeneratedEvidence]
    ):
        """验证诉求列表完整性"""
        if not claim_list.claims:
            report.add_issue(ValidationIssue(
                severity="error",
                category="claim_list",
                message="诉讼请求列表为空",
                suggestion="请检查是否正确提取诉讼请求"
            ))

        total_claim_amount = sum(claim.amount for claim in claim_list.claims)

        if total_claim_amount <= 0:
            report.add_issue(ValidationIssue(
                severity="error",
                category="claim_list",
                message="诉讼请求金额为零或负数",
                suggestion="请检查诉讼请求金额是否正确"
            ))

    def _validate_evidence_list(
        self,
        report: ValidationReport,
        case_data: CaseData,
        claim_list: ClaimList,
        evidence_list: EvidenceList,
        generated_evidence: List[GeneratedEvidence]
    ):
        """验证证据列表完整性"""
        if not evidence_list.items:
            report.add_issue(ValidationIssue(
                severity="error",
                category="evidence_list",
                message="证据列表为空",
                suggestion="请检查证据规划是否正确"
            ))

        if len(evidence_list.items) < 3:
            report.add_issue(ValidationIssue(
                severity="warning",
                category="evidence_list",
                message="证据数量过少，可能影响诉讼支持",
                suggestion="建议增加更多证据材料"
            ))

    def _validate_amount_consistency(
        self,
        report: ValidationReport,
        case_data: CaseData,
        claim_list: ClaimList,
        evidence_list: EvidenceList,
        generated_evidence: List[GeneratedEvidence]
    ):
        """验证金额一致性"""
        if case_data.contract and case_data.remaining_amount:
            if case_data.remaining_amount > case_data.contract.amount:
                report.add_issue(ValidationIssue(
                    severity="error",
                    category="amount",
                    message=f"剩余欠款({case_data.remaining_amount:,.2f})大于合同金额({case_data.contract.amount:,.2f})",
                    suggestion="请检查金额数据是否正确"
                ))

        if case_data.paid_amount and case_data.contract:
            if case_data.paid_amount > case_data.contract.amount:
                report.add_issue(ValidationIssue(
                    severity="error",
                    category="amount",
                    message=f"已付金额({case_data.paid_amount:,.2f})大于合同金额({case_data.contract.amount:,.2f})",
                    suggestion="请检查金额数据是否正确"
                ))

        principal_claims = [c for c in claim_list.claims if c.type == "本金"]
        if principal_claims and case_data.contract:
            for claim in principal_claims:
                if abs(claim.amount - case_data.contract.amount) > case_data.contract.amount * 0.1:
                    report.add_issue(ValidationIssue(
                        severity="warning",
                        category="amount",
                        message=f"本金诉求({claim.amount:,.2f})与合同金额({case_data.contract.amount:,.2f})差异较大",
                        suggestion="请检查本金诉求是否正确"
                    ))

    def _validate_date_logic(
        self,
        report: ValidationReport,
        case_data: CaseData,
        claim_list: ClaimList,
        evidence_list: EvidenceList,
        generated_evidence: List[GeneratedEvidence]
    ):
        """验证日期逻辑"""
        if case_data.contract:
            if case_data.contract.performance_date:
                if case_data.contract.performance_date < case_data.contract.signing_date:
                    report.add_issue(ValidationIssue(
                        severity="error",
                        category="date",
                        message="合同履行日期早于签订日期",
                        suggestion="请检查日期数据是否正确"
                    ))

            if case_data.contract.term_months:
                if case_data.contract.term_months <= 0:
                    report.add_issue(ValidationIssue(
                        severity="error",
                        category="date",
                        message="合同期限为负数或零",
                        suggestion="请检查合同期限是否正确"
                    ))

        if case_data.breach and case_data.breach.breach_date:
            if case_data.breach.breach_date < case_data.contract.signing_date:
                report.add_issue(ValidationIssue(
                    severity="error",
                    category="date",
                    message="违约日期早于合同签订日期",
                    suggestion="请检查违约日期是否正确"
                ))

    def _validate_party_info(
        self,
        report: ValidationReport,
        case_data: CaseData,
        claim_list: ClaimList,
        evidence_list: EvidenceList,
        generated_evidence: List[GeneratedEvidence]
    ):
        """验证当事人信息完整性"""
        for party_name, party in [("原告", case_data.plaintiff), ("被告", case_data.defendant)]:
            if party:
                if not party.name:
                    report.add_issue(ValidationIssue(
                        severity="critical",
                        category="party_info",
                        message=f"{party_name}名称缺失",
                        suggestion="请提供完整的当事人名称"
                    ))

                if not party.address:
                    report.add_issue(ValidationIssue(
                        severity="warning",
                        category="party_info",
                        message=f"{party_name}地址缺失",
                        suggestion="请提供完整的当事人地址"
                    ))

                if not party.legal_representative:
                    report.add_issue(ValidationIssue(
                        severity="warning",
                        category="party_info",
                        message=f"{party_name}法定代表人缺失",
                        suggestion="请提供法定代表人信息"
                    ))

    def _validate_evidence_coverage(
        self,
        report: ValidationReport,
        case_data: CaseData,
        claim_list: ClaimList,
        evidence_list: EvidenceList,
        generated_evidence: List[GeneratedEvidence]
    ):
        """验证证据覆盖完整性"""
        if not evidence_list.items:
            return

        evidence_types = set(item.type for item in evidence_list.items)

        has_contract = any(item.type.value == "合同类" for item in evidence_list.items)
        has_voucher = any(item.type.value == "凭证类" for item in evidence_list.items)

        if not has_contract:
            report.add_issue(ValidationIssue(
                severity="warning",
                category="evidence_coverage",
                message="缺少合同类证据",
                suggestion="建议添加融资租赁合同作为主要证据"
            ))

        if not has_voucher and case_data.paid_amount:
            report.add_issue(ValidationIssue(
                severity="warning",
                category="evidence_coverage",
                message="缺少付款凭证类证据",
                suggestion="建议添加收据或银行流水作为付款证明"
            ))

    def quick_validate(
        self,
        case_data: CaseData,
        claim_list: ClaimList,
        evidence_list: EvidenceList
    ) -> bool:
        """
        快速验证（仅检查关键项）

        Args:
            case_data: 案情基本数据
            claim_list: 诉求列表
            evidence_list: 证据列表
        Returns:
            bool: 是否通过快速验证
        """
        if not case_data.plaintiff or not case_data.defendant:
            return False

        if not case_data.contract:
            return False

        if not claim_list.claims:
            return False

        if not evidence_list.items:
            return False

        return True


class EvidenceQualityChecker:
    """
    证据质量检查器

    检查单个证据的质量和格式。
    """

    def __init__(self):
        self.min_content_length = 100
        self.required_sections = []

    def check(
        self,
        evidence: GeneratedEvidence,
        case_data: CaseData
    ) -> List[ValidationIssue]:
        """
        检查单个证据质量

        Args:
            evidence: 生成的证据
            case_data: 案情基本数据
        Returns:
            List[ValidationIssue]: 问题列表
        """
        issues = []

        if len(evidence.content) < self.min_content_length:
            issues.append(ValidationIssue(
                severity="warning",
                category="evidence_quality",
                message=f"证据'{evidence.filename}'内容过短",
                suggestion="请检查证据内容是否完整"
            ))

        if not evidence.filename:
            issues.append(ValidationIssue(
                severity="error",
                category="evidence_quality",
                message="证据文件名缺失",
                suggestion="请为证据指定文件名"
            ))

        if not evidence.evidence_type:
            issues.append(ValidationIssue(
                severity="error",
                category="evidence_quality",
                message="证据类型缺失",
                suggestion="请指定证据类型"
            ))

        return issues
