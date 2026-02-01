"""
LitigationComplaintGenerator - F2.6 起诉状生成器

功能：生成符合法院标准的民事起诉状

输入：CaseData + ClaimList + EvidenceList
输出：民事起诉状文本
"""

from typing import List


class LitigationComplaintGenerator:
    """
    起诉状生成器 - F2.6
    
    生成符合法院标准的民事起诉状。
    """
    
    def generate(
        self,
        case_data: "CaseData",
        claim_list: "ClaimList",
        evidence_list: "EvidenceList"
    ) -> str:
        """
        生成民事起诉状
        
        Args:
            case_data: 案情基本数据集
            claim_list: 诉求列表
            evidence_list: 证据列表
        Returns:
            str: 民事起诉状文本
        """
        sections = []
        
        sections.append(self._generate_header())
        sections.append(self._generate_parties(case_data))
        sections.append(self._generate_claims(claim_list))
        sections.append(self._generate_facts(case_data))
        sections.append(self._generate_evidence_list(evidence_list))
        sections.append(self._generate_footer(case_data))
        
        return "\n".join(sections)
    
    def _generate_header(self) -> str:
        """生成标题"""
        return "民事起诉状"
    
    def _generate_parties(self, case_data: "CaseData") -> str:
        """生成当事人信息"""
        lines = []
        lines.append("原告：")
        lines.append(f"名称：{case_data.plaintiff.name}")
        lines.append(f"住所地：{case_data.plaintiff.address}")
        lines.append(f"法定代表人：{case_data.plaintiff.legal_representative}")
        if case_data.plaintiff.bank_account:
            lines.append(f"银行账户：{case_data.plaintiff.bank_account}")
        lines.append("")
        
        lines.append("被告：")
        lines.append(f"名称：{case_data.defendant.name}")
        lines.append(f"住所地：{case_data.defendant.address}")
        lines.append(f"法定代表人：{case_data.defendant.legal_representative}")
        if case_data.defendant.bank_account:
            lines.append(f"银行账户：{case_data.defendant.bank_account}")
        lines.append("")
        
        if case_data.guarantor:
            lines.append("担保人：")
            lines.append(f"名称：{case_data.guarantor.name}")
            lines.append(f"住所地：{case_data.guarantor.address}")
            lines.append(f"法定代表人：{case_data.guarantor.legal_representative}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_claims(self, claim_list: "ClaimList") -> str:
        """生成诉讼请求"""
        lines = []
        lines.append("诉讼请求：")
        lines.append("")
        
        for i, claim in enumerate(claim_list.claims, 1):
            if claim.type == "本金":
                lines.append(f"{i}. 请求判令被告向原告支付欠款本金人民币{claim.amount:,.0f}元")
            elif claim.type == "利息":
                lines.append(f"{i}. 请求判令被告向原告支付欠款利息人民币{claim.amount:,.0f}元")
            elif claim.type == "违约金":
                lines.append(f"{i}. 请求判令被告向原告支付违约金人民币{claim.amount:,.0f}元")
            else:
                lines.append(f"{i}. {claim.description or claim.type}")
        
        lines.append("")
        
        if claim_list.litigation_cost:
            lines.append(f"{len(claim_list.claims) + 1}. 请求判令被告承担本案诉讼费用人民币{claim_list.litigation_cost:,.0f}元")
        
        return "\n".join(lines)
    
    def _generate_facts(self, case_data: "CaseData") -> str:
        """生成事实与理由"""
        lines = []
        lines.append("事实与理由：")
        lines.append("")
        
        lines.append("一、合同签订情况")
        lines.append(f"原告与被告于{case_data.contract.signing_date.strftime('%Y年%m月%d日')}签订《{case_data.contract.type.value}》。")
        lines.append(f"合同约定：被告向原告租赁{case_data.contract.subject}，合同金额为人民币{case_data.contract.amount:,.0f}元。")
        if case_data.contract.term_months:
            lines.append(f"租赁期限为{case_data.contract.term_months}个月。")
        lines.append("")
        
        if case_data.paid_amount is not None:
            lines.append("二、合同履行情况")
            lines.append(f"合同签订后，被告已支付租金人民币{case_data.paid_amount:,.0f}元。")
            if case_data.remaining_amount is not None:
                lines.append(f"被告尚欠租金人民币{case_data.remaining_amount:,.0f}元。")
            lines.append("")
        
        if case_data.breach:
            lines.append("三、被告违约事实")
            if case_data.breach.breach_date:
                lines.append(f"被告于{case_data.breach.breach_date.strftime('%Y年%m月%d日')}起未按合同约定履行付款义务。")
            if case_data.breach.breach_amount:
                lines.append(f"被告尚欠款项人民币{case_data.breach.breach_amount:,.0f}元。")
            if case_data.breach.breach_description:
                lines.append(case_data.breach.breach_description)
            lines.append("")
        
        lines.append("综上所述，被告的行为已构成违约，严重损害了原告的合法权益。为维护原告的合法权益，原告特向贵院提起诉讼，恳请贵院依法支持原告的全部诉讼请求。。")
        
        return "\n".join(lines)
    
    def _generate_evidence_list(self, evidence_list: "EvidenceList") -> str:
        """生成证据清单"""
        lines = []
        lines.append("证据清单：")
        lines.append("")
        
        for i, item in enumerate(evidence_list.items, 1):
            lines.append(f"{i}. {item.name}（{item.type.value}）")
        
        return "\n".join(lines)
    
    def _generate_footer(self, case_data: "CaseData") -> str:
        """生成落款"""
        lines = []
        lines.append("")
        lines.append("此致")
        lines.append("上海市浦东新区人民法院")
        lines.append("")
        lines.append("起诉人（盖章）：")
        lines.append("")
        date_str = case_data.extracted_at.strftime('%Y年%m月%d日') if case_data.extracted_at else '____年__月__日'
        lines.append(f"日期：{date_str}")
        return "\n".join(lines)
