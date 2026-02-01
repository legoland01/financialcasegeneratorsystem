"""
EvidenceIndexGenerator - F2.11 证据索引生成器

功能：根据证据列表生成证据清单索引

输入：EvidenceList（证据列表）
输出：EvidenceIndex（证据索引）

核心原则：
- P1 脱敏标记隔离：全程使用真实信息
- P2 要素驱动：系统负责生成证据索引
"""

from typing import List
from .data_models import (
    EvidenceList,
    EvidenceIndex,
    EvidenceIndexItem,
    EvidenceType,
    ClaimList
)


class EvidenceIndexGenerator:
    """
    证据索引生成器 - F2.11

    根据证据列表生成证据清单索引。
    为每个证据分配编号，并说明证明目的和支撑的诉求。
    """

    def generate(
        self,
        evidence_list: EvidenceList,
        claim_list: ClaimList
    ) -> EvidenceIndex:
        """
        生成证据索引

        Args:
            evidence_list: 证据列表
            claim_list: 诉求列表（用于确定证据支撑的诉求）
        Returns:
            EvidenceIndex: 证据索引
        """
        items = []

        for i, evidence_item in enumerate(evidence_list.items, 1):
            index_item = self._create_index_item(
                evidence_item,
                i,
                claim_list
            )
            items.append(index_item)

        return EvidenceIndex(
            items=items,
            total_count=len(items)
        )

    def _create_index_item(
        self,
        evidence_item: "EvidenceListItem",
        number: int,
        claim_list: ClaimList
    ) -> EvidenceIndexItem:
        """
        创建证据索引项

        Args:
            evidence_item: 证据列表项
            number: 证据编号
            claim_list: 诉求列表
        Returns:
            EvidenceIndexItem: 证据索引项
        """
        purpose = self._determine_purpose(evidence_item)
        claims_supported = self._determine_supported_claims(
            evidence_item,
            claim_list
        )

        return EvidenceIndexItem(
            number=number,
            name=evidence_item.name,
            type=evidence_item.type,
            purpose=purpose,
            claims_supported=claims_supported
        )

    def _determine_purpose(self, evidence_item: "EvidenceListItem") -> str:
        """
        确定证据的证明目的

        Args:
            evidence_item: 证据列表项
        Returns:
            str: 证明目的描述
        """
        evidence_type = evidence_item.type
        key_info = evidence_item.key_info

        if evidence_type == EvidenceType.CONTRACT:
            return "证明原告与被告之间存在合法有效的融资租赁合同关系"
        elif evidence_type == EvidenceType.VOUCHER:
            return "证明被告已履行部分合同义务的事实"
        elif evidence_type == EvidenceType.DOCUMENT:
            return "证明原告向被告催收债务的事实"
        elif evidence_type == EvidenceType.ATTACHMENT:
            attachment_type = key_info.get("附件类型", "")
            if attachment_type == "租赁物清单":
                return "证明租赁物的具体名称、规格和数量"
            elif attachment_type == "还款计划":
                return "证明被告应当履行的还款计划"
            else:
                return "证明与本案相关的其他事实"
        else:
            return "证明与本案相关的法律事实"

    def _determine_supported_claims(
        self,
        evidence_item: "EvidenceListItem",
        claim_list: ClaimList
    ) -> List[str]:
        """
        确定证据支撑的诉求

        Args:
            evidence_item: 证据列表项
            claim_list: 诉求列表
        Returns:
            List[str]: 支撑的诉求列表
        """
        supported = []
        evidence_type = evidence_item.type

        for claim in claim_list.claims:
            claim_type = claim.type

            if evidence_type == EvidenceType.CONTRACT:
                if claim_type in ["本金", "利息"]:
                    supported.append(claim.type)
                elif claim_type == "违约金":
                    supported.append(claim.type)
            elif evidence_type == EvidenceType.VOUCHER:
                if claim_type in ["本金", "利息"]:
                    supported.append(claim.type)
            elif evidence_type == EvidenceType.DOCUMENT:
                if claim_type == "违约金":
                    supported.append(claim.type)
            elif evidence_type == EvidenceType.ATTACHMENT:
                if claim_type == "本金":
                    supported.append(claim.type)

        if not supported:
            supported = ["全部诉讼请求"]

        return supported

    def generate_to_text(
        self,
        evidence_list: EvidenceList,
        claim_list: ClaimList
    ) -> str:
        """
        生成证据索引文本

        Args:
            evidence_list: 证据列表
            claim_list: 诉求列表
        Returns:
            str: 证据索引文本
        """
        evidence_index = self.generate(evidence_list, claim_list)
        return evidence_index.to_text()

    def generate_to_dict(
        self,
        evidence_list: EvidenceList,
        claim_list: ClaimList
    ) -> dict:
        """
        生成证据索引字典

        Args:
            evidence_list: 证据列表
            claim_list: 诉求列表
        Returns:
            dict: 证据索引字典
        """
        evidence_index = self.generate(evidence_list, claim_list)
        return evidence_index.to_dict()
