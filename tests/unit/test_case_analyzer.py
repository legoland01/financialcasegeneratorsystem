"""
Unit tests for case_analyzer.py - F2.1
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from src.core.case_analyzer import (
    JudgmentParser,
    PDFJudgmentParser,
    TextJudgmentParser,
    CaseAnalyzer
)


class TestTextJudgmentParser:
    """Test TextJudgmentParser class"""

    def test_parse_text_file(self, tmp_path):
        """测试解析文本文件"""
        content = "原告：测试公司\n被告：被告公司"
        judgment_file = tmp_path / "judgment.txt"
        judgment_file.write_text(content, encoding="utf-8")

        parser = TextJudgmentParser()
        result = parser.parse(judgment_file)

        assert result == content
        assert "原告" in result
        assert "测试公司" in result

    def test_parse_empty_file(self, tmp_path):
        """测试解析空文件"""
        judgment_file = tmp_path / "empty.txt"
        judgment_file.write_text("", encoding="utf-8")

        parser = TextJudgmentParser()
        result = parser.parse(judgment_file)

        assert result == ""

    def test_parse_utf8_encoding(self, tmp_path):
        """测试UTF-8编码"""
        content = "原告：测试公司有限公司"
        judgment_file = tmp_path / "judgment.txt"
        judgment_file.write_text(content, encoding="utf-8")

        parser = TextJudgmentParser()
        result = parser.parse(judgment_file)

        assert result == content


class TestCaseAnalyzer:
    """Test CaseAnalyzer class"""

    def test_analyze_returns_case_data(self, tmp_path):
        """测试分析返回CaseData"""
        content = """
原告：测试融资租赁有限公司
住所地：北京市朝阳区
法定代表人：张三

被告：测试制造有限公司
住所地：上海市浦东新区
法定代表人：李四

原告与被告于2023年1月15日签订《融资租赁合同》。
合同金额为人民币1,500,000元。
被告已支付人民币300,000元。
        """.strip()
        judgment_file = tmp_path / "judgment.txt"
        judgment_file.write_text(content, encoding="utf-8")

        analyzer = CaseAnalyzer()
        result = analyzer.analyze(judgment_file)

        assert result is not None
        assert result.plaintiff is not None
        assert result.defendant is not None

    def test_analyze_extracts_plaintiff(self, tmp_path):
        """测试提取原告信息"""
        content = "原告：测试原告公司\n住所地：北京\n被告：被告公司"
        judgment_file = tmp_path / "judgment.txt"
        judgment_file.write_text(content, encoding="utf-8")

        analyzer = CaseAnalyzer()
        result = analyzer.analyze(judgment_file)

        assert result.plaintiff is not None
        assert result.plaintiff.name is not None

    def test_analyze_extracts_defendant(self, tmp_path):
        """测试提取被告信息"""
        content = "原告：原告公司\n被告：测试被告公司\n住所地：上海"
        judgment_file = tmp_path / "judgment.txt"
        judgment_file.write_text(content, encoding="utf-8")

        analyzer = CaseAnalyzer()
        result = analyzer.analyze(judgment_file)

        assert result.defendant is not None
        assert result.defendant.name is not None

    def test_analyze_sets_extracted_time(self, tmp_path):
        """测试设置提取时间"""
        content = "原告：原告公司\n被告：被告公司"
        judgment_file = tmp_path / "judgment.txt"
        judgment_file.write_text(content, encoding="utf-8")

        before = datetime.now()
        analyzer = CaseAnalyzer()
        result = analyzer.analyze(judgment_file)
        after = datetime.now()

        assert result.extracted_at is not None
        assert before <= result.extracted_at <= after

    def test_analyze_sets_judgment_path(self, tmp_path):
        """测试设置判决书路径"""
        content = "原告：原告公司\n被告：被告公司"
        judgment_file = tmp_path / "judgment.txt"
        judgment_file.write_text(content, encoding="utf-8")

        analyzer = CaseAnalyzer()
        result = analyzer.analyze(judgment_file)

        assert result.judgment_path is not None
        assert "judgment.txt" in result.judgment_path

    def test_detect_parser_for_txt(self, tmp_path):
        """测试检测文本解析器"""
        judgment_file = tmp_path / "judgment.txt"
        judgment_file.write_text("content", encoding="utf-8")

        analyzer = CaseAnalyzer()
        parser = analyzer._detect_parser(judgment_file)

        assert isinstance(parser, TextJudgmentParser)

    def test_analyze_with_llm_client(self, tmp_path):
        """测试使用LLM客户端"""
        content = "原告：原告公司\n被告：被告公司"
        judgment_file = tmp_path / "judgment.txt"
        judgment_file.write_text(content, encoding="utf-8")

        class MockLLMClient:
            def complete(self, prompt):
                return '{"plaintiff": {"name": "LLM提取的原告"}, "defendant": {"name": "LLM提取的被告"}}'

        analyzer = CaseAnalyzer(llm_client=MockLLMClient())
        result = analyzer.analyze(judgment_file)

        assert result is not None


class TestCaseAnalyzerEdgeCases:
    """Test CaseAnalyzer edge cases"""

    def test_analyze_missing_plaintiff(self, tmp_path):
        """测试缺少原告信息"""
        content = "被告：被告公司"
        judgment_file = tmp_path / "judgment.txt"
        judgment_file.write_text(content, encoding="utf-8")

        analyzer = CaseAnalyzer()
        result = analyzer.analyze(judgment_file)

        assert result is not None
        assert result.plaintiff is not None

    def test_analyze_missing_defendant(self, tmp_path):
        """测试缺少被告信息"""
        content = "原告：原告公司"
        judgment_file = tmp_path / "judgment.txt"
        judgment_file.write_text(content, encoding="utf-8")

        analyzer = CaseAnalyzer()
        result = analyzer.analyze(judgment_file)

        assert result is not None
        assert result.defendant is not None

    def test_analyze_with_special_characters(self, tmp_path):
        """测试特殊字符"""
        content = "原告：北京-测试（融资）租赁公司"
        judgment_file = tmp_path / "judgment.txt"
        judgment_file.write_text(content, encoding="utf-8")

        analyzer = CaseAnalyzer()
        result = analyzer.analyze(judgment_file)

        assert result is not None

    def test_analyze_empty_file(self, tmp_path):
        """测试空文件"""
        judgment_file = tmp_path / "empty.txt"
        judgment_file.write_text("", encoding="utf-8")

        analyzer = CaseAnalyzer()
        result = analyzer.analyze(judgment_file)

        assert result is not None
