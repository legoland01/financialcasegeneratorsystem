"""
Unit tests for claim_extractor.py - F2.2
"""

import pytest
from src.core.claim_extractor import ClaimExtractor
from src.core.data_models import ClaimList, Claim


class TestClaimExtractor:
    """Test ClaimExtractor class"""

    def test_extract_from_text_returns_claim_list(self):
        """测试从文本提取返回ClaimList"""
        text = "请求判令被告支付欠款本金人民币1,500,000元"
        extractor = ClaimExtractor()
        result = extractor.extract_from_text(text)

        assert result is not None
        assert isinstance(result, ClaimList)

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

    def test_extract_multiple_claims(self):
        """测试提取多个诉求"""
        text = """
请求判令被告支付本金150万元，利息75,000元，违约金30,000元。
        """.strip()
        extractor = ClaimExtractor()
        result = extractor.extract_from_text(text)

        assert len(result.claims) >= 1

    def test_extract_litigation_cost(self):
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
        text = "这是判决书的正文，不包含诉讼请求。"
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

        has_principal = any(c.type == "本金" and c.amount > 0 for c in result.claims)
        assert has_principal

    def test_amount_without_commas(self):
        """测试不带逗号的金额"""
        text = "本金人民币1500000元"
        extractor = ClaimExtractor()
        result = extractor.extract_from_text(text)

        has_principal = any(c.type == "本金" and c.amount > 0 for c in result.claims)
        assert has_principal

    def test_amount_with_rmb_prefix(self):
        """测试带人民币前缀"""
        text = "人民币1,000,000元"
        extractor = ClaimExtractor()
        result = extractor.extract_from_text(text)

        assert result is not None


class TestClaimExtractorEdgeCases:
    """Test edge cases"""

    def test_zero_amount(self):
        """测试零金额"""
        text = "请求判令被告支付人民币0元"
        extractor = ClaimExtractor()
        result = extractor.extract_from_text(text)

        assert result is not None

    def test_decimal_amount(self):
        """测试小数金额"""
        text = "请求判令被告支付人民币1,234.56元"
        extractor = ClaimExtractor()
        result = extractor.extract_from_text(text)

        assert result is not None
