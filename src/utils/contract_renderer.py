from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PartyInfo:
    """当事人信息"""
    role: str
    name: str
    credit_code: str
    representative: str
    address: str
    phone: Optional[str] = None


@dataclass
class SignatureInfo:
    """签署信息"""
    party: str
    name: str
    date: str


class ContractRenderer:
    """合同渲染器 - 渲染合同格式到PDF元素"""

    def __init__(self):
        """初始化合同渲染器"""
        pass

    def render(
        self,
        title: str,
        contract_no: str,
        parties: List[PartyInfo],
        content: str,
        signatures: List[SignatureInfo]
    ) -> Dict[str, Any]:
        """
        渲染合同格式

        Args:
            title: 合同标题
            contract_no: 合同编号
            parties: 当事人列表
            content: 合同正文
            signatures: 签署信息
        Returns:
            渲染后的合同数据
        """
        result = {
            "title": title,
            "contract_no": contract_no,
            "parties": self._render_parties(parties),
            "content": self._render_content(content),
            "signatures": self._render_signatures(signatures)
        }

        return result

    def _render_parties(self, parties: List[PartyInfo]) -> List[Dict[str, str]]:
        """渲染当事人信息"""
        rendered = []
        for party in parties:
            party_text = {
                "role": party.role,
                "company_name": party.name,
                "credit_code": party.credit_code,
                "representative": party.representative,
                "address": party.address,
                "phone": party.phone or ""
            }
            rendered.append(party_text)
        return rendered

    def _render_content(self, content: str) -> List[str]:
        """渲染合同正文"""
        paragraphs = content.split('\n')
        rendered = []
        for para in paragraphs:
            if para.strip():
                rendered.append(para.strip())
        return rendered

    def _render_signatures(self, signatures: List[SignatureInfo]) -> List[Dict[str, str]]:
        """渲染签署信息"""
        rendered = []
        for sig in signatures:
            rendered.append({
                "party": sig.party,
                "name": sig.name,
                "date": sig.date
            })
        return rendered

    def format_title(self, title: str, font_size: int = 18) -> Dict[str, Any]:
        """格式化标题"""
        return {
            "type": "title",
            "text": title,
            "font_size": font_size,
            "font_name": "SimHei",
            "alignment": "center"
        }

    def format_contract_no(self, contract_no: str) -> Dict[str, Any]:
        """格式化合同编号"""
        return {
            "type": "contract_no",
            "text": f"合同编号：{contract_no}",
            "font_size": 12,
            "font_name": "SimSun",
            "alignment": "left"
        }

    def format_party_header(self, role: str) -> Dict[str, Any]:
        """格式化当事人标题"""
        return {
            "type": "party_header",
            "text": f"【{role}】",
            "font_size": 12,
            "font_name": "SimHei",
            "alignment": "left"
        }

    def format_party_info(self, label: str, value: str) -> Dict[str, Any]:
        """格式化当事人信息"""
        return {
            "type": "party_info",
            "text": f"{label}：{value}",
            "font_size": 12,
            "font_name": "SimSun",
            "alignment": "left"
        }

    def format_paragraph(
        self,
        text: str,
        alignment: str = "justify",
        font_size: int = 12
    ) -> Dict[str, Any]:
        """格式化段落"""
        return {
            "type": "paragraph",
            "text": text,
            "font_size": font_size,
            "font_name": "SimSun",
            "alignment": alignment
        }

    def format_signature(self, signature: Dict[str, str]) -> Dict[str, Any]:
        """格式化签署信息"""
        text = f"{signature['party']}（盖章）：{signature['name']}\n日期：{signature['date']}"
        return {
            "type": "signature",
            "text": text,
            "font_size": 12,
            "font_name": "SimSun",
            "alignment": "left"
        }
