"""
CaseAnalyzer - F2.1 案情分析器

功能：从判决书提取案情基本数据集（CaseData）

输入：判决书PDF/文本
输出：CaseData（包含当事人、合同、履行、违约等信息）

核心原则：
- P1 脱敏标记隔离：全程使用真实信息，不包含任何脱敏标记
- P2 要素驱动：系统负责提取要素，内容生成由LLM完成
"""

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import json


class JudgmentParser(ABC):
    """判决书解析器 - 抽象基类"""
    
    @abstractmethod
    def parse(self, judgment_path: Path) -> str:
        """解析判决书文件，返回纯文本"""
        pass


class PDFJudgmentParser(JudgmentParser):
    """PDF判决书解析器"""
    
    def __init__(self, pdf_engine: str = "pdfplumber"):
        self.pdf_engine = pdf_engine
    
    def parse(self, judgment_path: Path) -> str:
        """解析PDF判决书"""
        if self.pdf_engine == "pdfplumber":
            return self._parse_with_pdfplumber(judgment_path)
        elif self.pdf_engine == "pypdf":
            return self._parse_with_pypdf(judgment_path)
        else:
            raise ValueError(f"不支持的PDF引擎：{self.pdf_engine}")
    
    def _parse_with_pdfplumber(self, judgment_path: Path) -> str:
        """使用pdfplumber解析PDF"""
        import pdfplumber
        text_parts = []
        with pdfplumber.open(judgment_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        return "\n".join(text_parts)
    
    def _parse_with_pypdf(self, judgment_path: Path) -> str:
        """使用pypdf解析PDF"""
        from pypdf import PdfReader
        reader = PdfReader(judgment_path)
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return "\n".join(text_parts)


class TextJudgmentParser(JudgmentParser):
    """纯文本判决书解析器"""
    
    def parse(self, judgment_path: Path) -> str:
        """读取纯文本判决书"""
        return judgment_path.read_text(encoding="utf-8")


class CaseAnalyzer:
    """
    案情分析器 - F2.1
    
    从判决书提取案情基本数据集。
    支持LLM和正则表达式两种提取方式。
    
    输出：CaseData（案情基本数据集）
    """
    
    def __init__(
        self,
        llm_client: Optional["LLMClient"] = None,
        parser: Optional[JudgmentParser] = None
    ):
        """
        初始化案情分析器
        
        Args:
            llm_client: LLM客户端，如果为None则使用正则表达式提取
            parser: 判决书解析器，如果为None则自动检测
        """
        self.llm_client = llm_client
        self.parser = parser
    
    def analyze(self, judgment_path: Path) -> "CaseData":
        """
        分析判决书，生成案情基本数据集
        
        Args:
            judgment_path: 判决书文件路径
        Returns:
            CaseData：案情基本数据集
        """
        # 1. 确定解析器
        if self.parser is None:
            self.parser = self._detect_parser(judgment_path)
        
        # 2. 解析判决书
        judgment_text = self.parser.parse(judgment_path)
        
        # 3. 提取当事人信息
        parties = self._extract_parties(judgment_text)
        
        # 4. 分析合同信息
        contract = self._analyze_contract(judgment_text)
        
        # 5. 分析履行情况
        performance = self._analyze_performance(judgment_text)
        
        # 6. 分析违约情况
        breach = self._analyze_breach(judgment_text)
        
        # 7. 构建案情数据
        case_data = CaseData(
            plaintiff=parties["plaintiff"],
            defendant=parties["defendant"],
            guarantor=parties.get("guarantor"),
            contract=contract,
            paid_amount=performance.get("paid_amount"),
            remaining_amount=performance.get("remaining_amount"),
            breach=breach,
            judgment_path=str(judgment_path),
            extracted_at=datetime.now()
        )
        
        return case_data
    
    def _detect_parser(self, judgment_path: Path) -> JudgmentParser:
        """自动检测判决书格式，选择合适的解析器"""
        suffix = judgment_path.suffix.lower()
        if suffix == ".pdf":
            return PDFJudgmentParser()
        else:
            return TextJudgmentParser()
    
    def _extract_parties(self, text: str) -> Dict[str, Any]:
        """提取当事人信息"""
        if self.llm_client:
            return self._extract_parties_by_llm(text)
        else:
            return self._extract_parties_by_regex(text)
    
    def _extract_parties_by_llm(self, text: str) -> Dict[str, Any]:
        """使用LLM提取当事人信息"""
        prompt = self._build_party_extraction_prompt(text)
        response = self.llm_client.complete(prompt)
        return self._parse_party_response(response)
    
    def _build_party_extraction_prompt(self, text: str) -> str:
        """构建当事人提取Prompt"""
        return f"""
# 任务：从判决书中提取当事人信息

请从以下判决书文本中提取原告、被告、担保人的详细信息，以JSON格式输出。

## 提取要求
1. 只提取判决书中明确列出的信息
2. 如果某项信息判决书没有提及，标记为null
3. 公司名称必须是全称
4. 统一社会信用代码必须是18位代码

## 判决书文本
{text}

## 输出格式
```json
{{
  "plaintiff": {{
    "name": "公司全称",
    "credit_code": "统一社会信用代码",
    "address": "注册地址",
    "legal_representative": "法定代表人姓名",
    "bank_account": "银行账户（可选）"
  }},
  "defendant": {{
    "name": "公司全称",
    "credit_code": "统一社会信用代码",
    "address": "注册地址",
    "legal_representative": "法定代表人姓名",
    "bank_account": "银行账户（可选）"
  }},
  "guarantor": null
}}
```
"""
    
    def _parse_party_response(self, response: str) -> Dict[str, Any]:
        """解析LLM返回的当事人信息"""
        json_match = re.search(r'```json\s*\n(.+?)\n```', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
        else:
            json_match = re.search(r'\{.+\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
            else:
                raise ValueError("无法解析当事人信息")
        
        from .data_models import Party
        result = {}
        
        if data.get("plaintiff"):
            result["plaintiff"] = Party(**data["plaintiff"])
        else:
            result["plaintiff"] = Party(name="", credit_code="", address="", legal_representative="")
        
        if data.get("defendant"):
            result["defendant"] = Party(**data["defendant"])
        else:
            result["defendant"] = Party(name="", credit_code="", address="", legal_representative="")
        
        if data.get("guarantor"):
            result["guarantor"] = Party(**data["guarantor"])
        
        return result
    
    def _extract_parties_by_regex(self, text: str) -> Dict[str, Any]:
        """使用正则表达式提取当事人信息（备选方案）"""
        from .data_models import Party
        
        # 提取原告
        plaintiff_match = re.search(
            r'原告[：:](.+?)，(.+?)，法定代表人(.+?)[。\n]',
            text
        )
        if plaintiff_match:
            plaintiff = Party(
                name=plaintiff_match.group(1).strip(),
                credit_code="",
                address=plaintiff_match.group(2).strip(),
                legal_representative=plaintiff_match.group(3).strip()
            )
        else:
            plaintiff = Party(name="", credit_code="", address="", legal_representative="")
        
        # 提取被告
        defendant_match = re.search(
            r'被告[：:](.+?)，(.+?)，法定代表人(.+?)[。\n]',
            text
        )
        if defendant_match:
            defendant = Party(
                name=defendant_match.group(1).strip(),
                credit_code="",
                address=defendant_match.group(2).strip(),
                legal_representative=defendant_match.group(3).strip()
            )
        else:
            defendant = Party(name="", credit_code="", address="", legal_representative="")
        
        return {"plaintiff": plaintiff, "defendant": defendant}
    
    def _analyze_contract(self, text: str) -> "ContractInfo":
        """分析合同信息"""
        # 提取合同类型
        contract_type = self._extract_contract_type(text)
        
        # 提取合同金额
        amount = self._extract_amount(text)
        
        # 提取签订日期
        signing_date = self._extract_date(text)
        
        # 提取租期
        term = self._extract_term(text)
        
        # 提取标的物
        subject = self._extract_subject(text)
        
        from .data_models import ContractInfo, CaseType
        return ContractInfo(
            type=contract_type or CaseType.FINANCING_LEASE,
            subject=subject or "设备/货物",
            amount=amount or 0.0,
            signing_date=signing_date or datetime.now(),
            term_months=term
        )
    
    def _extract_contract_type(self, text: str) -> "CaseType":
        """提取合同类型"""
        if "融资租赁" in text:
            return CaseType.FINANCING_LEASE
        elif "借款" in text:
            return CaseType.LOAN
        elif "保理" in text:
            return CaseType.FACTORING
        elif "担保" in text:
            return CaseType.GUARANTEE
        return CaseType.FINANCING_LEASE
    
    def _extract_amount(self, text: str) -> float:
        """提取金额"""
        patterns = [
            r'人民币([\d,]+)\s*元',
            r'([\d,]+)\s*元',
            r'金额[为：:]*([\d,]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                amount_str = match.group(1).replace(',', '')
                return float(amount_str)
        return 0.0
    
    def _extract_date(self, text: str) -> Optional[datetime]:
        """提取日期"""
        pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
        match = re.search(pattern, text)
        if match:
            return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        return None
    
    def _extract_term(self, text: str) -> Optional[int]:
        """提取租期"""
        patterns = [
            r'(\d+)\s*个月',
            r'期限[为：:]*(\d+)\s*个月',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return None
    
    def _extract_subject(self, text: str) -> str:
        """提取标的物描述"""
        patterns = [
            r'租赁物[为：:](.+?)[。\n]',
            r'标的物[为：:](.+?)[。\n]',
            r'借款用于(.+?)[。\n]',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return ""
    
    def _analyze_performance(self, text: str) -> Dict[str, Any]:
        """分析履行情况"""
        result = {}
        
        # 提取已付金额
        paid_patterns = [
            r'已付[金额租金]*([\d,]+)\s*元',
            r'已支付([\d,]+)\s*元',
            r'支付了([\d,]+)\s*元',
        ]
        for pattern in paid_patterns:
            match = re.search(pattern, text)
            if match:
                result["paid_amount"] = float(match.group(1).replace(',', ''))
                break
        
        # 提取剩余欠款
        remaining_patterns = [
            r'尚欠[金额租金]*([\d,]+)\s*元',
            r'剩余([\d,]+)\s*元',
            r'欠款([\d,]+)\s*元',
        ]
        for pattern in remaining_patterns:
            match = re.search(pattern, text)
            if match:
                result["remaining_amount"] = float(match.group(1).replace(',', ''))
                break
        
        return result
    
    def _analyze_breach(self, text: str) -> Optional["BreachInfo"]:
        """分析违约情况"""
        if "未按约定" not in text and "违约" not in text:
            return None
        
        breach_date = None
        breach_amount = None
        breach_description = None
        
        # 提取违约日期
        date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日[起]?', text)
        if date_match:
            breach_date = datetime(int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3)))
        
        # 提取违约金额
        amount_match = re.search(r'欠款[人民币]*([\d,]+)\s*元', text)
        if amount_match:
            breach_amount = float(amount_match.group(1).replace(',', ''))
        
        # 提取违约描述
        desc_match = re.search(r'未按约定(.+?)[。\n]', text)
        if desc_match:
            breach_description = desc_match.group(1).strip()
        
        from .data_models import BreachInfo
        return BreachInfo(
            breach_date=breach_date,
            breach_amount=breach_amount,
            breach_description=breach_description
        )
