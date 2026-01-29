#!/usr/bin/env python3
"""
金融案件数据生成系统 - v2.0

集成新组件的完整系统：
1. 缓存管理 - 避免重复LLM调用
2. 边界条件提取 - 从判决书提取关键数据
3. 数据计算 - 租金计划、设备清单自动生成
4. Prompt构建 - 注入反脱敏上下文
5. 证据生成 - 起诉状、答辩状、庭审记录

使用方法：
    python3 run_v2.py                      # 执行所有阶段
    python3 run_v2.py --stage 0            # 只执行阶段0
    python3 run_v2.py --force-refresh      # 强制刷新缓存
    python3 run_v2.py --test-config xxx    # 应用测试配置
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(src_path / "utils"))

from loguru import logger
from cache_manager import CacheManager
from boundary_condition_extractor import BoundaryConditionExtractor
from template_library import TemplateLibrary
from data_calculator import DataCalculator
from dynamic_prompt_builder import DynamicPromptBuilder
from test_config_injector import TestConfigInjector


class FinancialCaseGeneratorV2:
    """金融案件生成器 v2.0"""

    def __init__(
        self,
        cache_dir: str = "cache",
        template_dir: str = "config/template_libraries",
        evidence_template_dir: str = "config/evidence_templates",
        llm_client: Any = None
    ):
        self.llm_client = llm_client
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.cache_manager = CacheManager(cache_dir=cache_dir)
        self.boundary_extractor = BoundaryConditionExtractor(llm_client=llm_client)
        self.template_library = TemplateLibrary(template_dir=template_dir)
        self.data_calculator = DataCalculator()
        self.prompt_builder = DynamicPromptBuilder(template_dir=evidence_template_dir)
        self.test_config_injector = TestConfigInjector()

    def generate(
        self,
        judgment_text: str,
        force_refresh: bool = False,
        test_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """生成完整案件数据"""
        import hashlib

        judgment_hash = hashlib.sha256(judgment_text.encode('utf-8')).hexdigest()
        cache_key = f"judgment:{judgment_hash}"

        cached_data = self.cache_manager.get(cache_key, force_refresh=force_refresh)
        if cached_data is not None:
            logger.info("使用缓存数据")
            return cached_data

        logger.info("生成新数据...")

        boundary_conditions = self.boundary_extractor.extract(judgment_text)

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

        self.cache_manager.save(cache_key, result)
        return result

    def _generate_detailed_data(
        self,
        boundary_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成详细数据"""
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

    def generate_prompts(
        self,
        boundary_conditions: Dict[str, Any],
        deanonymization_context: Dict[str, Any]
    ) -> Dict[str, str]:
        """生成各种Prompt"""
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


def generate_complaint(
    boundary_conditions: Dict[str, Any],
    deanonymization_context: Dict[str, Any],
    generated_data: Dict[str, Any],
    llm_client: Any = None
) -> str:
    """生成民事起诉状"""
    if llm_client is None:
        return _generate_complaint_template(boundary_conditions, deanonymization_context, generated_data)

    try:
        from utils.dynamic_prompt_builder import DynamicPromptBuilder
        prompt_builder = DynamicPromptBuilder()

        prompt = prompt_builder.build_prompt(
            task_type="生成民事起诉状",
            boundary_conditions=boundary_conditions,
            deanonymization_context=deanonymization_context,
            template_name="complaint_template.md"
        )

        response = llm_client.generate(prompt=prompt, max_tokens=4000)
        return response
    except Exception as e:
        logger.error(f"LLM生成起诉状失败: {e}")
        return _generate_complaint_template(boundary_conditions, deanonymization_context, generated_data)


def _generate_complaint_template(
    boundary_conditions: Dict[str, Any],
    deanonymization_context: Dict[str, Any],
    generated_data: Dict[str, Any]
) -> str:
    """模板生成起诉状"""
    lessor = deanonymization_context.get("公司Profile库", {}).get(
        boundary_conditions.get("当事人", {}).get("出租人", ""),
        {}
    )
    lessee = deanonymization_context.get("公司Profile库", {}).get(
        boundary_conditions.get("当事人", {}).get("承租人", ""),
        {}
    )

    contract_amount = boundary_conditions.get("合同金额", 150000000)
    lease_term = boundary_conditions.get("租赁期", 24)
    annual_rate = boundary_conditions.get("利率", 0.061)
    signing_date = boundary_conditions.get("签订日期", "2021-02-24")

    return f"""民事起诉状

原告：{lessor.get('公司名称', '某某公司5')}
统一社会信用代码：{lessor.get('信用代码', '91310000MA1FL3L123')}
住所地：{lessor.get('注册地址', '上海市浦东新区世纪大道100号')}
法定代表人：{lessor.get('法定代表人', '周明远')}，职务：董事长

被告：{lessee.get('公司名称', '某某公司1')}
统一社会信用代码：{lessee.get('信用代码', '91360121MA1XXXXXX')}
住所地：{lessee.get('注册地址', '江西省南昌市红谷滩区XX路XX号')}
法定代表人：{lessee.get('法定代表人', '张伟')}，职务：执行董事

诉讼请求：
1. 判令被告立即向原告支付未付租金人民币{contract_amount:,.0f}元；
2. 判令被告向原告支付逾期利息（按日万分之五计算）；
3. 判令被告承担本案全部诉讼费用。

事实与理由：
{signing_date}，原告与被告签订《融资租赁合同》，约定：
- 融资金额：人民币{contract_amount:,.0f}元
- 租赁期限：{lease_term}个月
- 年利率：{annual_rate*100:.1f}%

原告依约支付了融资金额，但被告未按期支付租金。

此致
上海金融法院

附：证据清单
1. 融资租赁合同
2. 租赁物清单
3. 租金支付计划
4. 银行转账凭证
"""


