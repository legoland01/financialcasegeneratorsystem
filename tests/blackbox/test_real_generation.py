#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实LLM生成质量测试

测试真实LLM生成的内容质量，包括：
- 模糊词检测（某某设备、若干台等）
- 占位符检测
- 数据一致性验证

运行方式：
    REAL_LLM_TEST=1 python3 -m pytest tests/blackbox/test_real_generation.py -v
"""

import unittest
import json
import tempfile
import shutil
import os
import re
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.services.evidence_file_generator import EvidenceFileGenerator
from src.utils import LLMClient


class TestRealEvidenceQuality(unittest.TestCase):
    """
    真实LLM生成质量测试

    仅在设置REAL_LLM_TEST环境变量时运行
    """

    def setUp(self):
        """测试前置设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.outputs_dir = self.temp_path / "outputs"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

        # 使用真实stage0数据
        stage0_dir = project_root / "outputs" / "stage0"
        if stage0_dir.exists():
            self.stage0_data = {}
            for f in stage0_dir.glob("0.*.json"):
                key = f.stem
                with open(f, 'r', encoding='utf-8') as fp:
                    self.stage0_data[key] = json.load(fp)

        # 证据规划（简化版）
        self.evidence_planning = {
            "证据归属规划表": [
                {
                    "证据序号": 1,
                    "证据名称": "融资租赁合同",
                    "应归属方": "原告",
                    "文件类型": "合同",
                    "是否需要生成": True,
                    "证据组": 1,
                    "证明目的": "证明融资租赁关系",
                    "关键数据提示": {
                        "涉及金额": {"数值": 150000000, "单位": "元"},
                        "涉及日期": "2021年02月24日",
                        "涉及方": ["某某公司5", "某某公司1"]
                    }
                }
            ],
            "证据分组": {
                "证据组_1": {
                    "组名称": "主合同",
                    "归属方": "原告",
                    "证据数量": 1,
                    "证明目的": "证明融资租赁关系"
                }
            }
        }

    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_no_vague_words_in_real_generation(self):
        """
        测试真实LLM生成内容不包含模糊词

        验收标准：
        - 无"某某设备"
        - 无"某某型号"
        - 无"若干台"
        - 无"人民币叁仟万元整"
        """
        # 仅在真实LLM测试时运行
        if not os.getenv("REAL_LLM_TEST"):
            self.skipTest("设置REAL_LLM_TEST=1环境变量运行此测试")

        generator = EvidenceFileGenerator(
            prompt_dir=str(project_root / "prompts"),
            output_dir=str(self.outputs_dir),
            llm_client=LLMClient()  # 使用真实LLM
        )

        # 生成证据
        evidence_index = generator.generate_all_evidence_files(
            stage0_data=self.stage0_data,
            evidence_planning=self.evidence_planning,
            party="原告"
        )

        # 模糊词列表（基于用户反馈）
        vague_patterns = [
            "某某设备",
            "某某型号",
            "若干台",
            "若干",
            "人民币叁仟万元整",
            "人民币壹亿伍仟万元整",
        ]

        # 检查每个生成的证据
        for evidence in evidence_index.get("证据列表", []):
            file_path = Path(evidence.get("文件路径", ""))
            if not file_path.exists():
                continue

            content = file_path.read_text(encoding='utf-8')

            # 检测模糊词
            found_vague = []
            for pattern in vague_patterns:
                if pattern in content:
                    found_vague.append(pattern)

            self.assertEqual(
                len(found_vague), 0,
                f"证据{evidence.get('证据名称')}包含模糊词: {found_vague}"
            )

    def test_no_placeholders_in_real_generation(self):
        """
        测试真实LLM生成内容不包含占位符

        验收标准：
        - 无"某某公司X"
        - 无"X年X月X日"
        - 无"人民币X元"
        """
        if not os.getenv("REAL_LLM_TEST"):
            self.skipTest("设置REAL_LLM_TEST=1环境变量运行此测试")

        generator = EvidenceFileGenerator(
            prompt_dir=str(project_root / "prompts"),
            output_dir=str(self.outputs_dir),
            llm_client=LLMClient()
        )

        evidence_index = generator.generate_all_evidence_files(
            stage0_data=self.stage0_data,
            evidence_planning=self.evidence_planning,
            party="原告"
        )

        # 占位符列表
        placeholder_patterns = [
            "某某公司",
            "X年",
            "X月",
            "X日",
            "人民币X元",
            "某公司",
        ]

        for evidence in evidence_index.get("证据列表", []):
            file_path = Path(evidence.get("文件路径", ""))
            if not file_path.exists():
                continue

            content = file_path.read_text(encoding='utf-8')

            found_placeholders = []
            for pattern in placeholder_patterns:
                if pattern in content:
                    found_placeholders.append(pattern)

            self.assertEqual(
                len(found_placeholders), 0,
                f"证据{evidence.get('证据名称')}包含占位符: {found_placeholders}"
            )

    def test_clause_numbering_consistency(self):
        """
        测试合同条款编号连续性

        验收标准：
        - 条款编号不出现断裂（如第4条后直接跟1.1）
        """
        if not os.getenv("REAL_LLM_TEST"):
            self.skipTest("设置REAL_LLM_TEST=1环境变量运行此测试")

        generator = EvidenceFileGenerator(
            prompt_dir=str(project_root / "prompts"),
            output_dir=str(self.outputs_dir),
            llm_client=LLMClient()
        )

        evidence_index = generator.generate_all_evidence_files(
            stage0_data=self.stage0_data,
            evidence_planning=self.evidence_planning,
            party="原告"
        )

        for evidence in evidence_index.get("证据列表", []):
            if "合同" not in evidence.get("证据名称", ""):
                continue

            file_path = Path(evidence.get("文件路径", ""))
            if not file_path.exists():
                continue

            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # 查找条款编号
            clause_numbers = []
            for i, line in enumerate(lines):
                # 匹配"第X条"格式
                if '第' in line and '条' in line:
                    match = re.search(r'第([一二三四五六七八九十\d]+)条', line)
                    if match:
                        clause_numbers.append((i, line.strip()))

            # 检查编号连续性
            if len(clause_numbers) >= 2:
                for i in range(len(clause_numbers) - 1):
                    curr = clause_numbers[i][1]
                    next_line = clause_numbers[i + 1][1]

                    # 如果当前是"第X条"，下一条应该也是"第Y条"
                    if '条' in curr and '条' in next_line:
                        # 简单检查：不应在"第X条"后直接出现"1.1"格式
                        if re.search(r'^\d+\.\d+', next_line.strip()):
                            self.fail(
                                f"证据{evidence.get('证据名称')}条款编号断裂: "
                                f"{curr} 后出现 {next_line}"
                            )

    def test_line_break_consistency(self):
        """
        测试回车符正确放置

        验收标准：
        - 无连续空行
        - 无过长行（>200字符且含条款内容）
        """
        if not os.getenv("REAL_LLM_TEST"):
            self.skipTest("设置REAL_LLM_TEST=1环境变量运行此测试")

        generator = EvidenceFileGenerator(
            prompt_dir=str(project_root / "prompts"),
            output_dir=str(self.outputs_dir),
            llm_client=LLMClient()
        )

        evidence_index = generator.generate_all_evidence_files(
            stage0_data=self.stage0_data,
            evidence_planning=self.evidence_planning,
            party="原告"
        )

        for evidence in evidence_index.get("证据列表", []):
            file_path = Path(evidence.get("文件路径", ""))
            if not file_path.exists():
                continue

            content = file_path.read_text(encoding='utf-8')

            # 检查连续空行
            if '\n\n\n' in content:
                self.fail(
                    f"证据{evidence.get('证据名称')}存在连续空行"
                )

            # 检查过长行
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if len(line) > 200:
                    if '条' in line or '款' in line:
                        self.fail(
                            f"证据{evidence.get('证据名称')}第{i+1}行过长 "
                            f"({len(line)}字符): {line[:50]}..."
                        )


