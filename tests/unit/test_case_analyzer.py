"""
Unit tests for case_analyzer.py - F2.1
"""

import pytest
from pathlib import Path
from datetime import datetime
from src.core.case_analyzer import CaseAnalyzer
from src.core.data_models import (
    CaseData, Party, ContractInfo, BreachInfo, CaseType
)


class TestCaseAnalyzer:
    """Test CaseAnalyzer class"""

    def test_analyze_with_mock_judgment(self, tmp_path):
        """测试分析判决书"""
        judgment_content = """
原告：测试原告融资租赁有限公司
住所地：北京市朝阳区
法定代表人：张三

被告：测试被告制造有限公司
住所地：上海市浦东新区
法定代表人：李四

原告与被告于2023年1月15日签订《融资租赁合同》，合同金额人民币1,500,000元。
被告已支付人民币300,000元，尚欠人民币1,200,000元。
被告自2023年6月1日起未按约定支付租金。
        """.strip()

        judgment_file = tmp_path / "judgment.txt"
        judgment_file.write_text(judgment_content, encoding="utf-8")

        analyzer = CaseAnalyzer()
        result = analyzer.analyze(judgment_file)

        assert result is not None
        assert result.plaintiff is not None
        assert result.defendant is not None
        assert result.contract is not None

    def test_analyze_extracts_plaintiff(self, tmp_path):
        """测试提取原告信息"""
        judgment_content = "原告：测试原告公司\n住所地：北京\n法定代表人：张三\n被告：被告公司"
        judgment_file = tmp_path / "judgment.txt"
        judgment_file.write_text(judgment_content, encoding="utf-8")

        analyzer = CaseAnalyzer()
        result = analyzer.analyze(judgment_file)

        assert "测试原告" in result.plaintiff.name or "原告" in result.plaintiff.name

    def test_analyze_extracts_defendant(self, tmp_path):
        """测试提取被告信息"""
        judgment_content = "原告：原告公司\n被告：测试被告公司\n住所地：上海\n法定代表人：李四"
        judgment_file = tmp_path / "judgment.txt"
        judgment_file.write_text(judgment_content, encoding="utf-8")

        analyzer = CaseAnalyzer()
        result = analyzer.analyze(judgment_file)

        assert "测试被告" in result.defendant.name or "被告" in result.defendant.name

    def test_analyze_extracts_contract(self, tmp_path):
        """测试提取合同信息"""
        judgment_content = """
原告：原告公司
被告：被告公司
合同金额：人民币1,500,000元
签订日期：2023年1月15日
        """.strip()
        judgment_file = tmp_path / "judgment.txt"
        judgment_file.write_text(judgment_content, encoding="utf-8")

        analyzer = CaseAnalyzer()
        result = analyzer.analyze(judgment_file)

        assert result.contract is not None

    def test_analyze_empty_file(self, tmp_path):
        """测试空文件"""
        judgment_file = tmp_path / "empty.txt"
        judgment_file.write_text("", encoding="utf-8")

        analyzer = CaseAnalyzer()
        result = analyzer.analyzeralyze(judgment_file)

        assert result is not None

    def test_analyze_nonexistent_file(self):
        """测试不存在的文件"""
        analyzer = CaseAnalyzer()
        result = analyzer.analyze(Path("/nonexistent/judgment.txt"))
        assert result is None

    def test_init_with_llm_client(self):
        """测试使用LLM客户端初始化"""
        class MockLLMClient:
            def complete(self, prompt):
                return '{"plaintiff": {"name": "测试公司"}}'

        analyzer = CaseAnalyzer(llm_client=MockLLMClient())
        assert analyzer.llm_client is not None


class TestCaseAnalyzerRegexPatterns:
    """Test regex patterns in CaseAnalyzer"""

    def test_plaintiff_pattern(self, tmp_path):
        """测试原告匹配模式"""
        content = "原告：测试融资租赁有限公司"
        judgment_file = tmp_path / "test.txt"
        judgment_file.write_text(content, encoding="utf-8")

        analyzer = CaseAnalyzer()
        result = analyzer.analyze(judgment_file)
        assert result.plaintiff is not None

    def test_defendant_pattern(self, tmp_path):
        """测试被告匹配模式"""
        content = "被告：测试制造有限公司"
        judgment_file = tmp_path / "test.txt"
        judgment_file.write_text(content, encoding="utf-8")

        analyzer = CaseAnalyzer()
        result = analyzer.analyze(judgment_file)
        assert result.defendant is not None

    def test_amount_pattern(self, tmp_path):
        """测试金额匹配模式"""
        content = "合同金额：人民币1,500,000元"
        judgment_file = tmp_path / "test.txt"
        judgment_file.write_text(content, encoding="utf-8")

        analyzer = CaseAnalyzer()
        result = analyzer.analyze(judgment_file)
        assert result.contract is not None


class TestCaseAnalyzerEdgeCases:
    """Test edge cases"""

    def test_missing_plaintiff_section(self, tmp_path):
        """测试缺少原告部分"""
        content = "被告：被告公司\n合同金额：100万"
        judgment_file = tmp_path / "test.txt"
        judgment_file.write_text(content, encoding="utf-8")

        analyzer = CaseAnalyzer()
        result = analyzer.analyze(judgment_file)
        assert result is not None

    def test_missing_defendant_section(self, tmp_path):
        """测试缺少被告部分"""
        content = "原告：原告公司\n合同金额：100万"
        judgment_file = tmp_path / "test.txt"
        judgment_file.write_text(content, encoding="utf-8")

        analyzer = CaseAnalyzer()
        result = analyzer.analyze(judgment_file)
        assert result is not None

    def test_special_characters_in_name(self, tmp_path):
        """测试特殊字符公司名"""
        content = "原告：北京-测试融资租赁有限公司"
        judgment_file = tmp_path / "test.txt"
        judgment_file.write_text(content, encoding="utf-8")

        analyzer = CaseAnalyzer()
        result = analyzer.analyze(judgment_file)
        assert result.plaintiff is not None
