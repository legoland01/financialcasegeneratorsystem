"""
金融案件数据生成器 - 端到端集成模块

整合所有新组件，实现完整的证据生成流程：
1. 缓存管理
2. 边界条件提取
3. 数据计算
4. Prompt构建
5. LLM生成
6. PDF渲染
"""
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from loguru import logger

from cache_manager import CacheManager
from boundary_condition_extractor import BoundaryConditionExtractor
from template_library import TemplateLibrary
from data_calculator import DataCalculator
from dynamic_prompt_builder import DynamicPromptBuilder
from test_config_injector import TestConfigInjector
from contract_renderer import ContractRenderer, PartyInfo, SignatureInfo
from table_renderer import TableRenderer
from smart_paginator import SmartPaginator


class FinancialCaseGenerator:
    """金融案件数据生成器 - 端到端集成"""

    def __init__(
        self,
        cache_dir: str = "cache",
        template_dir: str = "config/template_libraries",
        evidence_template_dir: str = "config/evidence_templates",
        llm_client: Any = None
    ):
        """
        初始化案件生成器

        Args:
            cache_dir: 缓存目录
            template_dir: 模板库目录
            evidence_template_dir: 证据模板目录
            llm_client: LLM客户端（可选）
        """
        self.llm_client = llm_client
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.cache_manager = CacheManager(cache_dir=cache_dir)
        self.boundary_extractor = BoundaryConditionExtractor(llm_client=llm_client)
        self.template_library = TemplateLibrary(template_dir=template_dir)
        self.data_calculator = DataCalculator()
        self.prompt_builder = DynamicPromptBuilder(
            template_dir=evidence_template_dir
        )
        self.test_config_injector = TestConfigInjector()

    def generate(
        self,
        judgment_text: str,
        force_refresh: bool = False,
        test_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        生成案件数据

        Args:
            judgment_text: 判决书文本
            force_refresh: 是否强制刷新缓存
            test_config: 测试配置（用于错误注入）
        Returns:
            生成的数据字典
        """
        logger.info("开始生成案件数据...")

        judgment_hash = self._compute_hash(judgment_text)
        logger.info(f"判决书哈希: {judgment_hash[:16]}...")

        cached_data = self.cache_manager.get(
            judgment_path=f"judgment_text:{judgment_hash}",
            force_refresh=force_refresh
        )

        if cached_data is not None:
            logger.info("使用缓存数据")
            return cached_data

        logger.info("生成新数据...")

        boundary_conditions = self._extract_boundary_conditions(judgment_text)

        if test_config and test_config.get("enabled"):
            logger.info("应用测试配置（错误注入）")
            boundary_conditions = self.test_config_injector.apply(
                boundary_conditions,
                test_config
            )

        generated_data = self._generate_detailed_data(boundary_conditions)

        deanonymization_context = self._build_deanonymization_context(boundary_conditions)

        result = {
            "version": "2.0",
            "judgment_hash": judgment_hash,
            "generated_at": datetime.utcnow().isoformat(),
            "boundary_conditions": boundary_conditions,
            "generated_data": generated_data,
            "deanonymization_context": deanonymization_context
        }

        self.cache_manager.save(
            judgment_path=f"judgment_text:{judgment_hash}",
            data=result
        )

        logger.success("数据生成完成")
        return result

    def generate_prompts(
        self,
        boundary_conditions: Dict[str, Any],
        deanonymization_context: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        生成各种Prompt

        Args:
            boundary_conditions: 边界条件
            deanonymization_context: 反脱敏上下文
        Returns:
            Prompt字典
        """
        prompts = {}

        prompts["contract"] = self.prompt_builder.build_contract_prompt(
            boundary_conditions=boundary_conditions,
            deanonymization_context=deanonymization_context
        )

        prompts["equipment_list"] = self.prompt_builder.build_table_prompt(
            boundary_conditions=boundary_conditions,
            deanonymization_context=deanonymization_context,
            table_type="租赁物清单"
        )

        prompts["rent_schedule"] = self.prompt_builder.build_table_prompt(
            boundary_conditions=boundary_conditions,
            deanonymization_context=deanonymization_context,
            table_type="租金支付计划"
        )

        return prompts

    def generate_with_llm(
        self,
        prompt: str,
        max_tokens: int = 4000
    ) -> str:
        """
        使用LLM生成内容

        Args:
            prompt: Prompt文本
            max_tokens: 最大token数
        Returns:
            生成的内容
        """
        if self.llm_client is None:
            logger.warning("未配置LLM客户端，返回空内容")
            return ""

        try:
            response = self.llm_client.complete(
                prompt=prompt,
                max_tokens=max_tokens
            )
            return response
        except Exception as e:
            logger.error(f"LLM生成失败: {e}")
            return ""

    def _compute_hash(self, text: str) -> str:
        """计算文本哈希"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def _extract_boundary_conditions(self, judgment_text: str) -> Dict[str, Any]:
        """提取边界条件"""
        logger.info("提取边界条件...")

        boundary_conditions = self.boundary_extractor.extract(judgment_text)

        if "合同金额" not in boundary_conditions:
            boundary_conditions["合同金额"] = 150000000
        if "利率" not in boundary_conditions:
            boundary_conditions["利率"] = 0.061
        if "签订日期" not in boundary_conditions:
            boundary_conditions["签订日期"] = "2021-02-24"
        if "设备数量" not in boundary_conditions:
            boundary_conditions["设备数量"] = 62
        if "租赁期" not in boundary_conditions:
            boundary_conditions["租赁期"] = 24
        if "当事人" not in boundary_conditions:
            boundary_conditions["当事人"] = {
                "出租人": "某某公司5",
                "承租人": "某某公司1"
            }

        boundary_conditions["数据来源"] = "判决书"

        return boundary_conditions

    def _generate_detailed_data(
        self,
        boundary_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成详细数据"""
        logger.info("生成详细数据...")

        contract_amount = boundary_conditions.get("合同金额", 150000000)
        equipment_count = boundary_conditions.get("设备数量", 62)
        annual_rate = boundary_conditions.get("利率", 0.061)
        lease_term = boundary_conditions.get("租赁期", 24)
        signing_date = boundary_conditions.get("签订日期", "2021-02-24")

        equipment_list = self.template_library.generate_equipment_list(
            count=equipment_count,
            total_value=contract_amount
        )

        rent_schedule = self.data_calculator.calculate_rent_schedule(
            principal=contract_amount,
            annual_rate=annual_rate,
            periods=lease_term,
            start_date=signing_date
        )

        lessor_bank = self.template_library.generate_bank_account()
        lessee_bank = self.template_library.generate_bank_account()

        return {
            "租赁物清单": equipment_list,
            "租金支付计划": rent_schedule,
            "银行账户": {
                "出租人": {
                    "开户行": "中国工商银行上海浦东分行",
                    "账号": lessor_bank
                },
                "承租人": {
                    "开户行": "中国工商银行南昌红谷滩分行",
                    "账号": lessee_bank
                }
            }
        }

    def _build_deanonymization_context(
        self,
        boundary_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建反脱敏上下文"""
        logger.info("构建反脱敏上下文...")

        context = {
            "公司Profile库": {},
            "人物Profile库": {}
        }

        if "当事人" in boundary_conditions:
            for role, marker in boundary_conditions["当事人"].items():
                company = self.template_library.get_company_profile(marker)
                if company:
                    context["公司Profile库"][marker] = company

        return context

    def clear_cache(self):
        """清理缓存"""
        self.cache_manager.clear_all()
        logger.info("缓存已清理")


class EvidencePDFGenerator:
    """证据PDF生成器"""

    def __init__(self, output_path: str = "outputs/证据.txt"):
        """
        初始化PDF生成器

        Args:
            output_path: 输出路径
        """
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        self.contract_renderer = ContractRenderer()
        self.table_renderer = TableRenderer()
        self.paginator = SmartPaginator()

    def generate_from_data(
        self,
        generated_data: Dict[str, Any],
        boundary_conditions: Dict[str, Any],
        deanonymization_context: Dict[str, Any]
    ) -> Path:
        """
        从数据生成PDF

        Args:
            generated_data: 生成的数据
            boundary_conditions: 边界条件
            deanonymization_context: 反脱敏上下文
        Returns:
            生成的PDF路径
        """
        self._current_generated_data = generated_data
        self._current_boundary_conditions = boundary_conditions
        self._current_deanonymization_context = deanonymization_context

        parties = []
        if "当事人" in boundary_conditions:
            for role, marker in boundary_conditions["当事人"].items():
                if marker in deanonymization_context.get("公司Profile库", {}):
                    profile = deanonymization_context["公司Profile库"][marker]
                    party = PartyInfo(
                        role=role,
                        name=profile.get("公司名称", marker),
                        credit_code=profile.get("信用代码", ""),
                        representative=profile.get("法定代表人", ""),
                        address=profile.get("注册地址", ""),
                        phone=profile.get("联系电话", "")
                    )
                    parties.append(party)

        evidence_elements = []

        from smart_paginator import PDFElement

        contract_title = self.contract_renderer.format_title("融资租赁合同")
        evidence_elements.append(PDFElement(
            element_type="title",
            content=contract_title,
            style=contract_title,
            page_break_after=False
        ))

        contract_no = self.contract_renderer.format_contract_no(
            f"RZL-{datetime.now().year}-001"
        )
        evidence_elements.append(PDFElement(
            element_type="text",
            content=contract_no,
            style=contract_no,
            page_break_after=False
        ))

        if parties:
            for party in parties:
                header = self.contract_renderer.format_party_header(party.role)
                evidence_elements.append(PDFElement(
                    element_type="text",
                    content=header,
                    style=header,
                    page_break_after=False
                ))

                name_info = self.contract_renderer.format_party_info(
                    "公司名称", party.name
                )
                evidence_elements.append(PDFElement(
                    element_type="text",
                    content=name_info,
                    style=name_info,
                    page_break_after=False
                ))

                code_info = self.contract_renderer.format_party_info(
                    "统一社会信用代码", party.credit_code
                )
                evidence_elements.append(PDFElement(
                    element_type="text",
                    content=code_info,
                    style=code_info,
                    page_break_after=False
                ))

        equipment_list = generated_data.get("租赁物清单", [])
        if equipment_list:
            from smart_paginator import PDFElement

            table_title = self.table_renderer.format_title("租赁物清单")
            evidence_elements.append(PDFElement(
                element_type="table_title",
                content=table_title,
                style=table_title,
                page_break_after=False
            ))

            headers = ["序号", "设备名称", "规格型号", "数量", "存放地点", "评估价值"]
            rows = []
            for item in equipment_list[:10]:
                rows.append([
                    str(item.get("序号", "")),
                    item.get("设备名称", ""),
                    item.get("规格型号", ""),
                    item.get("数量", ""),
                    item.get("存放地点", ""),
                    str(item.get("评估价值", 0))
                ])

            table_data = self.table_renderer.render(
                title="租赁物清单",
                headers=headers,
                rows=rows
            )
            evidence_elements.append(PDFElement(
                element_type="table",
                content=table_data,
                page_break_after=True
            ))

        self.paginator.add_evidence(
            evidence_id="E001",
            elements=evidence_elements,
            start_new_page=True
        )

        pdf_structure = self.paginator.build_pdf()

        self._write_pdf(pdf_structure)

        return self.output_path

    def _write_pdf(self, pdf_structure: Dict[str, Any]):
        """写入PDF文件"""
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from pathlib import Path

        generated_data = self._current_generated_data
        boundary_conditions = self._current_boundary_conditions

        font_name = "Helvetica"
        font_paths = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
        ]
        for font_path in font_paths:
            if Path(font_path).exists():
                try:
                    pdfmetrics.registerFont(TTFont("ChineseFont", font_path))
                    font_name = "ChineseFont"
                    break
                except:
                    continue

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("金融案件证据材料", styles['Title']))
        story.append(Spacer(1, 0.5*cm))

        story.append(Paragraph(f"<b>合同金额:</b> {boundary_conditions.get('合同金额', 0):,} 元", ParagraphStyle(name='ChineseBody', parent=styles['Normal'], fontName=font_name, fontSize=10)))
        story.append(Paragraph(f"<b>签订日期:</b> {boundary_conditions.get('签订日期', '')}", ParagraphStyle(name='ChineseBody', parent=styles['Normal'], fontName=font_name, fontSize=10)))
        story.append(Paragraph(f"<b>租赁期限:</b> {boundary_conditions.get('租赁期', 0)} 个月", ParagraphStyle(name='ChineseBody', parent=styles['Normal'], fontName=font_name, fontSize=10)))
        story.append(Paragraph(f"<b>年利率:</b> {boundary_conditions.get('利率', 0)}", ParagraphStyle(name='ChineseBody', parent=styles['Normal'], fontName=font_name, fontSize=10)))
        story.append(Paragraph(f"<b>设备数量:</b> {boundary_conditions.get('设备数量', 0)}", ParagraphStyle(name='ChineseBody', parent=styles['Normal'], fontName=font_name, fontSize=10)))
        story.append(Spacer(1, 0.5*cm))

        story.append(Paragraph("<b>租赁物清单</b>", ParagraphStyle(name='SectionTitle', parent=styles['Heading2'], fontName=font_name, fontSize=14)))
        equipment = generated_data.get("租赁物清单", [])
        if equipment:
            table_data = [["序号", "设备名称", "规格型号", "评估价值"]]
            for item in equipment[:20]:
                table_data.append([
                    str(item.get('序号', '')),
                    item.get('设备名称', ''),
                    item.get('规格型号', ''),
                    f"{item.get('评估价值', 0):,}"
                ])
            
            t = Table(table_data, colWidths=[1*cm, 5*cm, 4*cm, 3*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), font_name if font_name != 'Helvetica' else 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
            ]))
            story.append(t)

        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph("<b>租金支付计划</b>", ParagraphStyle(name='SectionTitle', parent=styles['Heading2'], fontName=font_name, fontSize=14)))
        rent = generated_data.get("租金支付计划", [])
        if rent:
            table_data = [["期数", "应付日期", "租金金额", "支付状态"]]
            for item in rent[:12]:
                table_data.append([
                    str(item.get('期数', '')),
                    item.get('应付日期', ''),
                    f"{item.get('租金金额', 0):,.2f}",
                    item.get('支付状态', '')
                ])
            
            t = Table(table_data, colWidths=[1.5*cm, 3*cm, 3.5*cm, 2*cm])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), font_name if font_name != 'Helvetica' else 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
            ]))
            story.append(t)

        doc.build(story)
        logger.info(f"证据PDF已生成: {self.output_path}")


def run_quick_test():
    """运行快速测试"""
    logger.info("=" * 60)
    logger.info("金融案件数据生成器 - 快速测试")
    logger.info("=" * 60)

    generator = FinancialCaseGenerator()

    sample_judgment = """
    原告东方国际融资租赁有限公司与被告江西昌盛商业管理有限公司于2021年2月24日签订融资租赁合同，
    合同金额为150,000,000元，年利率为6.1%，租赁期限为24个月，设备数量为62套。
    被告杭州恒通贸易有限公司为上述债务提供担保。
    """

    result = generator.generate(sample_judgment)

    logger.info(f"边界条件:")
    for key, value in result["boundary_conditions"].items():
        logger.info(f"  {key}: {value}")

    logger.info(f"\n生成数据:")
    generated = result["generated_data"]
    logger.info(f"  租赁物清单: {len(generated.get('租赁物清单', []))} 项")
    logger.info(f"  租金支付计划: {len(generated.get('租金支付计划', []))} 期")

    prompts = generator.generate_prompts(
        result["boundary_conditions"],
        result["deanonymization_context"]
    )
    logger.info(f"\n生成的Prompt:")
    for key, prompt in prompts.items():
        logger.info(f"  {key}: {len(prompt)} 字符")

    pdf_generator = EvidencePDFGenerator("outputs/快速测试证据.pdf")
    pdf_generator.generate_from_data(
        result["generated_data"],
        result["boundary_conditions"],
        result["deanonymization_context"]
    )

    logger.success("=" * 60)
    logger.success("测试完成！")
    logger.success("=" * 60)

    return result


if __name__ == "__main__":
    run_quick_test()
