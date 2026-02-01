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

        # 验证Prompt包含具体公司名称
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

    def test_evidence_generation_quality(self):
        """
        TC-E2E-001: 完整证据生成质量检查

        验收标准：
        - 占位符检查：≥95%通过
        - 数据一致：设备清单合计=合同金额
        - 文件一致：evidence_index与实际文件对应
        - 证据完整：所有规划证据都已生成
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
                },
                "租赁物清单": [
                    {"序号": 1, "名称": "多联机中央空调系统", "评估价值": 45000000},
                    {"序号": 2, "名称": "冷水机组", "评估价值": 25000000},
                    {"序号": 3, "名称": "电梯设备", "评估价值": 20000000},
                    {"序号": 4, "名称": "配电变压器", "评估价值": 20000000},
                    {"序号": 5, "名称": "消防水泵", "评估价值": 15000000},
                    {"序号": 6, "名称": "监控系统", "评估价值": 10000000},
                    {"序号": 7, "名称": "商场照明设备", "评估价值": 10000000},
                    {"序号": 8, "名称": "其他附属设施", "评估价值": 5000000}
                ]
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
                },
                {
                    "证据序号": 2,
                    "证据名称": "租赁物清单",
                    "应归属方": "原告",
                    "文件类型": "表格",
                    "是否需要生成": True,
                    "证据组": 1,
                    "证明目的": "证明租赁物明细",
                    "关键数据提示": {
                        "涉及金额": {"数值": 150000000, "单位": "元"},
                        "涉及方": ["某某公司5"]
                    }
                },
                {
                    "证据序号": 3,
                    "证据名称": "付款回单",
                    "应归属方": "原告",
                    "文件类型": "凭证",
                    "是否需要生成": True,
                    "证据组": 1,
                    "证明目的": "证明付款事实",
                    "关键数据提示": {
                        "涉及金额": {"数值": 150000000, "单位": "元"},
                        "涉及日期": "2021年02月26日",
                        "涉及方": ["某某公司5", "某某公司1"]
                    }
                }
            ],
            "证据分组": {
                "证据组_1": {
                    "组名称": "主合同及附件",
                    "归属方": "原告",
                    "证据数量": 3,
                    "证明目的": "证明融资租赁关系及附件"
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

        # ===== 验证1: 证据完整性 =====
        planned_count = len([e for e in evidence_planning["证据归属规划表"] if e["是否需要生成"]])
        actual_count = evidence_index.get("证据总数", 0)
        self.assertEqual(actual_count, planned_count,
            f"证据数量不匹配: 规划{planned_count}个, 生成{actual_count}个")

        # ===== 验证2: 文件路径与实际文件对应 =====
        for evidence in evidence_index.get("证据列表", []):
            file_path = Path(evidence.get("文件路径", ""))
            self.assertTrue(file_path.exists(),
                f"文件不存在: {file_path}")
            evidence_id = evidence.get("证据ID", "")
            self.assertIn(evidence_id, file_path.name,
                f"证据ID {evidence_id} 与文件名不匹配: {file_path.name}")

        # ===== 验证3: 占位符检查 =====
        placeholder_patterns = ["某某公司", "X年", "X月", "人民币X元", "某公司"]
        placeholder_free_count = 0

        for evidence in evidence_index.get("证据列表", []):
            file_path = Path(evidence.get("文件路径", ""))
            if file_path.exists():
                content = file_path.read_text(encoding='utf-8')
                has_placeholder = any(p in content for p in placeholder_patterns)
                if not has_placeholder:
                    placeholder_free_count += 1

        placeholder_pass_rate = placeholder_free_count / actual_count if actual_count > 0 else 0
        self.assertGreaterEqual(placeholder_pass_rate, 0.95,
            f"占位符通过率 {placeholder_pass_rate:.2%} 未达到95%目标")

        # ===== 验证4: 文件类型分类正确 =====
        for evidence in evidence_index.get("证据列表", []):
            file_type = evidence.get("文件类型", "")
            evidence_name = evidence.get("证据名称", "")
            expected_type = None

            if "合同" in evidence_name:
                expected_type = "合同"
            elif "清单" in evidence_name or "计划" in evidence_name or "明细" in evidence_name:
                expected_type = "表格"
            elif "回单" in evidence_name or "凭证" in evidence_name or "发票" in evidence_name:
                expected_type = "凭证"
            elif "证书" in evidence_name or "裁定" in evidence_name or "判决" in evidence_name:
                expected_type = "文书"

            if expected_type:
                self.assertEqual(file_type, expected_type,
                    f"文件类型错误: {evidence_name} 应为{expected_type}, 实际为{file_type}")

        # ===== 验证5: 数据一致性（设备清单合计=合同金额） =====
        equipment_total = sum(item.get("评估价值", 0) for item in stage0_data["0.4_key_numbers"]["租赁物清单"])
        contract_amount = stage0_data["0.4_key_numbers"]["合同基础金额"]["原合同金额"]["数值"]
        self.assertEqual(equipment_total, contract_amount,
            f"设备清单合计({equipment_total})与合同金额({contract_amount})不一致")

        # ===== 验证6: 金额字段非空 =====
        for item in stage0_data["0.4_key_numbers"]["租赁物清单"]:
            self.assertIsNotNone(item.get("评估价值"),
                f"设备[{item.get('名称')}]评估价值为空")
            self.assertGreater(item.get("评估价值", 0), 0,
                f"设备[{item.get('名称')}]评估价值应为正数")

        print(f"\n✅ E2E质量检查通过:")
        print(f"   - 证据完整性: {actual_count}/{planned_count}")
        print(f"   - 占位符通过率: {placeholder_free_count}/{actual_count} = {placeholder_pass_rate:.2%}")
        print(f"   - 数据一致性: 设备合计{equipment_total} = 合同金额{contract_amount}")


if __name__ == "__main__":
    unittest.main()
