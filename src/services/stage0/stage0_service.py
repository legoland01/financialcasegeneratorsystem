"""阶段0服务：判决书解析与全局规划"""
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger
import json

from src.utils import (
    load_prompt_template,
    load_json,
    save_json,
    LLMClient,
    check_generation_result
)


class Stage0Service:
    """阶段0服务"""
    
    def __init__(
        self,
        prompt_dir: str = "prompts",
        schema_dir: str = "schemas",
        output_dir: str = "outputs",
        llm_client: Optional[LLMClient] = None
    ):
        """
        初始化阶段0服务
        
        Args:
            prompt_dir: 提示词目录
            schema_dir: Schema目录
            output_dir: 输出目录
            llm_client: 大模型客户端
        """
        self.prompt_dir = Path(prompt_dir)
        self.schema_dir = Path(schema_dir)
        self.output_dir = Path(output_dir)
        self.llm_client = llm_client or LLMClient()
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run_subtask_0_1(self, judgment_text: str) -> Dict[str, Any]:
        """
        执行子任务0.1：结构化提取
        
        Args:
            judgment_text: 判决书文本
        
        Returns:
            结构化提取结果
        """
        logger.info("开始执行子任务0.1：结构化提取")
        
        # 加载提示词
        prompt_path = self.prompt_dir / "stage0" / "0.1_结构化提取.md"
        prompt = load_prompt_template(str(prompt_path))
        
        # 加载schema
        schema_path = self.schema_dir / "stage0_output_schema.json"
        schema = load_json(str(schema_path))
        
        # 构建完整提示词
        full_prompt = f"""
{prompt}

原始判决书文本：
{judgment_text}

请按照上述要求生成标准JSON格式的输出。
"""
        
        # 调用大模型
        response = self.llm_client.generate(full_prompt)
        
        # 解析响应
        try:
            result = json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败，尝试手动提取: {e}")
            # 尝试提取JSON部分
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    logger.info("成功从响应中提取JSON")
                except json.JSONDecodeError:
                    logger.warning("提取的JSON格式仍有问题，尝试解析Markdown代码块")
                    # 尝试从Markdown代码块提取
                    code_match = re.search(r'```json\s*(\{[\s\S]*\})\s*```', response)
                    if code_match:
                        result = json.loads(code_match.group(1))
                    else:
                        # 返回原始响应作为后备
                        result = {"raw_response": response, "error": str(e)}
            else:
                logger.warning("未找到JSON内容，返回原始响应")
                result = {"raw_response": response, "error": str(e)}
        
        # 保存结果
        output_path = self.output_dir / "stage0" / "0.1_structured_extraction.json"
        save_json(result, str(output_path))
        logger.info(f"子任务0.1完成，结果已保存到 {output_path}")
        
        return result
    
    def run_subtask_0_2(self, structured_extraction: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行子任务0.2：脱敏替换策划
        
        Args:
            structured_extraction: 结构化提取结果
        
        Returns:
            脱敏替换策划结果
        """
        logger.info("开始执行子任务0.2：脱敏替换策划")
        
        # 加载提示词
        prompt_path = self.prompt_dir / "stage0" / "0.2_脱敏替换策划.md"
        prompt = load_prompt_template(str(prompt_path))
        
        # 加载schema
        schema_path = self.schema_dir / "profile_library_schema.json"
        schema = load_json(str(schema_path))
        
        # 构建完整提示词
        full_prompt = f"""
{prompt}

结构化提取结果：
{json.dumps(structured_extraction, ensure_ascii=False, indent=2)}

请按照上述要求生成标准JSON格式的输出。
"""
        
        # 调用大模型
        response = self.llm_client.generate(full_prompt)
        
        # 解析响应
        try:
            result = json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败，尝试手动提取: {e}")
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    logger.info("成功从响应中提取JSON")
                except json.JSONDecodeError:
                    logger.warning("提取的JSON格式仍有问题，尝试解析Markdown代码块")
                    code_match = re.search(r'```json\s*(\{[\s\S]*\})\s*```', response)
                    if code_match:
                        result = json.loads(code_match.group(1))
                    else:
                        result = {"raw_response": response, "error": str(e)}
            else:
                logger.warning("未找到JSON内容，返回原始响应")
                result = {"raw_response": response, "error": str(e)}
        
        # 保存结果
        output_path = self.output_dir / "stage0" / "0.2_anonymization_plan.json"
        save_json(result, str(output_path))
        logger.info(f"子任务0.2完成，结果已保存到 {output_path}")
        
        return result
    
    def run_subtask_0_3(
        self,
        structured_extraction: Dict[str, Any],
        anonymization_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行子任务0.3：交易结构重构
        
        Args:
            structured_extraction: 结构化提取结果
            anonymization_plan: 脱敏替换策划结果
        
        Returns:
            交易结构重构结果
        """
        logger.info("开始执行子任务0.3：交易结构重构")
        
        # 加载提示词
        prompt_path = self.prompt_dir / "stage0" / "0.3_交易结构重构.md"
        prompt = load_prompt_template(str(prompt_path))
        
        # 构建完整提示词
        full_prompt = f"""
{prompt}

结构化提取结果：
{json.dumps(structured_extraction, ensure_ascii=False, indent=2)}

Profile库：
{json.dumps(anonymization_plan, ensure_ascii=False, indent=2)}

请按照上述要求生成标准JSON格式的输出。
"""
        
        # 调用大模型
        response = self.llm_client.generate(full_prompt)
        
        # 解析响应
        try:
            result = json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败，尝试手动提取: {e}")
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    logger.info("成功从响应中提取JSON")
                except json.JSONDecodeError:
                    logger.warning("提取的JSON格式仍有问题，尝试解析Markdown代码块")
                    code_match = re.search(r'```json\s*(\{[\s\S]*\})\s*```', response)
                    if code_match:
                        result = json.loads(code_match.group(1))
                    else:
                        result = {"raw_response": response, "error": str(e)}
            else:
                logger.warning("未找到JSON内容，返回原始响应")
                result = {"raw_response": response, "error": str(e)}
        
        # 保存结果
        output_path = self.output_dir / "stage0" / "0.3_transaction_reconstruction.json"
        save_json(result, str(output_path))
        logger.info(f"子任务0.3完成，结果已保存到 {output_path}")
        
        return result
    
    def run_subtask_0_4(
        self,
        structured_extraction: Dict[str, Any],
        transaction_reconstruction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行子任务0.4：关键数字提取
        
        Args:
            structured_extraction: 结构化提取结果
            transaction_reconstruction: 交易结构重构结果
        
        Returns:
            关键数字提取结果
        """
        logger.info("开始执行子任务0.4：关键数字提取")
        
        # 加载提示词
        prompt_path = self.prompt_dir / "stage0" / "0.4_关键数字提取.md"
        prompt = load_prompt_template(str(prompt_path))
        
        # 构建完整提示词
        full_prompt = f"""
{prompt}

结构化提取结果：
{json.dumps(structured_extraction, ensure_ascii=False, indent=2)}

交易时间线：
{json.dumps(transaction_reconstruction.get("交易时间线", {}), ensure_ascii=False, indent=2)}

请按照上述要求生成标准JSON格式的输出。
"""
        
        # 调用大模型
        response = self.llm_client.generate(full_prompt)
        
        # 解析响应
        try:
            result = json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败，尝试手动提取: {e}")
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    logger.info("成功从响应中提取JSON")
                except json.JSONDecodeError:
                    logger.warning("提取的JSON格式仍有问题，尝试解析Markdown代码块")
                    code_match = re.search(r'```json\s*(\{[\s\S]*\})\s*```', response)
                    if code_match:
                        result = json.loads(code_match.group(1))
                    else:
                        result = {"raw_response": response, "error": str(e)}
            else:
                logger.warning("未找到JSON内容，返回原始响应")
                result = {"raw_response": response, "error": str(e)}
        
        # 保存结果
        output_path = self.output_dir / "stage0" / "0.4_key_numbers.json"
        save_json(result, str(output_path))
        logger.info(f"子任务0.4完成，结果已保存到 {output_path}")
        
        return result
    
    def run_subtask_0_5(
        self,
        structured_extraction: Dict[str, Any],
        transaction_reconstruction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行子任务0.5：证据归属规划
        
        Args:
            structured_extraction: 结构化提取结果
            transaction_reconstruction: 交易结构重构结果
        
        Returns:
            证据归属规划结果
        """
        logger.info("开始执行子任务0.5：证据归属规划")
        
        # 加载提示词
        prompt_path = self.prompt_dir / "stage0" / "0.5_证据归属规划.md"
        prompt = load_prompt_template(str(prompt_path))
        
        # 加载schema
        schema_path = self.schema_dir / "evidence_planning_schema.json"
        schema = load_json(str(schema_path))
        
        # 构建完整提示词
        full_prompt = f"""
{prompt}

结构化提取结果：
{json.dumps(structured_extraction, ensure_ascii=False, indent=2)}

交易时间线：
{json.dumps(transaction_reconstruction.get("交易时间线", {}), ensure_ascii=False, indent=2)}

请按照上述要求生成标准JSON格式的输出。
"""
        
        # 调用大模型
        response = self.llm_client.generate(full_prompt)
        
        # 解析响应
        try:
            result = json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析失败，尝试手动提取: {e}")
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    logger.info("成功从响应中提取JSON")
                except json.JSONDecodeError:
                    logger.warning("提取的JSON格式仍有问题，尝试解析Markdown代码块")
                    code_match = re.search(r'```json\s*(\{[\s\S]*\})\s*```', response)
                    if code_match:
                        result = json.loads(code_match.group(1))
                    else:
                        result = {"raw_response": response, "error": str(e)}
            else:
                logger.warning("未找到JSON内容，返回原始响应")
                result = {"raw_response": response, "error": str(e)}
        
        # 保存结果
        output_path = self.output_dir / "stage0" / "0.5_evidence_planning.json"
        save_json(result, str(output_path))
        logger.info(f"子任务0.5完成，结果已保存到 {output_path}")
        
        return result
    
    def run_all(self, judgment_text: str) -> Dict[str, Any]:
        """
        执行阶段0的所有子任务
        
        Args:
            judgment_text: 判决书文本
        
        Returns:
            阶段0完整输出
        """
        logger.info("开始执行阶段0：判决书解析与全局规划")
        
        # 执行所有子任务
        task_0_1 = self.run_subtask_0_1(judgment_text)
        task_0_2 = self.run_subtask_0_2(task_0_1)
        task_0_3 = self.run_subtask_0_3(task_0_1, task_0_2)
        task_0_4 = self.run_subtask_0_4(task_0_1, task_0_3)
        task_0_5 = self.run_subtask_0_5(task_0_1, task_0_3)
        
        # 整合结果
        result = {
            "0.1_结构化提取": task_0_1,
            "0.2_脱敏替换策划": task_0_2,
            "0.3_交易结构重构": task_0_3,
            "0.4_关键数字清单": task_0_4,
            "0.5_证据归属规划": task_0_5
        }
        
        # 保存完整结果
        output_path = self.output_dir / "analysis_results.json"
        save_json(result, str(output_path))
        logger.info(f"阶段0完成，完整结果已保存到 {output_path}")
        
        return result
