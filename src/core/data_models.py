"""
核心数据模型 - v3.0

定义金融案件证据生成系统所需的所有数据模型。
遵循核心架构原则：
- P1 脱敏标记隔离：全程使用真实信息
- P2 要素驱动：系统提取要素，LLM生成内容
- P3 附件规划：F2.3必须规划附件形式
- P4 数据契约：EvidenceList结构化输出
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import json


class CaseType(Enum):
    """案件类型枚举"""
    FINANCING_LEASE = "融资租赁"
    LOAN = "金融借款"
    FACTORING = "保理"
    GUARANTEE = "担保"


class EvidenceType(Enum):
    """证据类型枚举"""
    CONTRACT = "合同类"
    VOUCHER = "凭证类"
    DOCUMENT = "文书类"
    ATTACHMENT = "附件类"


class AttachmentForm(Enum):
    """附件形式枚举"""
    INDEPENDENT_FILE = "独立文件"
    IN_BODY = "正文包含"
    NO_ATTACHMENT = "不需附件"


@dataclass
class Party:
    """当事人信息"""
    name: str                      # 公司名称
    credit_code: str               # 统一社会信用代码
    address: str                   # 注册地址
    legal_representative: str      # 法定代表人
    bank_account: Optional[str] = None  # 银行账户（可选）

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "credit_code": self.credit_code,
            "address": self.address,
            "legal_representative": self.legal_representative,
            "bank_account": self.bank_account
        }


@dataclass
class ContractInfo:
    """合同信息"""
    type: CaseType                 # 合同类型
    subject: str                   # 标的物描述
    amount: float                  # 合同金额
    signing_date: datetime         # 签订日期
    performance_date: Optional[datetime] = None  # 履行日期
    term_months: Optional[int] = None   # 租期/贷款期限（月）

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "subject": self.subject,
            "amount": self.amount,
            "signing_date": self.signing_date.isoformat() if self.signing_date else None,
            "performance_date": self.performance_date.isoformat() if self.performance_date else None,
            "term_months": self.term_months
        }


@dataclass
class BreachInfo:
    """违约信息"""
    breach_date: Optional[datetime] = None   # 违约日期
    breach_amount: Optional[float] = None    # 违约金额
    breach_description: Optional[str] = None # 违约描述

    def to_dict(self) -> Dict[str, Any]:
        return {
            "breach_date": self.breach_date.isoformat() if self.breach_date else None,
            "breach_amount": self.breach_amount,
            "breach_description": self.breach_description
        }


@dataclass
class CaseData:
    """
    案情基本数据集 - F2.1输出
    
    这是v3.0系统的核心数据载体，包含案件的所有关键信息。
    全程使用真实信息，不包含任何脱敏标记。
    """
    plaintiff: Party               # 原告
    defendant: Party               # 被告
    contract: ContractInfo         # 合同信息
    guarantor: Optional[Party] = None   # 担保人（可选）
    paid_amount: Optional[float] = None     # 已付金额
    remaining_amount: Optional[float] = None    # 剩余欠款
    breach: Optional[BreachInfo] = None         # 违约信息
    attachments: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    judgment_path: Optional[str] = None
    extracted_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plaintiff": self.plaintiff.to_dict(),
            "defendant": self.defendant.to_dict(),
            "contract": self.contract.to_dict(),
            "guarantor": self.guarantor.to_dict() if self.guarantor else None,
            "paid_amount": self.paid_amount,
            "remaining_amount": self.remaining_amount,
            "breach": self.breach.to_dict() if self.breach else None,
            "attachments": self.attachments,
            "judgment_path": self.judgment_path,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass
class Claim:
    """单个诉求"""
    type: str           # 诉求类型：本金/利息/违约金/其他
    amount: float       # 诉求金额
    description: Optional[str] = None  # 诉求描述

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "amount": self.amount,
            "description": self.description
        }


@dataclass
class ClaimList:
    """诉求列表 - F2.2输出"""
    claims: List[Claim]             # 诉求列表
    litigation_cost: Optional[float] = None  # 诉讼费用
    attorney_fee: Optional[float] = None     # 律师费用（可选）

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claims": [c.to_dict() for c in self.claims],
            "litigation_cost": self.litigation_cost,
            "attorney_fee": self.attorney_fee
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass
class AttachmentPlan:
    """附件规划"""
    type: str               # 附件类型：租赁物清单/还款计划
    form: AttachmentForm    # 形式
    source: str             # 来源：案情数据/配置文件/编造

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "form": self.form.value,
            "source": self.source
        }


@dataclass
class EvidenceRequirement:
    """证据需求 - F2.3输出"""
    name: str                       # 证据名称
    type: EvidenceType              # 证据类型
    facts_to_prove: List[str]       # 需要证明的事实
    claims_supported: List[str]     # 支撑的诉求
    attachment: Optional[AttachmentPlan] = None  # 附件规划（可选）

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.value,
            "facts_to_prove": self.facts_to_prove,
            "claims_supported": self.claims_supported,
            "attachment": self.attachment.to_dict() if self.attachment else None
        }


@dataclass
class EvidenceRequirements:
    """证据需求清单 - F2.3输出"""
    requirements: List[EvidenceRequirement]  # 证据需求列表
    case_type: CaseType                      # 案件类型

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requirements": [r.to_dict() for r in self.requirements],
            "case_type": self.case_type.value
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass
class EvidenceItem:
    """证据项 - F2.4输出"""
    name: str                       # 证据名称
    type: EvidenceType              # 证据类型
    source: str                     # 来源：判决书提取/自行编造
    fabricated: bool = False        # 是否为自行编造
    fabricated_note: Optional[str] = None  # 编造说明

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.value,
            "source": self.source,
            "fabricated": self.fabricated,
            "fabricated_note": self.fabricated_note
        }


@dataclass
class EvidenceCollection:
    """完整证据列表 - F2.4输出"""
    items: List[EvidenceItem]       # 证据项列表
    from_judgment: List[str] = field(default_factory=list)  # 来自判决书的证据
    fabricated: List[str] = field(default_factory=list)     # 自行编造的证据

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": [i.to_dict() for i in self.items],
            "from_judgment": self.from_judgment,
            "fabricated": self.fabricated
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass
class AttachmentInfo:
    """附件信息 - EvidenceList中的附件"""
    type: str               # 附件类型
    source: str             # 数据来源
    form: AttachmentForm    # 生成形式
    data: Optional[Dict[str, Any]] = None  # 附件数据

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "source": self.source,
            "form": self.form.value,
            "data": self.data
        }


@dataclass
class EvidenceListItem:
    """
    证据列表项 - F2.5输出 ← 核心
    
    这是v3.0最核心的数据结构。
    关键：EvidenceList只包含真实信息，是LLM生成证据的唯一依据。
    """
    name: str                       # 证据名称
    type: EvidenceType              # 证据类型
    key_info: Dict[str, Any]        # 关键信息（只包含真实信息）
    claims_supported: List[str]     # 支撑的诉求
    attachment: Optional[AttachmentInfo] = None  # 附件信息

    def to_prompt_context(self) -> str:
        """转换为LLM Prompt上下文"""
        lines = [f"证据名称：{self.name}", f"证据类型：{self.type.value}", ""]
        lines.append("关键信息：")
        for key, value in self.key_info.items():
            if isinstance(value, list):
                value = json.dumps(value, ensure_ascii=False)
            lines.append(f"  - {key}：{value}")
        if self.attachment:
            lines.append("")
            lines.append(f"附件：{self.attachment.type}")
            if self.attachment.data:
                lines.append("附件数据：")
                for key, value in self.attachment.data.items():
                    lines.append(f"  - {key}：{value}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.value,
            "key_info": self.key_info,
            "claims_supported": self.claims_supported,
            "attachment": self.attachment.to_dict() if self.attachment else None
        }


@dataclass
class EvidenceList:
    """
    证据列表 - F2.5输出 ← 核心输出
    
    这是LLM生成证据的依据。
    核心规则：EvidenceList只包含真实信息，不包含任何脱敏标记。
    """
    items: List[EvidenceListItem]   # 证据列表项
    case_type: CaseType             # 案件类型

    def to_llm_prompt(self) -> str:
        """转换为完整的LLM Prompt"""
        sections = ["=== 证据列表 ===", ""]
        for i, item in enumerate(self.items, 1):
            sections.append(f"【证据{i}】")
            sections.append(item.to_prompt_context())
            sections.append("")
        return "\n".join(sections)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": [i.to_dict() for i in self.items],
            "case_type": self.case_type.value
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


@dataclass
class GeneratedEvidence:
    """生成的证据"""
    filename: str           # 文件名，如：001_融资租赁合同.txt
    content: str            # 证据内容
    evidence_type: EvidenceType  # 证据类型

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filename": self.filename,
            "evidence_type": self.evidence_type.value
        }


@dataclass
class EvidenceIndexItem:
    """证据索引项 - F2.11输出"""
    number: int             # 证据编号
    name: str               # 证据名称
    type: EvidenceType      # 证据类型
    purpose: str            # 证明目的
    claims_supported: List[str]  # 支撑的诉求

    def to_dict(self) -> Dict[str, Any]:
        return {
            "number": self.number,
            "name": self.name,
            "type": self.type.value,
            "purpose": self.purpose,
            "claims_supported": self.claims_supported
        }


@dataclass
class EvidenceIndex:
    """证据索引 - F2.11输出"""
    items: List[EvidenceIndexItem]  # 索引项列表
    total_count: int                # 证据总数

    def to_text(self) -> str:
        """转换为文本"""
        lines = ["证据清单", "", f"证据总数：{self.total_count}", ""]
        for item in self.items:
            lines.append(f"证据{item.number}：{item.name}")
            lines.append(f"  类型：{item.type.value}")
            lines.append(f"  证明目的：{item.purpose}")
            lines.append(f"  支撑诉求：{', '.join(item.claims_supported)}")
            lines.append("")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": [i.to_dict() for i in self.items],
            "total_count": self.total_count
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
