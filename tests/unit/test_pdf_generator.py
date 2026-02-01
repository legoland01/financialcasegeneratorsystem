"""
Unit tests for pdf_generator.py
"""

import pytest
import tempfile
from pathlib import Path
from src.core.data_models import (
    EvidenceType,
    GeneratedEvidence
)
from src.core.pdf_generator import PDFGenerator, PDFGeneratorWithReportLab


@pytest.fixture
def sample_evidence():
    """创建测试用的GeneratedEvidence"""
    return GeneratedEvidence(
        filename="001_融资租赁合同.txt",
        content="""
融资租赁合同

合同编号：2023-001

甲方（出租人）：测试原告融资租赁公司
地址：北京市朝阳区
法定代表人：张三

乙方（承租人）：测试被告制造有限公司
地址：北京市海淀区
法定代表人：李四

鉴于甲方具有融资租赁业务资质，乙方具有良好商业信誉，双方经友好协商，达成如下协议：

第一条 租赁物
租赁物名称：数控机床设备
租赁物价值：人民币1,500,000.00元

第二条 租赁期限
租赁期限为24个月

第三条 租金及支付方式
租金总额：人民币1,500,000.00元
租金支付方式：按月等额本息还款

甲方（盖章）：                    乙方（盖章）：
日期：2023年01月15日             日期：2023年01月15日
        """.strip(),
        evidence_type=EvidenceType.CONTRACT
    )


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

    def test_generate_single_pdf_text(self, sample_evidence):
        """测试生成单个PDF文件（文本降级方案）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_evidence"
            generator = PDFGenerator()

            result = generator.generate_single(sample_evidence, output_path)

            assert result.exists()

    def test_generate_multiple_evidence(self, sample_evidence):
        """测试生成多个证据文件"""
        evidence_list = [
            sample_evidence,
            GeneratedEvidence(
                filename="002_收据.txt",
                content="收据内容",
                evidence_type=EvidenceType.VOUCHER
            ),
            GeneratedEvidence(
                filename="003_催款函.txt",
                content="催款函内容",
                evidence_type=EvidenceType.DOCUMENT
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generator = PDFGenerator()

            pdf_paths = generator.generate(evidence_list, output_dir)

            assert len(pdf_paths) == 3
            for path in pdf_paths:
                assert path.exists()

    def test_generate_creates_output_directory(self, sample_evidence):
        """测试生成输出目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "subdir" / "nested"
            generator = PDFGenerator()

            pdf_paths = generator.generate([sample_evidence], output_dir)

            assert output_dir.exists()
            assert len(pdf_paths) == 1

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

    def test_wrap_text_short(self):
        """测试短文本换行"""
        generator = PDFGenerator()
        result = generator._wrap_text("短文本", 100, None)
        assert len(result) >= 1


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

    def test_wrap_text_simple(self):
        """测试简单文本换行"""
        generator = PDFGeneratorWithReportLab()
        result = generator._wrap_text_simple("这是一个很长的文本需要换行处理", 10)
        assert len(result) >= 1

    def test_wrap_text_short(self):
        """测试短文本换行"""
        generator = PDFGeneratorWithReportLab()
        result = generator._wrap_text_simple("短文本", 50)
        assert len(result) == 1

    def test_generate_rich_pdf_fallback(self, sample_evidence):
        """测试丰富PDF生成（降级方案）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.pdf"
            generator = PDFGeneratorWithReportLab()

            result = generator.generate_rich_pdf(sample_evidence, output_path)

            assert result.exists()


class TestPDFGeneratorEdgeCases:
    """Test PDFGenerator edge cases"""

    def test_evidence_with_empty_content(self):
        """测试空内容证据"""
        evidence = GeneratedEvidence(
            filename="empty.txt",
            content="",
            evidence_type=EvidenceType.CONTRACT
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            generator = PDFGenerator()
            result = generator.generate_single(evidence, Path(tmpdir) / "empty")

            assert result.exists()

    def test_evidence_with_unicode_content(self, sample_evidence):
        """测试Unicode内容证据"""
        evidence = GeneratedEvidence(
            filename="unicode.txt",
            content="中文内容测试：融资租赁合同、被告公司、原告名称",
            evidence_type=EvidenceType.CONTRACT
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            generator = PDFGenerator()
            result = generator.generate_single(evidence, Path(tmpdir) / "unicode")

            assert result.exists()

    def test_evidence_with_special_filename(self):
        """测试特殊文件名证据"""
        evidence = GeneratedEvidence(
            filename="合同-2023-001_v2.txt",
            content="合同内容",
            evidence_type=EvidenceType.CONTRACT
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            generator = PDFGenerator()
            result = generator.generate_single(evidence, Path(tmpdir) / "special")

            assert result.exists()

    def test_output_path_with_spaces(self, sample_evidence):
        """测试带空格路径输出"""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output dir" / "sub dir"
            generator = PDFGenerator()

            pdf_paths = generator.generate([sample_evidence], output_dir)

            assert len(pdf_paths) == 1
            assert pdf_paths[0].exists()
