"""大模型集成"""
from typing import Dict, Any, Optional
from loguru import logger
import os


class LLMClient:
    """大模型客户端"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        api_base: Optional[str] = None,
        timeout: float = 600.0
    ):
        """
        初始化大模型客户端

        Args:
            api_key: API密钥
            model: 模型名称
            api_base: API基础URL
            timeout: 超时时间（秒），默认600秒（10分钟）
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.api_base = api_base or os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.timeout = timeout

        if not self.api_key:
            logger.warning("未设置API密钥,将使用模拟模式")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        生成文本
        
        Args:
            prompt: 提示词
            **kwargs: 其他参数
        
        Returns:
            生成的文本
        """
        if not self.api_key:
            logger.info("模拟模式:返回模拟响应")
            return self._mock_generate(prompt)
        
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_base,
                timeout=self.timeout
            )

            # 过滤掉可能引起问题的参数
            safe_kwargs = {
                'max_tokens': kwargs.get('max_tokens', 8192),
                'temperature': kwargs.get('temperature', 0.7),
                'top_p': kwargs.get('top_p', 0.9)
            }

            logger.info(f"调用大模型，超时时间: {self.timeout}秒")
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的法律文书生成助手。"},
                    {"role": "user", "content": prompt}
                ],
                **safe_kwargs
            )

            content = response.choices[0].message.content
            logger.success(f"大模型响应成功，长度: {len(content)} 字符")
            return content
        except Exception as e:
            logger.error(f"调用大模型失败: {e}")
            logger.info(f"提示：如果超时，可以尝试：")
            logger.info(f"1. 增加超时时间: LLMClient(timeout=600)")
            logger.info(f"2. 减少max_tokens参数")
            logger.info(f"3. 使用更快的模型")
            raise
    
    def _mock_generate(self, prompt: str) -> str:
        """
        模拟生成(用于测试)

        Args:
            prompt: 提示词

        Returns:
            模拟的响应（纯文本格式，不含markdown）
        """
        return """
【合同编号】FL-2021-NCHD-001

【转让方（甲方）】
名称：华鑫融资租赁有限公司
统一社会信用代码：91310000MA1XXXXXX
法定代表人：张某某
地址：上海市浦东新区某某路某某号

【受让方（乙方）】
名称：长江某某某某有限公司
统一社会信用代码：91310115MA1XXXXXX
法定代表人：李某某
地址：上海市某某区某某路某某号

【鉴于条款】
1. 甲方系依法设立并有效存续的融资租赁公司，具备开展融资租赁业务的资质；
2. 乙方系依法设立并有效存续的企业法人，具备良好的商业信誉；
3. 双方于2021年3月15日签订了《融资租赁合同（售后回租）》（合同编号：FL-2021-NCHD-001），约定甲方以售后回租方式向乙方提供融资租赁服务；
4. 为担保乙方履行上述融资租赁合同项下债务，双方经友好协商，就设备转让事宜达成如下协议：

【第一条 转让标的】
1.1 乙方同意将其合法拥有物的下列设备转让给甲方：
    - 设备名称：某某设备
    - 规格型号：某某型号
    - 数量：若干台
    - 转让价格：人民币叁仟万元整

【第二条 价款支付】
2.1 甲方应于本合同生效之日起5个工作日内，将设备转让价款支付至乙方指定账户。
2.2 乙方指定收款账户信息如下：
    - 户名：长江某某某某有限公司
    - 开户银行：某某银行某某支行
    - 账号：XXXXXXXXXXXXXXX

【第三条 权利义务】
3.1 甲方权利：
    - 取得转让设备的所有权；
    - 按本合同约定收取设备转让价款。
3.2 乙方权利：
    - 收取设备转让价款；
    - 在租赁期满并付清全部租金后，有权以名义价格回购设备。

【第四条 违约责任】
4.1 任何一方违反本合同约定的，应承担违约责任。
4.2 违约金为设备转让价款的百分之二十。

【第五条 争议解决】
本合同履行过程中发生的争议，双方应友好协商解决；协商不成的，任何一方均可向甲方住所地有管辖权的人民法院提起诉讼。

【签署栏】
甲方（盖章）：
法定代表人（签字）：

乙方（盖章）：
法定代表人（签字）：

签订日期：2021年3月15日
"""
