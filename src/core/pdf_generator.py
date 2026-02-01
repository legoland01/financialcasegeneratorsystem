"""
PDFGenerator - F3 PDF生成器

功能：将文本证据转换为PDF文件

输入：GeneratedEvidence列表
输出：PDF文件

核心原则：
- P1 脱敏标记隔离：全程使用真实信息
"""

from pathlib import Path
from typing import List, Optional
import os


class PDFGenerator:
    """
    PDF生成器 - F3

    将文本证据转换为PDF文件。
    支持中文字体和基本格式设置。
    """

    def __init__(self, font_path: Optional[str] = None):
        """
        初始化PDF生成器

        Args:
            font_path: 中文字体路径，如果为None则尝试自动查找
        """
        self.font_path = font_path or self._find_chinese_font()

    def generate(
        self,
        evidence_list: List["GeneratedEvidence"],
        output_dir: Path
    ) -> List[Path]:
        """
        生成PDF文件

        Args:
            evidence_list: 生成的证据列表
            output_dir: 输出目录
        Returns:
            List[Path]: 生成的PDF文件路径列表
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        pdf_paths = []

        for evidence in evidence_list:
            pdf_path = self._generate_single_pdf(evidence, output_dir)
            if pdf_path:
                pdf_paths.append(pdf_path)

        return pdf_paths

    def generate_single(
        self,
        evidence: "GeneratedEvidence",
        output_path: Path
    ) -> Path:
        """
        生成单个PDF文件

        Args:
            evidence: 生成的证据
            output_path: 输出文件路径
        Returns:
            Path: 生成的PDF文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if self.font_path and os.path.exists(self.font_path):
            return self._generate_pdf_with_font(evidence, output_path)
        else:
            return self._generate_pdf_text(evidence, output_path)

    def _generate_single_pdf(
        self,
        evidence: "GeneratedEvidence",
        output_dir: Path
    ) -> Optional[Path]:
        """
        生成单个PDF文件

        Args:
            evidence: 生成的证据
            output_dir: 输出目录
        Returns:
            Path: 生成的PDF文件路径
        """
        output_path = output_dir / evidence.filename.replace('.txt', '.pdf')
        return self.generate_single(evidence, output_path)

    def _generate_pdf_with_font(
        self,
        evidence: "GeneratedEvidence",
        output_path: Path
    ) -> Path:
        """
        使用中文字体生成PDF

        Args:
            evidence: 生成的证据
            output_path: 输出文件路径
        Returns:
            Path: 生成的PDF文件路径
        """
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import inch
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib import colors

            pdfmetrics.registerFont(TTFont('Chinese', self.font_path))

            c = canvas.Canvas(str(output_path), pagesize=A4)
            width, height = A4

            c.setFont("Chinese", 12)
            c.setFillColor(colors.black)

            y_position = height - 50
            margin = 50
            line_height = 18
            max_width = width - 2 * margin

            lines = evidence.content.split('\n')

            for line in lines:
                if y_position < margin:
                    c.showPage()
                    c.setFont("Chinese", 12)
                    y_position = height - 50

                if len(line) > 80:
                    wrapped_lines = self._wrap_text(line, max_width, c)
                    for wrapped_line in wrapped_lines:
                        if y_position < margin:
                            c.showPage()
                            c.setFont("Chinese", 12)
                            y_position = height - 50
                        c.drawString(margin, y_position, wrapped_line)
                        y_position -= line_height
                else:
                    c.drawString(margin, y_position, line)
                    y_position -= line_height

            c.save()
            return output_path

        except ImportError:
            return self._generate_pdf_text(evidence, output_path)

    def _generate_pdf_text(
        self,
        evidence: "GeneratedEvidence",
        output_path: Path
    ) -> Path:
        """
        生成文本文件（PDF不可用时降级方案）

        Args:
            evidence: 生成的证据
            output_path: 输出文件路径
        Returns:
            Path: 生成的PDF文件路径（实际上为文本文件）
        """
        text_path = output_path.with_suffix('.txt')

        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(evidence.content)

        return text_path

    def _wrap_text(
        self,
        text: str,
        max_width: float,
        canvas: "canvas.Canvas"
    ) -> List[str]:
        """
        文本换行处理

        Args:
            text: 原始文本
            max_width: 最大宽度
            canvas: PDF画布
        Returns:
            List[str]: 换行后的文本列表
        """
        words = text.split('')
        if not words:
            return [text]

        wrapped = []
        current_line = ""

        for word in words:
            test_line = current_line + word
            if canvas.stringWidth(test_line, "Chinese", 12) < max_width:
                current_line = test_line
            else:
                if current_line:
                    wrapped.append(current_line)
                current_line = word

        if current_line:
            wrapped.append(current_line)

        return wrapped if wrapped else [text]

    def _find_chinese_font(self) -> Optional[str]:
        """
        查找中文字体

        Returns:
            str: 中文字体路径，如果未找到则返回None
        """
        font_paths = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "C:\\Windows\\Fonts\\simhei.ttf",
            "C:\\Windows\\Fonts\\msyh.ttf",
        ]

        for path in font_paths:
            if os.path.exists(path):
                return path

        return None


class PDFGeneratorWithReportLab(PDFGenerator):
    """
    基于ReportLab的PDF生成器

    使用reportlab库生成格式更丰富的PDF文件。
    """

    def __init__(self):
        super().__init__()
        self._check_dependencies()

    def _check_dependencies(self):
        """检查依赖是否可用"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            self.reportlab_available = True
        except ImportError:
            self.reportlab_available = False

    def generate_rich_pdf(
        self,
        evidence: "GeneratedEvidence",
        output_path: Path,
        title: Optional[str] = None
    ) -> Path:
        """
        生成格式丰富的PDF文件

        Args:
            evidence: 生成的证据
            output_path: 输出文件路径
            title: PDF标题
        Returns:
            Path: 生成的PDF文件路径
        """
        if not self.reportlab_available:
            return self._generate_pdf_text(evidence, output_path)

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.units import mm
            from reportlab.lib import colors

            width, height = A4
            margin = 20 * mm

            c = canvas.Canvas(str(output_path), pagesize=A4)

            if title:
                c.setFont("Helvetica-Bold", 16)
                c.drawString(margin, height - margin - 20, title)

            c.setFont("Helvetica", 10)
            y_position = height - margin - 50

            lines = evidence.content.split('\n')

            for line in lines:
                if y_position < margin:
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y_position = height - margin

                if len(line) > 100:
                    wrapped_lines = self._wrap_text_simple(line, 95)
                    for wrapped_line in wrapped_lines:
                        if y_position < margin:
                            c.showPage()
                            c.setFont("Helvetica", 10)
                            y_position = height - margin
                        c.drawString(margin, y_position, wrapped_line)
                        y_position -= 12
                else:
                    c.drawString(margin, y_position, line)
                    y_position -= 12

            c.save()
            return output_path

        except Exception:
            return self._generate_pdf_text(evidence, output_path)

    def _wrap_text_simple(self, text: str, max_chars: int) -> List[str]:
        """
        简单文本换行

        Args:
            text: 原始文本
            max_chars: 每行最大字符数
        Returns:
            List[str]: 换行后的文本列表
        """
        words = text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            if len(current_line + word) < max_chars:
                current_line = current_line + word + " "
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "

        if current_line:
            lines.append(current_line.strip())

        return lines
