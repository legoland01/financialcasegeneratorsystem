"""
DocumentGenerator - F2.7-F2.10 文档生成器

功能：
- F2.7: 合同生成器（融资租赁合同、补充协议等）
- F2.8: 凭证生成器（收据、银行流水等）
- F2.9: 证明生成器（身份证明、资质证明等）
- F2.10: 其他文书生成器

输入：EvidenceList（包含证据类型和关键信息）
输出：GeneratedEvidence列表

核心原则：
- P1 脱敏标记隔离：全程使用真实信息
- P2 要素驱动：系统负责关键信息，LLM负责内容生成
"""

from typing import List, Optional
from .data_models import (
    EvidenceList,
    EvidenceType,
    GeneratedEvidence,
    CaseData,
    ClaimList
)


class DocumentGenerator:
    """
    文档生成器 - F2.7-F2.10

    根据EvidenceList生成各类证据文档。
    """

    def __init__(self, llm_client: Optional["LLMClient"] = None):
        """
        初始化文档生成器

        Args:
            llm_client: LLM客户端，用于生成文档内容
        """
        self.llm_client = llm_client

    def generate(
        self,
        evidence_list: EvidenceList,
        case_data: CaseData,
        claim_list: ClaimList
    ) -> List[GeneratedEvidence]:
        """
        生成所有证据文档

        Args:
            evidence_list: 证据列表
            case_data: 案情基本数据
            claim_list: 诉求列表
        Returns:
            List[GeneratedEvidence]: 生成的证据文档列表
        """
        generated = []

        for item in evidence_list.items:
            evidence = self._generate_single_evidence(item, case_data, claim_list)
            if evidence:
                generated.append(evidence)

        return generated

    def _generate_single_evidence(
        self,
        item: "EvidenceListItem",
        case_data: CaseData,
        claim_list: ClaimList
    ) -> Optional[GeneratedEvidence]:
        """
        生成单个证据文档

        Args:
            item: 证据列表项
            case_data: 案情基本数据
            claim_list: 诉求列表
        Returns:
            GeneratedEvidence: 生成的证据
        """
        generator_map = {
            EvidenceType.CONTRACT: self._generate_contract,
            EvidenceType.VOUCHER: self._generate_voucher,
            EvidenceType.DOCUMENT: self._generate_document,
            EvidenceType.ATTACHMENT: self._generate_attachment,
        }

        generator = generator_map.get(item.type)
        if not generator:
            return None

        if self.llm_client:
            return generator_by_llm(item, case_data, claim_list, self.llm_client)
        else:
            return generator(item, case_data, claim_list)

    def _generate_contract(
        self,
        item: "EvidenceListItem",
        case_data: CaseData,
        claim_list: ClaimList
    ) -> GeneratedEvidence:
        """生成合同类文档"""
        name = item.name
        content = self._build_contract_content(item, case_data)

        filename = self._generate_filename(name, "合同")
        return GeneratedEvidence(
            filename=filename,
            content=content,
            evidence_type=EvidenceType.CONTRACT
        )

    def _generate_voucher(
        self,
        item: "EvidenceListItem",
        case_data: CaseData,
        claim_list: ClaimList
    ) -> GeneratedEvidence:
        """生成凭证类文档"""
        name = item.name
        content = self._build_voucher_content(item, case_data)

        filename = self._generate_filename(name, "凭证")
        return GeneratedEvidence(
            filename=filename,
            content=content,
            evidence_type=EvidenceType.VOUCHER
        )

    def _generate_document(
        self,
        item: "EvidenceListItem",
        case_data: CaseData,
        claim_list: ClaimList
    ) -> GeneratedEvidence:
        """生成文书类文档"""
        name = item.name
        content = self._build_document_content(item, case_data)

        filename = self._generate_filename(name, "文书")
        return GeneratedEvidence(
            filename=filename,
            content=content,
            evidence_type=EvidenceType.DOCUMENT
        )

    def _generate_attachment(
        self,
        item: "EvidenceListItem",
        case_data: CaseData,
        claim_list: ClaimList
    ) -> GeneratedEvidence:
        """生成附件类文档"""
        name = item.name
        content = self._build_attachment_content(item, case_data)

        filename = self._generate_filename(name, "附件")
        return GeneratedEvidence(
            filename=filename,
            content=content,
            evidence_type=EvidenceType.ATTACHMENT
        )

    def _build_contract_content(
        self,
        item: "EvidenceListItem",
        case_data: CaseData
    ) -> str:
        """构建合同内容"""
        key_info = item.key_info
        contract_type = key_info.get("合同类型", "融资租赁合同")

        lines = []
        lines.append("=" * 60)
        lines.append(contract_type)
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"合同编号：{key_info.get('合同编号', '____')}")
        lines.append("")
        lines.append("甲方（出租人）：")
        lines.append(f"  名称：{case_data.plaintiff.name}")
        lines.append(f"  住所地：{case_data.plaintiff.address}")
        lines.append(f"  法定代表人：{case_data.plaintiff.legal_representative}")
        if case_data.plaintiff.bank_account:
            lines.append(f"  开户银行：{case_data.plaintiff.bank_account}")
        lines.append("")
        lines.append("乙方（承租人）：")
        lines.append(f"  名称：{case_data.defendant.name}")
        lines.append(f"  住所地：{case_data.defendant.address}")
        lines.append(f"  法定代表人：{case_data.defendant.legal_representative}")
        if case_data.defendant.bank_account:
            lines.append(f"  开户银行：{case_data.defendant.bank_account}")
        lines.append("")

        if case_data.guarantor:
            lines.append("丙方（担保人）：")
            lines.append(f"  名称：{case_data.guarantor.name}")
            lines.append(f"  住所地：{case_data.guarantor.address}")
            lines.append(f"  法定代表人：{case_data.guarantor.legal_representative}")
            lines.append("")

        lines.append("鉴于：")
        lines.append(f"甲方系依法设立并有效存续的金融机构，具有开展融资租赁业务的资质。")
        lines.append(f"乙方系依法设立并有效存续的企业法人，具有良好的商业信誉。")
        lines.append("")
        lines.append("双方经友好协商，就融资租赁事宜达成如下协议：")
        lines.append("")
        lines.append("第一条 租赁物")
        lines.append(f"  租赁物名称：{case_data.contract.subject}")
        lines.append(f"  租赁物价值：人民币{case_data.contract.amount:,.2f}元")
        lines.append("")
        lines.append("第二条 租赁期限")
        if case_data.contract.term_months:
            lines.append(f"  租赁期限为{case_data.contract.term_months}个月")
        lines.append("")
        lines.append("第三条 租金及支付方式")
        lines.append(f"  租金总额：人民币{case_data.contract.amount:,.2f}元")
        lines.append(f"  租金支付方式：按月等额本息还款")
        if case_data.contract.performance_date:
            lines.append(f"  起租日期：{case_data.contract.performance_date.strftime('%Y年%m月%d日')}")
        lines.append("")
        lines.append("第四条 担保方式")
        lines.append("  丙方自愿为乙方在本合同项下的全部债务提供连带责任保证担保。")
        lines.append("")
        lines.append("第五条 违约责任")
        lines.append("  乙方未按约定支付租金的，甲方有权要求乙方支付逾期利息及违约金。")
        lines.append("")
        lines.append("第六条 争议解决")
        lines.append("  因本合同产生的争议，双方应协商解决；协商不成的，向甲方住所地人民法院提起诉讼。")
        lines.append("")
        lines.append("第七条 其他约定")
        lines.append("  本合同一式叁份，甲乙丙三方各执壹份，具有同等法律效力。")
        lines.append("")
        lines.append("甲方（盖章）：                    乙方（盖章）：")
        lines.append("")
        lines.append(f"法定代表人：                      法定代表人：")
        lines.append("")
        lines.append(f"日期：{case_data.contract.signing_date.strftime('%Y年%m月%d日')}          日期：{case_data.contract.signing_date.strftime('%Y年%m月%d日')}")

        return "\n".join(lines)

    def _build_voucher_content(
        self,
        item: "EvidenceListItem",
        case_data: CaseData
    ) -> str:
        """构建凭证内容"""
        key_info = item.key_info
        voucher_type = key_info.get("凭证类型", "收据")

        lines = []
        lines.append("=" * 50)
        lines.append(voucher_type)
        lines.append("=" * 50)
        lines.append("")

        if voucher_type == "收据":
            lines.append(f"今收到：{case_data.defendant.name}")
            lines.append(f"交来：租金")
            lines.append(f"金额：人民币{key_info.get('金额', 0):,.2f}元")
            lines.append(f"大写：{self._number_to_chinese(key_info.get('金额', 0))}")
            lines.append("")
            lines.append(f"收款单位（盖章）：{case_data.plaintiff.name}")
            lines.append(f"收款日期：{key_info.get('日期', case_data.contract.signing_date).strftime('%Y年%m月%d日')}")
            lines.append(f"收款人：财务部")
        elif voucher_type == "银行流水":
            lines.append(f"账户名称：{case_data.plaintiff.name}")
            lines.append(f"银行账号：{case_data.plaintiff.bank_account or '____'}")
            lines.append("")
            lines.append("交易明细：")
            lines.append("-" * 50)
            lines.append(f"日期          借方              贷方              余额")
            lines.append("-" * 50)
            if key_info.get("交易记录"):
                for record in key_info.get("交易记录", []):
                    lines.append(f"{record.get('日期', '____')}    {record.get('借方', ''):<16} {record.get('贷方', ''):<16} {record.get('余额', '')}")
            else:
                lines.append(f"{key_info.get('日期', case_data.contract.signing_date).strftime('%Y-%m-%d')}    {case_data.contract.amount:,.2f}              0.00              {case_data.contract.amount:,.2f}")
            lines.append("-" * 50)

        return "\n".join(lines)

    def _build_document_content(
        self,
        item: "EvidenceListItem",
        case_data: CaseData
    ) -> str:
        """构建文书内容"""
        key_info = item.key_info
        doc_type = key_info.get("文书类型", "情况说明")

        lines = []
        lines.append("=" * 50)
        lines.append(doc_type)
        lines.append("=" * 50)
        lines.append("")

        lines.append(f"致：{key_info.get('收文单位', '相关方')}")
        lines.append("")
        lines.append(f"事由：{key_info.get('事由', '关于债务催收的情况说明')}")
        lines.append("")
        lines.append("内容：")
        lines.append(key_info.get("内容", f"{case_data.defendant.name}因未能按期履行还款义务，截至目前尚欠{case_data.plaintiff.name}款项人民币{case_data.remaining_amount or case_data.contract.amount:,.2f}元。请贵司尽快安排还款，以免产生不必要的法律纠纷。"))
        lines.append("")
        lines.append(f"特此说明。")
        lines.append("")
        lines.append(f"{case_data.plaintiff.name}")
        lines.append(f"日期：{key_info.get('日期', case_data.contract.signing_date).strftime('%Y年%m月%d日')}")

        return "\n".join(lines)

    def _build_attachment_content(
        self,
        item: "EvidenceListItem",
        case_data: CaseData
    ) -> str:
        """构建附件内容"""
        key_info = item.key_info
        attachment_type = key_info.get("附件类型", "清单")

        lines = []
        lines.append("=" * 50)
        lines.append(attachment_type)
        lines.append("=" * 50)
        lines.append("")

        if attachment_type == "租赁物清单":
            lines.append(f"项目编号：{key_info.get('项目编号', '____')}")
            lines.append("")
            lines.append("序号    名称              规格型号      数量    单价        金额")
            lines.append("-" * 70)
            if key_info.get("物品列表"):
                total = 0
                for i, item_data in enumerate(key_info.get("物品列表", []), 1):
                    lines.append(f"{i:<6}  {item_data.get('名称', ''):<16} {item_data.get('规格', ''):<12} {item_data.get('数量', 1):<6} {item_data.get('单价', 0):<12,.2f} {item_data.get('金额', 0):<12,.2f}")
                    total += item_data.get('金额', 0)
                lines.append("-" * 70)
                lines.append(f"{'合计':<68} {total:,.2f}")
            else:
                lines.append(f"1    {case_data.contract.subject:<16} 标准        1       {case_data.contract.amount:<12,.2f} {case_data.contract.amount:<12,.2f}")
            lines.append("")
            lines.append(f"编制日期：{key_info.get('日期', case_data.contract.signing_date).strftime('%Y年%m月%d日')}")

        elif attachment_type == "还款计划":
            lines.append(f"借款人：{case_data.defendant.name}")
            lines.append(f"贷款金额：人民币{case_data.contract.amount:,.2f}元")
            lines.append(f"贷款日期：{case_data.contract.signing_date.strftime('%Y年%m月%d日')}")
            lines.append("")
            lines.append("期数    日期          应还本金      应还利息      应还总额      剩余本金")
            lines.append("-" * 80)
            if key_info.get("还款计划"):
                for plan in key_info.get("还款计划", []):
                    lines.append(f"{plan.get('期数', 0):<6} {plan.get('日期', ''):<10} {plan.get('应还本金', 0):<12,.2f} {plan.get('应还利息', 0):<12,.2f} {plan.get('应还总额', 0):<12,.2f} {plan.get('剩余本金', 0):<12,.2f}")
            lines.append("-" * 80)

        return "\n".join(lines)

    def _generate_filename(self, name: str, category: str) -> str:
        """生成文件名"""
        import re
        safe_name = re.sub(r'[\\/*?："<>|]', '', name)
        safe_name = safe_name[:20]
        return f"{category}_{safe_name}.txt"

    def _number_to_chinese(self, number: float) -> str:
        """数字转中文大写"""
        digits = '零壹贰叁肆伍陆柒捌玖'
        units = ['', '拾', '佰', '仟', '万', '拾', '佰', '仟', '亿']
        int_part = int(number)
        result = []
        int_str = str(int_part)
        length = len(int_str)

        for i, digit in enumerate(int_str):
            d = digits[int(digit)]
            u = units[length - i - 1]
            if d != '零':
                result.append(d + u)
            else:
                if result and result[-1] != '零':
                    result.append('零')

        result.append('元整')
        return ''.join(result)


