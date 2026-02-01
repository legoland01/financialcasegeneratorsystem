"""
Pytest configuration and fixtures for unit tests
"""

import pytest
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing"""
    class MockLLMClient:
        def complete(self, prompt):
            return "模拟生成的合同内容"
    return MockLLMClient()


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_judgment_text():
    """Sample judgment text for testing"""
    return """
上海市浦东新区人民法院
民事判决书

（2024）沪0115民初12345号

原告：测试原告融资租赁有限公司，住所地北京市朝阳区。
法定代表人：张三，董事长。

被告：测试被告制造有限公司，住所地上海市浦东新区。
法定代表人：李四，总经理。

原告与被告于2023年1月15日签订《融资租赁合同》，合同约定被告向原告租赁数控机床设备一台，合同金额为人民币1,500,000元，租赁期限为24个月。合同签订后，被告支付了首期租金人民币300,000元，但自2023年6月起被告未再支付租金。截至起诉之日，被告尚欠原告租金人民币1,200,000元。

原告诉称：请求判令被告向原告支付欠款本金人民币1,500,000元，利息人民币75,000元，违约金人民币30,000元，并承担本案诉讼费用人民币5,000元。

本院认为：原、被告签订的融资租赁合同系双方当事人真实意思表示，合法有效。被告未按合同约定支付租金，构成违约。原告请求被告支付欠款本金、利息及违约金的诉讼请求，本院予以支持。

综上所述，判决如下：
一、被告向原告支付欠款本金人民币1,500,000元；
二、被告向原告支付利息人民币75,000元；
三、被告向原告支付违约金人民币30,000元；
四、被告向原告支付诉讼费用人民币5,000元。
    """.strip()
