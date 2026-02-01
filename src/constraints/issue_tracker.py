"""问题追踪器 - 防止问题复发 (EXE-004)

EXE-004 问题: PDF问题重复发生（占位符、分页等）
解决方案: 记录发现的问题，防止相同问题再次发生
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum
from datetime import datetime
from loguru import logger
import json
import hashlib


class IssueType(Enum):
    """问题类型"""
    PLACEHOLDER = "placeholder"
    PAGINATION = "pagination"
    LAYOUT = "layout"
    DATA_FORMAT = "data_format"
    MODE_CONFUSION = "mode_confusion"
    CONFIG_ERROR = "config_error"
    API_ERROR = "api_error"
    UNKNOWN = "unknown"


class IssueSeverity(Enum):
    """问题严重级别"""
    BLOCKER = "blocker"
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    TRIVIAL = "trivial"


@dataclass
class Issue:
    """问题记录"""
    issue_type: IssueType
    severity: IssueSeverity
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    evidence_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved: bool = False
    resolution: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "issue_type": self.issue_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "evidence_id": self.evidence_id,
            "timestamp": self.timestamp,
            "resolved": self.resolved,
            "resolution": self.resolution,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Issue':
        return cls(
            issue_type=IssueType(data.get("issue_type", "unknown")),
            severity=IssueSeverity(data.get("severity", "minor")),
            title=data.get("title", ""),
            description=data.get("description", ""),
            file_path=data.get("file_path"),
            line_number=data.get("line_number"),
            evidence_id=data.get("evidence_id"),
            timestamp=data.get("timestamp", ""),
            resolved=data.get("resolved", False),
            resolution=data.get("resolution"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )

    def get_signature(self) -> str:
        """获取问题签名，用于去重"""
        content = f"{self.issue_type.value}:{self.title}:{self.file_path}:{self.evidence_id}"
        return hashlib.md5(content.encode()).hexdigest()[:16]


@dataclass
class IssueStats:
    """问题统计"""
    total: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    by_severity: Dict[str, int] = field(default_factory=dict)
    resolved: int = 0
    unresolved: int = 0

    def update(self, issue: Issue):
        self.total += 1
        self.by_type[issue.issue_type.value] = self.by_type.get(issue.issue_type.value, 0) + 1
        self.by_severity[issue.severity.value] = self.by_severity.get(issue.severity.value, 0) + 1
        if issue.resolved:
            self.resolved += 1
        else:
            self.unresolved += 1

    def summary(self) -> str:
        lines = [
            f"问题统计: 共 {self.total} 个问题",
            f"  - 已解决: {self.resolved}",
            f"  - 未解决: {self.unresolved}",
            f"  - 按类型: {', '.join(f'{k}({v})' for k, v in self.by_type.items())}",
            f"  - 按级别: {', '.join(f'{k}({v})' for k, v in self.by_severity.items())}",
        ]
        return "\n".join(lines)


class IssueTracker:
    """问题追踪器

    功能:
    - 记录发现的问题
    - 防止重复记录相同问题
    - 统计问题分布
    - 导出问题报告
    - 提供问题查找和筛选
    """

    _instance: Optional['IssueTracker'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.issues: List[Issue] = []
            self.signatures: set = set()
            self.stats = IssueStats()
            self._initialized = True
            self.report_path = "issue_report.json"

    @classmethod
    def reset(cls):
        """重置追踪器（用于测试）"""
        cls._instance = None

    def track(
        self,
        issue_type: IssueType,
        severity: IssueSeverity,
        title: str,
        description: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        evidence_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Issue:
        """
        记录一个问题

        Args:
            issue_type: 问题类型
            severity: 严重级别
            title: 问题标题
            description: 问题描述
            file_path: 相关文件路径
            line_number: 相关行号
            evidence_id: 证据ID
            tags: 标签
            metadata: 元数据

        Returns:
            Issue: 记录的问题
        """
        issue = Issue(
            issue_type=issue_type,
            severity=severity,
            title=title,
            description=description,
            file_path=file_path,
            line_number=line_number,
            evidence_id=evidence_id,
            tags=tags or [],
            metadata=metadata or {},
        )

        signature = issue.get_signature()
        if signature in self.signatures:
            logger.debug(f"问题已存在，跳过: {title}")
            return issue

        self.issues.append(issue)
        self.signatures.add(signature)
        self.stats.update(issue)

        self._log_issue(issue)

        return issue

    def _log_issue(self, issue: Issue):
        """记录问题日志"""
        emoji = {
            IssueSeverity.BLOCKER: "🚫",
            IssueSeverity.CRITICAL: "🔴",
            IssueSeverity.MAJOR: "🟠",
            IssueSeverity.MINOR: "🟡",
            IssueSeverity.TRIVIAL: "🟢",
        }.get(issue.severity, "⚪")

        logger.warning(
            f"{emoji} [{issue.issue_type.value}] {issue.title}\n"
            f"    {issue.description[:100]}{'...' if len(issue.description) > 100 else ''}"
            + (f" ({issue.file_path})" if issue.file_path else "")
        )

    def track_placeholder(
        self,
        placeholder: str,
        file_path: str,
        evidence_id: Optional[str] = None,
    ):
        """记录占位符问题"""
        self.track(
            issue_type=IssueType.PLACEHOLDER,
            severity=IssueSeverity.CRITICAL,
            title=f"发现占位符: {placeholder[:30]}",
            description=f"在文件 {file_path} 中发现未替换的占位符",
            file_path=file_path,
            evidence_id=evidence_id,
            tags=["placeholder", "critical"],
            metadata={"placeholder": placeholder},
        )

    def track_pagination_error(
        self,
        file_path: str,
        page_number: int,
        error_description: str,
    ):
        """记录分页错误"""
        self.track(
            issue_type=IssueType.PAGINATION,
            severity=IssueSeverity.MAJOR,
            title=f"分页错误: 第{page_number}页",
            description=error_description,
            file_path=file_path,
            tags=["pagination", "layout"],
            metadata={"page_number": page_number},
        )

    def track_data_format_error(
        self,
        field_name: str,
        expected_format: str,
        actual_value: str,
        file_path: Optional[str] = None,
    ):
        """记录数据格式错误"""
        self.track(
            issue_type=IssueType.DATA_FORMAT,
            severity=IssueSeverity.MAJOR,
            title=f"数据格式错误: {field_name}",
            description=f"期望格式: {expected_format}, 实际值: {actual_value}",
            file_path=file_path,
            tags=["data", "format"],
            metadata={
                "field_name": field_name,
                "expected_format": expected_format,
                "actual_value": actual_value,
            },
        )

    def resolve(self, issue: Issue, resolution: str):
        """标记问题已解决"""
        issue.resolved = True
        issue.resolution = resolution
        logger.info(f"✅ 问题已解决: {issue.title} - {resolution}")

    def find_by_type(self, issue_type: IssueType) -> List[Issue]:
        """按类型查找问题"""
        return [i for i in self.issues if i.issue_type == issue_type]

    def find_by_severity(self, severity: IssueSeverity) -> List[Issue]:
        """按级别查找问题"""
        return [i for i in self.issues if i.severity == severity]

    def find_unresolved(self) -> List[Issue]:
        """查找未解决的问题"""
        return [i for i in self.issues if not i.resolved]

    def get_blockers(self) -> List[Issue]:
        """获取阻塞性问题"""
        return [i for i in self.issues if i.severity == IssueSeverity.BLOCKER and not i.resolved]

    def export_report(self, path: Optional[str] = None) -> str:
        """
        导出问题报告

        Args:
            path: 报告路径

        Returns:
            str: 报告路径
        """
        report_path = path or self.report_path

        report = {
            "generated_at": datetime.now().isoformat(),
            "stats": {
                "total": self.stats.total,
                "by_type": self.stats.by_type,
                "by_severity": self.stats.by_severity,
                "resolved": self.stats.resolved,
                "unresolved": self.stats.unresolved,
            },
            "issues": [issue.to_dict() for issue in self.issues],
        }

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"问题报告已导出: {report_path}")
        return report_path

    def load_report(self, path: str):
        """加载问题报告"""
        with open(path, 'r', encoding='utf-8') as f:
            report = json.load(f)

        self.issues = [Issue.from_dict(i) for i in report.get("issues", [])]
        self.signatures = {issue.get_signature() for issue in self.issues}
        self.stats = IssueStats()
        for issue in self.issues:
            self.stats.update(issue)

        logger.info(f"已加载问题报告: {path}，共 {len(self.issues)} 个问题")

    def print_summary(self):
        """打印问题摘要"""
        print("\n" + "=" * 60)
        print("问题追踪摘要")
        print("=" * 60)
        print(self.stats.summary())
        print("\n未解决问题:")
        for issue in self.find_unresolved():
            print(f"  - [{issue.issue_type.value}] {issue.title}")
        print("=" * 60 + "\n")

    def get_stats(self) -> IssueStats:
        """获取问题统计"""
        return self.stats


def get_tracker() -> IssueTracker:
    """获取问题追踪器实例"""
    return IssueTracker()


def track_issue(
    issue_type: IssueType,
    severity: IssueSeverity,
    title: str,
    description: str,
    **kwargs
) -> Issue:
    """
    记录问题的便捷函数

    Args:
        issue_type: 问题类型
        severity: 严重级别
        title: 问题标题
        description: 问题描述
        **kwargs: 其他参数

    Returns:
        Issue: 记录的问题
    """
    tracker = get_tracker()
    return tracker.track(issue_type, severity, title, description, **kwargs)
