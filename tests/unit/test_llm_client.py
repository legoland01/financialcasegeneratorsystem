"""
test_llm_client.py - LLMClient单元测试

测试LLM客户端的核心功能，包括MockLLMClient。
"""

import pytest
import os
from unittest.mock import patch, MagicMock
import requests

from src.core.llm_client import LLMClient, MockLLMClient


class TestMockLLMClient:
    """MockLLMClient测试类"""
    
    def test_init_with_default_response(self):
        """测试默认响应初始化"""
        client = MockLLMClient()
        assert client.mock_response == "测试响应"
        assert client.call_count == 0
    
    def test_init_with_custom_response(self):
        """测试自定义响应初始化"""
        custom_response = "自定义响应内容"
        client = MockLLMClient(mock_response=custom_response)
        assert client.mock_response == custom_response
    
    def test_complete_returns_mock_response(self):
        """测试complete方法返回模拟响应"""
        client = MockLLMClient(mock_response="模拟响应")
        result = client.complete("测试提示")
        assert result == "模拟响应"
    
    def test_complete_increments_call_count(self):
        """测试complete方法增加调用计数"""
        client = MockLLMClient()
        assert client.call_count == 0
        
        client.complete("测试1")
        assert client.call_count == 1
        
        client.complete("测试2")
        assert client.call_count == 2
        
        client.complete("测试3")
        assert client.call_count == 3
    
    def test_complete_records_last_prompt(self):
        """测试complete方法记录最后提示词"""
        client = MockLLMClient()
        assert client.last_prompt is None
        
        client.complete("第一个提示")
        assert client.last_prompt == "第一个提示"
        
        client.complete("第二个提示")
        assert client.last_prompt == "第二个提示"
    
    def test_complete_with_system_prompt(self):
        """测试带系统提示词的complete方法"""
        client = MockLLMClient(mock_response="系统响应")
        result = client.complete("用户提示", system_prompt="系统提示")
        assert result == "系统响应"
        assert client.call_count == 1
    
    def test_complete_with_temperature(self):
        """测试带温度参数的complete方法"""
        client = MockLLMClient(mock_response="温度响应")
        result = client.complete("提示", temperature=0.5)
        assert result == "温度响应"
    
    def test_complete_with_max_tokens(self):
        """测试带最大token数的complete方法"""
        client = MockLLMClient(mock_response="Token响应")
        result = client.complete("提示", max_tokens=100)
        assert result == "Token响应"
    
    def test_reset(self):
        """测试重置方法"""
        client = MockLLMClient()
        client.complete("测试1")
        client.complete("测试2")
        assert client.call_count == 2
        assert client.last_prompt == "测试2"
        
        client.reset()
        assert client.call_count == 0
        assert client.last_prompt is None
    
    def test_mock_client_inherits_from_llm_client(self):
        """测试MockLLMClient继承自LLMClient"""
        client = MockLLMClient()
        assert isinstance(client, LLMClient)
    
    def test_mock_client_has_model_info(self):
        """测试MockLLMClient有模型信息"""
        client = MockLLMClient()
        info = client.get_model_info()
        assert "model" in info
        assert info["model"] == "mock"


