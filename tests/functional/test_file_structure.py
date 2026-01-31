#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件结构验证测试
验证生成文件的目录结构和命名规范
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

class TestFileStructure(unittest.TestCase):
    """文件结构验证测试"""
    
    def setUp(self):
        """测试前置设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # 模拟阶段0数据
        self.stage0_data = {
            "0.1_structured_extraction": {"案件基本信息": {}},
            "0.2_anonymization_plan": {"人物Profile库": {}, "公司Profile库": {}},
            "0.3_transaction_reconstruction": {"交易时间线": []},
            "0.4_key_numbers": {"融资本金": 150000000},
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
                        "证据名称": "《融资租赁合同（售后回租）》及公证书",
                        "应归属方": "原告",
                        "文件类型": "合同",
                        "是否需要生成": True,
                        "证据组": 1,
                        "证明目的": "证明融资租赁关系成立"
                    },
                    {
                        "证据序号": 3,
                        "证据名称": "《抵押合同（单位）》",
                        "应归属方": "原告",
                        "文件类型": "合同",
                        "是否需要生成": True,
                        "证据组": 2,
                        "证明目的": "证明抵押担保关系"
                    }
                ],
                "证据分组": {
                    "证据组_1": {
                        "组名称": "主合同文件",
                        "归属方": "原告",
                        "证据数量": 2,
                        "证明目的": "证明融资租赁基础法律关系"
                    },
                    "证据组_2": {
                        "组名称": "抵押担保文件",
                        "归属方": "原告",
                        "证据数量": 1,
                        "证明目的": "证明抵押担保关系"
                    }
                }
            }
        }
    
    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_directory_structure(self):
        """测试目录结构"""
        generator = EvidenceFileGenerator(
            prompt_dir="prompts",
            output_dir=str(self.temp_path),
            llm_client=LLMClient()
        )
        
        # 生成证据文件
        evidence_index = generator.generate_all_evidence_files(
            stage0_data=self.stage0_data,
            evidence_planning=self.stage0_data["0.5_evidence_planning"],
            party="原告"
        )
        
        # 验证证据组目录直接位于output_dir下（与实际实现一致）
        group1_dir = self.temp_path / "证据组1"
        group2_dir = self.temp_path / "证据组2"

        self.assertTrue(group1_dir.exists())
        self.assertTrue(group1_dir.is_dir())
        self.assertTrue(group2_dir.exists())
        self.assertTrue(group2_dir.is_dir())
        
        # 验证索引文件
        index_file = self.temp_path / "evidence_index.json"
        self.assertTrue(index_file.exists())
    
    def test_file_naming_convention(self):
        """测试文件命名规范"""
        generator = EvidenceFileGenerator(
            prompt_dir="prompts",
            output_dir=str(self.temp_path),
            llm_client=LLMClient()
        )
        
        # 生成证据文件
        evidence_index = generator.generate_all_evidence_files(
            stage0_data=self.stage0_data,
            evidence_planning=self.stage0_data["0.5_evidence_planning"],
            party="原告"
        )
        
        # 验证文件命名格式
        for evidence in evidence_index["证据列表"]:
            file_path = Path(evidence["文件路径"])
            filename = file_path.name
            
            # 验证命名格式：证据组{N}_E{XXX}_{证据名称简写}.txt
            expected_prefix = f"证据组{evidence['证据组']}_"
            expected_evidence_id = evidence["证据ID"]  # 已经是 "E001" 格式
            
            self.assertTrue(filename.startswith(expected_prefix),
                f"文件名 {filename} 应以 {expected_prefix} 开头")
            self.assertIn(expected_evidence_id, filename,
                f"文件名 {filename} 应包含 {expected_evidence_id}")
            self.assertTrue(filename.endswith(".txt"),
                f"文件名 {filename} 应以 .txt 结尾")
    
    def test_file_distribution(self):
        """测试文件在证据组中的分布"""
        generator = EvidenceFileGenerator(
            prompt_dir="prompts",
            output_dir=str(self.temp_path),
            llm_client=LLMClient()
        )
        
        # 生成证据文件
        evidence_index = generator.generate_all_evidence_files(
            stage0_data=self.stage0_data,
            evidence_planning=self.stage0_data["0.5_evidence_planning"],
            party="原告"
        )
        
        # 验证文件分布（证据组目录直接位于output_dir下）
        group1_files = list((self.temp_path / "证据组1").glob("*.txt"))
        group2_files = list((self.temp_path / "证据组2").glob("*.txt"))
        
        self.assertEqual(len(group1_files), 2)  # 证据组1应该有2个文件
        self.assertEqual(len(group2_files), 1)  # 证据组2应该有1个文件
        
        # 验证文件内容不为空
        for file_path in group1_files + group2_files:
            content = file_path.read_text(encoding='utf-8')
            self.assertGreater(len(content), 0)
    
    def test_index_file_structure(self):
        """测试索引文件结构"""
        generator = EvidenceFileGenerator(
            prompt_dir="prompts",
            output_dir=str(self.temp_path),
            llm_client=LLMClient()
        )
        
        # 生成证据文件
        evidence_index = generator.generate_all_evidence_files(
            stage0_data=self.stage0_data,
            evidence_planning=self.stage0_data["0.5_evidence_planning"],
            party="原告"
        )
        
        # 读取索引文件
        index_file = self.temp_path / "evidence_index.json"
        index_data = json.loads(index_file.read_text(encoding='utf-8'))
        
        # 验证索引文件结构
        required_keys = ["证据总数", "证据组数", "证据列表", "证据组列表"]
        for key in required_keys:
            self.assertIn(key, index_data)
        
        # 验证统计数据
        self.assertEqual(index_data["证据总数"], 3)
        self.assertEqual(index_data["证据组数"], 2)
        
        # 验证证据列表
        evidence_list = index_data["证据列表"]
        self.assertEqual(len(evidence_list), 3)
        
        for evidence in evidence_list:
            required_evidence_keys = [
                "证据ID", "证据组", "证据名称", "证据名称简写", 
                "文件类型", "归属方", "文件路径", "文件大小"
            ]
            for key in required_evidence_keys:
                self.assertIn(key, evidence)
        
        # 验证证据组列表
        group_list = index_data["证据组列表"]
        self.assertEqual(len(group_list), 2)
        
        for group in group_list:
            required_group_keys = ["组编号", "组名称", "证据数量", "证明目的"]
            for key in required_group_keys:
                self.assertIn(key, group)
    
    def test_file_path_consistency(self):
        """测试文件路径一致性"""
        generator = EvidenceFileGenerator(
            prompt_dir="prompts",
            output_dir=str(self.temp_path),
            llm_client=LLMClient()
        )
        
        # 生成证据文件
        evidence_index = generator.generate_all_evidence_files(
            stage0_data=self.stage0_data,
            evidence_planning=self.stage0_data["0.5_evidence_planning"],
            party="原告"
        )
        
        # 验证每个证据文件路径的有效性
        for evidence in evidence_index["证据列表"]:
            file_path = Path(evidence["文件路径"])
            
            # 验证文件存在
            self.assertTrue(file_path.exists(), f"文件不存在: {file_path}")
            
            # 验证文件大小
            self.assertGreater(evidence["文件大小"], 0)
            
            # 验证文件大小与实际文件大小一致
            actual_size = file_path.stat().st_size
            self.assertEqual(evidence["文件大小"], actual_size)
    
    def test_directory_permissions(self):
        """测试目录权限"""
        generator = EvidenceFileGenerator(
            prompt_dir="prompts",
            output_dir=str(self.temp_path),
            llm_client=LLMClient()
        )
        
        # 生成证据文件
        evidence_index = generator.generate_all_evidence_files(
            stage0_data=self.stage0_data,
            evidence_planning=self.stage0_data["0.5_evidence_planning"],
            party="原告"
        )
        
        # 验证证据组目录可直接访问（与实际实现一致）
        group1_dir = self.temp_path / "证据组1"
        self.assertTrue(group1_dir.is_dir())
        self.assertTrue(Path(group1_dir).exists())

        # 验证可以列出目录内容
        try:
            list(group1_dir.iterdir())
        except PermissionError:
            self.fail("无法访问证据目录")
        
        # 验证可以读取文件
        for evidence in evidence_index["证据列表"]:
            file_path = Path(evidence["文件路径"])
            try:
                content = file_path.read_text(encoding='utf-8')
                self.assertGreater(len(content), 0)
            except PermissionError:
                self.fail(f"无法读取文件: {file_path}")

if __name__ == "__main__":
    unittest.main()