class TestRealGenerationSummary(unittest.TestCase):
    """
    真实生成测试汇总

    运行所有真实LLM生成测试并输出汇总报告
    """

    def test_run_all_real_generation_tests(self):
        """
        运行所有真实LLM生成测试并输出汇总

        这个测试整合所有质量检查，输出详细报告
        """
        if not os.getenv("REAL_LLM_TEST"):
            self.skipTest("设置REAL_LLM_TEST=1环境变量运行此测试")

        # 使用真实stage0数据
        stage0_dir = project_root / "outputs" / "stage0"
        if stage0_dir.exists():
            stage0_data = {}
            for f in stage0_dir.glob("0.*.json"):
                key = f.stem
                with open(f, 'r', encoding='utf-8') as fp:
                    stage0_data[key] = json.load(fp)

        # 证据规划
        evidence_planning = {
            "证据归属规划表": [
                {
                    "证据序号": 1,
                    "证据名称": "融资租赁合同",
                    "应归属方": "原告",
                    "文件类型": "合同",
                    "是否需要生成": True,
                    "证据组": 1,
                    "证明目的": "证明融资租赁关系",
                    "关键数据提示": {
                        "涉及金额": {"数值": 150000000, "单位": "元"},
                        "涉及日期": "2021年02月24日",
                        "涉及方": ["某某公司5", "某某公司1"]
                    }
                }
            ],
            "证据分组": {
                "证据组_1": {
                    "组名称": "主合同",
                    "归属方": "原告",
                    "证据数量": 1,
                    "证明目的": "证明融资租赁关系"
                }
            }
        }

        # 生成证据
        temp_dir = tempfile.mkdtemp()
        try:
            generator = EvidenceFileGenerator(
                prompt_dir=str(project_root / "prompts"),
                output_dir=temp_dir,
                llm_client=LLMClient()
            )

            evidence_index = generator.generate_all_evidence_files(
                stage0_data=stage0_data,
                evidence_planning=evidence_planning,
                party="原告"
            )

            # 质量问题汇总
            issues = {
                "vague_words": [],
                "placeholders": [],
                "clause_issues": [],
                "line_break_issues": [],
            }

            vague_patterns = [
                "某某设备", "某某型号", "若干台", "若干",
                "人民币叁仟万元整", "人民币壹亿伍仟万元整",
            ]
            placeholder_patterns = [
                "某某公司", "X年", "X月", "人民币X元", "某公司",
            ]

            for evidence in evidence_index.get("证据列表", []):
                file_path = Path(evidence.get("文件路径", ""))
                if not file_path.exists():
                    continue

                content = file_path.read_text(encoding='utf-8')
                evidence_name = evidence.get("证据名称", "")

                # 检查模糊词
                for pattern in vague_patterns:
                    if pattern in content:
                        issues["vague_words"].append(
                            f"{evidence_name}: {pattern}"
                        )

                # 检查占位符
                for pattern in placeholder_patterns:
                    if pattern in content:
                        issues["placeholders"].append(
                            f"{evidence_name}: {pattern}"
                        )

            # 输出汇总
            print("\n" + "=" * 60)
            print("真实LLM生成质量测试汇总")
            print("=" * 60)
            print(f"证据总数: {evidence_index.get('证据总数', 0)}")
            print(f"模糊词问题: {len(issues['vague_words'])}")
            print(f"占位符问题: {len(issues['placeholders'])}")

            if issues["vague_words"]:
                print("\n模糊词详情:")
                for item in issues["vague_words"]:
                    print(f"  - {item}")

            if issues["placeholders"]:
                print("\n占位符详情:")
                for item in issues["placeholders"]:
                    print(f"  - {item}")

            # 断言通过
            self.assertEqual(
                len(issues["vague_words"]), 0,
                f"发现{len(issues['vague_words'])}个模糊词问题"
            )
            self.assertEqual(
                len(issues["placeholders"]), 0,
                f"发现{len(issues['placeholders'])}个占位符问题"
            )

            print("\n✅ 真实LLM生成质量测试通过")

        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
