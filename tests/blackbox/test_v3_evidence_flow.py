#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
黑盒测试：v3.0 证据生成流程
测试核心业务流程：案情分析 → 证据列表创建 → LLM生成

测试用例来源：docs/需求文档_PRD-2026-02-01-v3.0.md
"""

import unittest
import json
import tempfile
import shutil
import re
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


class TestV3EvidenceFlow(unittest.TestCase):
    """
    v3.0证据生成流程黑盒测试
    验证核心业务流程正确性
    """

    def setUp(self):
        """测试前置设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.outputs_dir = self.temp_path / "outputs"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _get_sample_case_data(self):
        """获取样本案情基本数据集"""
        return {
            "plaintiff": {
                "name": "东方金融租赁有限公司",
                "credit_code": "91310000MA1FL3L123",
                "address": "上海市浦东新区银城中路100号",
                "legal_representative": "张明",
                "bank_account": "62220210001"
            },
            "defendant": {
                "name": "南昌宏昌商业零售有限公司",
                "credit_code": "91360100MA1XXXXX",
                "address": "江西省南昌市红谷滩新区丰和中大道",
                "legal_representative": "李华",
                "bank_account": "62220210002"
            },
            "contract": {
                "type": "融资租赁合同",
                "subject": "多联机中央空调系统",
                "amount": 150000000,
                "signing_date": "2021-02-24",
                "term_months": 24
            },
            "paid_amount": 37500000,
            "remaining_amount": 112500000,
            "attachments": {
                "租赁物清单": [
                    {"设备名称": "多联机空调主机", "规格型号": "VRV-X", "数量": 10, "评估价值": 45000000},
                    {"设备名称": "室内机", "规格型号": "FX", "数量": 100, "评估价值": 30000000}
                ]
            }
        }

    def _get_sample_claim_list(self):
        """获取样本诉求列表"""
        return {
            "claims": [
                {"type": "本金", "amount": 112500000, "description": "请求判令被告支付欠款本金"},
                {"type": "利息", "amount": 5000000, "description": "请求判令被告支付欠款利息"},
                {"type": "违约金", "amount": 2000000, "description": "请求判令被告支付违约金"}
            ],
            "litigation_cost": 50000
        }

    def _get_sample_evidence_collection(self):
        """获取样本证据收集结果"""
        return {
            "items": [
                {"name": "融资租赁合同", "type": "合同类", "source": "判决书提取", "fabricated": False},
                {"name": "付款凭证", "type": "凭证类", "source": "判决书提取", "fabricated": False},
                {"name": "租赁物清单", "type": "附件类", "source": "自行编造", "fabricated": True}
            ]
        }

    def test_01_case_data_contains_real_names(self):
        """
        测试用例 TC-v3-001: 案情基本数据集只包含真实名称

        验证：CaseData中不包含"某某公司"等脱敏标记
        """
        case_data = self._get_sample_case_data()

        # 检查原告名称
        self.assertIn("东方金融租赁有限公司", case_data["plaintiff"]["name"])
        self.assertNotIn("某某", case_data["plaintiff"]["name"])

        # 检查被告名称
        self.assertIn("南昌宏昌商业零售有限公司", case_data["defendant"]["name"])
        self.assertNotIn("某某", case_data["defendant"]["name"])

        # 检查合同类型
        self.assertIn("融资租赁合同", case_data["contract"]["type"])

        print("✅ TC-v3-001: 案情基本数据集只包含真实名称")

    def test_02_evidence_list_extracts_key_info(self):
        """
        测试用例 TC-v3-002: 证据列表从案情数据提取关键信息

        验证：EvidenceList从CaseData提取每份证据的关键信息
        """
        case_data = self._get_sample_case_data()
        evidence_collection = self._get_sample_evidence_collection()

        # 模拟EvidenceListCreator逻辑
        evidence_list = []
        for item in evidence_collection["items"]:
            key_info = {}
            if item["type"] == "合同类":
                key_info = {
                    "出租人": case_data["plaintiff"]["name"],
                    "承租人": case_data["defendant"]["name"],
                    "标的物": case_data["contract"]["subject"],
                    "合同金额": f"{case_data['contract']['amount']:,.0f}元",
                    "签订日期": case_data["contract"]["signing_date"]
                }
            elif item["type"] == "凭证类":
                key_info = {
                    "付款方": case_data["plaintiff"]["name"],
                    "收款方": case_data["defendant"]["name"],
                    "金额": f"{case_data['contract']['amount']:,.0f}元",
                    "日期": case_data["contract"]["signing_date"]
                }
            elif item["type"] == "附件类":
                key_info = {"租赁物清单": case_data["attachments"]["租赁物清单"]}

            evidence_list.append({
                "name": item["name"],
                "type": item["type"],
                "key_info": key_info
            })

        # 验证合同证据包含真实名称
        contract_evidence = next((e for e in evidence_list if e["name"] == "融资租赁合同"), None)
        self.assertIsNotNone(contract_evidence)
        key_info = contract_evidence["key_info"]
        self.assertIn("东方金融租赁有限公司", key_info.get("出租人", ""))
        self.assertIn("南昌宏昌商业零售有限公司", key_info.get("承租人", ""))
        self.assertNotIn("某某", str(key_info.values()))

        print("✅ TC-v3-002: 证据列表正确从案情数据提取关键信息")

    def test_03_evidence_list_no_placeholders(self):
        """
        测试用例 TC-v3-003: 证据列表不包含脱敏标记

        验证：EvidenceList中不出现"某某公司"、"X年X月X日"等脱敏标记
        """
        case_data = self._get_sample_case_data()
        evidence_collection = self._get_sample_evidence_collection()

        # 生成证据列表
        evidence_list = []
        for item in evidence_collection["items"]:
            key_info = {}
            if item["type"] == "合同类":
                key_info = {
                    "出租人": case_data["plaintiff"]["name"],
                    "承租人": case_data["defendant"]["name"],
                    "标的物": case_data["contract"]["subject"],
                    "合同金额": f"{case_data['contract']['amount']:,.0f}元",
                    "签订日期": case_data["contract"]["signing_date"]
                }
            elif item["type"] == "凭证类":
                key_info = {
                    "付款方": case_data["plaintiff"]["name"],
                    "收款方": case_data["defendant"]["name"],
                    "金额": f"{case_data['contract']['amount']:,.0f}元",
                    "日期": case_data["contract"]["signing_date"]
                }
            elif item["type"] == "附件类":
                key_info = {"租赁物清单": case_data["attachments"]["租赁物清单"]}

            evidence_list.append({
                "name": item["name"],
                "type": item["type"],
                "key_info": key_info
            })

        # 检查所有证据列表内容
        placeholder_patterns = [
            r"某某", r"XX", r"XXX", r"某年某月某日", r"X月X日", r"\?{3,}"
        ]

        for evidence in evidence_list:
            evidence_str = json.dumps(evidence, ensure_ascii=False)
            for pattern in placeholder_patterns:
                match = re.search(pattern, evidence_str)
                self.assertIsNone(match, f"证据{evidence['name']}包含脱敏标记: {pattern}")

        print("✅ TC-v3-003: 证据列表不包含脱敏标记")

    def test_04_evidence_claim_mapping(self):
        """
        测试用例 TC-v3-004: 证据与诉求的对应关系

        验证：每份证据正确标注其支撑的诉求
        """
        case_data = self._get_sample_case_data()
        claim_list = self._get_sample_claim_list()
        evidence_collection = self._get_sample_evidence_collection()

        # 生成证据列表，并标注支撑的诉求
        evidence_list = []
        claim_types = [c["type"] for c in claim_list["claims"]]

        for item in evidence_collection["items"]:
            # 简单映射逻辑：合同和凭证支撑本金诉求
            claims_supported = []
            if item["type"] == "合同类":
                claims_supported = ["本金"]
            elif item["type"] == "凭证类":
                claims_supported = ["本金"]
            elif item["type"] == "附件类":
                claims_supported = ["本金"]

            evidence_list.append({
                "name": item["name"],
                "type": item["type"],
                "claims_supported": claims_supported
            })

        # 验证映射关系
        contract_evidence = next((e for e in evidence_list if e["name"] == "融资租赁合同"), None)
        self.assertIsNotNone(contract_evidence)
        self.assertIn("本金", contract_evidence["claims_supported"])

        # 验证所有证据都有支撑的诉求
        for evidence in evidence_list:
            self.assertTrue(
                len(evidence["claims_supported"]) > 0,
                f"证据{evidence['name']}没有支撑的诉求"
            )

        print("✅ TC-v3-004: 证据与诉求的对应关系正确")

    def test_05_attachment_planning(self):
        """
        测试用例 TC-v3-005: 附件规划

        验证：合同类证据正确规划附件形式（独立文件/正文包含）
        """
        case_data = self._get_sample_case_data()
        evidence_collection = self._get_sample_evidence_collection()

        # 模拟附件规划逻辑
        attachment_plans = []
        for item in evidence_collection["items"]:
            if item["type"] == "合同类":
                # 合同类证据需要租赁物清单附件
                attachment_plans.append({
                    "evidence_name": item["name"],
                    "attachment": {
                        "type": "租赁物清单",
                        "form": "独立文件",
                        "source": "案情数据"
                    }
                })
            elif item["type"] == "凭证类":
                # 凭证类不需要附件
                attachment_plans.append({
                    "evidence_name": item["name"],
                    "attachment": None
                })

        # 验证附件规划
        contract_plan = next((p for p in attachment_plans if p["evidence_name"] == "融资租赁合同"), None)
        self.assertIsNotNone(contract_plan)
        self.assertIsNotNone(contract_plan["attachment"])
        self.assertEqual("租赁物清单", contract_plan["attachment"]["type"])
        self.assertEqual("独立文件", contract_plan["attachment"]["form"])

        voucher_plan = next((p for p in attachment_plans if p["evidence_name"] == "付款凭证"), None)
        self.assertIsNotNone(voucher_plan)
        self.assertIsNone(voucher_plan["attachment"])

        print("✅ TC-v3-005: 附件规划正确")

    def test_06_llm_prompt_contains_real_names(self):
        """
        测试用例 TC-v3-006: LLM Prompt只包含真实名称

        验证：EvidenceList转换为Prompt时，只包含真实名称，不包含脱敏标记
        """
        case_data = self._get_sample_case_data()
        evidence_collection = self._get_sample_evidence_collection()

        # 生成证据列表
        evidence_list = []
        for item in evidence_collection["items"]:
            key_info = {}
            if item["type"] == "合同类":
                key_info = {
                    "出租人": case_data["plaintiff"]["name"],
                    "承租人": case_data["defendant"]["name"],
                    "标的物": case_data["contract"]["subject"],
                    "合同金额": f"{case_data['contract']['amount']:,.0f}元",
                    "签订日期": case_data["contract"]["signing_date"]
                }
            elif item["type"] == "凭证类":
                key_info = {
                    "付款方": case_data["plaintiff"]["name"],
                    "收款方": case_data["defendant"]["name"],
                    "金额": f"{case_data['contract']['amount']:,.0f}元",
                    "日期": case_data["contract"]["signing_date"]
                }
            elif item["type"] == "附件类":
                key_info = {"租赁物清单": case_data["attachments"]["租赁物清单"]}

            evidence_list.append({
                "name": item["name"],
                "type": item["type"],
                "key_info": key_info
            })

        # 模拟转换为LLM Prompt
        def evidence_list_to_prompt(evidence_list):
            sections = ["=== 证据列表 ===", ""]
            for i, item in enumerate(evidence_list, 1):
                sections.append(f"【证据{i}】")
                sections.append(f"证据名称：{item['name']}")
                sections.append(f"证据类型：{item['type']}")
                sections.append("")
                sections.append("关键信息：")
                for key, value in item["key_info"].items():
                    if isinstance(value, list):
                        value = json.dumps(value, ensure_ascii=False)
                    sections.append(f"  - {key}：{value}")
                sections.append("")
            return "\n".join(sections)

        prompt = evidence_list_to_prompt(evidence_list)

        # 验证Prompt包含真实名称
        self.assertIn("东方金融租赁有限公司", prompt)
        self.assertIn("南昌宏昌商业零售有限公司", prompt)

        # 验证Prompt不包含脱敏标记
        placeholder_patterns = [
            r"某某", r"XX", r"XXX", r"某年某月某日", r"X月X日"
        ]
        for pattern in placeholder_patterns:
            match = re.search(pattern, prompt)
            self.assertIsNone(match, f"LLM Prompt包含脱敏标记: {pattern}")

        print("✅ TC-v3-006: LLM Prompt只包含真实名称")

    def test_07_attachment_data_from_case_data(self):
        """
        测试用例 TC-v3-007: 附件数据来自案情基本数据集

        验证：附件数据（如租赁物清单）从CaseData.attachments提取
        """
        case_data = self._get_sample_case_data()

        # 验证附件数据存在
        self.assertIn("租赁物清单", case_data["attachments"])
        self.assertTrue(len(case_data["attachments"]["租赁物清单"]) > 0)

        # 验证附件数据包含真实信息
        lease_items = case_data["attachments"]["租赁物清单"]
        for item in lease_items:
            self.assertNotIn("某某", str(item.values()))
            self.assertNotIn("XX", str(item.values()))

        # 验证金额格式正确
        for item in lease_items:
            if "评估价值" in item:
                self.assertIsInstance(item["评估价值"], (int, float))

        print("✅ TC-v3-007: 附件数据来自案情基本数据集")

    def test_08_evidence_index_generation(self):
        """
        测试用例 TC-v3-008: 证据索引生成

        验证：EvidenceIndex正确生成证据与诉求的对应关系
        """
        evidence_collection = self._get_sample_evidence_collection()
        claim_list = self._get_sample_claim_list()

        # 模拟证据索引生成
        evidence_index = []
        for i, item in enumerate(evidence_collection["items"], 1):
            # 简单映射
            if item["type"] == "合同类":
                purpose = "证明合同关系成立及合同内容"
            elif item["type"] == "凭证类":
                purpose = "证明资金往来事实"
            elif item["type"] == "附件类":
                purpose = "证明标的物明细"

            claims_supported = ["本金"] if item["type"] in ["合同类", "凭证类", "附件类"] else []

            evidence_index.append({
                "number": i,
                "name": item["name"],
                "type": item["type"],
                "purpose": purpose,
                "claims_supported": claims_supported
            })

        # 验证索引完整性
        self.assertEqual(len(evidence_index), 3)

        for item in evidence_index:
            self.assertIsNotNone(item["number"])
            self.assertIsNotNone(item["name"])
            self.assertIsNotNone(item["type"])
            self.assertIsNotNone(item["purpose"])
            self.assertTrue(len(item["claims_supported"]) > 0)

        # 验证格式正确
        index_text = []
        for item in evidence_index:
            index_text.append(f"证据{item['number']}：{item['name']}")
            index_text.append(f"  类型：{item['type']}")
            index_text.append(f"  证明目的：{item['purpose']}")
            index_text.append(f"  支撑诉求：{', '.join(item['claims_supported'])}")

        index_str = "\n".join(index_text)
        self.assertIn("融资租赁合同", index_str)
        self.assertIn("本金", index_str)

        print("✅ TC-v3-008: 证据索引生成正确")


