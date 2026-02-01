"""
LLM客户端 - v3.0

提供统一的LLM API调用接口。
支持多模型配置，包括OpenAI和其他兼容API。
"""

import os
import time
import requests
from typing import Optional, Dict, Any
from datetime import datetime


class LLMClient:
    """
    LLM客户端
    
    提供统一的LLM API调用接口。
    支持环境变量配置API Key和Base URL。
    """
    
    DEFAULT_MODEL = "gpt-4"
    DEFAULT_TIMEOUT = 120
    DEFAULT_MAX_RETRIES = 3
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES
    ):
        """
        初始化LLM客户端
        
        Args:
            api_key: API密钥，如果为None则从环境变量读取
            base_url: API基础URL，如果为None则从环境变量读取
            model: 模型名称
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        
        if not self.api_key:
            raise ValueError("未配置API Key，请设置OPENAI_API_KEY环境变量或传入api_key参数")
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        LLM补全请求
        
        Args:
            prompt: 用户Prompt
            system_prompt: 系统Prompt（可选）
            temperature: 温度参数（0-2），越低越确定
            max_tokens: 最大生成token数
        
        Returns:
            str: LLM响应文本
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self._call_api(payload)
                return response
            except requests.exceptions.Timeout:
                last_error = "请求超时"
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
            except requests.exceptions.ConnectionError as e:
                last_error = f"连接错误: {str(e)}"
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
            except Exception as e:
                last_error = str(e)
                break
        
        raise RuntimeError(f"LLM调用失败，已重试{self.max_retries}次：{last_error}")
    
    def _call_api(self, payload: Dict[str, Any]) -> str:
        """
        调用LLM API
        
        Args:
            payload: 请求payload
        
        Returns:
            str: LLM响应文本
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def embed(self, text: str) -> list:
        """
        获取文本的嵌入向量
        
        Args:
            text: 输入文本
        
        Returns:
            list: 嵌入向量
        """
        # 简化的嵌入调用，实际应使用embedding API
        raise NotImplementedError("嵌入功能待实现")
    
    def count_tokens(self, text: str) -> int:
        """
        计算文本的token数（估算）
        
        Args:
            text: 输入文本
        
        Returns:
            int: 估算的token数
        """
        # 简单估算：中文约1.5字符/token，英文约4字符/token
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars / 1.5 + other_chars / 4)
    
    def validate_response(self, response: str) -> bool:
        """
        验证LLM响应
        
        Args:
            response: LLM响应文本
        
        Returns:
            bool: 是否有效
        """
        if not response:
            return False
        
        if len(response.strip()) == 0:
            return False
        
        return True
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict: 模型信息
        """
        return {
            "model": self.model,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries
        }


class MockLLMClient(LLMClient):
    """
    Mock LLM客户端，用于测试
    """
    
    def __init__(self, mock_response: str = "测试响应"):
        super().__init__(api_key="mock", model="mock")
        self.mock_response = mock_response
        self.call_count = 0
        self.last_prompt = None
    
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ) -> str:
        self.call_count += 1
        self.last_prompt = prompt
        return self.mock_response
    
    def reset(self):
        """重置调用计数"""
        self.call_count = 0
        self.last_prompt = None
