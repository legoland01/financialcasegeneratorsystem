"""
边界条件提取器 - 从判决书文本直接提取关键数据

该模块实现了从判决书文本中提取边界条件的功能，支持两种提取方式：
1. LLM结构化提取（推荐）
2. 正则表达式提取（备选）

Author: OpenCode AI
Date: 2026-01-27
"""

import re
import json
from typing import Dict, Optional, Any
from pathlib import Path
from datetime import datetime


class BoundaryConditionExtractor:
    """边界条件提取器 - 从判决书文本直接提取关键数据"""
    
    def __init__(self, llm_client=None):
        """
        初始化边界条件提取器
        
        Args:
            llm_client: LLM客户端实例，如果为None则使用正则表达式提取
        """
        self.llm_client = llm_client
        
        # 正则表达式提取模式
        self.patterns = {
            'contract_amount': r'([\d,]+)\s*元',
            'interest_rate': r'(\d+(?:\.\d+)?)\s*%',
            'signing_date': r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            'equipment_count': r'(\d+)\s*(?:套|台|件)',
        }
    
    def extract(self, judgment_text: str) -> Dict[str, Any]:
        """
        从判决书文本提取边界条件
        
        Args:
            judgment_text: 判决书原始文本
        Returns:
            边界条件字典
        """
        if self.llm_client:
            # 使用LLM结构化提取（推荐）
            return self._extract_by_llm(judgment_text)
        else:
            # 使用正则表达式提取（备选）
            return self._extract_by_regex(judgment_text)
    
    def _extract_by_llm(self, judgment_text: str) -> Dict[str, Any]:
        """
        使用LLM结构化提取边界条件
        """
        prompt = self._build_extraction_prompt(judgment_text)
        response = self.llm_client.complete(prompt)
        
        # 解析JSON响应
        try:
            # 尝试直接解析JSON
            boundary_conditions = json.loads(response)
        except json.JSONDecodeError:
            # 从文本中提取JSON
            boundary_conditions = self._parse_json_from_response(response)
        
        # 验证必填字段
        self._validate_required_fields(boundary_conditions)
        
        return boundary_conditions
    
    def _build_extraction_prompt(self, judgment_text: str) -> str:
        """构建提取Prompt"""
        return f"""
# 任务：从判决书中提取关键数据

请从以下判决书文本中提取关键数据，以JSON格式输出。

## 提取要求
1. 只提取判决书中**明确列出**的数据
2. 如果某项数据判决书没有提及，标记为null
3. 金额使用数字格式（单位：元）
4. 日期使用YYYY-MM-DD格式

## 提取字段
- contract_amount: 合同金额（数字）
- interest_rate: 年利率（小数，如0.061表示6.1%）
- signing_date: 签订日期（YYYY-MM-DD）
- equipment_count: 设备数量（数字）
- lessor_marker: 出租人脱敏标识（如"某某公司5"）
- lessee_marker: 承租人脱敏标识（如"某某公司1"）
- guarantor_marker: 担保人脱敏标识（如有）

## 判决书文本
{judgment_text}

## 输出格式
```json
{{
  "contract_amount": 150000000,
  "interest_rate": 0.061,
  "signing_date": "2021-02-24",
  "equipment_count": 62,
  "lessor_marker": "某某公司5",
  "lessee_marker": "某某公司1",
  "guarantor_marker": null,
  "data_source": "判决书文本"
}}
```
"""
    
    def _extract_by_regex(self, judgment_text: str) -> Dict[str, Any]:
        """
        使用正则表达式提取边界条件（备选方案）
        """
        boundary_conditions = {
            "contract_amount": self._extract_amount(judgment_text),
            "interest_rate": self._extract_interest_rate(judgment_text),
            "signing_date": self._extract_date(judgment_text),
            "equipment_count": self._extract_equipment_count(judgment_text),
            "data_source": "正则表达式提取"
        }
        
        # 提取当事人标记（需要更复杂的模式匹配）
        party_markers = self._extract_party_markers(judgment_text)
        boundary_conditions.update(party_markers)
        
        return boundary_conditions
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """提取合同金额"""
        match = re.search(self.patterns['contract_amount'], text)
        if match:
            amount_str = match.group(1).replace(',', '')
            return float(amount_str)
        return None
    
    def _extract_interest_rate(self, text: str) -> Optional[float]:
        """提取利率"""
        match = re.search(self.patterns['interest_rate'], text)
        if match:
            rate_str = match.group(1)
            return float(rate_str) / 100  # 转换为小数
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """提取日期"""
        match = re.search(self.patterns['signing_date'], text)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        return None
    
    def _extract_equipment_count(self, text: str) -> Optional[int]:
        """提取设备数量"""
        match = re.search(self.patterns['equipment_count'], text)
        if match:
            return int(match.group(1))
        return None
    
    def _extract_party_markers(self, text: str) -> Dict[str, Optional[str]]:
        """提取当事人脱敏标识"""
        # 常见当事人标记模式
        patterns = [
            r'原告[^\s]+([^，,、\s]+)',
            r'被告[^\s]+([^，,、\s]+)',
            r'第三人[^\s]+([^，,、\s]+)',
        ]
        
        markers = {
            "lessor_marker": None,
            "lessee_marker": None,
            "guarantor_marker": None
        }
        
        # 查找"某某公司X"模式
        company_pattern = r'(某某公司[一二三四五六七八九十\d]+)'
        matches = re.findall(company_pattern, text)
        
        if matches:
            # 去重并按出现顺序分配
            unique_markers = list(dict.fromkeys(matches))
            if len(unique_markers) >= 1:
                markers["lessor_marker"] = unique_markers[0]
            if len(unique_markers) >= 2:
                markers["lessee_marker"] = unique_markers[1]
            if len(unique_markers) >= 3:
                markers["guarantor_marker"] = unique_markers[2]
        
        return markers
    
    def _validate_required_fields(self, data: Dict[str, Any]):
        """验证必填字段"""
        required = ['contract_amount', 'interest_rate', 'signing_date']
        for field in required:
            if field not in data or data[field] is None:
                raise ValueError(f"缺少必填字段: {field}")
    
    def _parse_json_from_response(self, response: str) -> Dict[str, Any]:
        """从LLM响应中解析JSON"""
        # 尝试匹配JSON块
        json_match = re.search(r'```json\s*\n(.+?)\n```', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(1))
        
        # 尝试匹配普通JSON
        json_match = re.search(r'\{.+\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        
        raise ValueError("无法解析JSON响应")


# 测试代码
if __name__ == "__main__":
    # 测试文本
    test_text = """
    原告某某公司5与被告某某公司1于2021年2月24日签订融资租赁合同，
    合同金额为人民币150,000,000元，年利率为6.1%。
    租赁物为某某商场设备及附属设施62套。
    某某公司6作为担保人提供连带责任担保。
    """
    
    # 创建提取器（使用正则表达式模式）
    extractor = BoundaryConditionExtractor()
    
    # 提取边界条件
    boundary_conditions = extractor.extract(test_text)
    
    print("提取的边界条件:")
    print(json.dumps(boundary_conditions, ensure_ascii=False, indent=2))
