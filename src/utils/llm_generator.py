"""
LLM生成器模块
负责调用大语言模型生成法律文书
"""
import json
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from loguru import logger


class LLMProvider(Enum):
    """支持的LLM提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    MOCK = "mock"  # 用于测试


@dataclass
class GenerationConfig:
    """生成配置"""
    provider: LLMProvider = LLMProvider.MOCK
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4096
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class LLMGenerator:
    """LLM生成器类"""
    
    def __init__(self, config: GenerationConfig = None):
        self.config = config or GenerationConfig()
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """初始化LLM客户端"""
        if self.config.provider == LLMProvider.OPENAI:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                )
            except ImportError:
                logger.warning("OpenAI SDK not installed, falling back to mock")
                self.config.provider = LLMProvider.MOCK
        
        elif self.config.provider == LLMProvider.ANTHROPIC:
            try:
                import anthropic
                self._client = anthropic.Anthropic(
                    api_key=self.config.api_key,
                )
            except ImportError:
                logger.warning("Anthropic SDK not installed, falling back to mock")
                self.config.provider = LLMProvider.MOCK
        
        elif self.config.provider == LLMProvider.DEEPSEEK:
            try:
                from openai import OpenAI
                # 使用配置的base_url（支持SiliconFlow等兼容OpenAI的API）
                base_url = self.config.base_url or "https://api.deepseek.com"
                self._client = OpenAI(
                    api_key=self.config.api_key,
                    base_url=base_url,
                )
            except ImportError:
                logger.warning("DeepSeek client failed, falling back to mock")
                self.config.provider = LLMProvider.MOCK
    
    def generate(self, prompt: str, evidence_type: str = "unknown") -> str:
        """
        根据提示词生成内容
        
        Args:
            prompt: 提示词
            evidence_type: 证据类型（用于日志和调试）
        
        Returns:
            生成的内容
        """
        logger.info(f"生成证据类型: {evidence_type}")
        logger.debug(f"提示词长度: {len(prompt)} 字符")
        
        if self.config.provider == LLMProvider.MOCK:
            return self._mock_generate(prompt, evidence_type)
        
        return self._call_llm(prompt)
    
    def _call_llm(self, prompt: str) -> str:
        """调用LLM API"""
        try:
            if self.config.provider == LLMProvider.OPENAI:
                response = self._client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": "你是一位专业的法律文书撰写人。请根据案件信息撰写准确、规范的法律文书。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
                return response.choices[0].message.content
            
            elif self.config.provider == LLMProvider.ANTHROPIC:
                response = self._client.messages.create(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    system="你是一位专业的法律文书撰写人。",
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text
            
            elif self.config.provider == LLMProvider.DEEPSEEK:
                response = self._client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": "你是一位专业的法律文书撰写人。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )
                return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"LLM API调用失败: {e}")
            logger.info("回退到模拟生成")
            return self._mock_generate(prompt, "fallback")
        
        return ""
    
    def _mock_generate(self, prompt: str, evidence_type: str) -> str:
        """
        模拟LLM生成（用于测试）
        
        这里可以实现一个基于规则的回退生成器，
        或者简单返回原始模板
        """
        # 根据证据类型返回不同的模拟内容
        mock_content = {
            "payment_receipt": self._mock_payment_receipt(prompt),
            "execution_certificate": self._mock_execution_certificate(prompt),
            "rent_record": self._mock_rent_record(prompt),
            "assessment_report": self._mock_assessment_report(prompt),
            "mortgage_certificate": self._mock_mortgage_certificate(prompt),
            "interest_calculation": self._mock_interest_calculation(prompt),
            "attorney_contract": self._mock_attorney_contract(prompt),
            "insurance_policy": self._mock_insurance_policy(prompt),
            "consulting_contract": self._mock_consulting_contract(prompt),
            "shareholder_decision": self._mock_shareholder_decision(prompt),
            "guarantee_contract": self._mock_guarantee_contract(prompt),
            "deposit_proof": self._mock_deposit_proof(prompt),
            "transfer_contract": self._mock_transfer_contract(prompt),
            "finance_lease_contract": self._mock_finance_lease_contract(prompt),
            "equipment_list": self._mock_equipment_list(prompt),
        }
        
        if evidence_type in mock_content:
            return mock_content[evidence_type]
        
        # 尝试从提示词中提取证据类型
        if "付款回单" in prompt:
            return mock_content["payment_receipt"]
        elif "执行证书" in prompt:
            return mock_content["execution_certificate"]
        elif "租金" in prompt:
            return mock_content["rent_record"]
        elif "评估" in prompt:
            return mock_content["assessment_report"]
        elif "抵押" in prompt:
            return mock_content["mortgage_certificate"]
        elif "利息" in prompt:
            return mock_content["interest_calculation"]
        elif "代理" in prompt:
            return mock_content["attorney_contract"]
        elif "保险" in prompt:
            return mock_content["insurance_policy"]
        elif "咨询" in prompt:
            return mock_content["consulting_contract"]
        elif "股东" in prompt:
            return mock_content["shareholder_decision"]
        elif "保证" in prompt:
            return mock_content["guarantee_contract"]
        elif "转让" in prompt:
            return mock_content["transfer_contract"]
        elif "融资租赁" in prompt:
            return mock_content["finance_lease_contract"]
        
        return self._extract_template_content(prompt)
    
    def _extract_template_content(self, prompt: str) -> str:
        """从提示词中提取模板内容并填充"""
        # 这是一个回退方案，尝试从提示词中提取关键信息生成内容
        lines = prompt.split('\n')
        content_lines = []
        
        in_data_section = False
        for line in lines:
            if '【案件数据】' in line:
                in_data_section = True
                continue
            if in_data_section and line.startswith('- '):
                content_lines.append(line)
        
        return f"【生成的证据内容】\n基于{len(content_lines)}个数据项生成\n\n" + "\n".join(content_lines[:10])
    
    # ============== 模拟生成函数 ==============
    
    def _mock_payment_receipt(self, prompt: str) -> str:
        """模拟生成付款回单"""
        # 尝试从提示词中提取金额和日期
        import re
        amount_match = re.search(r'(\d{11,12})', prompt)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', prompt)
        
        amount = "150,000,000" if amount_match else "XXX"
        date = "2021-02-26" if date_match else "XXXX-XX-XX"
        
        return f"""【付款回单】

