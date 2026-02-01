#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
黑盒测试：Prompt构建策略
使用真实数据和LLM验证Prompt构建效果

测试用例来源：docs/测试用例_TD-2026-02-01-002_Prompt构建策略.md
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.services.evidence_file_generator import EvidenceFileGenerator
from src.utils import LLMClient


class TestPromptBuilderBlackbox(unittest.TestCase):
    """
    黑盒测试：Prompt构建策略
    使用真实stage0数据和LLM验证生成效果
    """

    def setUp(self):
        """测试前置设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.outputs_dir = self.temp_path / "outputs"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

        # 使用真实的stage0数据（从已有文件加载）
        stage0_dir = project_root / "outputs" / "stage0"
        if stage0_dir.exists():
            self.stage0_data = {}
            for f in stage0_dir.glob("0.*.json"):
                key = f.stem
                with open(f, 'r', encoding='utf-8') as fp:
                    self.stage0_data[key] = json.load(fp)
        else:
            self.stage0_data = self._get_sample_stage0_data()

    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def _get_sample_stage0_data(self):
        """获取示例stage0数据（使用真实数据格式）"""
        return {
            "0.2_anonymization_plan": {
                "公司Profile库": {
                    "公司标识_1": {
                        "公司名称": "国信金融租赁股份有限公司",
                        "统一社会信用代码": "91310000123456789X",
                        "法定代表人": "周明远",
                        "注册地址": "中国（上海）自由贸易试验区世纪大道100号",
                        "原脱敏标识": "某某公司5"
                    },
                    "公司标识_2": {
                        "公司名称": "江西洪城商业管理有限公司",
                        "统一社会信用代码": "91360121MA35T12345",
                        "法定代表人": "吴国栋",
                        "注册地址": "江西省南昌市南昌县莲塘镇向阳路88号",
                        "原脱敏标识": "某某公司1"
                    }
                }
            },
            "0.4_key_numbers": {
                "合同基础金额": {
                    "原合同金额": {
                        "数值": 150000000,
                        "单位": "元",
                        "大写": "壹亿伍仟万元整"
                    }
                }
            }
        }

    def test_build_evidence_prompt_contains_company_names(self):
        """
        TC-PB-006: 验证生成的Prompt包含具体公司名称

        验收标准：100%包含具体公司名称
        """
        evidence = {
            "证据名称": "融资租赁合同",
            "证据组": 1,
            "证据序号": 1,
            "文件类型": "合同",
            "关键数据提示": {
                "涉及金额": {"数值": 150000000, "单位": "元"},
                "涉及日期": "2021年02月24日",
                "涉及方": ["某某公司5", "某某公司1"]
            }
        }

        generator = EvidenceFileGenerator(
            prompt_dir=str(project_root / "prompts"),
            output_dir=str(self.outputs_dir),
            llm_client=LLMClient()
        )

        prompt = generator.build_evidence_prompt(evidence, self.stage0_data)

        # 验证Prompt包含具体公司名称（从真实数据中提取）
        # 某某公司5 -> 国信金融租赁股份有限公司
        # 某某公司1 -> 江西洪城商业管理有限公司
        self.assertIn("国信金融租赁股份有限公司", prompt)
        self.assertIn("江西洪城商业管理有限公司", prompt)

    def test_build_evidence_prompt_contains_amount(self):
        """
        TC-PB-006: 验证生成的Prompt包含具体金额

        验收标准：100%包含具体金额
        """
        evidence = {
            "证据名称": "融资租赁合同",
            "证据组": 1,
            "证据序号": 1,
            "文件类型": "合同",
            "关键数据提示": {
                "涉及金额": {"数值": 150000000, "单位": "元"},
                "涉及日期": "2021年02月24日",
                "涉及方": ["某某公司5", "某某公司1"]
            }
        }

        generator = EvidenceFileGenerator(
            prompt_dir=str(project_root / "prompts"),
            output_dir=str(self.outputs_dir),
            llm_client=LLMClient()
        )

        prompt = generator.build_evidence_prompt(evidence, self.stage0_data)

        # 验证Prompt包含具体金额（实际格式带逗号）
        self.assertIn("150,000,000", prompt)
        self.assertIn("壹亿伍仟万元", prompt)

    def test_build_evidence_prompt_contains_date(self):
        """
        TC-PB-006: 验证生成的Prompt包含具体日期

        验收标准：100%包含具体日期
        """
        evidence = {
            "证据名称": "融资租赁合同",
            "证据组": 1,
            "证据序号": 1,
            "文件类型": "合同",
            "关键数据提示": {
                "涉及金额": {"数值": 150000000, "单位": "元"},
                "涉及日期": "2021年02月24日",
                "涉及方": ["某某公司5", "某某公司1"]
            }
        }

        generator = EvidenceFileGenerator(
            prompt_dir=str(project_root / "prompts"),
            output_dir=str(self.outputs_dir),
            llm_client=LLMClient()
        )

        prompt = generator.build_evidence_prompt(evidence, self.stage0_data)

        # 验证Prompt包含具体日期
        self.assertIn("2021年02月24日", prompt)

    def test_build_evidence_prompt_forbids_placeholders(self):
        """
        TC-PB-006: 验证生成的Prompt包含禁止占位符警告

        验收标准：100%包含禁止占位符警告
        """
        evidence = {
            "证据名称": "融资租赁合同",
            "证据组": 1,
            "证据序号": 1,
            "文件类型": "合同",
            "关键数据提示": {
                "涉及金额": {"数值": 150000000, "单位": "元"},
                "涉及日期": "2021年02月24日",
                "涉及方": ["某某公司5", "某某公司1"]
            }
        }

        generator = EvidenceFileGenerator(
            prompt_dir=str(project_root / "prompts"),
            output_dir=str(self.outputs_dir),
            llm_client=LLMClient()
        )

        prompt = generator.build_evidence_prompt(evidence, self.stage0_data)

        # 验证Prompt包含禁止占位符警告（匹配HTML标签包裹的格式）
        self.assertIn("使用以下占位符", prompt)
        self.assertIn("某某公司", prompt)


class TestPromptBuilderE2E(unittest.TestCase):
    """
    E2E测试：完整流程验证
    """

    def setUp(self):
        """测试前置设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.outputs_dir = self.temp_path / "outputs"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """测试后清理"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_evidence_generation_no_placeholders(self):
        """
        TC-E2E-001: 验证证据生成无占位符

        验收标准：≥95%通过率
        """
        stage0_data = {
            "0.2_anonymization_plan": {
                "公司Profile库": {
                    "公司标识_1": {
                        "公司名称": "国信金融租赁股份有限公司",
                        "统一社会信用代码": "91310000123456789X",
                        "法定代表人": "周明远",
                        "注册地址": "中国（上海）自由贸易试验区世纪大道100号",
                        "原脱敏标识": "某某公司5"
                    },
                    "公司标识_2": {
                        "公司名称": "江西洪城商业管理有限公司",
                        "统一社会信用代码": "91360121MA35T12345",
                        "法定代表人": "吴国栋",
                        "注册地址": "江西省南昌市南昌县莲塘镇向阳路88号",
                        "原脱敏标识": "某某公司1"
                    }
                }
            },
            "0.4_key_numbers": {
                "合同基础金额": {
                    "原合同金额": {
                        "数值": 150000000,
                        "单位": "元",
                        "大写": "壹亿伍仟万元整"
                    }
                }
            }
        }

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

        generator = EvidenceFileGenerator(
            prompt_dir=str(project_root / "prompts"),
            output_dir=str(self.outputs_dir),
            llm_client=LLMClient()
        )

        evidence_index = generator.generate_all_evidence_files(
            stage0_data=stage0_data,
            evidence_planning=evidence_planning,
            party="原告"
        )

        # 验证生成的证据文件
        total = evidence_index.get("证据总数", 0)
        self.assertGreater(total, 0)

        # 检查每个证据文件
        clean_count = 0
        placeholder_patterns = ["某某公司", "X年", "X月", "人民币X元"]

        for evidence in evidence_index.get("证据列表", []):
            file_path = Path(evidence.get("文件路径", ""))
            if file_path.exists():
                content = file_path.read_text(encoding='utf-8')
                has_placeholder = any(p in content for p in placeholder_patterns)
                if not has_placeholder:
                    clean_count += 1

        # 计算通过率
        pass_rate = clean_count / total if total > 0 else 0
        print(f"通过率: {clean_count}/{total} = {pass_rate:.2%}")

        # 验证通过率≥95%
        self.assertGreaterEqual(pass_rate, 0.95,
            f"通过率 {pass_rate:.2%} 未达到95%目标")


if __name__ == "__main__":
    unittest.main()
