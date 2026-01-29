"""PDF生成器 - 生成专业的法律文书PDF文档"""
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.units import cm, mm
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from loguru import logger


class PDFGenerator:
    """PDF生成器 - 生成专业的法律文书PDF文档"""

    def __init__(self, output_path: str, stage0_data: Dict = None):
        """初始化PDF生成器"""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab未安装")

        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.work_dir = Path.cwd()

        self.page_width = A4[0]
        self.page_height = A4[1]
        self.margin = 2.5 * cm
        self.content_width = self.page_width - 2 * self.margin

        self.doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=A4,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )

        # 加载脱敏映射
        self.anonymization_map = {}
        self._load_anonymization_map(stage0_data)

        self._register_chinese_fonts()
        self._setup_styles()
        self.elements = []

    def _load_anonymization_map(self, stage0_data: Dict):
        """加载脱敏替换映射"""
        if stage0_data is None:
            # 尝试从文件加载
            try:
                import json
                plan_path = Path("outputs/stage0/0.2_anonymization_plan.json")
                if plan_path.exists():
                    with open(plan_path, 'r', encoding='utf-8') as f:
                        plan = json.load(f)
                    self._build_anonymization_map(plan)
            except Exception as e:
                logger.warning(f"加载脱敏映射失败: {e}")
        else:
            self._build_anonymization_map(stage0_data)

    def _build_anonymization_map(self, plan: Dict):
        """构建脱敏映射字典"""
        # 从公司Profile库构建
        for key, company in plan.get("公司Profile库", {}).items():
            if "公司名称" in company:
                self.anonymization_map[key] = company["公司名称"]

        # 从人物Profile库构建
        for key, person in plan.get("人物Profile库", {}).items():
            if "姓名" in person:
                self.anonymization_map[key] = person["姓名"]

        # 添加已知的脱敏映射
        additional_mappings = {
            "某某律师事务所": "上海中伦律师事务所",
            "上海XX律师事务所": "上海中伦律师事务所",
            "某某公证处": "上海市东方公证处",
            "某某银行": "中国工商银行",
        }
        self.anonymization_map.update(additional_mappings)

    def deanonymize_text(self, text: str) -> str:
        """反脱敏：将脱敏标记替换为真实名称"""
        if not text:
            return text

        result = text
        for marker, real_name in self.anonymization_map.items():
            # 替换脱敏标记为真实名称
            result = result.replace(marker, real_name)
            # 也处理加粗格式的脱敏标记
            result = result.replace(f"**{marker}**", real_name)

        return result

    def _register_chinese_fonts(self):
        """注册中文字体"""
        try:
            import platform
            system = platform.system()

            font_paths = []
            if system == "Darwin":
                font_paths = ['/System/Library/Fonts/STHeiti Light.ttc']
            else:
                font_paths = ['/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc']

            self.font_name = 'Helvetica'
            for font_path in font_paths:
                if Path(font_path).exists():
                    try:
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                        self.font_name = 'ChineseFont'
                        logger.info(f"字体已注册: {font_path}")
                        break
                    except Exception:
                        continue
        except Exception as e:
            logger.warning(f"字体注册失败: {e}")

    def _setup_styles(self):
        """设置PDF样式"""
        self.styles = getSampleStyleSheet()

        # 文档标题
        self.styles.add(ParagraphStyle(
            name='DocTitle',
            parent=self.styles['Title'],
            fontName=self.font_name,
            fontSize=18,
            leading=28,
            spaceAfter=25,
            spaceBefore=20,
            alignment=TA_CENTER,
            fontWeight='bold',
        ))

        # 一级标题
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading1'],
            fontName=self.font_name,
            fontSize=14,
            leading=22,
            spaceAfter=15,
            spaceBefore=15,
            alignment=TA_LEFT,
            fontWeight='bold',
        ))

        # 二级标题
        self.styles.add(ParagraphStyle(
            name='SubsectionTitle',
            parent=self.styles['Heading2'],
            fontName=self.font_name,
            fontSize=12,
            leading=20,
            spaceAfter=10,
            spaceBefore=10,
            alignment=TA_LEFT,
            fontWeight='bold',
        ))

        # 修改Normal样式
        self.styles['Normal'].fontName = self.font_name
        self.styles['Normal'].fontSize = 10
        self.styles['Normal'].leading = 18
        self.styles['Normal'].spaceAfter = 8
        self.styles['Normal'].alignment = TA_JUSTIFY
        self.styles['Normal'].firstLineIndent = 20

        # 表格标题
        self.styles.add(ParagraphStyle(
            name='TableTitle',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=10,
            leading=16,
            spaceAfter=8,
            spaceBefore=8,
            alignment=TA_LEFT,
        ))

        # 证据文件标题
        self.styles.add(ParagraphStyle(
            name='EvidenceFileTitle',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=11,
            leading=18,
            spaceAfter=10,
            spaceBefore=10,
            alignment=TA_LEFT,
            textColor=colors.black,
        ))

        # 目录
        self.styles.add(ParagraphStyle(
            name='TOC',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=10,
            leading=16,
            spaceAfter=4,
            alignment=TA_LEFT,
        ))

    def clean_text(self, text: str) -> str:
        """清理文本，保留基本格式"""
        if not text:
            return ""

        # 先应用脱敏还原
        text = self.deanonymize_text(text)

        # 去除HTML标签
        text = re.sub(r'<[^>]+>', '', text)

        # 去除代码块
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)

        # 去除加粗斜体标记 - 但保留文字内容
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)

        # 去除markdown标题标记
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)

        return text

    def clean_table_cell(self, text: str) -> str:
        """清理表格单元格中的markdown标记"""
        if not text:
            return ""

        # 去除所有markdown格式标记（包括嵌套的）
        # 先处理嵌套的 bold italic
        text = re.sub(r'\*\*\*([^*]+)\*\*\*', r'\1', text)
        # 再处理bold
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        # 再处理italic
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        # 处理代码
        text = re.sub(r'`([^`]+)`', r'\1', text)

        # 去除HTML标签
        text = re.sub(r'<[^>]+>', '', text)

        # 去除markdown链接 [text](url)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # 去除多余空白，但保留单个空格
        text = re.sub(r'[ \t]+', ' ', text)

        return text.strip()

    def clean_field_value(self, text: str) -> str:
        """清理字段值对中的markdown标记"""
        if not text:
            return ""
        return self.clean_table_cell(text)

    def add_paragraph_with_lines(self, text: str, style_name: str = 'Normal'):
        """添加段落，保留原始行结构"""
        if not text:
            return

        # 清理markdown标记，但保留换行
        clean = self.clean_text(text)

        # 按行处理，每一行都是一个段落
        lines = clean.split('\n')
        for line in lines:
            line = line.strip()
            # 跳过质量检查相关内容
            if not line:
                continue
            if any(kw in line for kw in ['质量检查报告', '即时检查', '数据一致性检查', 
                                          '格式规范性检查', '逻辑合理性检查', '生成完成',
                                          '生成后质量检查', '生成逻辑与数据一致性验证',
                                          '数据一致性验证', '即时检查（嵌入生成过程）',
                                          '✅', '即所有文件已按要求生成', '质量检查',
                                          '一致性验证', '规范性检查', '合理性检查']):
                continue
            if line.startswith('好的，作为'):
                continue
            self.elements.append(Paragraph(line, self.styles[style_name]))

    def add_paragraph(self, text: str, style_name: str = 'Normal'):
        """添加段落"""
        if not text:
            return
        clean_text = self.clean_text(text)
        if clean_text:
            self.elements.append(Paragraph(clean_text, self.styles[style_name]))

    def add_spacer(self, height: float = 0.5):
        """添加空白"""
        self.elements.append(Spacer(1, height * cm))

    def add_page_break(self):
        """添加分页"""
        self.elements.append(PageBreak())

    def add_title(self, text: str, style_name: str = 'DocTitle'):
        """添加标题"""
        clean_text = self.clean_text(text)
        if clean_text:
            self.elements.append(Paragraph(clean_text, self.styles[style_name]))

    def parse_field_value_pairs(self, text: str) -> Tuple[bool, List[Tuple[str, str]]]:
        """解析字段值对格式，如 '字段：值' 或 '字段 值'"""
        pairs = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 匹配 "字段：值" 或 "字段:值" 格式
            match = re.match(r'^([^：:]+)[：:]\s*(.+)$', line)
            if match:
                field = self.clean_table_cell(match.group(1).strip())
                value = self.clean_table_cell(match.group(2).strip())
                if field and value:
                    pairs.append((field, value))

        return len(pairs) > 0, pairs

    def parse_field_value_table(self, text: str) -> Tuple[bool, List[List[str]]]:
        """解析markdown表格格式"""
        lines = text.strip().split('\n')
        table_data = []
        prev_row = None  # 保存上一行，用于合并空第一列的行

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检查是否是表格行（以 | 开头和结尾）
            if '|' in line and not line.startswith('```'):
                # 检查是否是分隔行（| --- | --- | 或 | :--- | :--- |）
                cells = line.split('|')[1:-1]  # 去掉首尾的空字符串
                is_separator = True
                for cell in cells:
                    cell = cell.strip()
                    # 分隔行应该只包含对齐标记（- : 和空格），允许文本形式如 "---"
                    # 检查是否包含任何非分隔标记字符
                    if cell and re.search(r'[^\s\-:]+', cell):
                        is_separator = False
                        break
                if is_separator:
                    continue
                
                # 清理markdown表格格式
                row = []
                for cell in cells:
                    cell = cell.strip()
                    # 清理单元格中的markdown标记
                    cell = self.clean_table_cell(cell)
                    row.append(cell)
                
                # 过滤空行
                row = [c for c in row if c]
                
                if len(row) >= 1 and not all(c == '' for c in row):
                    # 处理特殊格式：空第一列的行表示值延续
                    if len(row) == 1 and prev_row is not None:
                        # 只有一列，是延续行，将值追加到上一行的第二列
                        if len(prev_row) > 1:
                            prev_row[1] = prev_row[1] + '\n' + row[0]
                        else:
                            prev_row.append(row[0])
                        # 更新上一行
                        if table_data:
                            table_data[-1] = prev_row
                    elif len(row) >= 2:
                        # 正常行
                        table_data.append(row)
                        prev_row = row

        return len(table_data) > 0, table_data

    def create_table(self, data: List[List[str]], col_widths: List[float] = None, style_name: str = 'Normal') -> Table:
        """创建带格式的表格，支持单元格内文本换行"""
        if not data or len(data) == 0:
            return None

        # 清理表格数据中的markdown标记
        cleaned_data = []
        for row in data:
            cleaned_row = [self.clean_table_cell(str(cell)) for cell in row]
            cleaned_data.append(cleaned_row)

        # 计算列宽
        if col_widths is None:
            num_cols = len(cleaned_data[0]) if cleaned_data else 1
            # 自动计算列宽：每列平均分配，但考虑最大内容长度
            col_widths = []
            for col_idx in range(num_cols):
                # 计算该列最大内容长度
                max_len = 0
                for row in cleaned_data:
                    if col_idx < len(row):
                        cell_len = len(str(row[col_idx]))
                        if cell_len > max_len:
                            max_len = cell_len
                # 根据内容长度分配宽度，限制最大宽度
                max_col_width = self.content_width / num_cols
                col_widths.append(max_col_width)
        else:
            # 如果提供了固定列宽，确保总宽度不超过content_width
            total_width = sum(col_widths)
            if total_width > self.content_width:
                # 按比例缩放
                scale = self.content_width / total_width
                col_widths = [w * scale for w in col_widths]

        # 将单元格内容转换为Paragraph以支持自动换行
        cell_data = []
        for row_idx, row in enumerate(cleaned_data):
            cell_row = []
            for col_idx, cell_text in enumerate(row):
                # 使用较小的字体和ParagraphStyle以支持换行
                cell_para = Paragraph(
                    cell_text if cell_text else '',
                    ParagraphStyle(
                        name=f'Cell_{row_idx}_{col_idx}',
                        fontName=self.font_name,
                        fontSize=8,
                        leading=10,
                        alignment=TA_LEFT,
                        wordWrap='CJK',
                    )
                )
                cell_row.append(cell_para)
            cell_data.append(cell_row)

        # 创建Table对象
        table = Table(cell_data, colWidths=col_widths)

        # 设置表格样式
        style = TableStyle([
            # 表头样式
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.95)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), self.font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTNAME', (0, 1), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),

            # 网格线
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LINEBEFORE', (0, 0), (-1, -1), 0.5, colors.grey),
            ('LINEAFTER', (0, 0), (-1, -1), 0.5, colors.grey),

            # 单元格内边距
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ])

        table.setStyle(style)
        return table

    def process_evidence_content(self, content: str) -> List:
        """处理证据内容，提取表格和编号列表"""
        elements = []

        # 预先清理内容
        content = self.clean_text(content)
        # 清除分隔符 ---
        content = re.sub(r'^---\s*$', '', content, flags=re.MULTILINE)

        # 过滤掉不需要的内容
        lines = content.split('\n')
        filtered_lines = []
        skip_section = False
        for line in lines:
            # 跳过质量检查报告部分（多种变体）
            if any(kw in line for kw in ['质量检查报告', '即时检查', '数据一致性检查', 
                                          '格式规范性检查', '逻辑合理性检查', '生成完成',
                                          '生成后质量检查', '生成逻辑与数据一致性验证',
                                          '数据一致性验证', '即时检查（嵌入生成过程）',
                                          '✅', '即所有文件已按要求生成', '质量检查']):
                skip_section = True
                continue
            # 跳过 "好的，作为专业的法律文书生成助手" 开头的行
            if line.startswith('好的，作为'):
                skip_section = True
                continue
            # 恢复跳过后的内容（遇到证据相关行时恢复）
            if not skip_section:
                filtered_lines.append(line)
            else:
                # 在skip状态下，只有证据组标题和证据列表不被跳过
                if line.strip().startswith('证据组') or \
                   re.match(r'^\d+\.\s+证据', line.strip()):
                    filtered_lines.append(line)
                    skip_section = False
                elif line.strip() and not line.strip().startswith('---'):
                    # 非空行，恢复正常状态
                    skip_section = False
                    filtered_lines.append(line)

        content = '\n'.join(filtered_lines)

        # 移除质量检查报告部分（从"质量检查报告"或"生成完成"开始到文件结束）
        content = re.sub(r'\n(?:---)?\s*(?:质量检查报告|数据一致性验证报告|生成完成|生成结论)[^\n]*[\s\S]*$', '', content, flags=re.IGNORECASE)

        # 每个证据组文件作为一个整体处理，不做内部分割
        sections = [content]

        group_title_added = False  # 跟踪是否已添加证据组标题
        evidence_list_title_added = False  # 跟踪是否已添加证据列表标题

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # 提取证据组标题（如 "证据组 1：融资租赁基础法律关系文件"）
            group_title = ""
            evidence_list = []
            evidence_files = {}  # 按证据编号索引证据文件内容
            current_evidence_num = None
            current_evidence_title = ""
            current_evidence_content = []
            remaining_lines = []
            fields_in_table = set()

            lines = section.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue

                # 证据组标题（可能有markdown标题前缀，如 ###）
                if re.match(r'^(#+\s*)?证据组\s*\d+[：:]?\s*', line):
                    group_title = self.clean_text(line)
                    evidence_list_title_added = False
                    continue
                
                # 证据文件标题（支持两种格式）
                # 格式1: **1. 证据一：《...》** 或 1. 证据一：《...》
                # 格式2: ### **证据一：《...》** 或 ### 证据一：《...》
                cleaned_line = self.clean_table_cell(line)
                # 优先匹配格式1（有数字序号）
                evidence_match = re.match(r'^(\d+)\.\s*证据[一二三四五六七八九十]?[：:](.+)', cleaned_line)
                is_format2 = False
                if not evidence_match:
                    # 尝试匹配格式2（可能有###前缀，无数字序号，但有中文数字）
                    evidence_match = re.match(r'^#*\s*证据[一二三四五六七八九十]+[：:](.+)', cleaned_line)
                    is_format2 = True
                if evidence_match:
                    # 保存上一个证据文件的内容
                    if current_evidence_num is not None:
                        evidence_files[current_evidence_num] = {
                            'title': f"证据{current_evidence_num}：{current_evidence_title}",
                            'content': current_evidence_content
                        }
                    # 开始新的证据文件
                    if is_format2:
                        # 格式2：group(0)是完整匹配，提取中文数字和标题
                        full_match = evidence_match.group(0)
                        chinese_num_match = re.match(r'^证据[一二三四五六七八九十]+', full_match)
                        title_match = re.match(r'^证据[一二三四五六七八九十]+[：:](.+)', full_match)
                        if chinese_num_match and title_match:
                            chinese_num = chinese_num_match.group(0).replace('证据', '')
                            # 将中文数字转换为阿拉伯数字
                            num_map = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5', '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'}
                            current_evidence_num = num_map.get(chinese_num, chinese_num)
                            current_evidence_title = title_match.group(1).strip()
                    else:
                        # 格式1：group(1)是阿拉伯数字，group(2)是标题
                        current_evidence_num = evidence_match.group(1)
                        current_evidence_title = evidence_match.group(2).strip()
                    current_evidence_content = []
                    evidence_list.append(f"{current_evidence_num}. {current_evidence_title}")
                    # 不再将证据文件标题添加到remaining_lines，让它在分组时动态处理
                    continue
                
                # 跳过 "证据文件列表" 标题
                if '证据文件列表' in line:
                    continue
                
                # 跳过markdown表格分隔行（如 | --- | :--- |）和包含质量检查内容的表格行
                if line.startswith('|'):
                    cleaned_for_check = self.clean_table_cell(line)
                    if any(kw in cleaned_for_check for kw in ['✅', '质量检查', '一致性验证', 
                                                               '规范性检查', '合理性检查', '通过']):
                        continue
                    else:
                        remaining_lines.append(line)
                else:
                    remaining_lines.append(line)
            
            # 保存最后一个证据文件的内容
            if current_evidence_num is not None:
                evidence_files[current_evidence_num] = {
                    'title': f"证据{current_evidence_num}：{current_evidence_title}",
                    'content': current_evidence_content
                }

            # 如果没找到证据组标题，在remaining_lines中查找并移除
            if not group_title:
                for line in remaining_lines:
                    if re.match(r'^(#+\s*)?证据组\s*\d+：', line):
                        group_title = self.clean_text(line)
                        remaining_lines.remove(line)
                        break

            # 添加证据组标题（每个证据组只添加一次）
            if group_title and not group_title_added:
                elements.append(Paragraph(group_title, self.styles['SubsectionTitle']))
                elements.append(Spacer(1, 0.2*cm))
                group_title_added = True

            # 按证据文件分组处理内容
            # 首先将remaining_lines按内容分组（使用---分隔符或证据组标题作为分隔）
            content_blocks = []
            current_block = []
            
            for line in remaining_lines:
                line = line.strip()
                if not line:
                    continue
                
                # 检测分隔符或新证据组开始
                if line == '---' or re.match(r'^### \*\*证据组', line) or re.match(r'^## \*\*证据组', line):
                    if current_block:
                        content_blocks.append(current_block)
                        current_block = []
                    continue
                
                current_block.append(line)
            
            # 保存最后一个块
            if current_block:
                content_blocks.append(current_block)
            
            # 将内容块与证据文件关联
            evidence_file_blocks = []
            evidence_nums = sorted(evidence_files.keys(), key=lambda x: int(x))
            
            for i, block in enumerate(content_blocks):
                if i < len(evidence_nums):
                    evidence_num = evidence_nums[i]
                    evidence_info = evidence_files[evidence_num]
                    evidence_file_blocks.append({
                        'title': evidence_info['title'],
                        'lines': block
                    })
                else:
                    # 多余的内容块，使用空标题
                    evidence_file_blocks.append({
                        'title': '',
                        'lines': block
                    })
            
            # 处理每个证据文件块
            for block_idx, block in enumerate(evidence_file_blocks):
                block_title = block['title']
                block_lines = block['lines']
                
                print(f"DEBUG: 处理块 {block_idx+1}, title={repr(block_title)}, lines={len(block_lines)}")
                
                # 添加证据文件标题
                if block_title:
                    print(f"DEBUG: 添加证据文件标题: {block_title}")
                    elements.append(Paragraph(block_title, self.styles['EvidenceFileTitle']))
                
                # 在块内查找附件标题和表格
                attachment_tables = []
                non_table_lines = []
                current_attachment = None
                current_attachment_lines = []
                
                for line in block_lines:
                    # 检测附件标题
                    attachment_match = re.match(r'^附件[：:]\s*《(.+)》', line)
                    if attachment_match:
                        # 保存上一个附件（如果有）
                        if current_attachment and current_attachment_lines:
                            attachment_tables.append({
                                'title': current_attachment,
                                'lines': current_attachment_lines
                            })
                        # 开始新的附件
                        current_attachment = f"附件：《{attachment_match.group(1)}》"
                        current_attachment_lines = []
                        continue
                    
                    # 检测表格行
                    if line.startswith('|'):
                        if current_attachment is None:
                            # 没有附件标题的表格，保存为普通表格
                            non_table_lines.append(line)
                        else:
                            current_attachment_lines.append(line)
                        continue
                    
                    # 普通行
                    if current_attachment and current_attachment_lines:
                        # 保存附件
                        attachment_tables.append({
                            'title': current_attachment,
                            'lines': current_attachment_lines
                        })
                        current_attachment = None
                        current_attachment_lines = []
                    non_table_lines.append(line)
                
                # 保存最后一个附件（如果有）
                if current_attachment and current_attachment_lines:
                    attachment_tables.append({
                        'title': current_attachment,
                        'lines': current_attachment_lines
                    })
                
                # 处理非表格行（合同正文、字段值对等）
                pairs = []
                contract_texts = []
                proof_purpose_content = ""
                proof_purpose_added = False
                fields_in_table = set()
                
                for line in non_table_lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    cleaned_line = self.clean_table_cell(line)
                    
                    # 检测证明目的
                    if cleaned_line.startswith('证明目的：') and not proof_purpose_added:
                        proof_purpose_content = line
                        proof_purpose_added = True
                        continue
                    
                    # 跳过证明目的行
                    if cleaned_line.startswith('证明目的：') or \
                       re.match(r'^(#+\s*)?证据组\s*\d+[：:]\s*.+', cleaned_line) or \
                       cleaned_line.startswith('证据组名称：'):
                        continue
                    
                    # 检测合同正文
                    is_contract_text = False
                    if re.match(r'^鉴于[：:]?\s*$', cleaned_line) or \
                       cleaned_line.startswith('鉴于：') or cleaned_line.startswith('鉴于:'):
                        is_contract_text = True
                    elif re.match(r'^第[一二三四五六七八九十0-9]+条', cleaned_line) or \
                         re.match(r'^\*\*第[一二三四五六七八九十0-9]+条', cleaned_line):
                        is_contract_text = True
                    elif re.match(r'^\d+\.\d+\s+', cleaned_line) or \
                         re.match(r'^\d+\.\s+\S', cleaned_line):
                        is_contract_text = True
                    
                    if is_contract_text:
                        contract_texts.append(cleaned_line)
                        continue
                    
                    # 跳过证据列表项
                    if re.match(r'^[\d]+[\.、]\s+\S', cleaned_line) and len(cleaned_line) > 30:
                        is_evidence_item = not (
                            re.match(r'^第[一二三四五六七八九十0-9]+条', cleaned_line) or
                            re.match(r'^\*\*第[一二三四五六七八九十0-9]+条', cleaned_line) or
                            re.match(r'^\d+\.\d+\s+', cleaned_line)
                        )
                        if is_evidence_item:
                            continue
                    
                    # 字段值对
                    match = re.match(r'^([^：:]+)[：:]\s*(.+)$', line)
                    if match:
                        field = match.group(1).strip()
                        value = match.group(2).strip()
                        skip_fields_block = {'甲方（盖章）', '乙方（盖章）', 
                                            '法定代表人（或授权代表）签字', '日期', 
                                            '甲方送达地址', '乙方送达地址',
                                            '联系人', '产权第', '框架/15层', '证明目的',
                                            '证据组', '证据组名称'}
                        should_skip = (field in skip_fields_block or 
                                       any(kw in field for kw in ['盖章', '签字', '日期', '联系人']) or
                                       len(value) < 5)
                        if field and value and not should_skip:
                            pairs.append((field, value))
                
                # 显示证明目的
                if proof_purpose_content:
                    clean_proof = self.clean_text(proof_purpose_content)
                    if clean_proof.startswith('证明目的：'):
                        clean_proof = clean_proof[len('证明目的：'):].strip()
                    elif clean_proof.startswith('证明目的:'):
                        clean_proof = clean_proof[len('证明目的:'):].strip()
                    
                    items = re.split(r'[；;]', clean_proof)
                    for item in items:
                        item = item.strip()
                        if item:
                            elements.append(Paragraph(item, self.styles['Normal']))
                    elements.append(Spacer(1, 0.2*cm))
                
                # 显示合同正文
                for contract_line in contract_texts:
                    elements.append(Paragraph(contract_line, self.styles['Normal']))
                if contract_texts:
                    elements.append(Spacer(1, 0.2*cm))
                
                # 显示字段值对（作为段落）
                for field, value in pairs:
                    elements.append(Paragraph(f"{field}：{value}", self.styles['Normal']))
                if pairs:
                    elements.append(Spacer(1, 0.2*cm))
                
                # 显示附件表格（带标题）
                for attachment in attachment_tables:
                    elements.append(Paragraph(attachment['title'], self.styles['TableTitle']))
                    
                    table_content = '\n'.join(attachment['lines'])
                    has_table, table_data = self.parse_field_value_table(table_content)
                    if has_table and len(table_data) > 1:
                        num_cols = len(table_data[0]) if table_data else 2
                        if num_cols == 2:
                            col_widths = [70*mm, self.content_width - 70*mm]
                        else:
                            available_width = self.content_width - 12
                            base_width = available_width / num_cols
                            col_widths = [base_width] * num_cols
                        
                        table = self.create_table(table_data, col_widths)
                        if table:
                            elements.append(table)
                            elements.append(Spacer(1, 0.3*cm))
                
                # 处理普通段落（剩余行）
                signature_fields = {'甲方（盖章）', '乙方（盖章）', 
                                   '法定代表人（或授权代表）签字', '日期', 
                                   '甲方送达地址', '乙方送达地址', '联系人', '附件'}
                
                for line in non_table_lines:
                    line = line.strip()
                    if not line or line.startswith('好的，'):
                        continue
                    if '|' in line:
                        continue
                    if line.startswith('|') or '---' in line:
                        continue
                    if line.startswith('证明目的：'):
                        continue
                    if line.startswith('证据组名称：'):
                        continue
                    if line in contract_texts:
                        continue
                    
                    skip = False
                    for field in fields_in_table:
                        if line.startswith(f'{field}：') or line.startswith(f'{field}:'):
                            skip = True
                            break
                    if line in ['项目', '内容']:
                        continue
                    
                    is_signature = any(line.startswith(f'{field}：') or line.startswith(f'{field}:')
                                   for field in signature_fields)
                    if not skip and (line or is_signature):
                        elements.append(Paragraph(line, self.styles['Normal']))
                
                # 每个证据文件后添加分隔
                if block_idx < len(evidence_file_blocks) - 1:
                    elements.append(Spacer(1, 0.5*cm))

        return elements

    def generate_complete_docket(self, stage0_data: Dict, stage1_data: Dict,
                                  stage2_data: Dict, stage3_data: Dict):
        """生成完整卷宗PDF"""
        # 封面
        self._add_cover()

        # 目录
        self.add_page_break()
        self._add_toc()

        # 第一部分：原告起诉包
        self.add_page_break()
        self._add_stage1()

        # 第二部分：被告答辩包
        self.add_page_break()
        self._add_stage2()

        # 第三部分：法院审理包
        self.add_page_break()
        self._add_stage3()

        # 生成PDF
        self.doc.build(self.elements)
        logger.success(f"PDF已生成: {self.output_path}")

    def _add_cover(self):
        """添加封面"""
        self.add_title("金融案件测试卷宗", 'DocTitle')
        self.add_spacer(2)
        from datetime import datetime
        self.add_paragraph(f"生成时间：{datetime.now().strftime('%Y年%m月%d日')}", 'Normal')

    def _add_toc(self):
        """添加目录"""
        self.add_title("目  录", 'SectionTitle')
        self.add_spacer(0.5)

        toc_items = [
            ("第一部分 原告起诉包", "1"),
            ("  一、民事起诉状", "1"),
            ("  二、原告证据包", "2"),
            ("  三、原告程序性文件", "3"),
            ("第二部分 被告答辩包", "4"),
            ("  一、民事答辩状", "4"),
            ("  二、被告程序性文件", "5"),
            ("第三部分 法院审理包", "6"),
            ("  一、庭审笔录", "6"),
            ("  二、判决书（脱敏版）", "7"),
        ]

        for title, page in toc_items:
            self.elements.append(Paragraph(f"{title} ........................ {page}", self.styles['TOC']))

    def _add_stage1(self):
        """添加原告起诉包"""
        self.add_title("第一部分 原告起诉包", 'SectionTitle')

        # 1.1 民事起诉状 - 使用行模式保留格式
        self.add_title("一、民事起诉状", 'SubsectionTitle')
        complaint_path = Path("outputs/stage1/民事起诉状.txt")
        if complaint_path.exists():
            with open(complaint_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.add_paragraph_with_lines(content)
        else:
            self.add_paragraph("（文件不存在）")

        # 1.2 原告证据包
        self.add_page_break()
        self.add_title("二、原告证据包", 'SubsectionTitle')

        evidence_dir = Path("outputs/stage1")
        evidence_files = sorted(evidence_dir.glob("原告证据包_证据组*.txt"))

        for i, ef in enumerate(evidence_files, 1):
            self.add_spacer(0.3)
            # 证据组标题由 process_evidence_content 内部添加，这里不再单独添加

            with open(ef, 'r', encoding='utf-8') as f:
                content = f.read()
            self.elements.extend(self.process_evidence_content(content))

        # 1.3 原告程序性文件
        self.add_page_break()
        self.add_title("三、原告程序性文件", 'SubsectionTitle')
        procedural_path = Path("outputs/stage1/原告程序性文件.txt")
        if procedural_path.exists():
            with open(procedural_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.add_paragraph_with_lines(content)
        else:
            self.add_paragraph("（文件不存在）")

    def _add_stage2(self):
        """添加被告答辩包"""
        self.add_title("第二部分 被告答辩包", 'SectionTitle')

        # 2.1 民事答辩状
        self.add_title("一、民事答辩状", 'SubsectionTitle')
        defense_path = Path("outputs/stage2/民事答辩状.txt")
        if defense_path.exists():
            with open(defense_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.add_paragraph_with_lines(content)
        else:
            self.add_paragraph("（文件不存在）")

        # 2.2 被告程序性文件
        self.add_page_break()
        self.add_title("二、被告程序性文件", 'SubsectionTitle')
        procedural_path = Path("outputs/stage2/被告程序性文件.txt")
        if procedural_path.exists():
            with open(procedural_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.add_paragraph_with_lines(content)
        else:
            self.add_paragraph("（文件不存在）")

    def _add_stage3(self):
        """添加法院审理包"""
        self.add_title("第三部分 法院审理包", 'SectionTitle')

        # 3.1 庭审笔录
        self.add_title("一、庭审笔录", 'SubsectionTitle')
        trial_path = Path("outputs/stage3/庭审笔录.txt")
        if trial_path.exists():
            with open(trial_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.add_paragraph_with_lines(content)
        else:
            self.add_paragraph("（文件不存在）")

        # 3.2 判决书
        self.add_page_break()
        self.add_title("二、判决书（脱敏版）", 'SubsectionTitle')
        judgment_files = list(Path("outputs/stage3").glob("判决书*.txt"))
        if judgment_files:
            with open(judgment_files[0], 'r', encoding='utf-8') as f:
                content = f.read()
            self.add_paragraph_with_lines(content)
        else:
            self.add_paragraph("（文件不存在）")

    def generate_answer_key_pdf(self, answer_key: Dict):
        """生成标准答案集PDF"""
        # 封面
        self.add_title("标准答案集", 'DocTitle')
        self.add_spacer(1)
        from datetime import datetime
        self.add_paragraph(f"生成时间：{datetime.now().strftime('%Y年%m月%d日')}", 'Normal')

        # 一、案件基本信息
        self.add_page_break()
        self.add_title("一、案件基本信息", 'SectionTitle')
        case_info = answer_key.get("案件基本信息", {})
        for key, value in case_info.items():
            if isinstance(value, list):
                self.add_paragraph(f"{key}：{', '.join(str(v) for v in value)}")
            elif value:
                self.add_paragraph(f"{key}：{value}")

        # 二、诉讼请求
        self.add_page_break()
        self.add_title("二、原告诉讼请求", 'SectionTitle')
        claims = answer_key.get("原告诉讼请求", {})
        for key, value in claims.items():
            if value:
                self.add_paragraph(f"{key}：{value}")

        # 三、关键金额
        self.add_page_break()
        self.add_title("三、关键金额清单", 'SectionTitle')
        key_numbers = answer_key.get("关键金额清单", {})
        for section, data in key_numbers.items():
            self.add_title(section, 'SubsectionTitle')
            if isinstance(data, dict):
                table_data = [['项目', '金额']]
                for k, v in data.items():
                    if isinstance(v, dict):
                        val = v.get("数值", "")
                        unit = v.get("单位", "")
                        if val is not None:
                            try:
                                formatted = f"{float(val):,.2f}"
                            except:
                                formatted = str(val)
                            table_data.append([k, f"{formatted} {unit}"])
                    else:
                        table_data.append([k, str(v)])
                self.elements.append(self.create_table(table_data, [80*mm, self.content_width - 80*mm]))

        # 四、计算过程
        self.add_page_break()
        self.add_title("四、详细计算过程", 'SectionTitle')
        calcs = answer_key.get("详细计算过程", {})
        for name, data in calcs.items():
            self.add_title(name, 'SubsectionTitle')
            if isinstance(data, dict):
                table_data = [['项目', '内容']]
                for k, v in data.items():
                    if v:
                        table_data.append([k, str(v)])
                self.elements.append(self.create_table(table_data, [60*mm, self.content_width - 60*mm]))

        # 生成PDF
        self.doc.build(self.elements)
        logger.success(f"标准答案集PDF已生成: {self.output_path}")