【基本信息】
付款人名称：东方国际融资租赁有限公司
付款人账号：工商银行上海浦东分行 1234567890123456
付款人开户银行：中国工商银行上海浦东分行
收款人名称：江西昌盛商业管理有限公司
收款人账号：工商银行南昌县支行 9876543210987654
收款人开户银行：中国工商银行南昌县支行
币种：人民币

【交易信息】
交易金额：人民币{amount}元
大写金额：人民币壹亿伍仟万元整
交易日期：{date}
交易时间：09:30:00
交易流水号：BJ{date.replace('-', '')}12345
业务类型：转账汇款
用途：设备转让款

【附言】
设备转让款（合同编号：ZR-2021-001）

【凭证状态】
凭证打印日期：{date}
凭证打印时间：09:30:15
操作员号：XXXXXX
复核员号：XXXXXX

【银行印章】
（电子回单专用章）
"""
    
    def _mock_execution_certificate(self, prompt: str) -> str:
        """模拟生成执行证书"""
        import re
        amount_match = re.search(r'未付租金人民币([\d,]+)', prompt)
        amount = "120,467,622.06" if amount_match else "XXX"
        
        return f"""【执行证书】

【证书编号】（2021）沪长证执字第XXXX号

【公证处】
名称：上海市长宁公证处
地址：上海市长宁区某某路某某号
联系电话：XXXXXXXX

