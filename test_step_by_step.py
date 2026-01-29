"""简化测试脚本 - 分步测试"""
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


def test_api_connection():
    """测试API连接"""
    logger.info("=" * 50)
    logger.info("测试1：API连接")
    logger.info("=" * 50)
    
    try:
        from src.utils import LLMClient
        
        llm_client = LLMClient(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            api_base=OPENAI_API_BASE
        )
        
        logger.info("发送简单请求...")
        response = llm_client.generate("你好，请用一句话介绍你自己。")
        
        logger.success(f"✅ API连接成功！")
        logger.info(f"响应: {response}")
        return True
    except Exception as e:
        logger.error(f"❌ API连接失败: {e}")
        return False


def test_simple_extraction():
    """测试简单的结构化提取"""
    logger.info("")
    logger.info("=" * 50)
    logger.info("测试2：简单结构化提取")
    logger.info("=" * 50)
    
    try:
        from src.utils import LLMClient, parse_llm_json_response, load_prompt_template
        
        llm_client = LLMClient(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            api_base=OPENAI_API_BASE
        )
        
        # 使用简化的判决书
        simple_judgment = """(2024)沪74民初245号

原告：上海XX融资租赁有限公司，住所地上海市浦东新区XX路XX号。
法定代表人：张XX，该公司总经理。

被告：浙江XX机械制造有限公司，住所地浙江省杭州市XX区XX路XX号。
法定代表人：王XX，该公司总经理。

案由：融资租赁合同纠纷

原告向本院提出诉讼请求：
1. 判令被告支付租金人民币500万元；
2. 判令被告支付违约金人民币50万元；
3. 本案诉讼费用由被告承担。"""
        
        # 加载提示词
        prompt_path = Path("prompts/stage0/0.1_结构化提取.md")
        if not prompt_path.exists():
            logger.error(f"提示词文件不存在: {prompt_path}")
            return False
        
        prompt = load_prompt_template(str(prompt_path))
        
        # 构建完整提示词（简化版）
        full_prompt = f"""{prompt}

原始判决书文本：
{simple_judgment}

请按照上述要求生成标准JSON格式的输出。"""
        
        logger.info("调用LLM生成结构化提取结果...")
        response = llm_client.generate(full_prompt)
        
        logger.info("响应长度: " + str(len(response)) + " 字符")
        
        # 解析JSON
        result = parse_llm_json_response(response)
        
        if result:
            logger.success("✅ 成功解析JSON结果")
            
            # 保存结果
            output_path = Path("outputs/simple_extraction_result.json")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.success(f"✅ 结果已保存到: {output_path}")
            return True
        else:
            logger.error("❌ JSON解析失败")
            
            # 保存原始响应
            output_path = Path("outputs/simple_response.txt")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(response)
            
            logger.info(f"原始响应已保存到: {output_path}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 简单提取测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("金融案件测试数据生成系统 - 分步测试")
    logger.info("=" * 50)
    logger.info(f"API配置:")
    logger.info(f"  API Base: {OPENAI_API_BASE}")
    logger.info(f"  Model: {OPENAI_MODEL}")
    logger.info("=" * 50)
    print()
    
    # 测试1: API连接
    test1_ok = test_api_connection()
    print()
    
    # 测试2: 简单提取
    test2_ok = test_simple_extraction()
    print()
    
    # 总结
    logger.info("=" * 50)
    logger.info("测试总结")
    logger.info("=" * 50)
    
    if test1_ok and test2_ok:
        logger.success("✅ 所有测试通过！")
        logger.success("系统运行正常！")
        logger.info("")
        logger.info("下一步:")
        logger.info("  1. 查看 outputs/ 目录下的生成文件")
        logger.info("  2. 使用完整PDF进行测试")
        logger.info("  3. 启动API服务: python main.py")
        sys.exit(0)
    else:
        logger.error("❌ 测试未全部通过")
        if not test1_ok:
            logger.error("  - API连接失败")
        if not test2_ok:
            logger.error("  - 简单提取失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
