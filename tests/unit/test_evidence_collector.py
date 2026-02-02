"""
Unit tests for evidence_collector.py - F2.4
"""

import pytest
import tempfile
from pathlib import Path
from src.core.evidence_collector import EvidenceCollector
from src.core.data_models import (
    EvidenceRequirements, EvidenceRequirement, EvidenceItem,
    EvidenceType, CaseType
)


@pytest.fixture
def sample_judgment_file(tmp_path):
    """创建测试用的判决书文件"""
    content = """
原告：测试原告公司
住所地：北京市朝阳区
法定代表人：张三

被告：测试被告公司
住所地：上海市浦东新区
法定代表人：李四

原告与被告于2023年1月15日签订《融资租赁合同》。
合同金额为人民币1,500,000元。
被告已支付人民币300,000元。
    """.strip()
    judgment_file = tmp_path / "judgment.txt"
    judgment_file.write_text(content, encoding="utf-8")
    return judgment_file


@pytest.fixture
def sample_requirements():
    """创建测试用的EvidenceRequirements"""
    return EvidenceRequirements(
        requirements=[
            EvidenceRequirement(
                name="融资租赁合同",
                type=EvidenceType.CONTRACT,
                facts_to_prove=["合同成立"],
                claims_supported=["本金"]
            ),
            EvidenceRequirement(
                name="租金收据",
                type=EvidenceType.VOUCHER,
                facts_to_prove=["付款事实"],
                claims_supported=["本金"]
            )
        ],
        case_type=CaseType.FINANCING_LEASE
    )


class TestEvidenceCollector:
    """Test EvidenceCollector class"""

    def test_collect_returns_evidence_collection(self, sample_judgment_file, sample_requirements):
        """测试收集返回EvidenceCollection"""
        collector = EvidenceCollector()
        result = collector.collect(sample_judgment_file, sample_requirements)

        assert result is not None
        assert result.items is not None

    def test_collect_returns_items(self, sample_judgment_file, sample_requirements):
        """测试收集返回证据项"""
        collector = EvidenceCollector()
        result = collector.collect(sample_judgment_file, sample_requirements)

        assert len(result.items) > 0

    def test_collect_item_has_name(self, sample_judgment_file, sample_requirements):
        """测试证据项包含名称"""
        collector = EvidenceCollector()
        result = collector.collect(sample_judgment_file, sample_requirements)

        for item in result.items:
            assert item.name is not None
            assert len(item.name) > 0

    def test_collect_item_has_type(self, sample_judgment_file, sample_requirements):
        """测试证据项包含类型"""
        collector = EvidenceCollector()
        result = collector.collect(sample_judgment_file, sample_requirements)

        for item in result.items:
            assert item.type is not None

    def test_collect_item_has_source(self, sample_judgment_file, sample_requirements):
        """测试证据项包含来源"""
        collector = EvidenceCollector()
        result = collector.collect(sample_judgment_file, sample_requirements)

        for item in result.items:
            assert item.source is not None

    def test_collect_has_from_judgment_list(self, sample_judgment_file, sample_requirements):
        """测试收集包含来自判决书的证据列表"""
        collector = EvidenceCollector()
        result = collector.collect(sample_judgment_file, sample_requirements)

        assert result.from_judgment is not None


class TestEvidenceCollectorEdgeCases:
    """Test edge cases"""

    def test_collect_empty_requirements(self, sample_judgment_file):
        """测试空证据需求"""
        collector = EvidenceCollector()
        requirements = EvidenceRequirements(requirements=[], case_type=CaseType.FINANCING_LEASE)

        result = collector.collect(sample_judgment_file, requirements)

        assert result is not None
        assert len(result.items) >= 0

    def test_collect_with_llm_client(self, sample_judgment_file, sample_requirements):
        """测试使用LLM客户端"""
        class MockLLMClient:
            def complete(self, prompt):
                return '{"items": []}'

        collector = EvidenceCollector(llm_client=MockLLMClient())
        result = collector.collect(sample_judgment_file, sample_requirements)

        assert result is not None
