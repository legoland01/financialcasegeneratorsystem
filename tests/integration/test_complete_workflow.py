#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整工作流测试
测试系统从输入到输出的完整流程
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
import sys
import time

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.services.stage0.stage0_service import Stage0Service
from src.services.stage1.stage1_service import Stage1Service
from src.services.evidence_file_generator import EvidenceFileGenerator
from src.utils import LLMClient

class TestCompleteWorkflow(unittest.TestCase):
    """完整工作流测试"""
    
    def setUp(self):
        """测试前置设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # 创建临时输出目录
        self.outputs_dir = self.temp_path / "outputs"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # 测试判决书内容（简化版）
        self.test_judgment_text = """
        上海金融法院
        民事判决书
        
        （2024）沪74民初245号
        
        原告：某某公司5
        被告：某某公司1、某某公司2、某某公司3、某某公司4、某某公司5、某某公司6、某某公司7、某某公司8、某某公司9
        
        案由：融资租赁合同纠纷
        
        诉讼请求：
        1. 判令被告支付租金120,467,622.06元；
        2. 判令被告支付违约金；
        3. 判令原告对抵押物享有优先受偿权；
        4. 判令被告承担律师费200,000元、保全保险费121,663.17元。
        """
        
        # 创建测试判决书文件
        self.judgment_file = self.temp_path / "test_judgment.txt"
        self.judgment_file.write_text(self.test_judgment_text, encoding='utf-8')
    
    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_stage0_processing(self):
        """测试阶段0处理"""
        stage0_service = Stage0Service(
            prompt_dir="prompts",
            output_dir=str(self.outputs_dir / "stage0")
        )
        
        # 运行阶段0
        result = stage0_service.run_all(str(self.judgment_file))
        
        # 验证输出文件
        stage0_files = [
            "0.1_structured_extraction.json",
            "0.2_anonymization_plan.json", 
            "0.3_transaction_reconstruction.json",
            "0.4_key_numbers.json",
            "0.5_evidence_planning.json"
        ]
        
        for filename in stage0_files:
            file_path = self.outputs_dir / "stage0" / filename
            self.assertTrue(file_path.exists(), f"文件 {filename} 不存在")
    
    def test_new_architecture_workflow(self):
        """测试新架构工作流"""
        # 先运行阶段0
        stage0_service = Stage0Service(
            prompt_dir="prompts",
            output_dir=str(self.outputs_dir / "stage0")
        )
        
        stage0_result = stage0_service.run_all(str(self.judgment_file))
        
        # 加载阶段0数据
        stage0_data = {}
        for filename in ["0.1_structured_extraction.json", "0.2_anonymization_plan.json", 
                        "0.3_transaction_reconstruction.json", "0.4_key_numbers.json", 
                        "0.5_evidence_planning.json"]:
            file_path = self.outputs_dir / "stage0" / filename
            stage0_data[filename] = json.loads(file_path.read_text(encoding='utf-8'))
        
        # 运行新架构证据生成
        evidence_generator = EvidenceFileGenerator(
            prompt_dir="prompts",
            output_dir=str(self.outputs_dir / "evidence"),
            llm_client=LLMClient()
        )
        
        evidence_index = evidence_generator.generate_all_evidence_files(
            stage0_data=stage0_data,
            evidence_planning=stage0_data["0.5_evidence_planning.json"],
            party="原告"
        )
        
        # 验证新架构输出
        self.assertIn("证据总数", evidence_index)
        self.assertGreater(evidence_index["证据总数"], 0)
        
        # 验证文件结构
        evidence_files = list((self.outputs_dir / "evidence").glob("evidence/证据组*/*.txt"))
        self.assertEqual(len(evidence_files), evidence_index["证据总数"])
        
        # 验证索引文件
        index_file = self.outputs_dir / "evidence" / "evidence_index.json"
        self.assertTrue(index_file.exists())
    
    def test_end_to_end_timing(self):
        """测试端到端性能"""
        start_time = time.time()
        
        # 运行完整流程
        stage0_service = Stage0Service(
            prompt_dir="prompts",
            output_dir=str(self.outputs_dir / "stage0")
        )
        
        stage0_result = stage0_service.run_all(str(self.judgment_file))
        
        # 加载数据并运行新架构
        stage0_data = {}
        for filename in ["0.1_structured_extraction.json", "0.2_anonymization_plan.json", 
                        "0.3_transaction_reconstruction.json", "0.4_key_numbers.json", 
                        "0.5_evidence_planning.json"]:
            file_path = self.outputs_dir / "stage0" / filename
            stage0_data[filename] = json.loads(file_path.read_text(encoding='utf-8'))
        
        evidence_generator = EvidenceFileGenerator(
            prompt_dir="prompts",
            output_dir=str(self.outputs_dir / "evidence"),
            llm_client=LLMClient()
        )
        
        evidence_index = evidence_generator.generate_all_evidence_files(
            stage0_data=stage0_data,
            evidence_planning=stage0_data["0.5_evidence_planning.json"],
            party="原告"
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 验证性能（应在合理时间内完成）
        self.assertLess(execution_time, 60.0, "执行时间超过60秒")
        print(f"完整流程执行时间: {execution_time:.2f}秒")
    
    def test_data_consistency(self):
        """测试数据一致性"""
        # 运行阶段0
        stage0_service = Stage0Service(
            prompt_dir="prompts",
            output_dir=str(self.outputs_dir / "stage0")
        )
        
        stage0_result = stage0_service.run_all(str(self.judgment_file))
        
        # 加载数据
        stage0_data = {}
        for filename in ["0.1_structured_extraction.json", "0.2_anonymization_plan.json", 
                        "0.3_transaction_reconstruction.json", "0.4_key_numbers.json", 
                        "0.5_evidence_planning.json"]:
            file_path = self.outputs_dir / "stage0" / filename
            stage0_data[filename] = json.loads(file_path.read_text(encoding='utf-8'))
        
        # 运行新架构
        evidence_generator = EvidenceFileGenerator(
            prompt_dir="prompts",
            output_dir=str(self.outputs_dir / "evidence"),
            llm_client=LLMClient()
        )
        
        evidence_index = evidence_generator.generate_all_evidence_files(
            stage0_data=stage0_data,
            evidence_planning=stage0_data["0.5_evidence_planning.json"],
            party="原告"
        )
        
        # 验证数据一致性
        evidence_planning = stage0_data["0.5_evidence_planning.json"]
        plaintiff_evidence = [e for e in evidence_planning["证据归属规划表"] 
                             if e["应归属方"] == "原告"]
        
        self.assertEqual(evidence_index["证据总数"], len(plaintiff_evidence))
        
        # 验证每个证据组的信息
        for group in evidence_index["证据组列表"]:
            group_id = group["组编号"]
            group_evidences = [e for e in plaintiff_evidence if e["证据组"] == group_id]
            self.assertEqual(group["证据数量"], len(group_evidences))

if __name__ == "__main__":
    unittest.main()