【申请执行人】
名称：东方国际融资租赁有限公司
法定代表人：周明远
地址：中国（上海）自由贸易试验区世纪大道100号

【被执行人】
名称：江西昌盛商业管理有限公司
法定代表人：吴建华
地址：江西省南昌市南昌县莲塘镇向阳路199号

【执行依据】
公证书编号：（2021）沪长证经字第XXXX号
执行标的：未付租金人民币{amount}元及逾期利息

【事实概要】
申请执行人与被执行人于2021-02-24签订了《融资租赁合同》，经公证处公证赋予强制执行效力。

截至申请执行之日，被执行人尚欠租金本金人民币{amount}元及相应逾期利息。

【执行内容】
经审查，申请执行人的申请符合法律规定，本公证处出具本执行证书。

申请执行人可持本证书向有管辖权的人民法院申请强制执行。

【公证员】
公证员：张某某
公证员编号：XXXXXXXX

【日期】
出具日期：2022年X月X日

【备注】
本执行证书有效期为两年，自出具之日起计算。
"""
    
    def _mock_rent_record(self, prompt: str) -> str:
        """模拟生成租金支付记录"""
        import re
        paid_match = re.search(r'已付金额：人民币([\d,.]+)', prompt)
        unpaid_match = re.search(r'未付金额：人民币([\d,.]+)', prompt)
        
        paid = "40,155,653.92" if paid_match else "XXX"
        unpaid = "120,467,622.06" if unpaid_match else "XXX"
        
        return f"""【租金支付记录】

【合同信息】
合同编号：RZL-2021-001
承租人：江西昌盛商业管理有限公司
租赁期限：2021-02-26至2024年2月24日

【租金支付明细】
期数 | 应付日期   | 应付金额（元） | 实付日期   | 实付金额（元） | 状态
-----|------------|----------------|------------|----------------|--------
1    | 2021-02-24 | 6,692,645.67   | 2021-02-24 | 6,692,645.67   | 已付
2    | 2021-03-24 | 6,692,645.67   | 2021-03-24 | 6,692,645.67   | 已付
3    | 2021-04-24 | 6,692,645.67   | -          | 0.00           | 逾期
4    | 2021-05-24 | 6,692,645.67   | -          | 0.00           | 逾期
5    | 2021-06-24 | 6,692,645.67   | -          | 0.00           | 逾期
...  | ...        | ...            | ...        | ...            | ...
24   | 2024-02-24 | 6,692,645.67   | -          | 0.00           | 逾期

【汇总信息】
应支付数：24期
已支付数：2期
已付金额：人民币{paid}元
未付金额：人民币{unpaid}元

【制作信息】
制作日期：2024年2月24日
制表人：财务部
审核人：财务总监
"""
    
    def _mock_assessment_report(self, prompt: str) -> str:
        """模拟生成评估报告"""
        return f"""【报告编号】PG-2021-001

【委托方】
名称：江西昌盛商业管理有限公司
统一社会信用代码：91360121MA35L8T456
地址：江西省南昌市南昌县莲塘镇向阳路199号

【评估对象】
资产名称：某某商场设备及附属设施
资产位置：江西省南昌市某某路某某号
评估基准日：2021-02-24

【评估机构】
名称：上海某某资产评估有限公司
统一社会信用代码：91310000XXXXXXXX
地址：上海市某某区某某路某某号
资质等级：A级

【评估方法】
评估方法：成本法

【评估结论】
经评估，上述资产评估价值为人民币150,000,000元（大写：人民币壹亿伍仟万元整）。

【设备清单】
序号 | 设备名称 | 规格型号 | 数量 | 评估价值（元）
-----|----------|----------|------|--------------
1 | 多联机中央空调系统 | VRV VIII代 | 10套 | 45,000,000
2 | 冷水机组 | 离心式RF1-5000 | 2套 | 12,000,000
3 | 电梯设备 | 曳引式客梯KONIA-1000 | 4台 | 8,000,000
4 | 配电变压器 | SCB13-2500/10 | 8台 | 6,400,000
5 | 消防水泵 | XBD15/40 | 10套 | 3,200,000
6 | 监控系统 | 海康威视DS-7900 | 1套 | 2,500,000
7 | 商场照明设备 | 飞利浦LED | 1批 | 1,800,000
8 | 其他附属设施 | - | 1批 | 21,100,000
   | 合计 | - | - | 100,000,000

