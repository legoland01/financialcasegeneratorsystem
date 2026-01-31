#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""占位符检测器单元测试"""

import unittest
import tempfile
import shutil
from pathlib import Path

import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.utils.placeholder_checker import PlaceholderChecker


class TestPlaceholderChecker(unittest.TestCase):
    """占位符检测器测试"""

    def setUp(self):
        """测试前置设置"""
        self.checker = PlaceholderChecker()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_has_placeholder_某某(self):
        """测试检测某某开头的占位符"""
        text = "某某公司5签署合同"
        is_clean, found = self.checker.check(text)
        self.assertFalse(is_clean)
        # 正则匹配整个匹配项，不仅仅是公司名部分
        self.assertTrue(any("某某公司5" in str(p) for p in found))

    def test_has_placeholder_某(self):
        """测试检测某开头的占位符"""
        text = "某公司签署合同"
        is_clean, found = self.checker.check(text)
        self.assertFalse(is_clean)
        # 检查是否检测到某开头的占位符
        self.assertTrue(any("某公司" in str(p) for p in found))

    def test_has_placeholder_X4(self):
        """测试检测X+数字占位符"""
        text = "按X4计算违约金"
        is_clean, found = self.checker.check(text)
        self.assertFalse(is_clean)
        self.assertIn("X4", found)

    def test_has_placeholder_X5(self):
        """测试检测X5占位符"""
        text = "利息按X5%计算"
        is_clean, found = self.checker.check(text)
        self.assertFalse(is_clean)

    def test_has_date_placeholder(self):
        """测试检测日期占位符"""
        text = "签订日期为X年X月X日"
        is_clean, found = self.checker.check(text)
        self.assertFalse(is_clean)
        self.assertTrue(any("X年X月X日" in str(p) for p in found))

    def test_has_empty_brackets(self):
        """测试检测空白括号占位符"""
        text = "开户行：银行支行【】账号："
        is_clean, found = self.checker.check(text)
        self.assertFalse(is_clean)
        self.assertIn("【】", found)

    def test_has_empty_parentheses(self):
        """测试检测空白圆括号占位符"""
        text = "法定代表人（签字）：某某"
        is_clean, found = self.checker.check(text)
        self.assertFalse(is_clean)

    def test_has_signature_placeholder(self):
        """测试检测签名占位符"""
        text = "法定代表人（签字）：或授权代表"
        is_clean, found = self.checker.check(text)
        self.assertFalse(is_clean)
        self.assertIn("或授权代表", found)

    def test_clean_text(self):
        """测试正常文本通过检测"""
        text = "华夏金融租赁有限公司签署合同"
        is_clean, found = self.checker.check(text)
        self.assertTrue(is_clean)
        self.assertEqual(len(found), 0)

    def test_clean_real_company(self):
        """测试真实公司名通过检测"""
        text = "江西宏昌商业管理有限公司于2021年3月15日成立"
        is_clean, _ = self.checker.check(text)
        self.assertTrue(is_clean)

    def test_mixed_content(self):
        """测试混合内容（部分占位符）"""
        text = "某某公司5（法定代表人：张伟）签署合同，金额X4元"
        is_clean, found = self.checker.check(text)
        self.assertFalse(is_clean)
        self.assertTrue(len(found) >= 2)

    def test_percentage_placeholder(self):
        """测试百分比占位符"""
        text = "违约金按X5%计算"
        is_clean, found = self.checker.check(text)
        self.assertFalse(is_clean)

    def test_get_placeholder_count(self):
        """测试占位符数量统计"""
        text1 = "某某公司5签署"
        text2 = "某某公司5签署，金额X4元"

        count1 = self.checker.get_placeholder_count(text1)
        count2 = self.checker.get_placeholder_count(text2)

        self.assertGreaterEqual(count1, 1)
        self.assertGreaterEqual(count2, 2)

    def test_deduplication(self):
        """测试占位符列表包含性（不去重）"""
        text = "某某公司5签署，某某公司5盖章"
        is_clean, found = self.checker.check(text)
        self.assertFalse(is_clean)
        # 检查是否检测到某某公司5
        self.assertTrue(any("某某公司5" in str(p) for p in found))


class TestPlaceholderCheckerEdgeCases(unittest.TestCase):
    """占位符检测器边界情况测试"""

    def setUp(self):
        self.checker = PlaceholderChecker()

    def test_empty_text(self):
        """测试空文本"""
        is_clean, found = self.checker.check("")
        self.assertTrue(is_clean)
        self.assertEqual(len(found), 0)

    def test_only_whitespace(self):
        """测试仅空白字符"""
        is_clean, found = self.checker.check("   \n\n  ")
        self.assertTrue(is_clean)
        self.assertEqual(len(found), 0)

    def test_special_characters(self):
        """测试特殊字符"""
        text = "《合同》编号：FL-2021-001"
        is_clean, _ = self.checker.check(text)
        self.assertTrue(is_clean)

    def test_chinese_punctuation(self):
        """测试中文标点"""
        text = "原告：华夏金融租赁有限公司，被告：江西宏昌商业管理有限公司。"
        is_clean, _ = self.checker.check(text)
        self.assertTrue(is_clean)


if __name__ == "__main__":
    unittest.main()
