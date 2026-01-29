"""快速测试脚本 - 使用API直接测试"""
import sys
import os
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


def quick_test():
    """快速测试LLM连接和基本功能"""
    logger.info("开始快速测试...")
    
    try:
        from src.utils import LLMClient
        
        # 创建LLM客户端
        llm_client = LLMClient(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            api_base=OPENAI_API_BASE
        )
        
        logger.info(f"LLM客户端初始化成功")
        logger.info(f"  API Base: {OPENAI_API_BASE}")
        logger.info(f"  Model: {OPENAI_MODEL}")
        
        # 测试简单查询
        logger.info("发送测试请求...")
        test_prompt = "请用一句话介绍你自己。"
        response = llm_client.generate(test_prompt)
        
        logger.success(f"LLM响应: {response}")
        logger.success("快速测试通过！")
        
        return True
        
    except Exception as e:
        logger.error(f"快速测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stage0_sample():
    """测试阶段0的简单样本"""
    logger.info("=" * 50)
    logger.info("开始测试阶段0（简化版本）")
    logger.info("=" * 50)
    
    # 简化的判决书文本
    sample_judgment = """
(2024)沪74民初245号

原告：上海XX融资租赁有限公司，住所地上海市浦东新区XX路XX号。
法定代表人：张XX，该公司总经理。
委托代理人：李XX，上海XX律师事务所律师。

被告：浙江XX机械制造有限公司，住所地浙江省杭州市XX区XX路XX号。
法定代表人：王XX，该公司总经理。

案由：融资租赁合同纠纷

原告向本院提出诉讼请求：
1. 判令被告支付租金人民币500万元；
2. 判令被告支付违约金人民币50万元；
3. 本案诉讼费用由被告承担。
"""
    
    try:
        from src.utils import LLMClient, load_prompt_template, save_json
        
        # 创建LLM客户端
        llm_client = LLMClient(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            api_base=OPENAI_API_BASE
        )
        
        # 加载提示词
        prompt_path = Path("prompts/stage0/0.1_结构化提取.md")
        if not prompt_path.exists():
            logger.error(f"提示词文件不存在: {prompt_path}")
            return False
        
        prompt = load_prompt_template(str(prompt_path))
        
        # 构建完整提示词
        full_prompt = f"""
{prompt}

原始判决书文本：
{sample_judgment}

请按照上述要求生成标准JSON格式的输出。
"""
        
        logger.info("调用LLM生成结构化提取结果...")
        response = llm_client.generate(full_prompt)
        
        logger.info("响应内容:")
        print(response)
        print()
        
        # 尝试解析JSON
        from src.utils import parse_llm_json_response
        
        result = parse_llm_json_response(response)
        if result:
            logger.success("成功解析JSON结果")
        else:
            logger.error("JSON解析失败")
                    else:
                        logger.error("未找到JSON格式的内容")
                        result = None
            else:
                # 方法3: 提取大括号内的内容
                json_match = re.search(r'\{[\s\S]*\}', response, re.DOTALL)
                if json_match:
                    try:
                        # 尝试修复常见的JSON格式问题
                        json_str = json_match.group()
                        # 修复缩进问题
                        json_str = re.sub(r'\n\s{0,1}(\S)', r'\n    \1', json_str)
                        # 修复多余逗号
                        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
                        result = json.loads(json_str)
                        logger.success("成功解析JSON结果（修复后）")
                    except Exception as e:
                        logger.error(f"JSON解析失败: {e}")
                        logger.info("使用模拟结果")
                        result = None
                else:
                    logger.error("未找到JSON格式的内容")
                    result = None
            
            # 保存结果
            output_path = Path("outputs/test_result.json")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.success(f"结果已保存到: {output_path}")
            return True
        else:
            logger.warning("未找到JSON格式的响应")
            return False
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("金融案件测试数据生成系统 - 快速测试")
    logger.info("=" * 50)
    logger.info(f"API配置:")
    logger.info(f"  API Base: {OPENAI_API_BASE}")
    logger.info(f"  Model: {OPENAI_MODEL}")
    logger.info("=" * 50)
    print()
    
    # 先进行快速测试
    quick_ok = quick_test()
    print()
    
    if quick_ok:
        # 测试阶段0
        stage0_ok = test_stage0_sample()
        
        if stage0_ok:
            logger.success("=" * 50)
            logger.success("所有测试通过！")
            logger.success("=" * 50)
            sys.exit(0)
        else:
            logger.error("阶段0测试失败")
            sys.exit(1)
    else:
        logger.error("快速测试失败，请检查API配置")
        sys.exit(1)