【评估师】
评估师：张某某（注册资产评估师 证书编号：XXXXXXXX）
评估师：李某某（注册资产评估师 证书编号：XXXXXXXX）

【评估日期】
评估基准日：2021-02-24
报告出具日期：2021-02-24

【附件】
1. 设备照片（详见附件）
2. 设备购置发票复印件
3. 设备技术参数表
"""
    
    def _mock_mortgage_certificate(self, prompt: str) -> str:
        """模拟生成抵押证书"""
        return f"""【不动产权证书】

【证书编号】赣（2021）南昌市不动产权第XXXXXXX号

【权利人】
权利人：东方国际融资租赁有限公司
共有情况：单独所有

【义务人】
义务人：南昌长风房地产开发有限公司

【坐落】
江西省南昌市西湖区抚生路369号

【不动产单元号】
XXXXXXXXXXXXXXXXXX

【权利类型】
国有建设用地使用权/房屋所有权

【权利性质】
出让/自建房

【用途】
商业用地/商业

【面积】
建筑面积：15,000.00平方米
土地使用权面积：5,000.00平方米

【使用期限】
国有建设用地使用权：2051年XX月XX日

【抵押信息】
抵押权人：东方国际融资租赁有限公司
抵押方式：一般抵押
债权数额：人民币150,000,000元
债务履行期限：2021-02-24至2024年2月24日
登记时间：2021-02-24
登记证明编号：赣（2021）南昌市不动产证明第1234567号

【发证机关】
南昌市自然资源局
发证日期：2021-02-24
"""
    
    def _mock_interest_calculation(self, prompt: str) -> str:
        """模拟生成利息计算表"""
        import re
        interest_match = re.search(r'逾期利息：人民币([\d,.]+)', prompt)
        interest = "31,198,572" if interest_match else "XXX"
        
        return f"""【逾期利息计算表】

【基本信息】
合同编号：RZL-2021-001
承租人：江西昌盛商业管理有限公司
计算日期：2024年2月24日
计算依据：《融资租赁合同》第五条第5.1款

【计算公式】
逾期利息 = 逾期本金 × 日利率 × 逾期天数
日利率 = 年利率 ÷ 360 = 0.0169%

【计算明细】
期数 | 本金（元） | 逾期起算日 | 逾期天数 | 日利率 | 逾期利息（元）
-----|------------|------------|----------|--------|----------------
3    | 6,692,645.67 | 2021-04-24 | 700 | 0.0169% | 2,342,426.98
4    | 6,692,645.67 | 2021-05-24 | 670 | 0.0169% | 2,242,036.30
5    | 6,692,645.67 | 2021-06-24 | 640 | 0.0169% | 2,141,645.62
...  | ... | ... | ... | ... | ...
22   | 6,692,645.67 | 2023-02-24 | 30 | 0.0169% | 100,289.69
23   | 6,692,645.67 | 2023-03-24 | 0 | 0.0169% | 0.00
24   | 6,692,645.67 | 2024-02-24 | 0 | 0.0169% | 0.00

【汇总信息】
逾期本金总额：人民币120,467,622.06元
逾期利息总额：人民币{interest}元
已扣保证金：人民币4,500,000元
应付逾期利息净额：人民币{interest}元

【计算说明】
1. 逾期天数计算至2024年2月24日
2. 日利率按年利率6.1%÷360计算
3. 逾期利息计算至实际清偿之日止
4. 保证金人民币4,500,000元已用于抵扣逾期利息

