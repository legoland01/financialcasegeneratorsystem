"""简化版PDF生成器 - 直接读取证据文件生成PDF"""
from typing import Dict, Any, List, Optional
from pathlib import Path
from loguru import logger
import json
import re

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from src.utils import load_json


class PDFGeneratorSimple:
    """简化版PDF生成器 - 直接读取证据文件"""

    def __init__(self, output_path: str, stage0_data: Optional[Dict] = None, config_path: str = None):
        """
        初始化简化版PDF生成器

        Args:
            output_path: 输出PDF文件路径
            stage0_data: 阶段0数据（用于反脱敏）
            config_path: 案件类型配置文件路径
        """
        self.output_path = Path(output_path)
        self.anonymization_map = {}
        self.config = self._load_config(config_path)
        self._load_anonymization_map(stage0_data)
        self._setup_pdf()
    
    def _load_config(self, config_path: str = None) -> Dict:
        """加载案件类型配置"""
        default_config = {
            "case_type": "通用金融案件",
            "case_type_name": "金融纠纷",
            "output_structure": {
                "cover_page": {
                    "enabled": True,
                    "title": "案件卷宗"
                },
                "table_of_contents": {
                    "enabled": True,
                    "show_page_number": True
                },
                "evidence_page_break": True,
                "page_number_format": "第{page}页"
            }
        }
        
        if config_path is None:
            # 尝试从默认路径加载
            config_file = Path("config/case_types/financing_lease.json")
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        return config
                except Exception as e:
                    logger.warning(f"加载配置文件失败: {e}")
            return default_config
        
        config_file = Path(config_path)
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载配置文件失败: {e}")
        
        return default_config

    def _load_anonymization_map(self, stage0_data: Optional[Dict]):
        """加载脱敏替换映射"""
        if stage0_data is None:
            try:
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
        # 检查plan结构：可能是 {"0.2_anonymization_plan": {...}} 或直接是 {...}
        if "0.2_anonymization_plan" in plan:
            anonymization_plan = plan["0.2_anonymization_plan"]
        else:
            # 数据直接在根级别
            anonymization_plan = plan
        
        # 处理公司Profile库
        company_profiles = anonymization_plan.get("公司Profile库", {})
        for key, company in company_profiles.items():
            anonymized = company.get("原脱敏标识")
            real_name = company.get("公司名称")
            if anonymized and real_name:
                self.anonymization_map[anonymized] = real_name
        
        # 处理人物Profile库
        person_profiles = anonymization_plan.get("人物Profile库", {})
        for key, person in person_profiles.items():
            anonymized = person.get("原脱敏标识")
            real_name = person.get("姓名")
            if anonymized and real_name:
                self.anonymization_map[anonymized] = real_name
        
        # 从替换映射表添加更多映射
        replace_map = anonymization_plan.get("替换映射表", {})
        for placeholder, real_value in replace_map.items():
            if placeholder and real_value:
                self.anonymization_map[placeholder] = real_value

    def deanonymize_text(self, text: str) -> str:
        """反脱敏：将脱敏标记替换为真实名称"""
        if not text:
            return text

        result = text
        
        # 第一步：先进行增强反脱敏（处理复杂模式）
        result = self._enhanced_deanonymize(result)
        
        # 第二步：按长度降序排列，先替换长的标记
        # 跳过长度小于3的标记，但保留人物名称（以"某"结尾的模式）
        sorted_markers = sorted(
            [(k, v) for k, v in self.anonymization_map.items() if len(k) >= 3 or k.endswith('某')],
            key=lambda x: len(x[0]),
            reverse=True
        )
        for marker, real_name in sorted_markers:
            result = result.replace(marker, real_name)
        
        # 第三步：清理Markdown表格
        result = self._clean_markdown_tables(result)
        
        # 第四步：清理无关内容（大模型前缀、质量检查报告等）
        result = self._clean_irrelevant_content(result)
        
        return result
    
    def _clean_irrelevant_content(self, text: str) -> str:
        """清理与大模型相关的无关内容"""
        # 清理大模型前缀
        prefixes = [
            r'^好的，我将作为专业的法律文书生成助手，.*?\n',
            r'^好的，.*?生成助手，.*?\n',
            r'^我将作为.*?生成助手，.*?\n',
            r'^以下是根据.*?生成的内容[：:]\s*\n',
            r'^根据您的要求，.*?\n',
            r'^按您的要求，.*?\n',
            r'^请您审核以下内容[：:]\s*\n',
        ]
        for prefix in prefixes:
            text = re.sub(prefix, '', text, flags=re.MULTILINE | re.DOTALL)
        
        # 清理质量检查报告部分
        # 匹配 "生成完成与质量检查报告" 到下一个文件或结束
        text = re.sub(
            r'生成完成与质量检查报告\s*\n.*?(?=\n文件\d+：|$)',
            '',
            text,
            flags=re.DOTALL
        )
        
        # 清理 "一致性及格式规范性检查报告" 及其后续内容（如果是独立部分）
        text = re.sub(
            r'一致性及格式规范性检查报告\s*\n.*?(?=\n文件\d+：|$)',
            '',
            text,
            flags=re.DOTALL
        )
        
        # 清理质量检查相关的标记
        text = re.sub(r'✅ 即时检查.*?(?=\n|$)', '', text)
        text = re.sub(r'· ✅ .*?(?=\n|$)', '', text)
        
        # 清理多余的空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _clean_markdown_tables(self, text: str) -> str:
        """清理Markdown表格，将表格转换为纯文本格式"""
        lines = text.split('\n')
        result_lines = []
        in_table = False
        table_rows = []
        
        for line in lines:
            # 检测表格行（以 | 开头或结尾，且包含 | 分隔）
            if '|' in line and (line.strip().startswith('|') or line.strip().endswith('|')):
                # 跳过表头分隔行（如 |:---|）
                if re.match(r'^\s*\|?\s*[:\-\s]+\s*\|', line):
                    continue
                in_table = True
                table_rows.append(line)
            else:
                if in_table and table_rows:
                    # 将表格转换为纯文本
                    for row in table_rows:
                        cols = [c.strip() for c in row.strip('|').split('|')]
                        # 添加列数据，用 " / " 分隔
                        result_lines.append(' | '.join(cols))
                        result_lines.append('\n')
                    table_rows = []
                    in_table = False
                # 保留原行和换行符
                result_lines.append(line)
                result_lines.append('\n')
        
        # 处理最后可能残留的表格
        if in_table and table_rows:
            for row in table_rows:
                result_lines.append(row)
                result_lines.append('\n')
        
        text = ''.join(result_lines)
        
        # 去除多余空行（3个以上换行 -> 2个）
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text
    
    def _enhanced_deanonymize(self, text: str) -> str:
        """增强反脱敏：处理不一致的脱敏模式"""
        # 收集所有真实信息
        all_real_names = []
        
        for anonymized, real_name in self.anonymization_map.items():
            if real_name and "某某" not in real_name:
                all_real_names.append(real_name)
        
        # 模式1: 处理"X某"（如"张伟某" -> "张伟"）- 必须最先处理
        for name in all_real_names:
            if name and len(name) >= 2:
                pattern = re.escape(name) + r'某'
                text = re.sub(pattern + r'([^\w])', name + r'\1', text)
                text = re.sub(pattern + r'$', name, text)
        
        # 模式2: 处理常见脱敏人名
        text = re.sub(r'张伟某', '张伟', text)
        text = re.sub(r'李某某', '李明', text)
        
        # 模式3: 处理地址脱敏 - 多种模式匹配
        address_replacements = [
            # 上海地址 - 完整模式
            (r'上海市某某区某某路某某号', '上海市浦东新区世纪大道100号'),
            (r'上海市浦东新区某某路某某号', '上海市浦东新区世纪大道100号'),
            (r'上海市某某路某某号', '上海市浦东新区世纪大道100号'),
            (r'上海市浦东新区世纪大道\d+号', '上海市浦东新区世纪大道100号'),
            # 南昌地址 - 多种模式
            (r'江西省某某市某某区某某路某某号', '江西省南昌市红谷滩新区赣江中大道1888号'),
            (r'江西省南昌市某某区某某路某某号', '江西省南昌市红谷滩新区赣江中大道1888号'),
            (r'江西省南昌市某某路某某号', '江西省南昌市红谷滩新区赣江中大道1888号'),
            (r'南昌市某某区某某路某某号', '江西省南昌市红谷滩新区赣江中大道1888号'),
            # 深圳地址
            (r'广东省某某市某某区某某路某某号', '广东省深圳市福田区深南大道6008号'),
            (r'广东省深圳市某某区某某路某某号', '广东省深圳市福田区深南大道6008号'),
            (r'广东省深圳市某某路某某号', '广东省深圳市福田区深南大道6008号'),
            # 更通用的模式 - 处理残留的某某
            (r'某某路', '路'),
            (r'某某号', '号'),
        ]
        
        for pattern, replacement in address_replacements:
            text = re.sub(pattern, replacement, text)
        
        # 模式4: 处理证书编号模式
        certificate_replacements = [
            (r'（2022）XXX证执行字第35号', '（2022）沪东证执行字第35号'),
            (r'（2021）XXX证经字第1643号', '（2021）沪东证经字第1643号'),
            (r'（2021）XXX证经字第1644号', '（2021）沪东证经字第1644号'),
            (r'（2021）XXX证经字第1645号', '（2021）沪东证经字第1645号'),
            (r'（2021）XXX证经字第1646号', '（2021）沪东证经字第1646号'),
            (r'赣\（2021）南昌市不动产证名第XXXXXXX号', '赣（2021）南昌市不动产证明第0123456号'),
            (r'赣\（2016）南昌市不动产权第XXXXXXX号', '赣（2016）南昌市不动产权第0789012号'),
            (r'JRRZ\(21\)XXXXXXX', 'JRRZ(21)20210224'),
            (r'JRRZ\(21\)XXXXXXX-GM001', 'JRRZ(21)20210224-GM001'),
            (r'JRRZ\(21\)XXXXXXX-DY001', 'JRRZ(21)20210224-DY001'),
            # 统一社会信用代码中的XX
            (r'MA1昌盛XX', 'MA1HA12345'),
            (r'MA1XXXXXX', 'MA1HA12345'),
        ]
        
        for pattern, replacement in certificate_replacements:
            text = re.sub(pattern, replacement, text)
        
        # 模式5: 处理LLM自行创造的脱敏名称 (BUG-010)
        llm_patterns = [
            # 处理 "张伟 (公司2)" -> "张伟"
            (r'张伟\s*\(公司\d+\)', '张伟'),
            # 处理 "张海峰 (公司6)" -> "张海峰"
            (r'张海峰\s*\(公司\d+\)', '张海峰'),
            # 处理 "长江某有限公司" -> 根据上下文查找真实公司名
            (r'长江某有限公司', '南昌宏昌商业零售有限公司'),
            # 处理 "华鑫某" 模式
            (r'华鑫某有限公司', '东方国际融资租赁有限公司'),
        ]
        
        for pattern, replacement in llm_patterns:
            text = re.sub(pattern, replacement, text)
        
        # 模式6: 清理残余脱敏标记 - 只清理明显的占位符
        text = re.sub(r'某某某', '', text)

        # 模式7: 清理LLM生成的异常模式
        # 清理 "某地址" -> "地址："（LLM错误地在地址标签前加了"某"）
        text = re.sub(r'）某地址：', '）地址：', text)
        text = re.sub(r'\d法定代表人：某地址：', '法定代表人：', text)
        text = re.sub(r'）某地址', '）地址', text)
        text = re.sub(r'某地址：', '地址：', text)

        # 清理 "某某区" 等残留
        text = re.sub(r'某某区', '', text)

        return text

    def _setup_pdf(self):
        """初始化PDF文档"""
        self._register_chinese_fonts()

        self.doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=A4,
            rightMargin=2.5*cm,
            leftMargin=2.5*cm,
            topMargin=2.5*cm,
            bottomMargin=2.5*cm
        )

        self.styles = getSampleStyleSheet()
        self._setup_styles()

        self.elements = []

        self.page_width = A4[0]
        self.page_height = A4[1]
        self.content_width = self.page_width - 5*cm

    def _register_chinese_fonts(self):
        """注册中文字体"""
        try:
            font_paths = [
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/STHeiti Light.ttc",
                "/System/Library/Fonts/STHeiti Medium.ttc",
            ]

            font_registered = False
            for font_path in font_paths:
                if Path(font_path).exists():
                    try:
                        from reportlab.pdfbase.ttfonts import TTFont
                        from reportlab.pdfbase import pdfmetrics
                        
                        font_name = "ChineseFont"
                        pdfmetrics.registerFont(TTFont(font_name, font_path))
                        self.font_name = font_name
                        font_registered = True
                        logger.info(f"已注册中文字体: {font_path}")
                        break
                    except Exception as e:
                        logger.warning(f"字体 {font_path} 注册失败: {e}")
                        continue

            if not font_registered:
                self.font_name = "Helvetica"
                logger.warning("未找到中文字体，将使用默认字体")
        except Exception as e:
            logger.warning(f"字体注册失败: {e}")
            self.font_name = "Helvetica"

    def _setup_styles(self):
        """设置PDF样式"""
        self.styles.add(ParagraphStyle(
            name='ChineseBody',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=10,
            leading=16,
            alignment=TA_JUSTIFY,
        ))

        self.styles.add(ParagraphStyle(
            name='DocTitle',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=24,
            leading=36,
            alignment=TA_CENTER,
            spaceAfter=30,
        ))

        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=18,
            leading=28,
            alignment=TA_LEFT,
            spaceBefore=20,
            spaceAfter=15,
        ))

        self.styles.add(ParagraphStyle(
            name='SubsectionTitle',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=14,
            leading=22,
            alignment=TA_LEFT,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.black,
        ))

        self.styles.add(ParagraphStyle(
            name='EvidenceTitle',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=12,
            leading=20,
            alignment=TA_LEFT,
            spaceBefore=10,
            spaceAfter=8,
            textColor=colors.black,
        ))

    def generate_complete_docket(
        self,
        stage0_data: Dict[str, Any],
        evidence_index: Dict[str, Any],
        complaint_text: str = "",
        procedural_text: str = ""
    ):
        """生成完整卷宗PDF"""
        logger.info("开始生成完整卷宗PDF")

        self._add_cover(stage0_data)

        self._add_table_of_contents(evidence_index)

        self.add_page_break()
        self._add_stage1_content(stage0_data, evidence_index, complaint_text, procedural_text)

        self.add_page_break()
        self._add_stage2_content(stage0_data, evidence_index)

        self.add_page_break()
        self._add_stage3_content(stage0_data)

        self.doc.build(self.elements)
        logger.success(f"PDF已生成: {self.output_path}")

    def _add_cover(self, stage0_data: Dict[str, Any]):
        """添加封面"""
        # 从配置读取封面设置
        output_config = self.config.get("output_structure", {})
        cover_config = output_config.get("cover_page", {})
        
        title = cover_config.get("title", "案件卷宗")
        
        self.add_title(title, 'DocTitle')
        self.add_spacer(2)

        case_info = stage0_data.get("0.1_structured_extraction", {}).get("案件基本信息", {})
        
        court = case_info.get("受理法院", "未指定法院")
        case_no = case_info.get("案号", "（未指定案号）")
        case_type = self.config.get("case_type_name", "金融纠纷")

        self.add_paragraph(f"案件类型：{case_type}", 'ChineseBody')
        self.add_paragraph(f"受理法院：{court}", 'ChineseBody')
        self.add_paragraph(f"案号：{case_no}", 'ChineseBody')
        self.add_spacer(2)

        from datetime import datetime
        self.add_paragraph(f"生成时间：{datetime.now().strftime('%Y年%m月%d日')}", 'ChineseBody')
        self.add_spacer(2)

        court = case_info.get("受理法院", "上海金融法院")
        case_no = case_info.get("案号", "（2024）沪74民初XXX号")

        self.add_paragraph(f"案件类型：金融借款合同纠纷", 'ChineseBody')
        self.add_paragraph(f"受理法院：{court}", 'ChineseBody')
        self.add_paragraph(f"案号：{case_no}", 'ChineseBody')
        self.add_spacer(2)

        from datetime import datetime
        self.add_paragraph(f"生成时间：{datetime.now().strftime('%Y年%m月%d日')}", 'ChineseBody')

    def _add_table_of_contents(self, evidence_index: Dict[str, Any]):
        """添加目录"""
        self.add_title("目  录", 'SectionTitle')
        self.add_spacer(0.5)

        self.add_paragraph("第一部分 原告起诉包", 'ChineseBody')
        evidence_list = evidence_index.get("证据列表", [])
        plaintiff_evidence = [e for e in evidence_list if e.get("归属方") == "原告"]

        groups = {}
        for e in plaintiff_evidence:
            group_id = e.get("证据组", 0)
            if group_id not in groups:
                groups[group_id] = []
            groups[group_id].append(e)

        for group_id in sorted(groups.keys()):
            group_evidence = groups[group_id]
            self.add_paragraph(f"  证据组{group_id}（{len(group_evidence)}个证据）", 'ChineseBody')
            for e in group_evidence:
                self.add_paragraph(f"    {e['证据ID']} {e['证据名称']}", 'ChineseBody')

        self.add_spacer(0.5)
        self.add_paragraph("第二部分 被告答辩包", 'ChineseBody')
        defendant_evidence = [e for e in evidence_list if e.get("归属方") == "被告"]

        if defendant_evidence:
            for e in defendant_evidence:
                self.add_paragraph(f"  {e['证据ID']} {e['证据名称']}", 'ChineseBody')
        else:
            self.add_paragraph("  （被告未提交证据）", 'ChineseBody')

        self.add_spacer(0.5)
        self.add_paragraph("第三部分 法院审理包", 'ChineseBody')
        self.add_paragraph("  1. 庭审笔录", 'ChineseBody')
        self.add_paragraph("  2. 判决书（脱敏版）", 'ChineseBody')

    def _add_stage1_content(
        self,
        stage0_data: Dict[str, Any],
        evidence_index: Dict[str, Any],
        complaint_text: str,
        procedural_text: str
    ):
        """添加阶段1内容"""
        self.add_title("第一部分 原告起诉包", 'SectionTitle')
        self.add_spacer(0.5)

        self.add_title("一、民事起诉状", 'SubsectionTitle')
        if complaint_text:
            deanonymized = self.deanonymize_text(complaint_text)
            self.add_paragraph(deanonymized)
        else:
            self.add_paragraph("（民事起诉状内容）")

        self.add_spacer(0.5)

        self.add_title("二、证据材料", 'SubsectionTitle')

        evidence_list = evidence_index.get("证据列表", [])
        plaintiff_evidence = [e for e in evidence_list if e.get("归属方") == "原告"]

        groups = {}
        for e in plaintiff_evidence:
            group_id = e.get("证据组", 0)
            if group_id not in groups:
                groups[group_id] = []
            groups[group_id].append(e)

        for group_id in sorted(groups.keys()):
            group_evidence = groups[group_id]

            self.add_title(f"证据组{group_id}", 'SubsectionTitle')

            # 检查是否需要每份证据另起一页
            evidence_page_break = self.config.get("output_structure", {}).get("evidence_page_break", True)
            
            for i, evidence in enumerate(group_evidence):
                # 每份证据另起一页（第一份证据在证据组标题后，不需要分页）
                if i > 0 and evidence_page_break:
                    self.add_page_break()
                self._add_evidence(evidence)
            
            # 证据组1之后添加附件（租赁物清单和抵押物清单）
            if group_id == 1:
                self.add_page_break()
                self._add_rental_list(stage0_data)
                self.add_spacer(0.5)
                self._add_collateral_list(stage0_data)
                self.add_spacer(0.5)
        
        self.add_spacer(0.5)
        
        # 添加租金支付计划表格
        self._add_rent_payment_table(stage0_data)
        
        self.add_spacer(0.5)
        
        self.add_title("三、程序性文件", 'SubsectionTitle')
        if procedural_text:
            deanonymized = self.deanonymize_text(procedural_text)
            self.add_paragraph(deanonymized)
        else:
            self.add_paragraph("（程序性文件内容）")

    def _add_stage2_content(
        self,
        stage0_data: Dict[str, Any],
        evidence_index: Dict[str, Any]
    ):
        """添加阶段2内容"""
        self.add_title("第二部分 被告答辩包", 'SectionTitle')
        self.add_spacer(0.5)

        self.add_title("一、民事答辩状", 'SubsectionTitle')
        self.add_paragraph("（被告答辩状内容）")

        self.add_spacer(0.5)

        self.add_title("二、证据材料", 'SubsectionTitle')

        evidence_list = evidence_index.get("证据列表", [])
        defendant_evidence = [e for e in evidence_list if e.get("归属方") == "被告"]

        if defendant_evidence:
            for evidence in defendant_evidence:
                self._add_evidence(evidence)
        else:
            self.add_paragraph("（被告未提交证据）")

    def _add_stage3_content(self, stage0_data: Dict[str, Any]):
        """添加阶段3内容"""
        self.add_title("第三部分 法院审理包", 'SectionTitle')
        self.add_spacer(0.5)

        self.add_title("一、庭审笔录", 'SubsectionTitle')
        self.add_paragraph("（庭审笔录内容）")

        self.add_spacer(0.5)

        self.add_title("二、判决书（脱敏版）", 'SubsectionTitle')
        self.add_paragraph("（判决书脱敏版内容）")

    def _add_evidence(self, evidence: Dict[str, Any]):
        """添加单个证据"""
        evidence_title = f"{evidence['证据ID']} {evidence['证据名称']}"
        self.add_title(evidence_title, 'EvidenceTitle')

        file_path = evidence.get("文件路径", "")
        if file_path and Path(file_path).exists():
            content = Path(file_path).read_text(encoding='utf-8')
            deanonymized = self.deanonymize_text(content)
            self.add_paragraph(deanonymized)
        else:
            self.add_paragraph("（证据文件不存在）")

        self.add_spacer(0.3)
    
    def _add_rental_list(self, stage0_data: Dict[str, Any]):
        """添加租赁物清单"""
        key_numbers = stage0_data.get("0.4_key_numbers", {})
        rental_list = key_numbers.get("租赁物清单", [])
        
        if not rental_list:
            return
        
        self.add_title("附件一：租赁物清单", 'SubsectionTitle')
        
        # 获取样式
        styles = self.styles
        
        # 构建表格数据 - 使用Paragraph包裹长文本
        table_data = []
        # 表头
        header_row = []
        for col in ["序号", "名称", "规格型号", "数量", "存放地点", "评估价值"]:
            header_row.append(Paragraph(col, styles['ChineseBody']))
        table_data.append(header_row)
        
        for item in rental_list:
            # 反脱敏处理存放地点
            location = item.get("存放地点", "")
            if location:
                location = self.deanonymize_text(location)
            
            row = [
                Paragraph(str(item.get("序号", "")), styles['ChineseBody']),
                Paragraph(item.get("名称", ""), styles['ChineseBody']),
                Paragraph(item.get("规格型号", ""), styles['ChineseBody']),
                Paragraph(item.get("数量", ""), styles['ChineseBody']),
                Paragraph(location, styles['ChineseBody']),
                Paragraph(f"{item.get('评估价值', 0):,.0f}元", styles['ChineseBody']) if isinstance(item.get('评估价值'), (int, float)) else Paragraph(str(item.get("评估价值", "")), styles['ChineseBody'])
            ]
            table_data.append(row)
        
        # 创建表格
        col_widths = [0.8, 3.0, 2.0, 1.2, 3.5, 2.0]
        table = Table(table_data, colWidths=[w*cm for w in col_widths])
        
        # 设置表格样式
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'ChineseFont'),
            ('FONTNAME', (0, 1), (-1, -1), 'ChineseFont'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        self.elements.append(table)
    
    def _add_collateral_list(self, stage0_data: Dict[str, Any]):
        """添加抵押物清单"""
        key_numbers = stage0_data.get("0.4_key_numbers", {})
        collateral_list = key_numbers.get("抵押物清单", [])
        
        if not collateral_list:
            return
        
        self.add_title("附件二：抵押物清单", 'SubsectionTitle')
        
        # 获取样式
        styles = self.styles
        
        # 构建表格数据 - 使用Paragraph包裹长文本
        table_data = []
        # 表头
        header_row = []
        for col in ["序号", "名称", "不动产权证号", "地址", "建筑面积", "评估价值", "产权人"]:
            header_row.append(Paragraph(col, styles['ChineseBody']))
        table_data.append(header_row)
        
        for item in collateral_list:
            # 反脱敏处理产权人
            owner = item.get("产权人", "")
            if owner:
                owner = self.deanonymize_text(owner)
            
            row = [
                Paragraph(str(item.get("序号", "")), styles['ChineseBody']),
                Paragraph(item.get("名称", ""), styles['ChineseBody']),
                Paragraph(item.get("不动产权证号", ""), styles['ChineseBody']),
                Paragraph(item.get("地址", ""), styles['ChineseBody']),
                Paragraph(f"{item.get('建筑面积', 0)}㎡", styles['ChineseBody']),
                Paragraph(f"{item.get('评估价值', 0):,.0f}元", styles['ChineseBody']) if isinstance(item.get('评估价值'), (int, float)) else Paragraph(str(item.get("评估价值", "")), styles['ChineseBody']),
                Paragraph(owner, styles['ChineseBody'])
            ]
            table_data.append(row)
        
        # 创建表格 - 调整列宽
        col_widths = [0.8, 2.8, 2.8, 4.0, 1.2, 1.8, 1.2]
        table = Table(table_data, colWidths=[w*cm for w in col_widths])
        
        # 设置表格样式
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'ChineseFont'),
            ('FONTNAME', (0, 1), (-1, -1), 'ChineseFont'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        self.elements.append(table)
    
    def _add_rent_payment_table(self, stage0_data: Dict[str, Any]):
        """添加租金支付计划表格"""
        key_numbers = stage0_data.get("0.4_key_numbers", {})
        rent_plan = key_numbers.get("租金支付计划", [])
        
        if not rent_plan:
            return
        
        self.add_title("租金支付计划表", 'SubsectionTitle')
        
        # 构建表格数据
        table_data = []
        # 表头
        table_data.append(["期数", "应付日期", "租金金额", "本金金额", "利息金额", "支付状态"])
        
        for item in rent_plan:
            rent_amount = item.get("租金金额") or {}
            principal_amount = item.get("本金金额") or {}
            interest_amount = item.get("利息金额") or {}
            
            # 安全格式化金额
            rent_value = rent_amount.get('数值', 0)
            if isinstance(rent_value, (int, float)):
                rent_str = f"{rent_value:,.2f}{rent_amount.get('单位', '元')}"
            else:
                rent_str = str(rent_value)
                
            principal_value = principal_amount.get('数值', 0)
            if isinstance(principal_value, (int, float)):
                principal_str = f"{principal_value:,.2f}{principal_amount.get('单位', '元')}"
            else:
                principal_str = str(principal_value)
                
            interest_value = interest_amount.get('数值', 0)
            if isinstance(interest_value, (int, float)):
                interest_str = f"{interest_value:,.2f}{interest_amount.get('单位', '元')}"
            else:
                interest_str = str(interest_value)
            
            table_data.append([
                str(item.get("期数", "")),
                item.get("应付日期", ""),
                rent_str,
                principal_str,
                interest_str,
                item.get("支付状态", "")
            ])
        
        # 创建表格
        col_widths = [1.2*cm, 2.2*cm, 2.5*cm, 2.5*cm, 2.5*cm, 1.8*cm]
        table = Table(table_data, colWidths=col_widths)
        
        # 设置表格样式
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'ChineseFont'),
            ('FONTNAME', (0, 1), (-1, -1), 'ChineseFont'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ]))
        
        self.elements.append(table)
        self.add_spacer(0.3)

    def add_title(self, text: str, style_name: str):
        """添加标题"""
        deanonymized = self.deanonymize_text(text)
        paragraph = Paragraph(deanonymized, self.styles[style_name])
        self.elements.append(paragraph)

    def add_paragraph(self, text: str, style_name: str = 'ChineseBody'):
        """添加段落"""
        clean_text = self._clean_text(text)
        deanonymized = self.deanonymize_text(clean_text)

        lines = deanonymized.split('\n')
        for line in lines:
            line = line.strip()
            if line:
                paragraph = Paragraph(line, self.styles[style_name])
                self.elements.append(paragraph)

    def add_spacer(self, count: float = 1):
        """添加间距"""
        self.elements.append(Spacer(1, count*cm))

    def add_page_break(self):
        """添加分页"""
        self.elements.append(PageBreak())

    def _clean_text(self, text: str) -> str:
        """清理文本中的特殊字符"""
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
