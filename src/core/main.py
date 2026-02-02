"""
Financial Case Generator v3.0 - Main Entry Point

金融案件证据生成系统 v3.0

功能：
- 从判决书自动生成诉讼所需的证据材料
- 支持融资租赁、金融借款、保理、担保等案件类型

核心架构原则：
- P1 脱敏标记隔离：全程使用真实信息
- P2 要素驱动：系统负责关键信息，LLM负责内容生成
- P3 附件规划：F2.3必须规划附件形式
- P4 数据契约：EvidenceList结构化输出

使用方式：
    from main import FinancialCaseGenerator

    generator = FinancialCaseGenerator()
    result = generator.generate_from_judgment("path/to/judgment.txt")
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
import json

if TYPE_CHECKING:
    from .data_models import (
        CaseData,
        ClaimList,
        EvidenceList,
        GeneratedEvidence,
        EvidenceIndex,
        CaseType,
        EvidenceRequirements,
        EvidenceCollection
    )
    from .quality_validator import ValidationReport
    from .llm_client import LLMClient
else:
    # 运行时导入
    from .data_models import (
        CaseData,
        ClaimList,
        EvidenceList,
        GeneratedEvidence,
        EvidenceIndex,
        CaseType
    )
from .case_analyzer import CaseAnalyzer
from .claim_extractor import ClaimExtractor
from .evidence_planner import EvidencePlanner
from .evidence_collector import EvidenceCollector
from .evidence_list_creator import EvidenceListCreator
from .document_generator import DocumentGenerator
from .evidence_index_generator import EvidenceIndexGenerator
from .pdf_generator import PDFGenerator
from .quality_validator import QualityValidator
from .litigation_complaint_generator import LitigationComplaintGenerator


class GenerationResult:
    """生成结果"""

    def __init__(
        self,
        success: bool,
        case_data: Optional[CaseData] = None,
        claim_list: Optional[ClaimList] = None,
        evidence_list: Optional[EvidenceList] = None,
        evidence_index: Optional[EvidenceIndex] = None,
        generated_evidence: Optional[list] = None,
        litigation_complaint: Optional[str] = None,
        validation_report: Optional["ValidationReport"] = None,
        output_dir: Optional[Path] = None,
        errors: Optional[list] = None
    ):
        self.success = success
        self.case_data = case_data
        self.claim_list = claim_list
        self.evidence_list = evidence_list
        self.evidence_index = evidence_index
        self.generated_evidence = generated_evidence or []
        self.litigation_complaint = litigation_complaint
        self.validation_report = validation_report
        self.output_dir = output_dir
        self.errors = errors or []
        self.generated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "generated_at": self.generated_at.isoformat(),
            "case_data": self.case_data.to_dict() if self.case_data else None,
            "claim_list": self.claim_list.to_dict() if self.claim_list else None,
            "evidence_list": self.evidence_list.to_dict() if self.evidence_list else None,
            "evidence_index": self.evidence_index.to_dict() if self.evidence_index else None,
            "evidence_count": len(self.generated_evidence),
            "litigation_complaint": self.litigation_complaint,
            "validation": self.validation_report.to_dict() if self.validation_report else None,
            "output_dir": str(self.output_dir) if self.output_dir else None,
            "errors": self.errors
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


class FinancialCaseGenerator:
    """
    金融案件证据生成器 v3.0

    统一的入口类，封装整个证据生成流程。
    """

    def __init__(
        self,
        llm_client: Optional["LLMClient"] = None,
        output_dir: Optional[Path] = None
    ):
        """
        初始化证据生成器

        Args:
            llm_client: LLM客户端（可选，如果不提供则使用规则引擎）
            output_dir: 输出目录（可选，默认为当前目录的output文件夹）
        """
        self.llm_client = llm_client
        self.output_dir = output_dir or Path("output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.case_analyzer = CaseAnalyzer(llm_client)
        self.claim_extractor = ClaimExtractor(llm_client)
        self.evidence_planner = EvidencePlanner(llm_client)
        self.evidence_collector = EvidenceCollector()
        self.evidence_list_creator = EvidenceListCreator()
        self.document_generator = DocumentGenerator(llm_client)
        self.evidence_index_generator = EvidenceIndexGenerator()
        self.pdf_generator = PDFGenerator()
        self.quality_validator = QualityValidator()
        self.litigation_complaint_generator = LitigationComplaintGenerator()

    def generate_from_judgment(
        self,
        judgment_path: str,
        case_type: Optional[CaseType] = None,
        output_subdir: Optional[str] = None
    ) -> GenerationResult:
        """
        从判决书生成证据材料

        Args:
            judgment_path: 判决书文件路径
            case_type: 案件类型（可选，自动识别）
            output_subdir: 输出子目录名（可选）
        Returns:
            GenerationResult: 生成结果
        """
        result = GenerationResult(success=False)

        try:
            judgment_path = Path(judgment_path)
            if not judgment_path.exists():
                result.errors.append(f"判决书文件不存在: {judgment_path}")
                return result

            output_dir = self.output_dir
            if output_subdir:
                output_dir = output_dir / output_subdir
            output_dir.mkdir(parents=True, exist_ok=True)
            result.output_dir = output_dir

            print(f"开始处理判决书: {judgment_path}")

            print("步骤1/7: 分析案情...")
            case_data = self.case_analyzer.analyze(judgment_path)
            if case_type:
                case_data.contract.type = case_type
            result.case_data = case_data
            print(f"  - 原告: {case_data.plaintiff.name}")
            print(f"  - 被告: {case_data.defendant.name}")
            print(f"  - 合同金额: {case_data.contract.amount:,.2f}元")

            print("步骤2/7: 提取诉求...")
            claim_list = self.claim_extractor.extract(judgment_path)
            result.claim_list = claim_list
            print(f"  - 诉求数量: {len(claim_list.claims)}")
            for claim in claim_list.claims:
                print(f"    * {claim.type}: {claim.amount:,.2f}元")

            print("步骤3/7: 规划证据...")
            evidence_requirements = self.evidence_planner.plan(case_data, claim_list, environment="production")
            print(f"  - 规划证据数量: {len(evidence_requirements.requirements)}")

            print("步骤4/7: 收集证据...")
            evidence_collection = self.evidence_collector.collect(
                case_data,
                claim_list,
                evidence_requirements,
                environment="production"
            )
            print(f"  - 收集证据数量: {len(evidence_collection.items)}")

            print("步骤5/7: 创建证据列表...")
            evidence_list = self.evidence_list_creator.create(
                case_data,
                evidence_collection,
                evidence_requirements
            )
            result.evidence_list = evidence_list
            print(f"  - 创建证据列表数量: {len(evidence_list.items)}")

            print("步骤6/7: 生成证据文档...")
            generated_evidence = self.document_generator.generate(
                evidence_list,
                case_data,
                claim_list
            )
            result.generated_evidence = generated_evidence
            print(f"  - 生成证据数量: {len(generated_evidence)}")

            evidence_index = self.evidence_index_generator.generate(
                evidence_list,
                claim_list
            )
            result.evidence_index = evidence_index
            print(f"  - 生成证据索引数量: {len(evidence_index.items)}")

            litigation_complaint = self.litigation_complaint_generator.generate(
                case_data,
                claim_list,
                evidence_list
            )
            result.litigation_complaint = litigation_complaint
            print(f"  - 生成起诉状")

            print("步骤7/7: 质量验证...")
            validation_report = self.quality_validator.validate(
                case_data,
                claim_list,
                evidence_list,
                generated_evidence,
                evidence_index
            )
            result.validation_report = validation_report
            print(f"  - 验证通过: {validation_report.is_valid}")
            print(f"  - 质量评分: {validation_report.score}/100")
            if validation_report.issues:
                for issue in validation_report.issues[:3]:
                    print(f"    * [{issue.severity}] {issue.message}")

            self._save_outputs(result, output_dir)

            result.success = True
            print(f"\n生成完成！输出目录: {output_dir}")
            print(f"质量评分: {validation_report.score}/100")

        except Exception as e:
            result.errors.append(str(e))
            print(f"生成过程出错: {e}")
            import traceback
            traceback.print_exc()

        return result

    def _save_outputs(
        self,
        result: GenerationResult,
        output_dir: Path
    ):
        """保存输出文件"""
        evidence_dir = output_dir / "evidence"
        evidence_dir.mkdir(exist_ok=True)

        for evidence in result.generated_evidence:
            evidence_path = evidence_dir / evidence.filename
            evidence_path.write_text(evidence.content, encoding="utf-8")

        evidence_index_path = output_dir / "evidence_index.json"
        evidence_index_path.write_text(
            result.evidence_index.to_json(),
            encoding="utf-8"
        )

        evidence_index_text_path = output_dir / "evidence_index.txt"
        evidence_index_text_path.write_text(
            result.evidence_index.to_text(),
            encoding="utf-8"
        )

        if result.litigation_complaint:
            complaint_path = output_dir / "litigation_complaint.txt"
            complaint_path.write_text(
                result.litigation_complaint,
                encoding="utf-8"
            )

        result_path = output_dir / "result.json"
        result_path.write_text(
            result.to_json(),
            encoding="utf-8"
        )

    def generate_from_data(
        self,
        case_data: CaseData,
        claim_list: ClaimList,
        output_subdir: Optional[str] = None
    ) -> GenerationResult:
        """
        从已有数据生成证据材料

        Args:
            case_data: 案情基本数据
            claim_list: 诉求列表
            output_subdir: 输出子目录名（可选）
        Returns:
            GenerationResult: 生成结果
        """
        result = GenerationResult(success=False)

        try:
            output_dir = self.output_dir
            if output_subdir:
                output_dir = output_dir / output_subdir
            output_dir.mkdir(parents=True, exist_ok=True)
            result.output_dir = output_dir
            result.case_data = case_data
            result.claim_list = claim_list

            print("开始从数据生成证据材料...")

            print("步骤1/5: 规划证据...")
            evidence_requirements = self.evidence_planner.plan(case_data, claim_list, environment="test")

            print("步骤2/5: 收集证据...")
            evidence_collection = self.evidence_collector.collect(
                case_data,
                claim_list,
                evidence_requirements,
                environment="test"
            )

            print("步骤3/5: 创建证据列表...")
            evidence_list = self.evidence_list_creator.create(
                case_data,
                evidence_collection,
                evidence_requirements
            )
            result.evidence_list = evidence_list

            print("步骤4/5: 生成证据文档...")
            generated_evidence = self.document_generator.generate(
                evidence_list,
                case_data,
                claim_list
            )
            result.generated_evidence = generated_evidence

            evidence_index = self.evidence_index_generator.generate(
                evidence_list,
                claim_list
            )
            result.evidence_index = evidence_index

            litigation_complaint = self.litigation_complaint_generator.generate(
                case_data,
                claim_list,
                evidence_list
            )
            result.litigation_complaint = litigation_complaint

            print("步骤5/5: 质量验证...")
            validation_report = self.quality_validator.validate(
                case_data,
                claim_list,
                evidence_list,
                generated_evidence,
                evidence_index
            )
            result.validation_report = validation_report

            self._save_outputs(result, output_dir)

            result.success = True
            print(f"生成完成！输出目录: {output_dir}")
            print(f"质量评分: {validation_report.score}/100")

        except Exception as e:
            result.errors.append(str(e))
            print(f"生成过程出错: {e}")
            import traceback
            traceback.print_exc()

        return result


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="金融案件证据生成器 v3.0"
    )
    parser.add_argument(
        "judgment_path",
        help="判决书文件路径"
    )
    parser.add_argument(
        "-o", "--output",
        help="输出目录",
        default="output"
    )
    parser.add_argument(
        "-t", "--type",
        help="案件类型",
        choices=["FINANCING_LEASE", "LOAN", "FACTORING", "GUARANTEE"],
        default=None
    )

    args = parser.parse_args()

    case_type = None
    if args.type:
        case_type = CaseType(args.type)

    output_dir = Path(args.output)
    generator = FinancialCaseGenerator(output_dir=output_dir)
    result = generator.generate_from_judgment(args.judgment_path, case_type=case_type)

    if result.success:
        print("\n生成成功！")
        sys.exit(0)
    else:
        print("\n生成失败！")
        for error in result.errors:
            print(f"  - {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