【制作信息】
制作日期：2024年2月24日
制表人：财务部
复核人：财务总监
"""
    
    def _mock_attorney_contract(self, prompt: str) -> str:
        """模拟生成委托代理合同"""
        return f"""【合同编号】LV-2024-001

【委托方】
名称：东方国际融资租赁有限公司
统一社会信用代码：91310000MA1FL3L123
地址：中国（上海）自由贸易试验区世纪大道100号

【受托方】
名称：上海华通律师事务所
统一社会信用代码：31310000XXXXXXXX
地址：上海市某某区某某路某某号
负责人：王某某

【委托事项】
受托方接受委托方委托，指派左安平、蔡晓薇律师代理委托方与江西昌盛商业管理有限公司、南昌长风房地产开发有限公司、深圳前海恒信担保有限公司融资租赁合同纠纷一案。

案号：（2024）沪74民初721号
案由：融资租赁合同纠纷
代理权限：特别授权代理

【律师费】
律师费金额：人民币200,000元

【签署栏】
委托方（盖章）：东方国际融资租赁有限公司

受托方（盖章）：上海华通律师事务所

签订日期：2024年X月X日
"""
    
    def _mock_insurance_policy(self, prompt: str) -> str:
        """模拟生成保险单"""
        return f"""【诉讼财产保全责任保险保单】

【保险人】
名称：XX保险股份有限公司上海分公司
统一社会信用代码：91310000XXXXXXXX
地址：上海市某某区某某路某某号

【投保人】
名称：东方国际融资租赁有限公司
统一社会信用代码：91310000MA1FL3L123
地址：中国（上海）自由贸易试验区世纪大道100号

【保险信息】
保单号：XXXXXXXX
保险期间：2024年X月X日0时起至2025年X月X日24时止

【保险标的】
被申请人：江西昌盛商业管理有限公司、南昌长风房地产开发有限公司、深圳前海恒信担保有限公司
保全标的：银行账户、房产等

【保险金额】
保险金额：人民币120,467,622.06元

【保费】
保费金额：人民币121,663.17元

【批单信息】
批单日期：2024年X月X日
批单内容：增加被申请人

【保险条款】
（详见保险条款）
"""
    
    def _mock_consulting_contract(self, prompt: str) -> str:
        """模拟生成咨询服务合同"""
        return f"""【合同编号】FW-2021-001

【委托方】
名称：江西昌盛商业管理有限公司
统一社会信用代码：91360121MA35L8T456
法定代表人：吴建华
地址：江西省南昌市南昌县莲塘镇向阳路199号

【服务方】
名称：东方国际融资租赁有限公司
统一社会信用代码：91310000MA1FL3L123
法定代表人：周明远
地址：中国（上海）自由贸易试验区世纪大道100号

【服务内容】
服务方为委托方提供融资咨询服务，包括：
1. 融资方案设计
2. 融资渠道推荐
3. 融资流程指导

【服务费】
服务费金额：人民币4,650,000元

【支付凭证】
支付金额：人民币4,650,000元
支付日期：2021年X月X日
支付方式：银行转账

【签署栏】
委托方（盖章）：江西昌盛商业管理有限公司
法定代表人（签字）：吴建华

服务方（盖章）：东方国际融资租赁有限公司
法定代表人（签字）：周明远

签订日期：2021-02-24
"""
    
    def _mock_shareholder_decision(self, prompt: str) -> str:
        """模拟生成股东决定"""
        # 根据提示词判断是抵押人还是保证人
        if "南昌长风" in prompt:
            company = "南昌长风房地产开发有限公司"
            legal = "张立军"
        else:
            company = "深圳前海恒信担保有限公司"
            legal = "李伟"
        
        return f"""【股东决定】

【公司信息】
公司名称：{company}
统一社会信用代码：91360103MA35H7U789
公司地址：江西省南昌市西湖区抚生路369号

【会议信息】
会议类型：股东决定
会议日期：2021-02-24
出席股东：全体股东

