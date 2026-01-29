"""数据模型定义"""
from typing import Optional, List
from pydantic import BaseModel, Field


class CaseBasicInfo(BaseModel):
    """案件基本信息"""
    案号: str
    法院: str
    案由: str
    程序: str = Field(..., description="一审/二审/再审等")
    立案日期: Optional[str] = None
    开庭日期: Optional[str] = None
    判决日期: Optional[str] = None
    合议庭: Optional[dict] = None


class PartyAgent(BaseModel):
    """当事人代理人"""
    姓名: str
    律师事务所: Optional[str] = None
    职务: Optional[str] = None


class PlaintiffInfo(BaseModel):
    """原告信息"""
    名称: str
    住所: str
    法定代表人: Optional[str] = None
    委托代理人: List[PartyAgent] = []


class DefendantInfo(BaseModel):
    """被告信息"""
    被告序号: int
    名称: str
    住所: str
    法定代表人: Optional[str] = None
    委托代理人: List[PartyAgent] = []


class ClaimRequest(BaseModel):
    """诉讼请求"""
    序号: int
    请求内容: str
    金额: Optional[dict] = None


class DefenseOpinion(BaseModel):
    """被告抗辩意见"""
    被告序号: int
    答辩要点: List[str]


class CourtFindings(BaseModel):
    """法院认定部分"""
    事实认定: Optional[dict] = None
    证据认定: Optional[dict] = None
    法律分析: Optional[dict] = None
    判决结果: Optional[dict] = None


class AnonymizedMarkers(BaseModel):
    """脱敏标识列表"""
    人物标识: List[str] = []
    公司标识: List[str] = []
    机构标识: List[str] = []
    其他标识: List[str] = []


class Stage0StructuredExtraction(BaseModel):
    """阶段0.1结构化提取输出"""
    案件基本信息: CaseBasicInfo
    原告信息: PlaintiffInfo
    被告信息: List[DefendantInfo]
    原告诉讼请求: List[ClaimRequest]
    被告抗辩意见: List[DefenseOpinion]
    法院认定部分: CourtFindings
    脱敏标识列表: AnonymizedMarkers


class PersonProfile(BaseModel):
    """人物Profile"""
    姓名: str
    性别: Optional[str] = None
    身份证号: Optional[str] = None
    出生日期: Optional[str] = None
    手机号码: Optional[str] = None
    电子邮箱: Optional[str] = None
    家庭住址: Optional[str] = None
    在案件中的角色: Optional[str] = None
    原脱敏标识: Optional[str] = None


class Shareholder(BaseModel):
    """股东信息"""
    股东名称: str
    持股比例: float


class CompanyProfile(BaseModel):
    """公司Profile"""
    公司名称: str
    统一社会信用代码: Optional[str] = None
    公司类型: Optional[str] = None
    注册资本: Optional[dict] = None
    成立日期: Optional[str] = None
    注册地址: Optional[str] = None
    法定代表人: Optional[str] = None
    经营范围: Optional[str] = None
    股东信息: List[Shareholder] = []
    银行账户: Optional[dict] = None
    联系人: Optional[dict] = None
    在案件中的角色: Optional[str] = None
    原脱敏标识: Optional[str] = None


class Stage0AnonymizationPlan(BaseModel):
    """阶段0.2脱敏替换策划输出"""
    人物Profile库: dict = {}
    公司Profile库: dict = {}
    机构Profile库: dict = {}
    编号体系规则: dict = {}
    补充Profile库: dict = {}
    替换映射表: dict = {}


class TransactionEvent(BaseModel):
    """交易事件"""
    序号: int
    时间: str
    事件类型: str
    事件描述: str
    涉及方: List[str]
    关键数据: dict


class GuaranteeStructure(BaseModel):
    """担保结构"""
    抵押担保: List[dict] = []
    质押担保: List[dict] = []
    保证担保: List[dict] = []


class Stage0TransactionReconstruction(BaseModel):
    """阶段0.3交易结构重构输出"""
    交易结构图: dict
    交易时间线: List[TransactionEvent]
    担保结构: GuaranteeStructure


class RentPayment(BaseModel):
    """租金支付计划"""
    期数: int
    应付日期: str
    租金金额: dict
    本金金额: Optional[dict] = None
    利息金额: Optional[dict] = None
    实际支付日期: Optional[str] = None
    支付状态: str


class Stage0KeyNumbers(BaseModel):
    """阶段0.4关键数字提取输出"""
    合同基础金额: dict
    租金安排: dict
    租金支付计划: List[RentPayment]
    放款明细: List[dict]
    保险理赔明细: List[dict]
    违约相关金额: dict
    诉讼费用: dict
    判决金额: dict
    关键时间点: dict


class EvidencePlanning(BaseModel):
    """证据规划"""
    证据序号: int
    证据名称: str
    应归属方: str
    文件类型: str
    是否需要生成: bool
    关键数据提示: dict
    关联交易节点: Optional[int] = None
    证据组: Optional[int] = None
    证明目的: Optional[str] = None


class Stage0EvidencePlanning(BaseModel):
    """阶段0.5证据归属规划输出"""
    证据归属规划表: List[EvidencePlanning]
    证据分组: dict


class Stage0Output(BaseModel):
    """阶段0完整输出"""
    "0.1_结构化提取": Stage0StructuredExtraction
    "0.2_脱敏替换策划": Stage0AnonymizationPlan
    "0.3_交易结构重构": Stage0TransactionReconstruction
    "0.4_关键数字清单": Stage0KeyNumbers
    "0.5_证据归属规划": Stage0EvidencePlanning
