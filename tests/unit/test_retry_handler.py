#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重试处理器单元测试"""

import unittest
from typing import Callable

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.utils.retry_handler import RetryHandler


class TestRetryHandler(unittest.TestCase):
    """重试处理器测试"""

    def setUp(self):
        """测试前置设置"""
        self.handler = RetryHandler(max_retries=3)

    def test_first_try_success(self):
        """测试首次生成成功"""
        def generate_success():
            return "华夏金融租赁有限公司签署合同"

        result = self.handler.execute_with_retry(generate_success)

        self.assertTrue(result["success"])
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(result["result"], "华夏金融租赁有限公司签署合同")
        self.assertIsNone(result["error"])

    def test_retry_until_success(self):
        """测试重试直到成功"""
        call_count = 0

        def generate_with_placeholder():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return "某某公司5签署合同"
            return "华夏金融租赁有限公司签署合同"

        result = self.handler.execute_with_retry(generate_with_placeholder)

        self.assertTrue(result["success"])
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(call_count, 2)

    def test_max_retries_exceeded(self):
        """测试超过最大重试次数"""
        call_count = 0

        def always_has_placeholder():
            nonlocal call_count
            call_count += 1
            return "某某公司5签署合同，金额X4元"

        result = self.handler.execute_with_retry(always_has_placeholder)

        self.assertFalse(result["success"])
        self.assertEqual(result["attempts"], 4)  # max_retries + 1
        self.assertEqual(call_count, 4)
        self.assertIn("超过最大重试次数", result["error"])

    def test_retry_with_exception(self):
        """测试重试时发生异常"""
        call_count = 0

        def generate_with_exception():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("临时错误")
            return "华夏金融租赁有限公司签署合同"

        result = self.handler.execute_with_retry(generate_with_exception)

        self.assertTrue(result["success"])
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(call_count, 2)

    def test_all_attempts_fail_with_exception(self):
        """测试所有尝试都因异常失败"""
        call_count = 0

        def always_fail():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("永久错误")

        result = self.handler.execute_with_retry(always_fail)

        self.assertFalse(result["success"])
        self.assertEqual(result["attempts"], 4)
        self.assertIsNone(result["result"])
        # 失败时的错误信息是"超过最大重试次数"
        self.assertIn("超过最大重试次数", result["error"])

    def test_function_with_args(self):
        """测试带参数的生成函数"""
        call_count = 0

        def generate_with_args(prefix: str, suffix: str) -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                if "某某" in prefix:
                    return f"{prefix}{suffix}"
            return f"华夏金融租赁有限公司{suffix}"

        result = self.handler.execute_with_retry(
            generate_with_args,
            prefix="某某公司5",
            suffix="签署合同"
        )

        # 由于我们让它第三次成功，应该通过
        self.assertTrue(result["success"])
        self.assertIn("华夏金融租赁有限公司", result["result"])

    def test_retry_history记录(self):
        """测试重试历史记录"""
        call_count = 0

        def generate():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return "某某公司5"
            return "华夏金融租赁有限公司"

        self.handler.execute_with_retry(generate)
        stats = self.handler.get_retry_stats()

        self.assertEqual(len(stats["history"]), 2)
        self.assertFalse(stats["history"][0]["success"])
        self.assertTrue(stats["history"][1]["success"])


class TestRetryHandlerEdgeCases(unittest.TestCase):
    """重试处理器边界情况测试"""

    def test_none_result(self):
        """测试生成返回None视为失败"""
        handler = RetryHandler(max_retries=2)

        def return_none():
            return None

        result = handler.execute_with_retry(return_none)

        # None结果应该被视为失败（需要重试）
        self.assertFalse(result["success"])
        self.assertIsNone(result["result"])

    def test_empty_result(self):
        """测试生成返回空字符串"""
        handler = RetryHandler(max_retries=2)

        def return_empty():
            return ""

        result = handler.execute_with_retry(return_empty)

        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "")


if __name__ == "__main__":
    unittest.main()