【决议内容】
经全体股东研究决定，同意公司以下事项：

一、同意以公司名下位于江西省南昌市西湖区抚生路369号的土地使用权及在建建筑物为江西昌盛商业管理有限公司与东方国际融资租赁有限公司之间的《融资租赁合同》（合同编号：RZL-2021-001）项下债务提供抵押担保。

二、抵押担保范围包括主债权本金人民币150,000,000元及利息、违约金、实现债权的费用等。

三、授权公司法定代表人{legal}代表公司签署相关抵押合同及办理抵押登记手续。

四、本决定自签署之日起生效。

【股东签字】
股东（盖章）：（全体股东签章）

法定代表人（签字）：{legal}

日期：2021-02-24
"""
    
    def _mock_guarantee_contract(self, prompt: str) -> str:
        """模拟生成保证合同"""
        return f"""【合同编号】BZ-2021-001

【保证人】
名称：深圳前海恒信担保有限公司
统一社会信用代码：91440300MA5FQ2K012
法定代表人：李伟
地址：广东省深圳市福田区福田街道福华一路6号

【债权人】
名称：东方国际融资租赁有限公司
统一社会信用代码：91310000MA1FL3L123
法定代表人：周明远
地址：中国（上海）自由贸易试验区世纪大道100号

【鉴于条款】
1. 保证人系依法设立并有效存续的企业法人；
2. 债权人系依法设立并有效存续的融资租赁公司；
3. 债务人（江西昌盛商业管理有限公司）与债权人于2021-02-24签订了《融资租赁合同》（合同编号：RZL-2021-001）；
4. 保证人愿意为债务人的上述债务提供连带责任保证；

【第一条 被担保主债权】
1.1 被担保主债权本金：人民币150,000,000元
1.2 被担保主债权利息：按《融资租赁合同》约定计算

【第二条 保证方式】
2.1 保证方式：连带责任保证
2.2 债权人有权直接要求保证人承担保证责任

【第三条 保证期间】
3.1 保证期间：主债务履行期限届满之日起两年
3.2 债权人宣布债务提前到期的，保证期间为债务提前到期之日起两年

【第四条 保证范围】
4.1 保证担保范围包括：
    - 主债权本金及利息
    - 违约金
    - 损害赔偿金
    - 实现债权的费用

【第五条 公证】
本合同办理公证，公证书编号：（2021）沪长证经字第XXXX号

【签署栏】
保证人（盖章）：深圳前海恒信担保有限公司
法定代表人（签字）：李伟

债权人（盖章）：东方国际融资租赁有限公司
法定代表人（签字）：周明远

签订日期：2021-02-24
"""
    
    def _mock_deposit_proof(self, prompt: str) -> str:
        """模拟生成保证金收据"""
        return f"""【保证金支付凭证】

【凭证信息】
凭证编号：BZPZ-2021-001
凭证日期：2021-02-24

【付款信息】
付款单位：江西昌盛商业管理有限公司
收款单位：东方国际融资租赁有限公司
付款金额：人民币4,500,000元
大写金额：人民币肆佰伍拾万元整
付款用途：融资租赁保证金
合同编号：RZL-2021-001

【收款收据】
收据编号：SL-2021-001
收款单位：东方国际融资租赁有限公司
付款单位：江西昌盛商业管理有限公司
金额：人民币4,500,000元
事由：融资租赁保证金

【财务信息】
会计主管：赵某某
出纳：陈某某

