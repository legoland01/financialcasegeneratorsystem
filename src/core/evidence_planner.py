"""
EvidencePlanner - F2.3 证据规划器

功能：根据诉求和案情，规划需要的证据

输入：CaseData + ClaimList
输出：EvidenceRequirements（证据需求清单）

核心原则：
- P3 附件规划：F2.3必须规划附件形式（独立文件/正文包含/不需附件）
"""

from typing import List, Dict, Any
from pathlib import Path


class EvidencePlanner:
    """
    证据规划器 - F2.3
    
    根据诉求和案情，规划需要的证据。
    支持根据案件类型配置证据类型。
    
    输出：EvidenceRequirements（证据需求清单）
    """
    
    # 默认证据类型配置
    DEFAULT_EVIDENCE_TYPES = {
        "融资租赁": [
            {"name": "融资租赁合同", "type": "合同类", "attachment": "租赁物清单"},
            {"name": "付款凭证", "type": "凭证类", "attachment": None},
            {"name": "公证书", "type": "文书类", "attachment": None},
        ],
        "金融借款": [
            {"name": "借款合同", "type": "合同类", "attachment": "还款计划"},
            {"name": "银行流水", "type": "凭证类", "attachment": None},
        ],
        "保理": [
            {"name": "保理合同", "type": "合同类", "attachment": "应收账款清单"},
            {"name": "应收账款转让通知", "type": "文书类", "attachment": None},
        ],
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化证据规划器
        
        Args:
            config_path: 证据类型配置文件路径
        """
        self.config_path = config_path
        self.evidence_types = self._load_evidence_types()
    
    def _load_evidence_types(self) -> Dict[str, List[Dict[str, Any]]]:
        """加载证据类型配置"""
        if self.config_path and self.config_path.exists():
            import json
            return json.loads(self.config_path.read_text(encoding="utf-8"))
        return self.DEFAULT_EVIDENCE_TYPES.copy()
    
    def plan(
        self,
        case_data: "CaseData",
        claim_list: "ClaimList"
    ) -> "EvidenceRequirements":
        """
        根据诉求和案情，规划需要的证据
        
        Args:
            case_data: 案情基本数据集
            claim_list: 诉求列表
        Returns:
            EvidenceRequirements：证据需求清单
        """
        # 1. 获取案件类型的证据类型配置
        evidence_types = self._get_evidence_types(case_data.contract.type)
        
        # 2. 根据诉求确定需要证明的事实
        facts_to_prove = self._determine_facts_to_prove(claim_list)
        
        # 3. 规划每项诉求需要哪些证据支撑
        requirements = []
        for claim in claim_list.claims:
            evidence_for_claim = self._plan_evidence_for_claim(
                claim, case_data.contract.type, evidence_types, facts_to_prove
            )
            requirements.extend(evidence        
        # _for_claim)
4. 规划附件形式
        for req in requirements:
            req.attachment = self._plan_attachment(req, case_data.contract.type)
        
        from .data_models import EvidenceRequirements
        return EvidenceRequirements(
            requirements=requirements,
            case_type=case_data.contract.type
        )
    
    def _get_evidence_types(self, case_type: "CaseType") -> List[Dict[str, Any]]:
        """根据案件类型获取证据类型配置"""
        case_type_name = case_type.value
        return self.evidence_types.get(case_type_name, self.evidence_types["融资租赁"])
    
    def _determine_facts_to_prove(self, claim_list: "ClaimList") -> Dict[str, List[str]]:
        """根据诉求确定需要证明的事实"""
        facts = {}
        
        for claim in claim_list.claims:
            if claim.type in ["本金", "租金"]:
                facts[claim.type] = [
                    "合同关系成立",
                    "合同金额",
                    "被告未按约定支付"
                ]
            elif claim.type == "利息":
                facts[claim.type] = [
                    "利息计算方式",
                    "利息计算期间"
                ]
            elif claim.type == "违约金":
                facts[claim.type] = [
                    "违约金计算方式",
                    "被告违约事实"
                ]
        
        return facts
    
    def _plan_evidence_for_claim(
        self,
        claim: "Claim",
        case_type: "CaseType",
        evidence_types: List[Dict[str, Any]],
        facts_to_prove: Dict[str, List[str]]
    ) -> List["EvidenceRequirement"]:
        """为单个诉求规划证据"""
        from .data_models import EvidenceRequirement, EvidenceType
        
        requirements = []
        claim_facts = facts_to_prove.get(claim.type, [])
        
        for evidence_config in evidence_types:
            # 检查该证据是否支撑当前诉求
            if self._evidence_supports_claim(evidence_config, claim.type):
                requirements.append(EvidenceRequirement(
                    name=evidence_config["name"],
                    type=EvidenceType(evidence_config["type"]),
                    facts_to_prove=claim_facts,
                    claims_supported=[claim.type]
                ))
        
        return requirements
    
    def _evidence_supports_claim(
        self,
        evidence_config: Dict[str, Any],
        claim_type: str
    ) -> bool:
        """判断证据是否支撑诉求"""
        evidence_name = evidence_config.get("name", "")
        evidence_type = evidence_config.get("type", "")
        
        # 合同类证据支撑本金/租金诉求
        if claim_type in ["本金", "租金"] and evidence_type == "合同类":
            return True
        # 凭证类证据支撑本金诉求
        if claim_type == "本金" and evidence_type == "凭证类":
            return True
        
        return False
    
    def _plan_attachment(
        self,
        requirement: "EvidenceRequirement",
        case_type: "CaseType"
    ) -> Optional["AttachmentPlan"]:
        """规划附件形式"""
        from .data_models import AttachmentPlan, AttachmentForm
        
        if requirement.type != EvidenceType.CONTRACT:
            return None
        
        attachment_type = None
        if case_type.value == "融资租赁":
            attachment_type = "租赁物清单"
        elif case_type.value == "金融借款":
            attachment_type = "还款计划"
        elif case_type.value == "保理":
            attachment_type = "应收账款清单"
        
        if attachment_type:
            return AttachmentPlan(
                type=attachment_type,
                form=AttachmentForm.INDEPENDENT_FILE,
                source="案情数据"
            )
        
        return None
    
    def add_evidence_type(self, case_type: str, evidence_config: Dict[str, Any]):
        """添加新的证据类型配置"""
        if case_type not in self.evidence_types:
            self.evidence_types[case_type] = []
        self.evidence_types[case_type].append(evidence_config)
    
    def save_config(self, config_path: Path):
        """保存配置到文件"""
        import json
        config_path.write_text(
            json.dumps(self.evidence_types, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
