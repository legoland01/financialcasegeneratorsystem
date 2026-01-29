"""改进的LLM客户端 - 增加超时时间，改进JSON解析"""
from typing import Dict, Any, Optional
from loguru import logger
import os
import re
import json


class LLMClient:
    """大模型客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        api_base: Optional[str] = None,
        timeout: float = 300.0  # 默认5分钟超时
    ):
        """
        初始化大模型客户端

        Args:
            api_key: API密钥
            model: 模型名称
            api_base: API基础URL
            timeout: 超时时间（秒），默认300秒（5分钟）
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.api_base = api_base or os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.timeout = timeout

        if not self.api_key:
            logger.warning("未设置API密钥,将使用模拟模式")

    def generate(self, prompt: str, **kwargs) -> str:
        """
        生成文本

        Args:
            prompt: 提示词
            **kwargs: 其他参数

        Returns:
            生成的文本
        """
        if not self.api_key:
            logger.info("模拟模式:返回模拟响应")
            return self._mock_generate(prompt)

        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_base,
                timeout=self.timeout
            )

            # 过滤掉可能引起问题的参数
            safe_kwargs = {
                'max_tokens': kwargs.get('max_tokens', 8192),
                'temperature': kwargs.get('temperature', 0.7),
                'top_p': kwargs.get('top_p', 0.9)
            }

            logger.info(f"调用大模型，超时时间: {self.timeout}秒")
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的法律文书生成助手。"},
                    {"role": "user", "content": prompt}
                ],
                **safe_kwargs
            )

            content = response.choices[0].message.content
            logger.success(f"大模型响应成功，长度: {len(content)} 字符")
            return content

        except Exception as e:
            logger.error(f"调用大模型失败: {e}")
            logger.info(f"提示：如果超时，可以尝试：")
            logger.info(f"1. 增加超时时间: LLMClient(timeout=600)")
            logger.info(f"2. 减少max_tokens参数")
            logger.info(f"3. 使用更快的模型")
            raise

    def generate_json(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        生成JSON格式响应（带改进的解析逻辑）

        Args:
            prompt: 提示词
            **kwargs: 其他参数

        Returns:
            解析后的JSON对象
        """
        response = self.generate(prompt, **kwargs)

        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取JSON部分（支持多种格式）
        # 格式1: ```json ... ```
        json_pattern1 = r'```json\s*([\s\S]*?)\s*```'
        match1 = re.search(json_pattern1, response)
        if match1:
            try:
                return json.loads(match1.group(1))
            except json.JSONDecodeError:
                pass

        # 格式2: ``` ... ```
        json_pattern2 = r'```\s*([\s\S]*?)\s*```'
        match2 = re.search(json_pattern2, response)
        if match2:
            try:
                return json.loads(match2.group(1))
            except json.JSONDecodeError:
                pass

        # 格式3: { ... }
        json_pattern3 = r'\{[\s\S]*\}'
        match3 = re.search(json_pattern3, response)
        if match3:
            try:
                return json.loads(match3.group())
            except json.JSONDecodeError:
                pass

        # 都失败了，报错
        logger.error(f"无法从响应中解析JSON")
        logger.debug(f"原始响应: {response[:500]}")
        raise ValueError("无法解析JSON响应")

    def _mock_generate(self, prompt: str) -> str:
        """
        模拟生成(用于测试)

        Args:
            prompt: 提示词

        Returns:
            模拟的响应
        """
        return """
模拟响应:
{
  "案件基本信息": {
    "案号": "(2024)沪74民初721号",
    "法院": "上海金融法院",
    "案由": "融资租赁合同纠纷",
    "程序": "一审"
  }
}
"""
