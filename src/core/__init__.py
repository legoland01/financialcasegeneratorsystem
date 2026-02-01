"""
核心模块 - v3.0

金融案件证据集生成系统的核心业务逻辑模块。

模块结构：
- data_models.py: 核心数据模型
- case_analyzer.py: F2.1 案情分析
- claim_extractor.py: F2.2 诉求提取
- evidence_planner.py: F2.3 证据规划
- evidence_collector.py: F2.4 证据收集
- evidence_list_creator.py: F2.5 证据列表创建（核心）
- litigation_complaint_generator.py: F2.6 起诉状生成
- document_generator.py: F2.7-F2.10 文档生成
- evidence_index_generator.py: F2.11 证据索引生成
- llm_client.py: LLM客户端
- quality_validator.py: 质量验证器
- pdf_generator.py: PDF生成器
"""

from .data_models import (
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
    EvidenceIndex,
)

__all__ = [
    # Enums
    "CaseType",
    "EvidenceType",
    "AttachmentForm",
    # Data classes
    "Party",
    "ContractInfo",
    "BreachInfo",
    "CaseData",
    "Claim",
    "ClaimList",
    "AttachmentPlan",
    "EvidenceRequirement",
    "EvidenceRequirements",
    "EvidenceItem",
    "EvidenceCollection",
    "AttachmentInfo",
    "EvidenceListItem",
    "EvidenceList",
    "GeneratedEvidence",
    "EvidenceIndexItem",
    "EvidenceIndex",
]
