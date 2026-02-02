"""
test_main.py - Main模块单元测试

测试FinancialCaseGenerator和GenerationResult的核心功能。
"""

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
import tempfile
import os

from src.core.main import FinancialCaseGenerator, GenerationResult
from src.core.data_models import (
    CaseData,
    Party,
    ContractInfo,
    BreachInfo,
    ClaimList,
    Claim,
    CaseType,
    EvidenceList,
    EvidenceListItem,
    EvidenceIndex,
    GeneratedEvidence,
    EvidenceType
)


class TestGenerationResult:
    """GenerationResult测试类"""
    
    def test_init_default_values(self):
        """测试默认初始化值"""
        result = GenerationResult(success=True)
        
        assert result.success is True
        assert result.case_data is None
        assert result.claim_list is None
        assert result.evidence_list is None
        assert result.evidence_index is None
        assert result.generated_evidence == []
        assert result.litigation_complaint is None
        assert result.validation_report is None
        assert result.output_dir is None
        assert result.errors == []
        assert result.generated_at is not None
    
    def test_init_with_values(self):
        """测试带值的初始化"""
        case_data = CaseData(
            plaintiff=Party(
                name="原告",
                credit_code="91310000123456789A",
                address="地址",
                legal_representative="甲"
            ),
            defendant=Party(
                name="被告",
                credit_code="91110108123456789B",
                address="地址",
                legal_representative="乙"
            ),
            contract=ContractInfo(
                type=CaseType.FINANCING_LEASE,
                subject="设备",
                amount=1000000.00,
                signing_date=datetime(2022, 1, 1)
            )
        )
        
        claim_list = ClaimList(
            claims=[Claim(type="本金", amount=1000000.00)]
        )
        
        evidence_list = EvidenceList(
            items=[
                EvidenceListItem(
                    name="合同",
                    type=EvidenceType.CONTRACT,
                    key_info={"金额": "1000000"},
                    claims_supported=["本金"]
                )
            ],
            case_type=CaseType.FINANCING_LEASE
        )
        
        evidence_index = EvidenceIndex(
            items=[],
            total_count=1
        )
        
        generated_evidence = [
            GeneratedEvidence(
                filename="001_合同.txt",
                content="合同内容",
                evidence_type=EvidenceType.CONTRACT
            )
        ]
        
        validation_report = {
            "is_valid": True,
            "score": 100,
            "issues": []
        }
        
        output_dir = Path("/tmp/test")
        
        result = GenerationResult(
            success=True,
            case_data=case_data,
            claim_list=claim_list,
            evidence_list=evidence_list,
            evidence_index=evidence_index,
            generated_evidence=generated_evidence,
            litigation_complaint="起诉状内容",
            validation_report=validation_report,
            output_dir=output_dir,
            errors=[]
        )
        
        assert result.success is True
        assert result.case_data == case_data
        assert result.claim_list == claim_list
        assert result.evidence_list == evidence_list
        assert result.evidence_index == evidence_index
        assert len(result.generated_evidence) == 1
        assert result.litigation_complaint == "起诉状内容"
        assert result.validation_report == validation_report
        assert result.output_dir == output_dir
        assert result.errors == []
    
    def test_init_with_errors(self):
        """测试带错误的初始化"""
        result = GenerationResult(
            success=False,
            errors=["错误1", "错误2"]
        )
        
        assert result.success is False
        assert len(result.errors) == 2
        assert "错误1" in result.errors
        assert "错误2" in result.errors
    
    def test_to_dict(self):
        """测试转换为字典"""
        case_data = CaseData(
            plaintiff=Party(
                name="原告",
                credit_code="91310000123456789A",
                address="地址",
                legal_representative="甲"
            ),
            defendant=Party(
                name="被告",
                credit_code="91110108123456789B",
                address="地址",
                legal_representative="乙"
            ),
            contract=ContractInfo(
                type=CaseType.FINANCING_LEASE,
                subject="设备",
                amount=1000000.00,
                signing_date=datetime(2022, 1, 1)
            )
        )
        
        result = GenerationResult(success=True, case_data=case_data)
        result_dict = result.to_dict()
        
        assert result_dict["success"] is True
        assert "generated_at" in result_dict
        assert result_dict["case_data"]["plaintiff"]["name"] == "原告"
        assert result_dict["evidence_count"] == 0
    
    def test_to_json(self):
        """测试转换为JSON"""
        result = GenerationResult(success=True)
        json_str = result.to_json()
        
        assert isinstance(json_str, str)
        assert '"success": true' in json_str
    
    def test_generated_evidence_default_empty_list(self):
        """测试generated_evidence默认为空列表"""
        result = GenerationResult(success=True)
        assert result.generated_evidence == []
    
    def test_errors_default_empty_list(self):
        """测试errors默认为空列表"""
        result = GenerationResult(success=True)
        assert result.errors == []


