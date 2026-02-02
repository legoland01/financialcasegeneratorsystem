"""
EvidenceListCreator - F2.5 证据列表创建器 ← 核心

功能：从案情基本数据集提取每份证据的关键信息

输入：CaseData + EvidenceCollection + EvidenceRequirements
输出：EvidenceList（证据列表）

核心原则：
- P1 脱敏标记隔离：EvidenceList只包含真实信息，不包含任何脱敏标记
- P2 要素驱动：从CaseData提取关键信息，不让LLM自己从判决书提取
- P4 数据契约：EvidenceList结构化输出，每份证据有关键信息字段

这是v3.0最核心的模块，确保LLM只接收真实信息。
"""

from typing import Dict, Any, List, Optional


class EvidenceListCreator:
    """
    证据列表创建器 - F2.5 ← 核心
    
    从案情基本数据集（CaseData）提取每份证据的关键信息。
    
    核心规则：
    1. 关键信息必须从CaseData提取，不能让LLM自己从判决书提取
    2. EvidenceList只包含真实信息，不包含任何脱敏标记
    3. 每份证据标注支撑的诉求
    
    输出：EvidenceList（证据列表）
    """
    
    def create(
        self,
        case_data: "CaseData",
        collection: "EvidenceCollection",
        requirements: "EvidenceRequirements"
    ) -> "EvidenceList":
        """
        从案情数据创建证据列表
        
        Args:
            case_data: 案情基本数据集（包含真实信息）
            collection: 完整证据列表
            requirements: 证据需求清单
        Returns:
            EvidenceList：证据列表
        """
        items = []
        
        for item in collection.items:
            # 1. 从CaseData提取证据关键信息
            key_info = self._extract_key_info(item, case_data)
            
            # 2. 确定支撑的诉求
            claims_supported = self._get_claims_supported(item, requirements)
            
            # 3. 确定附件信息
            attachment = self._get_attachment(item, case_data, requirements)
            
            # 4. 创建EvidenceListItem
            from .data_models import EvidenceListItem
            evidence_list_item = EvidenceListItem(
                name=item.name,
                type=item.type,
                key_info=key_info,
                claims_supported=claims_supported,
                attachment=attachment
            )
            
            items.append(evidence_list_item)
        
        from .data_models import EvidenceList
        return EvidenceList(items=items, case_type=case_data.contract.type)
    
    def _extract_key_info(
        self,
        item: "EvidenceItem",
        case_data: "CaseData"
    ) -> Dict[str, Any]:
        """
        从案情数据提取证据关键信息
        
        核心：只从CaseData提取，不使用任何脱敏标记
        """
        key_info = {}
        
        if item.type.value == "合同类":
            key_info = {
                "出租人": case_data.plaintiff.name,
                "承租人": case_data.defendant.name,
                "标的物": case_data.contract.subject,
                "合同金额": f"{case_data.contract.amount:,.0f}元",
                "签订日期": case_data.contract.signing_date.strftime("%Y年%m月%d日"),
                "租期": f"{case_data.contract.term_months}个月" if case_data.contract.term_months else None
            }
        
        elif item.type.value == "凭证类":
            key_info = {
                "付款方": case_data.plaintiff.name,
                "收款方": case_data.defendant.name,
                "金额": f"{case_data.paid_amount:,.0f}元" if case_data.paid_amount else f"{case_data.contract.amount:,.0f}元",
                "日期": case_data.contract.signing_date.strftime("%Y年%m月%d日")
            }
        
        elif item.type.value == "文书类":
            key_info = {
                "文书类型": item.name,
                "发证机关": "相关机关",
                "日期": case_data.contract.signing_date.strftime("%Y年%m月%d日")
            }
        
        elif item.type.value == "附件类":
            # 附件数据从CaseData.attachments获取
            key_info = self._get_attachment_data(item, case_data)
        
        return key_info
    
    def _get_attachment_data(
        self,
        item: "EvidenceItem",
        case_data: "CaseData"
    ) -> Dict[str, Any]:
        """获取附件数据"""
        if "租赁物" in item.name and "租赁物清单" in case_data.attachments:
            return {"租赁物清单": case_data.attachments["租赁物清单"]}
        elif "还款" in item.name and "还款计划" in case_data.attachments:
            return {"还款计划": case_data.attachments["还款计划"]}
        elif "应收" in item.name and "应收账款清单" in case_data.attachments:
            return {"应收账款清单": case_data.attachments["应收账款清单"]}
        
        return {}
    
    def _get_claims_supported(
        self,
        item: "EvidenceItem",
        requirements: "EvidenceRequirements"
    ) -> List[str]:
        """获取支撑的诉求"""
        for req in requirements.requirements:
            if req.name == item.name:
                return req.claims_supported
        return []
    
    def _get_attachment(
        self,
        item: "EvidenceItem",
        case_data: "CaseData",
        requirements: "EvidenceRequirements"
    ) -> Optional["AttachmentInfo"]:
        """获取附件信息"""
        from .data_models import AttachmentInfo, AttachmentForm
        
        for req in requirements.requirements:
            if req.name == item.name and req.attachment:
                return AttachmentInfo(
                    type=req.attachment.type,
                    source=req.attachment.source,
                    form=req.attachment.form
                )
        return None
    
    def validate_no_deanonymization(self, evidence_list: "EvidenceList") -> List[str]:
        """
        验证证据列表不包含脱敏标记
        
        Returns:
            List[str]: 发现的脱敏标记列表
        """
        issues = []
        placeholder_patterns = ["某某", "XX", "XXX", "某年某月某日", "X月X日"]
        
        for item in evidence_list.items:
            content = json.dumps(item.key_info, ensure_ascii=False)
            for pattern in placeholder_patterns:
                if pattern in content:
                    issues.append(f"证据{item.name}包含脱敏标记: {pattern}")
        
        return issues


# 引用json模块
import json