【备注】
保证金在租赁期满后用于抵扣最后一期租金或作为违约金扣除。
"""

    def _mock_equipment_list(self, prompt: str) -> str:
        """模拟生成租赁物清单（JSON格式）"""
        import re
        # 尝试从提示词中提取合同金额
        amount_match = re.search(r'合同金额[:：]\s*人民币([\d,]+)元', prompt)
        total_value = 150000000 if amount_match else 150000000
        
        # 生成6-8项设备
        return f"""[
  {{
    "序号": 1,
    "名称": "多联机中央空调系统",
    "规格型号": "VRV VIII代",
    "数量": "10套",
    "存放地点": "江西省南昌市南昌县莲塘镇向阳路199号",
    "评估价值": 45000000
  }},
  {{
    "序号": 2,
    "名称": "冷水机组",
    "规格型号": "离心式RF1-5000",
    "数量": "2套",
    "存放地点": "江西省南昌市南昌县莲塘镇向阳路199号",
    "评估价值": 12000000
  }},
  {{
    "序号": 3,
    "名称": "电梯设备",
    "规格型号": "曳引式客梯KONIA-1000",
    "数量": "4台",
    "存放地点": "江西省南昌市南昌县莲塘镇向阳路199号",
    "评估价值": 8000000
  }},
  {{
    "序号": 4,
    "名称": "配电变压器",
    "规格型号": "SCB13-2500/10",
    "数量": "8台",
    "存放地点": "江西省南昌市南昌县莲塘镇向阳路199号",
    "评估价值": 6400000
  }},
  {{
    "序号": 5,
    "名称": "消防水泵",
    "规格型号": "XBD15/40",
    "数量": "10套",
    "存放地点": "江西省南昌市南昌县莲塘镇向阳路199号",
    "评估价值": 3200000
  }},
  {{
    "序号": 6,
    "名称": "监控系统",
    "规格型号": "海康威视DS-7900",
    "数量": "1套",
    "存放地点": "江西省南昌市南昌县莲塘镇向阳路199号",
    "评估价值": 2500000
  }},
  {{
    "序号": 7,
    "名称": "商场照明设备",
    "规格型号": "飞利浦LED",
    "数量": "1批",
    "存放地点": "江西省南昌市南昌县莲塘镇向阳路199号",
    "评估价值": 1800000
  }},
  {{
    "序号": 8,
    "名称": "其他附属设施",
    "规格型号": "-",
    "数量": "1批",
    "存放地点": "江西省南昌市南昌县莲塘镇向阳路199号",
    "评估价值": 21100000
  }}
]"""

    def _mock_transfer_contract(self, prompt: str) -> str:
        """模拟生成转让合同"""
        return f"""【合同编号】ZR-2021-001

【转让方（甲方）】
名称：江西昌盛商业管理有限公司
统一社会信用代码：91360121MA35L8T456
法定代表人：吴建华
地址：江西省南昌市南昌县莲塘镇向阳路199号

【受让方（乙方）】
名称：东方国际融资租赁有限公司
统一社会信用代码：91310000MA1FL3L123
法定代表人：周明远
地址：中国（上海）自由贸易试验区世纪大道100号

【鉴于条款】
1. 甲方系依法设立并有效存续的企业法人，具备良好的商业信誉；
2. 乙方系依法设立并有效存续的融资租赁公司，具备开展融资租赁业务的资质；
3. 双方于2021-02-24签订了《融资租赁合同（售后回租）》（合同编号：RZL-2021-001），约定乙方以售后回租方式向甲方提供融资租赁服务；
4. 为担保甲方履行上述融资租赁合同项下债务，双方经友好协商，就设备转让事宜达成如下协议：

【第一条 转让标的】
1.1 甲方同意将其合法拥有物的下列设备转让给乙方：
    - 设备名称：某某商场设备及附属设施
    - 规格型号：详见设备清单
    - 数量：详见设备清单
    - 转让价格：人民币150,000,000元

【第二条 价款支付】
2.1 乙方应于本合同生效之日起5个工作日内，将设备转让价款支付至甲方指定账户。
2.2 甲方指定收款账户信息如下：
    - 户名：江西昌盛商业管理有限公司
    - 开户银行：中国工商银行南昌县支行
    - 账号：XXXXXXXXXXXXXXX

【第三条 权利义务】
3.1 乙方权利：
    - 取得转让设备的所有权；
    - 按本合同约定收取设备转让价款。