class TestFinancialCaseGenerator:
    """FinancialCaseGenerator测试类"""
    
    def test_init_default(self):
        """测试默认初始化"""
        generator = FinancialCaseGenerator()
        
        assert generator.llm_client is None
        assert generator.output_dir == Path("output")
        assert generator.case_analyzer is not None
        assert generator.claim_extractor is not None
        assert generator.evidence_planner is not None
        assert generator.evidence_collector is not None
        assert generator.evidence_list_creator is not None
        assert generator.document_generator is not None
        assert generator.evidence_index_generator is not None
        assert generator.pdf_generator is not None
        assert generator.quality_validator is not None
        assert generator.litigation_complaint_generator is not None
    
    def test_init_with_llm_client(self):
        """测试带LLM客户端初始化"""
        mock_llm = MagicMock()
        generator = FinancialCaseGenerator(llm_client=mock_llm)
        
        assert generator.llm_client == mock_llm
    
    def test_init_with_output_dir(self, tmp_path):
        """测试带输出目录初始化"""
        custom_dir = tmp_path / "custom_output"
        generator = FinancialCaseGenerator(output_dir=custom_dir)
        
        assert generator.output_dir == custom_dir
        assert custom_dir.exists()
    
    def test_init_creates_output_dir(self, tmp_path):
        """测试初始化时创建输出目录"""
        new_dir = tmp_path / "new_output"
        generator = FinancialCaseGenerator(output_dir=new_dir)
        
        assert new_dir.exists()
    
    def test_generate_from_judgment_nonexistent_file(self, tmp_path):
        """测试不存在的判决书文件"""
        generator = FinancialCaseGenerator(output_dir=tmp_path)
        result = generator.generate_from_judgment("/nonexistent/path.txt")
        
        assert result.success is False
        assert len(result.errors) > 0
        assert "不存在" in result.errors[0]
    
    def test_generate_from_judgment_creates_subdir(self, tmp_path, sample_judgment_file):
        """测试生成时创建子目录"""
        generator = FinancialCaseGenerator(output_dir=tmp_path)
        result = generator.generate_from_judgment(
            str(sample_judgment_file),
            output_subdir="test_case"
        )
        
        assert (tmp_path / "test_case").exists()
        assert result.output_dir == tmp_path / "test_case"
    
    def test_generate_from_data_success(self, tmp_path, sample_case_data, sample_claim_list):
        """测试从数据成功生成"""
        generator = FinancialCaseGenerator(output_dir=tmp_path)
        result = generator.generate_from_data(sample_case_data, sample_claim_list)
        
        assert result.case_data == sample_case_data
        assert result.claim_list == sample_claim_list
        assert result.evidence_list is not None
        assert result.generated_evidence is not None
    
    def test_generate_from_data_with_subdir(self, tmp_path, sample_case_data, sample_claim_list):
        """测试从数据生成时使用子目录"""
        generator = FinancialCaseGenerator(output_dir=tmp_path)
        result = generator.generate_from_data(
            sample_case_data,
            sample_claim_list,
            output_subdir="subdir_test"
        )
        
        assert (tmp_path / "subdir_test").exists()
        assert result.output_dir == tmp_path / "subdir_test"
    
    def test_save_outputs_creates_evidence_dir(self, tmp_path, sample_case_data, sample_claim_list):
        """测试保存输出时创建证据目录"""
        generator = FinancialCaseGenerator(output_dir=tmp_path)
        result = generator.generate_from_data(sample_case_data, sample_claim_list)
        
        evidence_dir = tmp_path / "evidence"
        assert evidence_dir.exists()
    
    def test_save_outputs_saves_evidence_index_json(self, tmp_path, sample_case_data, sample_claim_list):
        """测试保存证据索引JSON"""
        generator = FinancialCaseGenerator(output_dir=tmp_path)
        result = generator.generate_from_data(sample_case_data, sample_claim_list)
        
        index_path = tmp_path / "evidence_index.json"
        assert index_path.exists()
    
    def test_save_outputs_saves_evidence_index_text(self, tmp_path, sample_case_data, sample_claim_list):
        """测试保存证据索引文本"""
        generator = FinancialCaseGenerator(output_dir=tmp_path)
        result = generator.generate_from_data(sample_case_data, sample_claim_list)
        
        index_path = tmp_path / "evidence_index.txt"
        assert index_path.exists()
    
    def test_save_outputs_saves_litigation_complaint(self, tmp_path, sample_case_data, sample_claim_list):
        """测试保存起诉状"""
        generator = FinancialCaseGenerator(output_dir=tmp_path)
        result = generator.generate_from_data(sample_case_data, sample_claim_list)
        
        complaint_path = tmp_path / "litigation_complaint.txt"
        assert complaint_path.exists()
    
    def test_save_outputs_saves_result_json(self, tmp_path, sample_case_data, sample_claim_list):
        """测试保存结果JSON"""
        generator = FinancialCaseGenerator(output_dir=tmp_path)
        result = generator.generate_from_data(sample_case_data, sample_claim_list)
        
        result_path = tmp_path / "result.json"
        assert result_path.exists()
    
    def test_all_components_initialized(self):
        """测试所有组件都已初始化"""
        generator = FinancialCaseGenerator()
        
        assert hasattr(generator, 'case_analyzer')
        assert hasattr(generator, 'claim_extractor')
        assert hasattr(generator, 'evidence_planner')
        assert hasattr(generator, 'evidence_collector')
        assert hasattr(generator, 'evidence_list_creator')
        assert hasattr(generator, 'document_generator')
        assert hasattr(generator, 'evidence_index_generator')
        assert hasattr(generator, 'pdf_generator')
        assert hasattr(generator, 'quality_validator')
        assert hasattr(generator, 'litigation_complaint_generator')
    
    def test_output_dir_is_path(self, tmp_path):
        """测试输出目录是Path对象"""
        generator = FinancialCaseGenerator(output_dir=tmp_path)
        
        assert isinstance(generator.output_dir, Path)


