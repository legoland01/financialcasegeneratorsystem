#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新架构功能测试
专门测试新架构证据生成功能
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

class TestNewArchitecture(unittest.TestCase):
    """新架构证据生成测试"""
    
    def setUp(self):
        """测试前置设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # 模拟阶段0数据
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
            },
            "0.5_evidence_planning": {
                "证据归属规划表": [
                    {
                        "证据序号": 1,
                        "证据名称": "《转让合同》及公证书",
                        "应归属方": "原告",
                        "文件类型": "合同",
                        "是否需要生成": True,
                        "证据组": 1,
                        "证明目的": "证明融资租赁基础法律关系"
                    },
                    {
                        "证据序号": 2,
                        "证据名称": "《融资租赁合同》及公证书",
                        "应归属方": "原告",
                        "文件类型": "合同",
                        "是否需要生成": True,
                        "证据组": 1,
                        "证明目的": "证明融资租赁关系成立"
                    }
                ],
                "证据分组": {
                    "证据组_1": {
                        "组名称": "主合同文件",
                        "归属方": "原告",
                        "证据数量": 2,
                        "证明目的": "证明融资租赁基础法律关系"
                    }
                }
            }
        }
    
    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_evidence_file_generator_init(self):
        """测试证据生成器初始化"""
        generator = EvidenceFileGenerator(
            prompt_dir="prompts",
            output_dir=self.temp_dir,
            llm_client=LLMClient()
        )
        
        self.assertEqual(generator.prompt_dir.name, "prompts")
        self.assertEqual(generator.output_dir.name, Path(self.temp_dir).name)
        self.assertIsInstance(generator.llm_client, LLMClient)
    
    def test_evidence_files_generation(self):
        """测试证据文件生成"""
        generator = EvidenceFileGenerator(
            prompt_dir="prompts",
            output_dir=self.temp_dir,
            llm_client=LLMClient()
        )
        
        evidence_index = generator.generate_all_evidence_files(
            stage0_data=self.stage0_data,
            evidence_planning=self.stage0_data["0.5_evidence_planning"],
            party="原告"
        )
        
        # 验证证据索引结构
        self.assertIn("证据总数", evidence_index)
        self.assertIn("证据组数", evidence_index)
        self.assertIn("证据列表", evidence_index)
        self.assertIn("证据组列表", evidence_index)
        
        # 验证证据数量
        self.assertEqual(evidence_index["证据总数"], 2)
        self.assertEqual(evidence_index["证据组数"], 1)
        
        # 验证文件生成
        evidence_files = list(Path(self.temp_dir).glob("evidence/证据组*/*.txt"))
        self.assertEqual(len(evidence_files), 2)
        
        # 验证索引文件生成
        index_file = Path(self.temp_dir) / "evidence_index.json"
        self.assertTrue(index_file.exists())
    
    def test_file_naming_convention(self):
        """测试文件命名规范"""
        generator = EvidenceFileGenerator(
            prompt_dir="prompts",
            output_dir=self.temp_dir,
            llm_client=LLMClient()
        )
        
        evidence_index = generator.generate_all_evidence_files(
            stage0_data=self.stage0_data,
            evidence_planning=self.stage0_data["0.5_evidence_planning"],
            party="原告"
        )
        
        # 验证文件命名格式：证据组{N}_E{XXX}_{证据名称简写}.txt
        for evidence in evidence_index["证据列表"]:
            filename = Path(evidence["文件路径"]).name
            expected_prefix = f"证据组{evidence['证据组']}_"
            expected_evidence_id = evidence["证据ID"]  # 已经是 "E001" 格式
            
            self.assertTrue(filename.startswith(expected_prefix),
                f"文件名 {filename} 应以 {expected_prefix} 开头")
            self.assertIn(expected_evidence_id, filename,
                f"文件名 {filename} 应包含 {expected_evidence_id}")
            self.assertTrue(filename.endswith(".txt"),
                f"文件名 {filename} 应以 .txt 结尾")
    
    def test_evidence_file_content(self):
        """测试证据文件内容"""
        generator = EvidenceFileGenerator(
            prompt_dir="prompts",
            output_dir=self.temp_dir,
            llm_client=LLMClient()
        )
        
        evidence_index = generator.generate_all_evidence_files(
            stage0_data=self.stage0_data,
            evidence_planning=self.stage0_data["0.5_evidence_planning"],
            party="原告"
        )
        
        # 验证每个证据文件都有内容
        for evidence in evidence_index["证据列表"]:
            file_path = Path(evidence["文件路径"])
            self.assertTrue(file_path.exists())
            
            content = file_path.read_text(encoding='utf-8')
            self.assertGreater(len(content), 0)
            self.assertGreater(evidence["文件大小"], 0)
    
    def test_evidence_group_structure(self):
        """测试证据组结构"""
        generator = EvidenceFileGenerator(
            prompt_dir="prompts",
            output_dir=self.temp_dir,
            llm_client=LLMClient()
        )
        
        evidence_index = generator.generate_all_evidence_files(
            stage0_data=self.stage0_data,
            evidence_planning=self.stage0_data["0.5_evidence_planning"],
            party="原告"
        )
        
        # 验证证据组结构
        evidence_groups = evidence_index["证据组列表"]
        self.assertEqual(len(evidence_groups), 1)
        
        group = evidence_groups[0]
        self.assertEqual(group["组编号"], 1)
        self.assertEqual(group["组名称"], "主合同文件")
        self.assertEqual(group["证据数量"], 2)
        
        # 验证目录结构
        group_dir = Path(self.temp_dir) / "evidence" / "证据组1"
        self.assertTrue(group_dir.exists())
        self.assertTrue(group_dir.is_dir())
        
        group_files = list(group_dir.glob("*.txt"))
        self.assertEqual(len(group_files), 2)

if __name__ == "__main__":
    unittest.main()