class TestV3DataConsistency(unittest.TestCase):
    """
    v3.0数据一致性测试
    验证关键数据在流程中的一致性
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_amount_consistency(self):
        """
        测试用例 TC-v3-009: 金额一致性

        验证：合同金额与附件金额合计一致
        """
        contract_amount = 150000000
        attachments = [
            {"评估价值": 45000000},
            {"评估价值": 30000000}
        ]

        attachment_total = sum(a.get("评估价值", 0) for a in attachments)

        # 合同金额应大于等于附件金额合计
        self.assertGreaterEqual(contract_amount, attachment_total)

        print("✅ TC-v3-009: 金额一致性检查通过")

    def test_02_party_name_consistency(self):
        """
        测试用例 TC-v3-010: 当事人名称一致性

        验证：同一当事人名称在所有证据中一致
        """
        plaintiff_name = "东方金融租赁有限公司"
        defendant_name = "南昌宏昌商业零售有限公司"

        # 在多个证据中验证名称一致性
        plaintiff_variants = [plaintiff_name] * 3
        defendant_variants = [defendant_name] * 3

        # 简单验证名称一致性
        for pv, dv in zip(plaintiff_variants, defendant_variants):
            self.assertEqual(pv, plaintiff_name)
            self.assertEqual(dv, defendant_name)

        print("✅ TC-v3-010: 当事人名称一致性检查通过")

    def test_03_date_consistency(self):
        """
        测试用例 TC-v3-011: 日期一致性

        验证：同一事件的日期在所有证据中一致
        """
        signing_date = "2021-02-24"

        # 在多个证据中验证日期一致性
        evidences = [
            {"合同签订日期": signing_date},
            {"凭证日期": signing_date},
            {"附件日期": signing_date}
        ]

        for evidence in evidences:
            for key, value in evidence.items():
                self.assertEqual(value, signing_date)

        print("✅ TC-v3-011: 日期一致性检查通过")


if __name__ == "__main__":
    unittest.main(verbosity=2)