def generate_defense(
    boundary_conditions: Dict[str, Any],
    deanonymization_context: Dict[str, Any],
    generated_data: Dict[str, Any],
    llm_client: Any = None
) -> str:
    """生成民事答辩状"""
    if llm_client is None:
        return _generate_defense_template(boundary_conditions, deanonymization_context, generated_data)

    try:
        from utils.dynamic_prompt_builder import DynamicPromptBuilder
        prompt_builder = DynamicPromptBuilder()

        prompt = prompt_builder.build_prompt(
            task_type="生成民事答辩状",
            boundary_conditions=boundary_conditions,
            deanonymization_context=deanonymization_context,
            template_name="defense_template.md"
        )

        response = llm_client.generate(prompt=prompt, max_tokens=4000)
        return response
    except Exception as e:
        logger.error(f"LLM生成答辩状失败: {e}")
        return _generate_defense_template(boundary_conditions, deanonymization_context, generated_data)


def _generate_defense_template(
    boundary_conditions: Dict[str, Any],
    deanonymization_context: Dict[str, Any],
    generated_data: Dict[str, Any]
) -> str:
    """模板生成答辩状"""
    lessor = deanonymization_context.get("公司Profile库", {}).get(
        boundary_conditions.get("当事人", {}).get("出租人", ""),
        {}
    )
    lessee = deanonymization_context.get("公司Profile库", {}).get(
        boundary_conditions.get("当事人", {}).get("承租人", ""),
        {}
    )

    return f"""民事答辩状

答辩人：{lessee.get('公司名称', '某某公司1')}
统一社会信用代码：{lessee.get('信用代码', '91360121MA1XXXXXX')}
住所地：{lessee.get('注册地址', '江西省南昌市红谷滩区XX路XX号')}

被答辩人：{lessor.get('公司名称', '某某公司5')}
统一社会信用代码：{lessor.get('信用代码', '91310000MA1FL3L123')}

答辩意见：
答辩人对原告的诉讼请求有异议，理由如下：
1. 原告计算的租金金额有误；
2. 被告已支付部分租金，应予扣除；
3. 逾期利息计算标准过高。

综上，请求法院依法查明事实，驳回原告不合理的诉讼请求。

此致
上海金融法院
"""


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='金融案件数据生成系统 v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python3 run_v2.py                      # 执行所有阶段
  python3 run_v2.py --stage 0            # 只执行数据生成
  python3 run_v2.py --force-refresh      # 强制刷新缓存
  python3 run_v2.py --test-config        # 使用测试配置
  python3 run_v2.py --no-llm             # 不使用LLM（快速模式）
        """
    )
    parser.add_argument(
        '--stage',
        type=str,
        default='all',
        help='执行阶段：0(数据生成), 1(起诉状), 2(答辩状), 3(庭审记录), all(全部)'
    )
    parser.add_argument(
        '--force-refresh',
        action='store_true',
        help='强制刷新缓存'
    )
    parser.add_argument(
        '--test-config',
        action='store_true',
        help='应用测试配置（错误注入）'
    )
    parser.add_argument(
        '--no-llm',
        action='store_true',
        help='不使用LLM（快速模式，使用模板生成）'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='outputs_v2',
        help='输出目录（默认：outputs_v2）'
    )
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
    logger.add(output_dir / "run_v2.log", rotation="10MB", encoding="utf-8")

    logger.info("=" * 60)
    logger.info("金融案件数据生成系统 v2.0")
    logger.info("=" * 60)
    logger.info(f"输出目录: {output_dir}")
    logger.info(f"阶段: {args.stage}")
    logger.info(f"强制刷新: {args.force_refresh}")
    logger.info(f"测试配置: {args.test_config}")
    logger.info(f"使用LLM: {not args.no_llm}")
    logger.info("=" * 60)

    sample_judgment = """
    原告东方国际融资租赁有限公司与被告江西昌盛商业管理有限公司于2021年2月24日签订融资租赁合同，
    合同金额为150,000,000元，年利率为6.1%，租赁期限为24个月，设备数量为62套。
    被告杭州恒通贸易有限公司为上述债务提供担保。
    """

    llm_client = None if args.no_llm else _create_llm_client()

    generator = FinancialCaseGeneratorV2()

    test_config = None
    if args.test_config:
        test_config = {
            "enabled": True,
            "description": "测试数据",
            "errors": [
                {
                    "target": "boundary_conditions.合同金额",
                    "operation": "multiply",
                    "value": 1.1
                }
            ]
        }

    result = generator.generate(
        sample_judgment,
        force_refresh=args.force_refresh,
        test_config=test_config
    )

    logger.info(f"边界条件:")
    for key, value in result["boundary_conditions"].items():
        if key not in ["当事人"]:
            logger.info(f"  {key}: {value}")

    logger.info(f"\n生成数据:")
    generated = result["generated_data"]
    logger.info(f"  租赁物清单: {len(generated.get('租赁物清单', []))} 项")
    logger.info(f"  租金支付计划: {len(generated.get('租金支付计划', []))} 期")

    if args.stage in ['all', '0']:
        logger.info("\n" + "=" * 60)
        logger.info("保存数据生成结果")
        logger.info("=" * 60)

        with open(output_dir / "boundary_conditions.json", 'w', encoding='utf-8') as f:
            json.dump(result["boundary_conditions"], f, ensure_ascii=False, indent=2)

        with open(output_dir / "generated_data.json", 'w', encoding='utf-8') as f:
            json.dump(result["generated_data"], f, ensure_ascii=False, indent=2)

        with open(output_dir / "deanonymization_context.json", 'w', encoding='utf-8') as f:
            json.dump(result["deanonymization_context"], f, ensure_ascii=False, indent=2)

        logger.success(f"数据已保存到: {output_dir}/")

    if args.stage in ['all', '1']:
        logger.info("\n" + "=" * 60)
        logger.info("生成民事起诉状")
        logger.info("=" * 60)

        complaint = generate_complaint(
            result["boundary_conditions"],
            result["deanonymization_context"],
            result["generated_data"],
            llm_client
        )

        with open(output_dir / "民事起诉状.txt", 'w', encoding='utf-8') as f:
            f.write(complaint)

        logger.success(f"起诉状已生成: {output_dir}/民事起诉状.txt")

    if args.stage in ['all', '2']:
        logger.info("\n" + "=" * 60)
        logger.info("生成民事答辩状")
        logger.info("=" * 60)

        defense = generate_defense(
            result["boundary_conditions"],
            result["deanonymization_context"],
            result["generated_data"],
            llm_client
        )

        with open(output_dir / "民事答辩状.txt", 'w', encoding='utf-8') as f:
            f.write(defense)

        logger.success(f"答辩状已生成: {output_dir}/民事答辩状.txt")

    if args.stage in ['all', '3']:
        logger.info("\n" + "=" * 60)
        logger.info("生成庭审记录")
        logger.info("=" * 60)

        court_record = _generate_court_record(
            result["boundary_conditions"],
            result["deanonymization_context"]
        )

        with open(output_dir / "庭审笔录.txt", 'w', encoding='utf-8') as f:
            f.write(court_record)

        logger.success(f"庭审记录已生成: {output_dir}/庭审笔录.txt")

    logger.info("\n" + "=" * 60)
    logger.success("执行完成！")
    logger.info("=" * 60)

    logger.info(f"\n生成的文件:")
    for f in sorted(output_dir.glob("*")):
        logger.info(f"  {f.name}")

    return True


def _create_llm_client():
    """创建LLM客户端"""
    try:
        from utils.llm import LLMClient
        return LLMClient(
            api_key="sk-fjephnssumhgkxhakpxlfrqayiuckkyogvwkchqutqolqilk",
            model="deepseek-ai/DeepSeek-V3.2",
            api_base="https://api.siliconflow.cn/v1",
            timeout=600.0
        )
    except Exception as e:
        logger.warning(f"无法创建LLM客户端: {e}")
        return None


def _generate_court_record(
    boundary_conditions: Dict[str, Any],
    deanonymization_context: Dict[str, Any]
) -> str:
    """生成庭审记录"""
    lessor = deanonymization_context.get("公司Profile库", {}).get(
        boundary_conditions.get("当事人", {}).get("出租人", ""),
        {}
    )
    lessee = deanonymization_context.get("公司Profile库", {}).get(
        boundary_conditions.get("当事人", {}).get("承租人", ""),
        {}
    )

    return f"""庭审笔录

案号：（2024）沪74民初XXX号
案由：融资租赁合同纠纷
开庭时间：2024年X月X日
开庭地点：上海金融法院第X法庭

审判长：XXX
审判员：XXX
书记员：XXX

原告：{lessor.get('公司名称', '某某公司5')}（委托代理人：XXX）
被告：{lessee.get('公司名称', '某某公司1')}（委托代理人：XXX）

审：核对当事人身份...
（身份核对过程略）

审：现在开庭...
原告陈述诉讼请求...
被告答辩...
法庭调查...
法庭辩论...
最后陈述...
休庭。

以上记录经当事人核对无误后签字。
"""


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