3.2 甲方权利：
    - 收取设备转让价款；
    - 在租赁期满并付清全部租金后，有权以名义价格回购设备。

【第四条 违约责任】
4.1 任何一方违反本合同约定的，应承担违约责任。
4.2 违约金为设备转让价款的百分之二十。

【第五条 争议解决】
本合同履行过程中发生的争议，双方应友好协商解决；协商不成的，任何一方均可向乙方住所地有管辖权的人民法院提起诉讼。

【第六条 公证】
本合同办理公证，公证书编号：（2021）沪长证经字第XXXX号

【签署栏】
甲方（盖章）：江西昌盛商业管理有限公司
法定代表人（签字）：吴建华

乙方（盖章）：东方国际融资租赁有限公司
法定代表人（签字）：周明远

签订日期：2021-02-24
"""
    
    def _mock_finance_lease_contract(self, prompt: str) -> str:
        """模拟生成融资租赁合同"""
        return f"""【合同编号】RZL-2021-001

【出租人】
名称：东方国际融资租赁有限公司
统一社会信用代码：91310000MA1FL3L123
法定代表人：周明远
地址：中国（上海）自由贸易试验区世纪大道100号

【承租人】
名称：江西昌盛商业管理有限公司
统一社会信用代码：91360121MA35L8T456
法定代表人：吴建华
地址：江西省南昌市南昌县莲塘镇向阳路199号

【鉴于条款】
1. 出租人系依法设立并有效存续的融资租赁公司，具备开展融资租赁业务的资质；
2. 承租人系依法设立并有效存续的企业法人，具备良好的商业信誉；
3. 双方于2021-02-24签订了《转让合同》（合同编号：ZR-2021-001），约定承租人将其设备转让给出租人，再由承租人租回使用；

【第一条 租赁物】
1.1 租赁物名称：某某商场设备及附属设施
1.2 租赁物评估价值：人民币150,000,000元
1.3 租赁物数量：详见设备清单

【第二条 租赁期限】
2.1 租赁期限：24个月
2.2 起租日：2021-02-26
2.3 租赁期满日：2024年2月24日

【第三条 租金及支付】
3.1 租金总额：人民币160,623,496.08元
3.2 年利率：6.10%
3.3 支付方式：按月支付
3.4 每期租金：人民币6,692,645.67元
3.5 支付日期：每月24日

【第四条 保证金】
4.1 保证金金额：人民币4,500,000元
4.2 保证金在租赁期满后用于抵扣最后一期租金或作为违约金扣除

【第五条 违约责任】
5.1 承租人逾期支付租金的，应按日万分之五支付逾期利息；
5.2 承租人逾期支付租金超过30日的，出租人有权解除合同并要求支付全部未付租金。

【第六条 公证】
本合同办理公证，公证书编号：（2021）沪长证经字第XXXX号

【签署栏】
出租人（盖章）：东方国际融资租赁有限公司
法定代表人（签字）：周明远

承租人（盖章）：江西昌盛商业管理有限公司
法定代表人（签字）：吴建华

签订日期：2021-02-24
"""


def create_generator(config: Dict[str, Any] = None) -> LLMGenerator:
    """创建LLM生成器的工厂函数"""
    if config is None:
        config = {}
    
    provider = LLMProvider(config.get("provider", "mock"))
    model = config.get("model", "gpt-4")
    temperature = config.get("temperature", 0.7)
    max_tokens = config.get("max_tokens", 4096)
    api_key = config.get("api_key")
    base_url = config.get("base_url")
    
    gen_config = GenerationConfig(
        provider=provider,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=api_key,
        base_url=base_url,
    )
    
    return LLMGenerator(gen_config)


if __name__ == "__main__":
    # 测试生成器
    generator = create_generator({"provider": "mock"})
    
    test_prompt = "生成一份付款回单..."
    result = generator.generate(test_prompt, "payment_receipt")
    print("生成的付款回单:")
    print(result[:500])
