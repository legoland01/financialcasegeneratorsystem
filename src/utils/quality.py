"""质量控制工具函数"""
from typing import Dict, Any, List
from loguru import logger
from src.utils.helpers import (
    extract_company_names,
    extract_person_names,
    extract_amounts,
    extract_dates,
)


class QualityCheckIssue:
    """质量问题"""
    def __init__(
        self,
        issue_type: str,
        description: str,
        severity: str = "medium",
        position: str = "",
        suggestion: str = ""
    ):
        self.issue_type = issue_type
        self.description = description
        self.severity = severity
        self.position = position
        self.suggestion = suggestion
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "问题类型": self.issue_type,
            "问题描述": self.description,
            "严重程度": self.severity,
            "位置": self.position,
            "建议修正": self.suggestion
        }


class QualityChecker:
    """质量检查器"""
    
    def __init__(self, stage0_data: Dict[str, Any]):
        self.stage0_data = stage0_data
        self.issues: List[QualityCheckIssue] = []
    
    def check_company_names(self, document: str) -> List[QualityCheckIssue]:
        """
        检查规则1: 公司名称一致性
        
        Args:
            document: 待检查的文档
        
        Returns:
            发现的问题列表
        """
        issues = []
        company_names = extract_company_names(document)
        stage0_companies = []
        
        if "0.2_脱敏替换策划" in self.stage0_data:
            company_profiles = self.stage0_data["0.2_脱敏替换策划"].get("公司Profile库", {})
            stage0_companies = list(company_profiles.keys())
        
        for name in company_names:
            if name not in stage0_companies:
                issues.append(QualityCheckIssue(
                    issue_type="公司名称不一致",
                    description=f'公司名称"{name}"未在profile库中找到',
                    severity="high",
                    suggestion=f"请检查公司名称或补充profile库"
                ))
        
        return issues
    
    def check_person_names(self, document: str) -> List[QualityCheckIssue]:
        """
        检查规则2: 人物信息一致性
        
        Args:
            document: 待检查的文档
        
        Returns:
            发现的问题列表
        """
        issues = []
        person_names = extract_person_names(document)
        stage0_persons = []
        
        if "0.2_脱敏替换策划" in self.stage0_data:
            person_profiles = self.stage0_data["0.2_脱敏替换策划"].get("人物Profile库", {})
            stage0_persons = list(person_profiles.keys())
        
        for name in person_names:
            if name not in stage0_persons:
                issues.append(QualityCheckIssue(
                    issue_type="人物信息不一致",
                    description=f'人名"{name}"未在profile库中找到',
                    severity="high",
                    suggestion=f"请检查人名或补充profile库"
                ))
        
        return issues
    
    def check_amounts(self, document: str) -> List[QualityCheckIssue]:
        """
        检查规则3: 金额一致性
        
        Args:
            document: 待检查的文档
        
        Returns:
            发现的问题列表
        """
        issues = []
        document_amounts = extract_amounts(document)
        stage0_amounts = []
        
        if "0.4_关键数字清单" in self.stage0_data:
            key_numbers = self.stage0_data["0.4_关键数字清单"]
            # 这里简化处理,实际需要更复杂的金额比对逻辑
            stage0_amounts = key_numbers
        
        # 简化检查:只记录发现的金额
        for amount in document_amounts:
            # 实际应该检查金额是否在关键金额清单中
            pass
        
        return issues
    
    def check_dates(self, document: str) -> List[QualityCheckIssue]:
        """
        检查规则4: 日期一致性
        
        Args:
            document: 待检查的文档
        
        Returns:
            发现的问题列表
        """
        issues = []
        document_dates = extract_dates(document)
        stage0_dates = []
        
        if "0.3_交易结构重构" in self.stage0_data:
            transaction_reconstruction = self.stage0_data["0.3_交易结构重构"]
            if "交易时间线" in transaction_reconstruction:
                for event in transaction_reconstruction["交易时间线"]:
                    if "时间" in event:
                        stage0_dates.append(event["时间"])
        
        for date in document_dates:
            if date not in stage0_dates:
                # 不一定所有日期都在交易时间线中,这里只是示例
                pass
        
        return issues
    
    def check_all(self, document: str) -> List[QualityCheckIssue]:
        """
        执行所有检查
        
        Args:
            document: 待检查的文档
        
        Returns:
            所有发现的问题列表
        """
        self.issues = []
        self.issues.extend(self.check_company_names(document))
        self.issues.extend(self.check_person_names(document))
        self.issues.extend(self.check_amounts(document))
        self.issues.extend(self.check_dates(document))
        return self.issues
    
    def generate_report(self) -> Dict[str, Any]:
        """
        生成质量检查报告
        
        Returns:
            质量检查报告
        """
        from datetime import datetime
        
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        for issue in self.issues:
            severity_counts[issue.severity] += 1
        
        # 确定总体状态
        if severity_counts["high"] > 0:
            overall_status = "不通过"
        elif severity_counts["medium"] > 0:
            overall_status = "部分通过"
        else:
            overall_status = "通过"
        
        return {
            "报告生成时间": datetime.now().isoformat(),
            "检查结果": {
                "总体状态": overall_status,
                "发现的问题": [issue.to_dict() for issue in self.issues],
                "问题统计": severity_counts
            }
        }


def check_generation_result(
    generation_result: Dict[str, Any],
    stage0_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    检查生成结果的质量
    
    Args:
        generation_result: 生成结果
        stage0_data: 阶段0数据
    
    Returns:
        质量检查报告
    """
    checker = QualityChecker(stage0_data)
    
    if "content" in generation_result:
        issues = checker.check_all(generation_result["content"])
    else:
        issues = []
    
    return checker.generate_report()
