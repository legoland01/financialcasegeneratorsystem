"""
EvidenceCollector - F2.4 证据收集器

功能：从判决书提取证据 + 自行编造缺失证据

输入：判决书 + EvidenceRequirements + CaseData
输出：EvidenceCollection（完整证据列表）

核心原则：
- P3 附件规划：附件类证据可能需要自行编造
- RFC-2026-02-002 Q1: 证据编造规则区分生产环境和测试环境
  - 生产环境：不允许编造，缺失证据则跳过
  - 测试环境：从配置文件加载预设数据
"""

from pathlib import Path
from typing import List, Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .data_models import CaseData, ClaimList, EvidenceRequirements, EvidenceCollection, EvidenceItem
    from .llm_client import LLMClient


class EvidenceCollector:
    """
    证据收集器 - F2.4
    
    从判决书提取原告证据，并识别缺失的证据进行自行编造。
    
    RFC-2026-02-002 Q1 证据编造规则：
    - 生产环境：不允许编造，缺失证据则跳过
    - 测试环境：从配置文件加载预设数据
    
    输出：EvidenceCollection（完整证据列表）
    """
    
    def __init__(
        self, 
        llm_client: Optional["LLMClient"] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化证据收集器
        
        Args:
            llm_client: LLM客户端，如果为None则使用正则表达式提取
            config: 配置字典，用于测试环境编造规则
        """
        self.llm_client = llm_client
        self.config = config or {}
    
    def collect(
        self,
        case_data: "CaseData",
        claim_list: "ClaimList",
        requirements: "EvidenceRequirements",
        environment: str = "production"
    ) -> "EvidenceCollection":
        """
        收集证据
        
        Args:
            case_data: 案情基本数据集
            claim_list: 诉求列表
            requirements: 证据需求清单
            environment: 环境类型，"production"或"test"
        Returns:
            EvidenceCollection：完整证据列表
        """
        # 1. 从判决书提取证据（如果提供了判决书路径）
        from_judgment = []
        if case_data.judgment_path:
            from_judgment = self._extract_from_judgment(Path(case_data.judgment_path))
        
        # 2. 对照需求，识别缺失的证据
        missing = self._identify_missing(requirements, from_judgment)
        
        # 3. 根据环境规则处理缺失证据
        if environment == "production":
            # 生产环境：不允许编造，跳过缺失证据
            fabricated = []
        else:
            # 测试环境：从配置文件加载或编造
            fabricated = self._fabricate_missing(missing, requirements, case_data)
        
        # 4. 构建完整证据列表
        all_items = from_judgment + fabricated
        
        from .data_models import EvidenceCollection
        return EvidenceCollection(
            items=all_items,
            from_judgment=[item.name for item in from_judgment],
            fabricated=[item.name for item in fabricated]
        )
    
    def _extract_from_judgment(self, judgment_path: Path) -> List["EvidenceItem"]:
        """从判决书提取证据"""
        text = judgment_path.read_text(encoding="utf-8")
        
        if self.llm_client:
            return self._extract_by_llm(text)
        else:
            return self._extract_by_regex(text)
    
    def _extract_by_llm(self, text: str) -> List["EvidenceItem"]:
        """使用LLM提取证据"""
        if not self.llm_client:
            return []
        prompt = self._build_evidence_extraction_prompt(text)
        response = self.llm_client.complete(prompt)
        return self._parse_evidence_response(response)
    
    def _build_evidence_extraction_prompt(self, text: str) -> str:
        """构建证据提取Prompt"""
        return f"""
# 任务：从判决书中提取原告提交的证据

请从以下判决书文本中提取原告提交的证据列表，以JSON格式输出。

## 提取要求
1. 只提取判决书中认定的证据
2. 标注每份证据法院是否采纳

## 判决书文本
{text}

## 输出格式
```json
[
  {{"name": "融资租赁合同", "type": "合同类", "adopted": true}},
  {{"name": "付款凭证", "type": "凭证类", "adopted": true}},
  {{"name": "公证书", "type": "文书类", "adopted": true}}
]
```
"""
    
    def _parse_evidence_response(self, response: str) -> List["EvidenceItem"]:
        """解析LLM返回的证据列表"""
        import json
        from .data_models import EvidenceType, EvidenceItem
        
        json_match = self._extract_json(response)
        if json_match:
            data = json.loads(json_match)
        else:
            return []
        
        items = []
        for item in data:
            evidence_type = self._parse_evidence_type(item.get("type", ""))
            items.append(EvidenceItem(
                name=item["name"],
                type=evidence_type,
                source="判决书提取",
                fabricated=False
            ))
        
        return items
    
    def _extract_json(self, response: str) -> Optional[str]:
        """从响应中提取JSON"""
        import re
        json_match = re.search(r'```json\s*\n(.+?)\n```', response, re.DOTALL)
        if json_match:
            return json_match.group(1)
        json_match = re.search(r'\[.+\]', response, re.DOTALL)
        if json_match:
            return json_match.group(0)
        return None
    
    def _parse_evidence_type(self, type_str: str) -> "EvidenceType":
        """解析证据类型字符串"""
        from .data_models import EvidenceType
        if "合同" in type_str:
            return EvidenceType.CONTRACT
        elif "凭证" in type_str:
            return EvidenceType.VOUCHER
        elif "文书" in type_str:
            return EvidenceType.DOCUMENT
        elif "附件" in type_str:
            return EvidenceType.ATTACHMENT
        return EvidenceType.CONTRACT
    
    def _extract_by_regex(self, text: str) -> List["EvidenceItem"]:
        """使用正则表达式提取证据（备选方案）"""
        from .data_models import EvidenceType, EvidenceItem
        
        items = []
        
        # 提取合同类证据
        if "融资租赁合同" in text or "借款合同" in text:
            items.append(EvidenceItem(
                name="融资租赁合同",
                type=EvidenceType.CONTRACT,
                source="判决书提取",
                fabricated=False
            ))
        
        # 提取凭证类证据
        if "付款凭证" in text or "银行流水" in text:
            items.append(EvidenceItem(
                name="付款凭证",
                type=EvidenceType.VOUCHER,
                source="判决书提取",
                fabricated=False
            ))
        
        # 提取文书类证据
        if "公证书" in text:
            items.append(EvidenceItem(
                name="公证书",
                type=EvidenceType.DOCUMENT,
                source="判决书提取",
                fabricated=False
            ))
        
        return items
    
    def _identify_missing(
        self,
        requirements: "EvidenceRequirements",
        from_judgment: List["EvidenceItem"]
    ) -> List[str]:
        """识别缺失的证据"""
        judgment_evidence_names = {item.name for item in from_judgment}
        required_evidence_names = {req.name for req in requirements.requirements}
        return list(required_evidence_names - judgment_evidence_names)
    
    def _fabricate_missing(
        self,
        missing: List[str],
        requirements: "EvidenceRequirements",
        case_data: Optional["CaseData"] = None
    ) -> List["EvidenceItem"]:
        """
        自行编造缺失的证据
        
        RFC-2026-02-002 Q1 证据编造规则：
        - 可编造：设备名称、型号、数量等（根据案件类型配置）
        - 不可编造：当事人信息、金额、日期（必须来自案情基本数据集）
        - 编造数据来源优先级：配置文件 > 模板生成 > LLM有限编造
        """
        from .data_models import EvidenceType, EvidenceItem
        
        fabricated = []
        
        for name in missing:
            req = next((r for r in requirements.requirements if r.name == name), None)
            if req and req.type == EvidenceType.ATTACHMENT:
                fabricated.append(EvidenceItem(
                    name=name,
                    type=EvidenceType.ATTACHMENT,
                    source="自行编造",
                    fabricated=True,
                    fabricated_note="根据案件类型配置自动生成"
                ))
        
        return fabricated
