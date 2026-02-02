"""
ClaimExtractor - F2.2 诉求提取器

功能：从判决书提取诉求列表（ClaimList）

输入：判决书文本
输出：ClaimList（包含本金、利息、违约金等诉求）

核心原则：
- P1 脱敏标记隔离：全程使用真实信息
- P2 要素驱动：系统负责提取要素
"""

import re
import json
from pathlib import Path
from typing import Optional


class ClaimExtractor:
    """
    诉求提取器 - F2.2
    
    从判决书中提取原告的诉讼请求。
    支持LLM和正则表达式两种提取方式。
    
    输出：ClaimList（诉求列表）
    """
    
    def __init__(self, llm_client: Optional["LLMClient"] = None):
        """
        初始化诉求提取器
        
        Args:
            llm_client: LLM客户端，如果为None则使用正则表达式提取
        """
        self.llm_client = llm_client
    
    def extract(self, judgment_path: Path) -> "ClaimList":
        """
        从判决书中提取诉求
        
        Args:
            judgment_path: 判决书文件路径
        Returns:
            ClaimList：诉求列表
        """
        text = judgment_path.read_text(encoding="utf-8")
        
        if self.llm_client:
            return self._extract_by_llm(text)
        else:
            return self._extract_by_regex(text)
    
    def extract_from_text(self, text: str) -> "ClaimList":
        """
        从文本中提取诉求
        
        Args:
            text: 判决书文本
        Returns:
            ClaimList：诉求列表
        """
        if self.llm_client:
            return self._extract_by_llm(text)
        else:
            return self._extract_by_regex(text)
    
    def _extract_by_llm(self, text: str) -> "ClaimList":
        """使用LLM提取诉求"""
        prompt = self._build_claim_extraction_prompt(text)
        response = self.llm_client.complete(prompt)
        return self._parse_claim_response(response)
    
    def _build_claim_extraction_prompt(self, text: str) -> str:
        """构建诉求提取Prompt"""
        return f"""
# 任务：从判决书中提取原告诉求

请从以下判决书文本中提取原告的诉讼请求，以JSON格式输出。

## 提取要求
1. 只提取判决书中原告诉称部分的诉讼请求
2. 金额使用数字格式（单位：元）
3. 如果某项诉求判决书没有提及，标记为null

## 判决书文本
{text}

## 输出格式
```json
{{
  "claims": [
    {{
      "type": "本金",
      "amount": 150000000,
      "description": "请求判令被告支付欠款本金"
    }},
    {{
      "type": "利息",
      "amount": 5000000,
      "description": "请求判令被告支付欠款利息"
    }},
    {{
      "type": "违约金",
      "amount": 2000000,
      "description": "请求判令被告支付违约金"
    }}
  ],
  "litigation_cost": 50000,
  "attorney_fee": null
}}
```
"""
    
    def _parse_claim_response(self, response: str) -> "ClaimList":
        """解析LLM返回的诉求"""
        from .data_models import Claim, ClaimList
        
        json_match = re.search(r'```json\s*\n(.+?)\n```', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
        else:
            json_match = re.search(r'\{.+\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
            else:
                raise ValueError("无法解析诉求")
        
        claims = []
        for c in data.get("claims", []):
            claims.append(Claim(
                type=c.get("type", ""),
                amount=c.get("amount", 0),
                description=c.get("description")
            ))
        
        return ClaimList(
            claims=claims,
            litigation_cost=data.get("litigation_cost"),
            attorney_fee=data.get("attorney_fee")
        )
    
    def _extract_by_regex(self, text: str) -> "ClaimList":
        """使用正则表达式提取诉求（备选方案）"""
        from .data_models import Claim, ClaimList
        
        claims = []
        
        # 提取本金诉求
        principal_match = re.search(
            r'请求判令被告支付欠款本金[人民币]*([\d,]+)\s*元',
            text
        )
        if principal_match:
            claims.append(Claim(
                type="本金",
                amount=float(principal_match.group(1).replace(',', '')),
                description="请求判令被告支付欠款本金"
            ))
        
        # 提取利息诉求
        interest_match = re.search(
            r'请求判令被告支付欠款利息[人民币]*([\d,]+)\s*元',
            text
        )
        if interest_match:
            claims.append(Claim(
                type="利息",
                amount=float(interest_match.group(1).replace(',', '')),
                description="请求判令被告支付欠款利息"
            ))
        
        # 提取违约金诉求
        penalty_match = re.search(
            r'请求判令被告支付违约金[人民币]*([\d,]+)\s*元',
            text
        )
        if penalty_match:
            claims.append(Claim(
                type="违约金",
                amount=float(penalty_match.group(1).replace(',', '')),
                description="请求判令被告支付违约金"
            ))
        
        # 提取诉讼费用
        litigation_cost = None
        cost_match = re.search(
            r'诉讼费用[人民币]*([\d,]+)\s*元',
            text
        )
        if cost_match:
            litigation_cost = float(cost_match.group(1).replace(',', ''))
        
        return ClaimList(claims=claims, litigation_cost=litigation_cost)