@pytest.fixture
def sample_case_data():
    """提供测试用的CaseData"""
    plaintiff = Party(
        name="上海融资租赁有限公司",
        credit_code="91310000123456789A",
        address="上海市浦东新区陆家嘴环路1000号",
        legal_representative="张三",
        bank_account="6222021001067890"
    )
    
    defendant = Party(
        name="北京设备有限公司",
        credit_code="91110108123456789B",
        address="北京市朝阳区建国路100号",
        legal_representative="李四",
        bank_account="6222021001067891"
    )
    
    contract = ContractInfo(
        type=CaseType.FINANCING_LEASE,
        subject="数控机床设备5台",
        amount=5000000.00,
        signing_date=datetime(2022, 3, 15),
        term_months=36
    )
    
    breach = BreachInfo(
        breach_date=datetime(2023, 6, 1),
        breach_amount=3500000.00,
        breach_description="被告自2023年6月起未按合同约定支付租金"
    )
    
    return CaseData(
        plaintiff=plaintiff,
        defendant=defendant,
        contract=contract,
        breach=breach,
        paid_amount=1500000.00,
        remaining_amount=3500000.00,
        extracted_at=datetime(2024, 1, 15)
    )


@pytest.fixture
def sample_claim_list():
    """提供测试用的ClaimList"""
    claims = [
        Claim(type="本金", amount=3500000.00, description="欠款本金"),
        Claim(type="利息", amount=350000.00, description="欠款利息"),
        Claim(type="违约金", amount=175000.00, description="违约金")
    ]
    
    return ClaimList(
        claims=claims,
        litigation_cost=50000.00
    )


@pytest.fixture
def sample_judgment_file(tmp_path):
    """创建临时判决书文件"""
    judgment_content = """
    上海金融法院
    民事判决书
    
    (2024)沪74民初721号
    
    原告上海融资租赁有限公司与被告北京设备有限公司融资租赁合同纠纷一案，本院受理后，依法适用简易程序公开开庭进行了审理。
    
    原告请求判令被告支付欠款本金人民币3,500,000元。
    原告请求判令被告支付欠款利息人民币350,000元。
    原告请求判令被告支付违约金人民币175,000元。
    
    审理查明：2022年3月15日，原告与被告签订《融资租赁合同》，合同金额为人民币5,000,000元，租赁期限为36个月。
    被告自2023年6月1日起未按合同约定支付租金，至今尚欠租金人民币3,500,000元。
    
    判决如下：
    一、被告应于本判决生效之日起十日内向原告支付欠款本金人民币3,500,000元。
    二、被告应于本判决生效之日起十日内向原告支付欠款利息人民币350,000元。
    三、被告应于本判决生效之日起十日内向原告支付违约金人民币175,000元。
    
    案件受理费人民币50,000元，由被告负担。
    """
    
    judgment_path = tmp_path / "judgment.txt"
    judgment_path.write_text(judgment_content, encoding="utf-8")
    
    return judgment_path