class TestLLMClient:
    """LLMClient测试类 - 需要模拟API调用"""
    
    def test_init_with_api_key(self):
        """测试带API Key初始化"""
        client = LLMClient(api_key="test-api-key")
        assert client.api_key == "test-api-key"
    
    def test_init_with_environment_variable(self):
        """测试从环境变量读取API Key"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-api-key"}):
            client = LLMClient()
            assert client.api_key == "env-api-key"
    
    def test_init_without_api_key_raises_error(self):
        """测试无API Key时抛出异常"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                LLMClient()
            assert "未配置API Key" in str(exc_info.value)
    
    def test_init_with_base_url(self):
        """测试带Base URL初始化"""
        client = LLMClient(api_key="test", base_url="https://custom.api.com/v1")
        assert client.base_url == "https://custom.api.com/v1"
    
    def test_init_with_default_base_url(self):
        """测试默认Base URL"""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}):
            client = LLMClient()
            assert client.base_url == "https://api.openai.com/v1"
    
    def test_init_with_model(self):
        """测试指定模型"""
        client = LLMClient(api_key="test", model="gpt-3.5-turbo")
        assert client.model == "gpt-3.5-turbo"
    
    def test_init_with_default_model(self):
        """测试默认模型"""
        client = LLMClient(api_key="test")
        assert client.model == "gpt-4"
    
    def test_init_with_timeout(self):
        """测试指定超时时间"""
        client = LLMClient(api_key="test", timeout=60)
        assert client.timeout == 60
    
    def test_init_with_default_timeout(self):
        """测试默认超时时间"""
        client = LLMClient(api_key="test")
        assert client.timeout == 120
    
    def test_init_with_max_retries(self):
        """测试指定最大重试次数"""
        client = LLMClient(api_key="test", max_retries=5)
        assert client.max_retries == 5
    
    def test_init_with_default_max_retries(self):
        """测试默认最大重试次数"""
        client = LLMClient(api_key="test")
        assert client.max_retries == 3
    
    @patch('requests.post')
    def test_complete_success(self, mock_post):
        """测试成功调用"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "测试响应"}}]
        }
        mock_post.return_value = mock_response
        
        client = LLMClient(api_key="test-key")
        result = client.complete("测试提示")
        
        assert result == "测试响应"
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_complete_with_system_prompt(self, mock_post):
        """测试带系统提示词的调用"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "响应内容"}}]
        }
        mock_post.return_value = mock_response
        
        client = LLMClient(api_key="test-key")
        result = client.complete("用户提示", system_prompt="系统提示")
        
        assert result == "响应内容"
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][1]["role"] == "user"
    
    @patch('requests.post')
    def test_complete_with_temperature(self, mock_post):
        """测试带温度参数的调用"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "响应"}}]
        }
        mock_post.return_value = mock_response
        
        client = LLMClient(api_key="test-key")
        client.complete("提示", temperature=0.5)
        
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["temperature"] == 0.5
    
    @patch('requests.post')
    def test_complete_with_max_tokens(self, mock_post):
        """测试带最大token数的调用"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "响应"}}]
        }
        mock_post.return_value = mock_response
        
        client = LLMClient(api_key="test-key")
        client.complete("提示", max_tokens=100)
        
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["max_tokens"] == 100
    
    @patch('requests.post')
    def test_complete_timeout_retry(self, mock_post):
        """测试超时重试"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "最终响应"}}]
        }
        
        mock_post.side_effect = [
            requests.exceptions.Timeout(),
            requests.exceptions.Timeout(),
            mock_response
        ]
        
        client = LLMClient(api_key="test-key", max_retries=3)
        result = client.complete("提示")
        
        assert result == "最终响应"
        assert mock_post.call_count == 3
    
    @patch('requests.post')
    def test_complete_connection_error_retry(self, mock_post):
        """测试连接错误重试"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "响应"}}]
        }
        
        mock_post.side_effect = [
            requests.exceptions.ConnectionError("连接失败"),
            mock_response
        ]
        
        client = LLMClient(api_key="test-key", max_retries=3)
        result = client.complete("提示")
        
        assert result == "响应"
        assert mock_post.call_count == 2
    
    @patch('requests.post')
    def test_complete_max_retries_exceeded(self, mock_post):
        """测试超过最大重试次数"""
        mock_post.side_effect = requests.exceptions.Timeout()
        
        client = LLMClient(api_key="test-key", max_retries=2)
        
        with pytest.raises(RuntimeError) as exc_info:
            client.complete("提示")
        assert "LLM调用失败，已重试2次" in str(exc_info.value)
    
    def test_count_tokens_all_chinese(self):
        """测试中文字符token计算"""
        client = LLMClient(api_key="test")
        text = "这是中文字符"
        token_count = client.count_tokens(text)
        assert token_count > 0
        assert token_count == int(4 / 1.5)
    
    def test_count_tokens_all_english(self):
        """测试英文字符token计算"""
        client = LLMClient(api_key="test")
        text = "hello world"
        token_count = client.count_tokens(text)
        assert token_count > 0
        assert token_count == int(11 / 4)  # 11个字符
    
    def test_count_tokens_mixed(self):
        """测试混合字符token计算"""
        client = LLMClient(api_key="test")
        text = "hello你好world世界"
        chinese_count = 4
        english_count = 10
        token_count = client.count_tokens(text)
        expected = int(chinese_count / 1.5 + english_count / 4)
        assert token_count == expected
    
    def test_validate_response_empty_string(self):
        """测试空字符串验证"""
        client = LLMClient(api_key="test")
        assert client.validate_response("") is False
    
    def test_validate_response_whitespace_only(self):
        """测试纯空白字符串验证"""
        client = LLMClient(api_key="test")
        assert client.validate_response("   \t\n  ") is False
    
    def test_validate_response_valid(self):
        """测试有效响应验证"""
        client = LLMClient(api_key="test")
        assert client.validate_response("有效响应") is True
    
    def test_validate_response_empty_string_false(self):
        """测试空字符串响应验证"""
        client = LLMClient(api_key="test")
        assert client.validate_response("") is False
    
    def test_get_model_info(self):
        """测试获取模型信息"""
        client = LLMClient(
            api_key="test-key",
            base_url="https://custom.api.com",
            model="gpt-3.5-turbo",
            timeout=60,
            max_retries=5
        )
        info = client.get_model_info()
        
        assert info["model"] == "gpt-3.5-turbo"
        assert info["base_url"] == "https://custom.api.com"
        assert info["timeout"] == 60
        assert info["max_retries"] == 5
    
    def test_embed_raises_not_implemented(self):
        """测试嵌入方法未实现"""
        client = LLMClient(api_key="test")
        with pytest.raises(NotImplementedError):
            client.embed("测试文本")
    
    @patch('requests.post')
    def test_api_call_with_correct_headers(self, mock_post):
        """测试API调用使用正确的请求头"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "响应"}}]
        }
        mock_post.return_value = mock_response
        
        client = LLMClient(api_key="my-api-key")
        client.complete("提示")
        
        call_args = mock_post.call_args
        headers = call_args[1]["headers"]
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer my-api-key"
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
    
    @patch('requests.post')
    def test_api_endpoint(self, mock_post):
        """测试API端点"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "响应"}}]
        }
        mock_post.return_value = mock_response
        
        client = LLMClient(api_key="test", base_url="https://custom.api.com/v1")
        client.complete("提示")
        
        call_args = mock_post.call_args
        url = call_args[0][0]
        assert url == "https://custom.api.com/v1/chat/completions"
    
    def test_mock_client_supports_all_complete_params(self):
        """测试MockLLMClient支持所有complete参数"""
        client = MockLLMClient()
        result = client.complete(
            prompt="提示",
            system_prompt="系统提示",
            temperature=0.7,
            max_tokens=200
        )
        assert result == "测试响应"
        assert client.call_count == 1


class TestLLMClientTokenEstimation:
    """Token估算测试类"""
    
    def test_empty_string(self):
        """测试空字符串"""
        client = LLMClient(api_key="test")
        assert client.count_tokens("") == 0
    
    def test_single_chinese_character(self):
        """测试单个汉字"""
        client = LLMClient(api_key="test")
        result = client.count_tokens("中")
        assert result == int(1 / 1.5)
    
    def test_single_english_character(self):
        """测试单个英文字符"""
        client = LLMClient(api_key="test")
        assert client.count_tokens("a") == 0
    
    def test_numbers_count_as_other(self):
        """测试数字计入其他字符"""
        client = LLMClient(api_key="test")
        token_count = client.count_tokens("12345")
        assert token_count == int(5 / 4)
    
    def test_punctuation_counts_as_other(self):
        """测试标点符号计入其他字符"""
        client = LLMClient(api_key="test")
        token_count = client.count_tokens("，。！？")
        assert token_count == int(4 / 4)
