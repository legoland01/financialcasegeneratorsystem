"""
Unit tests for claim_extractor.py - F2.2
"""

import pytest
from pathlib import Path
from src.core.claim_extractor import ClaimExtractor
from src.core.data_models import ClaimList, Claim


class TestClaimExtractor:
    """Test ClaimExtractor class"""

    def test_extract_from_text_basic(self):
        """测试从文本提取诉求"""
        text = """
原告诉称：请求判令被告向原告支付欠款本金人民币1,500,000元，
利息人民币75,000元，违约金人民币30,000元。
        """.strip()

        extractor = ClaimExtractor()
        result = extractor.extract_from_text(text)

        assert result is not None
        assert len(result.claims) > 0

    def test_extract_principal_claim(self):
        """测试提取本金诉求"""
        text = "请求判令被告向原告支付欠款本金人民币1,500,000元"
        extractor = ClaimExtractor()
        result = extractor.extract_from_text(text)

        has_principal = any(c.type == "本金" for c in result.claims)
        assert has_principal

    def test_extract_interest_claim(self):
        """测试提取利息诉求"""
        text = "请求判令被告向原告支付欠款利息人民币75,000元"
        extractor = ClaimExtractor()
        result = extractor.extract_from_text(text)

        has_interest = any(c.type == "利息" for c in result.claims)
        assert has_interest

    def test_extract_penalty_claim(self):
        """测试提取违约金诉求"""
        text = "请求判令被告向原告支付违约金人民币30,000元"
        extractor = ClaimExtractor()
        result = extractor.extract_from_text(text)

        has_penalty = any(c.type == "违约金" for c in result.claims)
        assert has_penalty

    def test_extract_with_litigation_cost(self):
        """测试提取诉讼费用"""
        text = """
请求判令被告支付本金100万元。
诉讼费用人民币5,000元由被告承担。
        """.strip()
        extractor = ClaimExtractor()
        result = extractor.extract_from_text(text)

        assert result.litigation_cost is not None

    def test_extract_empty_text(self):
        """测试空文本"""
        extractor = ClaimExtractor()
        result = extractor.extract_from_text("")

        assert result is not None
        assert len(result.claims) == 0

    def test_extract_no_claims(self):
        """测试无诉求文本"""
        text = "这是判决书的正文内容，不包含诉求。"
        extractor = ClaimExtractor()
        result = extractor.extract_from_text(text)

        assert result is not None

    def test_init_with_llm_client(self):
        """测试使用LLM客户端初始化"""
        class MockLLMClient:
            def complete(self, prompt):
                return '{"claims": [{"type": "本金", "amount": 1000000}]}'

        extractor = ClaimExtractor(llm_client=MockLLMClient())
        assert extractor.llm_client is not None


class TestClaimExtractorRegex:
    """Test regex extraction patterns"""

    def test_amount_with_commas(self):
        """测试带逗号的金额"""
        text = "本金人民币1,500,000元"
        extractor = ClaimExtractor()
        result = extractor.extract_from_text(text)

        has_amount = any(c.amount > 0 for c in result.claims)
        assert has_amount

    def test_amount_without_commas(self):
        """测试不带逗号的金额"""
        text = "本金人民币1500000元"
        extractor = ClaimExtractor()
        result = extractor.extract_from_text(text)

        has_amount = any(c.amount > 0 for c in result.claims)
        assert has_amount

    def test_amount_with_rmb_prefix(self):
        """测试带人民币前缀的金额"""
        text = "人民币1,000,000元"
        extractor = ClaimExtractor()
        result = extractor.extract_from_text(text)

        assert result is not None


class TestClaimExtractorEdgeCases:
    """Test edge cases"""

    def test_multiple_same_type_claims(self):
        """测试多个同类型诉求"""
        text = "请求支付本金100万元和利息5万元"
        extractor = ClaimExtractor()
        result = extractor.extract_from_text(text)

        assert result is not None

    def test_zero_amount(self):
        """测试零金额"""
        text = "请求判令被告支付人民币0元"
        extractor = ClaimExtractor()
        result = extractor.extract_from_text(text)

        assert result is not None

    def test_extract_from_file(self, tmp_path):
        """测试从文件提取"""
        text = "请求判令被告支付本金人民币100万元"
        judgment_file = tmp_path / "judgment.txt"
        judgment_file.write_text(text, encoding="utf-8")

        extractor = ClaimExtractor()
        result = extractor.extract(judgment_file)

        assert result is not None