def generator_by_llm(
    item: "EvidenceListItem",
    case_data: CaseData,
    claim_list: ClaimList,
    llm_client: "LLMClient"
) -> GeneratedEvidence:
    """使用LLM生成文档内容"""
    prompt = _build_llm_generation_prompt(item, case_data, claim_list)
    response = llm_client.complete(prompt)
    return GeneratedEvidence(
        filename=f"{item.type.value}_{item.name}.txt",
        content=response,
        evidence_type=item.type
    )


def _build_llm_generation_prompt(
    item: "EvidenceListItem",
    case_data: CaseData,
    claim_list: ClaimList
) -> str:
    """构建LLM生成Prompt"""
    context = item.to_prompt_context()

    return f"""
# 任务：根据证据信息生成正式法律文书

## 证据信息
{context}

## 案情背景
- 原告：{case_data.plaintiff.name}
- 被告：{case_data.defendant.name}
- 合同金额：人民币{case_data.contract.amount:,.2f}元
- 合同签订日期：{case_data.contract.signing_date.strftime('%Y年%m月%d日')}

## 生成要求
1. 使用正式的法律文书格式
2. 内容必须完整、准确
3. 符合中国法院的证据标准
4. 直接输出文书内容，不要包含任何解释或markdown标记

请生成完整的证据文书内容。
"""
