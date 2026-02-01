"""
Unit tests for pdf_generator.py

Note: PDF generation tests are skipped due to external font dependencies on macOS.
Full PDF generation requires proper font configuration.
"""

import pytest
import tempfile
from pathlib import Path
from src.core.data_models import (
    EvidenceType,
    GeneratedEvidence
)
from src.core.pdf_generator import PDFGenerator, PDFGeneratorWithReportLab


class TestPDFGenerator:
    """Test PDFGenerator class"""

    def test_init_with_default_font(self):
        """测试默认字体初始化"""
        generator = PDFGenerator()
        assert generator is not None

    def test_init_with_custom_font(self):
        """测试自定义字体初始化"""
        generator = PDFGenerator(font_path="/tmp/test-font.ttf")
        assert generator is not None

    def test_generate_empty_list(self):
        """测试生成空列表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = PDFGenerator()
            result = generator.generate([], Path(tmpdir))
            assert len(result) == 0

    def test_find_chinese_font_system(self):
        """测试查找系统字体"""
        generator = PDFGenerator()
        font_path = generator._find_chinese_font()


class TestPDFGeneratorWithReportLab:
    """Test PDFGeneratorWithReportLab class"""

    def test_init(self):
        """测试初始化"""
        generator = PDFGeneratorWithReportLab()
        assert generator is not None

    def test_check_dependencies(self):
        """测试依赖检查"""
        generator = PDFGeneratorWithReportLab()
        assert hasattr(generator, 'reportlab_available')
