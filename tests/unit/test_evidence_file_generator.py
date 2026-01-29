#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
证据生成单元测试
专门测试EvidenceFileGenerator类的方法
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
import sys

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.services.evidence_file_generator import EvidenceFileGenerator
from src.utils import LLMClient

class TestEvidenceFileGenerator(unittest.TestCase):
    """EvidenceFileGenerator单元测试"""
    
    def setUp(self):
        """测试前置设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        self.generator = EvidenceFileGenerator(
            prompt_dir="prompts",
            output_dir=str(self.temp_path),
            llm_client=LLMClient()
        )
        
        # 测试用证据数据
        self.test_evidence = {
            "证据序号": 1,
            "证据名称": "《转让合同》及公证书",
            "应归属方": "原告",
            "文件类型": "合同",
            "是否需要生成": True,
            "证据组": 1,
            "证明目的": "证明融资租赁基础法律关系",
            "关键数据提示": {
                "涉及金额": {"数值": 150000000, "单位": "元"},
                "涉及日期": "2021-02-24",
                "涉及方": ["某某公司5", "某某公司1"]
            }
        }
        
        # 测试用证据规划
        self.evidence_planning = {
            "证据归属规划表": [self.test_evidence],
            "证据分组": {
                "证据组_1": {
                    "组名称": "主合同文件",
                    "归属方": "原告",
                    "证据数量": 1,
                    "证明目的": "证明融资租赁基础法律关系"
                }
            }
        }
        
        # 测试用阶段0数据
        self.stage0_data = {
            "0.1_structured_extraction": {
                "案件基本信息": {"案号": "（2024）沪74民初245号"}
            },
            "0.2_anonymization_plan": {
                "人物Profile库": {},
                "公司Profile库": {}
            },
            "0.3_transaction_reconstruction": {
                "交易时间线": []
            },
            "0.4_key_numbers": {
                "融资本金": 150000000
            }
        }
    
    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_group_evidences(self):
        """测试证据分组功能"""
        evidence_list = [
            {"证据组": 1, "证据序号": 1, "证据名称": "证据1"},
            {"证据组": 1, "证据序号": 2, "证据名称": "证据2"},
            {"证据组": 2, "证据序号": 3, "证据名称": "证据3"}
        ]
        
        groups = self.generator._group_evidences(evidence_list)
        
        self.assertEqual(len(groups), 2)
        self.assertEqual(len(groups[1]), 2)
        self.assertEqual(len(groups[2]), 1)
    
    def test_simplify_evidence_name(self):
        """测试证据名称简化功能"""
        test_cases = [
            ("《转让合同》及公证书", "转让合同"),
            ("《融资租赁合同（售后回租）》及公证书", "融资租赁合同"),
            ("抵押人股东决定及公证书", "抵押人股东决定"),
            ("（营业执照）", ""),  # 括号内容会被移除
            ("法院判决书（民事）", "法院判决书"),
            ("银行回单", "银行回单")
        ]
        
        for input_name, expected_output in test_cases:
            result = self.generator._simplify_evidence_name(input_name)
            self.assertEqual(result, expected_output)
    
    def test_clean_markdown(self):
        """测试markdown清理功能"""
        markdown_text = """
        # 标题
        
        **加粗文本**和*斜体文本*
        
        - 列表项1
        - 列表项2
        
        [链接文本](https://example.com)
        
        ```python
        code block
        ```
        
        `inline code`
        """
        
        cleaned = self.generator._clean_markdown(markdown_text)
        
        # 验证markdown符号被移除
        self.assertNotIn("# 标题", cleaned)
        self.assertNotIn("**加粗文本**", cleaned)
        self.assertNotIn("```python", cleaned)
        self.assertNotIn("`inline code`", cleaned)
        self.assertNotIn("[链接文本]", cleaned)
        
        # 验证内容保留
        self.assertIn("标题", cleaned)
        self.assertIn("加粗文本", cleaned)
        self.assertIn("斜体文本", cleaned)
        self.assertIn("列表项1", cleaned)
        self.assertIn("code block", cleaned)
        self.assertIn("inline code", cleaned)
    
    def test_get_default_prompt(self):
        """测试默认提示词获取"""
        # 测试合同类型
        prompt = self.generator._get_default_prompt({"文件类型": "合同"})
        self.assertIn("合同编号", prompt)
        self.assertIn("甲方", prompt)
        self.assertIn("乙方", prompt)
        
        # 测试文书类型
        prompt = self.generator._get_default_prompt({"文件类型": "文书"})
        self.assertIn("致", prompt)
        self.assertIn("正文内容", prompt)
        
        # 测试凭证类型
        prompt = self.generator._get_default_prompt({"文件类型": "凭证"})
        self.assertIn("日期", prompt)
        self.assertIn("金额", prompt)
        
        # 测试未定义类型
        prompt = self.generator._get_default_prompt({"文件类型": "未知"})
        self.assertIn("合同编号", prompt)  # 应该使用默认合同模板
    
    def test_build_prompt(self):
        """测试提示词构建功能"""
        prompt = "这是一个基础提示词模板"
        
        built_prompt = self.generator._build_prompt(
            evidence=self.test_evidence,
            stage0_data=self.stage0_data,
            base_prompt=prompt
        )
        
        # 验证提示词包含所有必要部分
        self.assertIn("这是一个基础提示词模板", built_prompt)
        self.assertIn("证据信息", built_prompt)
        self.assertIn("案件基本信息", built_prompt)
        self.assertIn("Profile库", built_prompt)
        self.assertIn("交易时间线", built_prompt)
        self.assertIn("关键金额清单", built_prompt)
        
        # 验证证据信息
        self.assertIn("《转让合同》及公证书", built_prompt)
        self.assertIn("2021-02-24", built_prompt)
        self.assertIn("150000000", built_prompt)
    
    def test_generate_evidence_file(self):
        """测试单个证据文件生成"""
        group_dir = self.temp_path / "test_group"
        group_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = self.generator._generate_evidence_file(
            evidence=self.test_evidence,
            stage0_data=self.stage0_data,
            group_dir=group_dir
        )
        
        # 验证文件生成
        self.assertTrue(file_path.exists())
        self.assertEqual(file_path.suffix, ".txt")
        
        # 验证文件内容
        content = file_path.read_text(encoding='utf-8')
        self.assertGreater(len(content), 0)
        
        # 验证文件名格式
        filename = file_path.name
        self.assertTrue(filename.startswith("证据组1_E001"))
        self.assertIn("转让合同", filename)
    
    def test_generate_evidence_index(self):
        """测试证据索引生成"""
        evidence_files = [
            {
                "证据ID": "E001",
                "证据组": 1,
                "证据名称": "证据1",
                "证据名称简写": "证据1",
                "文件类型": "合同",
                "归属方": "原告",
                "文件路径": "path1",
                "文件大小": 1000
            },
            {
                "证据ID": "E002",
                "证据组": 1,
                "证据名称": "证据2",
                "证据名称简写": "证据2",
                "文件类型": "文书",
                "归属方": "原告",
                "文件路径": "path2",
                "文件大小": 2000
            }
        ]
        
        evidence_groups = {
            1: [evidence_files[0], evidence_files[1]]
        }
        
        evidence_index = self.generator._generate_evidence_index(
            evidence_files=evidence_files,
            evidence_groups=evidence_groups,
            evidence_planning=self.evidence_planning
        )
        
        # 验证索引结构
        self.assertIn("证据总数", evidence_index)
        self.assertIn("证据组数", evidence_index)
        self.assertIn("证据列表", evidence_index)
        self.assertIn("证据组列表", evidence_index)
        
        # 验证统计数据
        self.assertEqual(evidence_index["证据总数"], 2)
        self.assertEqual(evidence_index["证据组数"], 1)
        
        # 验证证据列表
        self.assertEqual(len(evidence_index["证据列表"]), 2)
        self.assertEqual(evidence_index["证据列表"][0]["证据ID"], "E001")
        self.assertEqual(evidence_index["证据列表"][1]["证据ID"], "E002")
        
        # 验证证据组列表
        self.assertEqual(len(evidence_index["证据组列表"]), 1)
        group_info = evidence_index["证据组列表"][0]
        self.assertEqual(group_info["组编号"], 1)
        self.assertEqual(group_info["组名称"], "主合同文件")
        self.assertEqual(group_info["证据数量"], 2)

if __name__ == "__main__":
    unittest.main()