"""标准答案集生成器 - 从阶段0数据生成标准答案集"""
import json
from pathlib import Path
from typing import Dict, Any

from loguru import logger


class AnswerKeyGenerator:
    """标准答案集生成器"""

    def __init__(self, llm_client, output_dir: str):
        """
        初始化标准答案集生成器

        Args:
            llm_client: LLM客户端
            output_dir: 输出目录
        """
        self.llm_client = llm_client
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_answer_key(self, stage0_data: Dict, stage1_data: Dict = None,
                             stage2_data: Dict = None) -> Dict:
        """
        生成标准答案集

        Args:
            stage0_data: 阶段0数据
            stage1_data: 阶段1数据（可选）
            stage2_data: 阶段2数据（可选）

        Returns:
            标准答案集数据
        """
        logger.info("开始生成标准答案集...")

        # 生成各部分数据
        case_info = self._generate_case_info(stage0_data)
        claims = self._generate_claims(stage0_data, stage1_data)
        defenses = self._generate_defenses(stage0_data, stage2_data)
        key_numbers = self._generate_key_numbers(stage0_data)
        calculations = self._generate_calculations(stage0_data)
        court_findings = self._generate_court_findings(stage0_data)
        timeline = self._generate_timeline(stage0_data)

        # 整合为标准答案集
        answer_key = {
            "案件基本信息": case_info,
            "原告诉讼请求": claims,
            "被告抗辩意见": defenses,
            "关键金额清单": key_numbers,
            "详细计算过程": calculations,
            "法院认定": court_findings,
            "关键时间线": timeline
        }

        # 保存JSON格式
        json_path = self.output_dir / "标准答案集.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(answer_key, f, ensure_ascii=False, indent=2)

        logger.success(f"标准答案集JSON已保存: {json_path}")

        return answer_key

    def _generate_case_info(self, stage0_data: Dict) -> Dict:
        """生成案件基本信息"""
        extraction = stage0_data.get("0.1_structured_extraction", {})
        
        # 如果extraction直接包含案件基本信息（没有嵌套），使用它
        # 否则，尝试从嵌套结构中获取
        if "案件基本信息" in extraction:
            case_info_raw = extraction.get("案件基本信息", {})
        else:
            case_info_raw = extraction
        
        case_info = {
            "案号": case_info_raw.get("案号", ""),
            "法院": case_info_raw.get("法院", ""),
            "案由": case_info_raw.get("案由", ""),
            "程序": case_info_raw.get("程序", ""),
            "立案日期": case_info_raw.get("立案日期", ""),
            "开庭日期": case_info_raw.get("开庭日期", ""),
            "判决日期": case_info_raw.get("判决日期", ""),
            "合议庭": self._format_collegial_body(case_info_raw.get("合议庭") or {})
        }

        # 添加当事人信息
        parties = case_info_raw.get("当事人信息", {}) or extraction.get("当事人信息", {})
        if parties:
            case_info["原告信息"] = parties.get("原告", [])
            case_info["被告信息"] = parties.get("被告", [])

        return case_info

    def _format_collegial_body(self, collegial_body: Dict) -> str:
        """格式化合议庭信息"""
        if not collegial_body:
            return ""
        
        parts = []
        
        # 审判长
        president = collegial_body.get("审判长", "")
        if president:
            parts.append(f"审判长：{president}")
        
        # 审判员
        judges = collegial_body.get("审判员", [])
        if judges:
            if isinstance(judges, list):
                judges_str = "、".join(judges)
            else:
                judges_str = str(judges)
            parts.append(f"审判员：{judges_str}")
        
        # 人民陪审员
        jurors = collegial_body.get("人民陪审员", [])
        if jurors:
            if isinstance(jurors, list):
                jurors_str = "、".join(jurors)
            else:
                jurors_str = str(jurors)
            parts.append(f"人民陪审员：{jurors_str}")
        
        # 书记员
        clerk = collegial_body.get("书记员", "")
        if clerk:
            parts.append(f"书记员：{clerk}")
        
        return " | ".join(parts)

    def _generate_claims(self, stage0_data: Dict, stage1_data: Dict = None) -> Dict:
        """生成原告诉讼请求"""
        extraction = stage0_data.get("0.1_structured_extraction", {})
        
        claims = {}
        
        # 从阶段1数据提取
        if stage1_data:
            complaint_file = Path("outputs/stage1/民事起诉状.txt")
            if complaint_file.exists():
                with open(complaint_file, 'r', encoding='utf-8') as f:
                    complaint_text = f.read()
                
                claims["诉讼请求文本"] = complaint_text
        
        # 如果没有阶段1数据，从阶段0提取
        if not claims:
            claims_text = extraction.get("原告诉讼请求", "")
            if claims_text:
                claims["诉讼请求文本"] = claims_text
            else:
                # 生成默认文本
                claims["诉讼请求文本"] = self._generate_default_claims(extraction)
        
        return claims

    def _generate_default_claims(self, extraction: Dict) -> str:
        """生成默认的诉讼请求文本"""
        basic_info = extraction.get("案件基本信息", {})
        parties = extraction.get("当事人信息", {})
        
        plaintiff = parties.get("原告", [{}])[0] if parties.get("原告") else {}
        defendant = parties.get("被告", [{}])[0] if parties.get("被告") else {}
        
        plaintiff_name = plaintiff.get("名称", "原告")
        defendant_name = defendant.get("名称", "被告")
        
        return f"""民事起诉状

原告：{plaintiff_name}
住所：{plaintiff.get("住所", "")}
法定代表人：{plaintiff.get("法定代表人", "")}

被告：{defendant_name}
住所：{defendant.get("住所", "")}
法定代表人：{defendant.get("法定代表人", "")}

诉讼请求：
1. 判令被告向原告支付未付租金人民币元；
2. 判令被告向原告支付逾期利息人民币元；
3. 判令被告承担本案诉讼费用。

事实与理由：
（根据案件具体情况填写）
"""

    def _generate_defenses(self, stage0_data: Dict, stage2_data: Dict = None) -> Dict:
        """生成被告抗辩意见"""
        extraction = stage0_data.get("0.1_structured_extraction", {})
        
        defenses = {}
        
        # 从阶段2数据提取
        if stage2_data:
            defense_file = Path("outputs/stage2/民事答辩状.txt")
            if defense_file.exists():
                with open(defense_file, 'r', encoding='utf-8') as f:
                    defense_text = f.read()
                
                defenses["答辩意见文本"] = defense_text
        
        # 如果没有阶段2数据，从阶段0提取
        if not defenses:
            defense_text = extraction.get("被告抗辩意见", "")
            if defense_text:
                defenses["答辩意见文本"] = defense_text
        
        return defenses

    def _generate_key_numbers(self, stage0_data: Dict) -> Dict:
        """生成关键金额清单"""
        key_numbers = stage0_data.get("0.4_key_numbers", {})
        
        return {
            "合同基础金额": key_numbers.get("合同基础金额", {}),
            "租金安排": key_numbers.get("租金安排", {}),
            "租金支付计划": key_numbers.get("租金支付计划", []),
            "放款明细": key_numbers.get("放款明细", []),
            "保险理赔明细": key_numbers.get("保险理赔明细", []),
            "违约相关金额": key_numbers.get("违约相关金额", {}),
            "诉讼费用": key_numbers.get("诉讼费用", {}),
            "判决金额": key_numbers.get("判决金额", {}),
            "关键时间点": key_numbers.get("关键时间点", {})
        }

    def _generate_calculations(self, stage0_data: Dict) -> Dict:
        """生成详细计算过程"""
        key_numbers = stage0_data.get("0.4_key_numbers", {})
        
        violation_amounts = key_numbers.get("违约相关金额", {})
        litigation_costs = key_numbers.get("诉讼费用", {})
        time_points = key_numbers.get("关键时间点", {})

        calculations = {}

        # 获取数据，添加默认值处理
        overdue_rent_data = violation_amounts.get("逾期租金总额", {})
        overdue_rent = overdue_rent_data.get("数值", 0) if overdue_rent_data else 0
        
        overdue_interest_data = violation_amounts.get("逾期利息总额", {})
        overdue_interest = overdue_interest_data.get("数值", 0) if overdue_interest_data else 0
        
        violation_method = violation_amounts.get("违约金计算方式", "") or violation_amounts.get("计算依据", "")
        violation_date = time_points.get("违约发生日期", "") or time_points.get("租金逾期起始日期", "主合同到期日")

        calculations["逾期利息计算"] = {
            "计算基数": f"{overdue_rent:,.2f} 元" if isinstance(overdue_rent, (int, float)) else f"{overdue_rent} 元",
            "利率": "每日万分之五 (0.05%)",
            "起算日期": violation_date,
            "截止日期": "实际清偿之日",
            "计算公式": "逾期利息 = 逾期租金总额 × 日利率 × 逾期天数",
            "计算公式说明": "日利率 = 年利率 / 365 = 0.05% × 365 ≈ 18.25%",
            "计算结果": f"{overdue_interest:,.2f} 元" if isinstance(overdue_interest, (int, float)) else f"{overdue_interest} 元",
            "计算依据": violation_method if violation_method else "根据《融资租赁合同》约定"
        }

        # 违约金计算
        penalty_amount = violation_amounts.get("违约金总额", {}).get("数值", 0)

        calculations["违约金计算"] = {
            "计算基数": f"{overdue_rent:,.2f} 元" if isinstance(overdue_rent, (int, float)) else f"{overdue_rent} 元",
            "违约金比例": "0%（本案无违约金约定）",
            "计算公式": "违约金 = 逾期金额 × 违约金比例",
            "计算结果": f"{penalty_amount:,.2f} 元" if isinstance(penalty_amount, (int, float)) else "0 元",
            "说明": "本案合同仅约定逾期利息，未约定违约金"
        }

        # 诉讼费用计算
        case_fee = litigation_costs.get("案件受理费", {}).get("数值", 0)
        preservation_fee = litigation_costs.get("保全费", {}).get("数值", 0)
        lawyer_fee = litigation_costs.get("律师费", {}).get("数值", 0)

        # 计算其他费用合计
        other_fees = litigation_costs.get("其他费用", [])
        other_fees_total = sum(
            item.get("金额", {}).get("数值", 0)
            for item in other_fees
            if isinstance(item, dict) and "金额" in item
        ) if other_fees else 0

        litigation_total = (case_fee or 0) + (preservation_fee or 0) + (lawyer_fee or 0) + other_fees_total

        calculations["诉讼费用计算"] = {
            "案件受理费": f"{case_fee:,.2f} 元" if isinstance(case_fee, (int, float)) else f"{case_fee} 元",
            "保全费": f"{preservation_fee:,.2f} 元" if isinstance(preservation_fee, (int, float)) else f"{preservation_fee} 元",
            "律师费": f"{lawyer_fee:,.2f} 元" if isinstance(lawyer_fee, (int, float)) else f"{lawyer_fee} 元",
            "其他费用": f"{other_fees_total:,.2f} 元" if isinstance(other_fees_total, (int, float)) else f"{other_fees_total} 元",
            "合计": f"{litigation_total:,.2f} 元" if isinstance(litigation_total, (int, float)) else f"{litigation_total} 元",
            "其他费用明细": [
                f"{item.get('费用名称', '费用')}: {item.get('金额', {}).get('数值', 0):,.2f} 元"
                for item in other_fees
                if isinstance(item, dict)
            ] if other_fees else []
        }

        return calculations

    def _generate_court_findings(self, stage0_data: Dict) -> Dict:
        """生成法院认定部分"""
        extraction = stage0_data.get("0.1_structured_extraction", {})
        
        court_findings = extraction.get("法院认定部分", {})
        
        return {
            "本院认为": court_findings.get("本院认为", ""),
            "判决结果": court_findings.get("判决结果", ""),
            "诉讼费用负担": court_findings.get("诉讼费用负担", "")
        }

    def _generate_timeline(self, stage0_data: Dict) -> Dict:
        """生成关键时间线"""
        reconstruction = stage0_data.get("0.3_transaction_reconstruction", {})
        
        return {
            "交易时间线": reconstruction.get("交易时间线", []),
            "关键时间点": stage0_data.get("0.4_key_numbers", {}).get("关键时间点", {})
        }
