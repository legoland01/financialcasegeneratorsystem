"""完整测试脚本 - 使用文本内容直接测试"""
import sys
import os
import json
from pathlib import Path

# 添加src到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from loguru import logger

# API配置
OPENAI_API_KEY = "sk-fjephnssumhgkxhakpxlfrqayiuckkyogvwkchqutqolqilk"
OPENAI_API_BASE = "https://api.siliconflow.cn/v1"
OPENAI_MODEL = "deepseek-ai/DeepSeek-V3.2"

# 设置环境变量
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["OPENAI_API_BASE"] = OPENAI_API_BASE


# 测试用的判决书文本（简化版本，用于快速测试）
SAMPLE_JUDGMENT = """(2024)沪74民初245号

原告：上海XX融资租赁有限公司，住所地上海市浦东新区XX路XX号。
法定代表人：张XX，该公司总经理。
委托代理人：李XX，上海XX律师事务所律师。

被告：浙江XX机械制造有限公司，住所地浙江省杭州市XX区XX路XX号。
法定代表人：王XX，该公司总经理。

案由：融资租赁合同纠纷

原告诉称：原告与被告签订《融资租赁合同》，约定被告向原告租赁一批生产设备。合同约定租赁期限为24个月，租金总额为500万元。被告已支付部分租金，但仍拖欠租金300万元。原告多次催讨未果，遂诉至法院。

原告向本院提出诉讼请求：
1. 判令被告支付剩余租金人民币300万元；
2. 判令被告支付逾期利息人民币10万元；
3. 本案诉讼费用由被告承担。

被告辩称：对拖欠租金的事实无异议，但因经营困难，请求减免利息。

经审理查明：2023年1月15日，原告与被告签订《融资租赁合同》，约定被告向原告租赁一批生产设备，租赁期限24个月，租金总额500万元。被告已支付租金200万元，尚欠300万元。

本院认为：原告与被告签订的《融资租赁合同》合法有效，双方均应按约履行。被告未按约支付租金，构成违约，应承担相应的违约责任。

判决如下：
一、被告浙江XX机械制造有限公司于本判决生效之日起十日内向原告上海XX融资租赁有限公司支付租金人民币300万元；
二、被告浙江XX机械制造有限公司于本判决生效之日起十日内向原告上海XX融资租赁有限公司支付逾期利息人民币10万元；
三、本案案件受理费30800元，由被告负担。
"""


def test_full_workflow(judgment_text: str):
    """执行完整的工作流测试"""
    logger.info("=" * 60)
    logger.info("开始执行完整工作流测试")
    logger.info("=" * 60)
    
    try:
        from src.services import Stage0Service, Stage1Service
        from src.utils import LLMClient
        
        # 创建LLM客户端
        llm_client = LLMClient(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            api_base=OPENAI_API_BASE
        )
        
        # ==================== 阶段0：判决书解析与全局规划 ====================
        logger.info("")
        logger.info("=" * 60)
        logger.info("【阶段0】判决书解析与全局规划")
        logger.info("=" * 60)
        
        stage0_service = Stage0Service(llm_client=llm_client)
        stage0_result = stage0_service.run_all(judgment_text)
        
        logger.success("【阶段0】完成！")
        logger.info(f"📁 结果已保存到: outputs/analysis_results.json")
        
        # 保存到测试输出
        test_output_path = Path("outputs/test_stage0_result.json")
        with open(test_output_path, 'w', encoding='utf-8') as f:
            json.dump(stage0_result, f, ensure_ascii=False, indent=2)
        logger.info(f"📁 测试结果已保存到: {test_output_path}")
        
        # ==================== 阶段1：原告起诉包生成 ====================
        logger.info("")
        logger.info("=" * 60)
        logger.info("【阶段1】原告起诉包生成")
        logger.info("=" * 60)
        
        stage1_service = Stage1Service(llm_client=llm_client)
        stage1_result = stage1_service.run_all(stage0_result)
        
        logger.success("【阶段1】完成！")
        logger.info(f"📁 结果已保存到: outputs/stage1/plaintiff_package.json")
        
        # ==================== 阶段2：被告答辩包生成 ====================
        logger.info("")
        logger.info("=" * 60)
        logger.info("【阶段2】被告答辩包生成")
        logger.info("=" * 60)
        
        from src.services import Stage2Service
        stage2_service = Stage2Service(llm_client=llm_client)
        stage2_result = stage2_service.run_all(stage0_result)
        
        logger.success("【阶段2】完成！")
        logger.info(f"📁 结果已保存到: outputs/stage2/defendant_package.json")
        
        # ==================== 阶段3：法院审理包生成 ====================
        logger.info("")
        logger.info("=" * 60)
        logger.info("【阶段3】法院审理包生成")
        logger.info("=" * 60)
        
        from src.services import Stage3Service
        stage3_service = Stage3Service(llm_client=llm_client)
        stage3_result = stage3_service.run_all(judgment_text, stage0_result)
        
        logger.success("【阶段3】完成！")
        logger.info(f"📁 结果已保存到: outputs/stage3/court_package.json")
        
        # ==================== 测试总结 ====================
        logger.info("")
        logger.info("=" * 60)
        logger.info("🎉 测试总结")
        logger.info("=" * 60)
        logger.success("✅ 所有阶段测试通过！")
        logger.info(f"📁 输出目录: {Path('outputs').absolute()}")
        logger.info("")
        logger.info("生成的文件:")
        logger.info("  1. outputs/analysis_results.json - 阶段0完整结果")
        logger.info("  2. outputs/stage0/ - 阶段0各子任务结果")
        logger.info("  3. outputs/stage1/ - 阶段1生成文件（原告包）")
        logger.info("  4. outputs/stage2/ - 阶段2生成文件（被告包）")
        logger.info("  5. outputs/stage3/ - 阶段3生成文件（法院包）")
        logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("金融案件测试数据生成系统 - 完整测试")
    logger.info("=" * 60)
    logger.info(f"API配置:")
    logger.info(f"  API Base: {OPENAI_API_BASE}")
    logger.info(f"  Model: {OPENAI_MODEL}")
    logger.info("=" * 60)
    print()
    
    logger.info("📄 使用示例判决书文本进行测试")
    logger.info(f"文本长度: {len(SAMPLE_JUDGMENT)} 字符")
    print()
    
    # 执行完整测试
    success = test_full_workflow(SAMPLE_JUDGMENT)
    
    return success


if __name__ == "__main__":
    success = main()
    
    if success:
        logger.info("")
        logger.success("🎉 恭喜！金融案件测试数据生成系统测试完成！")
        logger.success("✅ 所有功能运行正常")
        logger.info("")
        logger.info("接下来您可以：")
        logger.info("  1. 查看 outputs/ 目录下的生成文件")
        logger.info("  2. 启动API服务: python main.py")
        logger.info("  3. 使用真实的判决书PDF文件进行测试")
        logger.info("")
        sys.exit(0)
    else:
        logger.error("❌ 测试失败")
        sys.exit(1)
