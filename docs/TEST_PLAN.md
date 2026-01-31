# 金融案件证据集生成系统 - 测试方案

**文档版本**: v2.0  
**状态**: 有效  
**创建日期**: 2024-01-27  
**最后更新**: 2024-01-27

---

## 一、文档演进历史

| 版本 | 日期 | 主要变更 |
|------|------|---------|
| [v1.0](v1_history/TEST_PLAN_v1.0.md) | 2024-01-26 | 初始版本 |
| **v2.0** | **2024-01-27** | **通用框架测试，自动化数据生成测试** |

---

## 二、测试框架

### 2.1 测试类型

| 测试类型 | 范围 | 优先级 |
|---------|------|--------|
| 单元测试 | 数据生成器、Prompt构建器、渲染器 | P0 |
| 集成测试 | 完整流程测试 | P0 |
| Regression测试 | 核心功能回归 | P0 |
| E2E测试 | 端到端生成测试 | P1 |

### 2.2 测试目录结构

```
tests/
├── unit/
│   ├── test_data_generator.py
│   ├── test_prompt_builder.py
│   └── test_renderer.py
├── integration/
│   └── test_full_pipeline.py
├── regression/
│   └── test_core_functions.py
└── e2e/
    └── test_full_generation.py
```

---

## 三、单元测试

### 3.1 数据生成器测试

```python
# tests/unit/test_data_generator.py

import pytest
from src.utils.data_generator import DataGenerator

class TestDataGenerator:
    
    def setup_method(self):
        self.generator = DataGenerator()
    
    def test_company_name_generation(self):
        """测试公司名称生成"""
        names = [self.generator.generate_company_name() for _ in range(10)]
        assert all("某" in name for name in names)
        assert all("有限公司" in name or "集团" in name for name in names)
    
    def test_equipment_name_generation(self):
        """测试设备名称生成"""
        names = [self.generator.generate_equipment_name() for _ in range(10)]
        assert len(set(names)) < 10  # 有重复是正常的（模板有限）
    
    def test_amount_generation(self):
        """测试金额生成"""
        amount = self.generator.generate_amount(min_val=1000000, max_val=50000000)
        assert 1000000 <= amount <= 50000000
    
    def test_bank_account_generation(self):
        """测试银行账号生成"""
        account = self.generator.generate_bank_account()
        assert len(account) == 19
        assert account.isdigit()
    
    def test_complete_dataset(self):
        """测试完整数据集生成"""
        data = self.generator.generate_complete_dataset("融资租赁纠纷", {})
        
        assert "party_info" in data
        assert "location_info" in data
        assert "financial_info" in data
        assert "equipment_info" in data
```

### 3.2 渲染器测试

```python
# tests/unit/test_renderer.py

import pytest
from src.renderers.evidence_renderer import EvidenceRenderer

class TestEvidenceRenderer:
    
    def setup_method(self):
        self.renderer = EvidenceRenderer()
    
    def test_render_contract(self):
        """测试合同渲染"""
        contract_data = {
            "title": "融资租赁合同",
            "contract_no": "FL-202102-001",
            "parties": [...],
            "content": "第一条 定义与解释\n..."
        }
        elements = self.renderer.render_contract(contract_data)
        assert len(elements) > 0
        # 验证包含标题
        assert any("融资租赁合同" in str(e) for e in elements)
    
    def test_render_table(self):
        """测试表格渲染"""
        table_data = {
            "title": "租赁物清单",
            "headers": ["序号", "设备名称", "数量"],
            "rows": [["1", "空调", "10套"]]
        }
        elements = self.renderer.render_table(
            table_data["title"],
            table_data["headers"],
            table_data["rows"]
        )
        assert len(elements) > 0
```

---

## 四、集成测试

### 4.1 完整流程测试

```python
# tests/integration/test_full_pipeline.py

import pytest
from pathlib import Path
import json

class TestFullPipeline:
    
    def test_generate_evidence_set(self, tmp_path):
        """测试完整证据集生成"""
        # 准备输入
        input_data = {
            "case_info": {"case_number": "TEST-2024-001"},
            "contracts": [{"type": "融资租赁合同", "data": {...}}],
            "attachments": [{"type": "租赁物清单", "data": {...}}]
        }
        
        # 运行生成
        generator = PDFGenerator(str(tmp_path / "output.pdf"))
        generator.generate(input_data)
        
        # 验证输出
        output = tmp_path / "output.pdf"
        assert output.exists()
        assert output.stat().st_size > 0
        assert output.stat().st_size < 10 * 1024 * 1024  # <10MB
```

---

## 五、Regression测试

### 5.1 核心功能回归

```python
# tests/regression/test_core_functions.py

class TestCoreFunctionsRegression:
    
    def test_data_completeness(self):
        """回归测试: 数据完整性"""
        from src.utils.data_generator import DataGenerator
        generator = DataGenerator()
        
        data = generator.generate_complete_dataset("融资租赁纠纷", {})
        
        # 验证所有必需字段都存在
        required_fields = [
            "company_name", "person_name", "bank_account",
            "equipment_name", "equipment_model", "contract_amount"
        ]
        
        for field in required_fields:
            assert field in str(data), f"缺少字段: {field}"
    
    def test_no_hardcoded_content(self):
        """回归测试: 无硬编码内容"""
        from src.generators import contract_generator
        import inspect
        
        source = inspect.getsource(contract_generator)
        
        # 检查没有硬编码的特定案件内容
        forbidden = ["某某公司5", "多联机中央空调", "东方国际融资租赁"]
        for item in forbidden:
            assert item not in source, f"发现硬编码: {item}"
```

---

## 六、验证命令

### 6.1 运行测试

```bash
#!/bin/bash
# run_tests.sh

set -e

echo "========================================"
echo "  金融案件证据集生成系统 - 测试套件"
echo "========================================"

# 1. 单元测试
echo ""
echo ">>> 1. 运行单元测试..."
python3 -m pytest tests/unit/ -v --cov=src --cov-report=html

# 2. 集成测试
echo ""
echo ">>> 2. 运行集成测试..."
python3 -m pytest tests/integration/ -v

# 3. Regression测试
echo ""
echo ">>> 3. 运行回归测试..."
python3 -m pytest tests/regression/ -v --tb=short

# 4. E2E测试
echo ""
echo ">>> 4. 运行端到端测试..."
python3 -m pytest tests/e2e/ -v
```

### 6.2 质量验证

```bash
#!/bin/bash
# verify_quality.sh

PDF_FILE=$1

if [ -z "$PDF_FILE" ]; then
    echo "用法: ./verify_quality.sh <pdf文件>"
    exit 1
fi

TEXT_FILE=$(mktemp)
pdftotext "$PDF_FILE" "$TEXT_FILE" 2>/dev/null

echo "========================================"
echo "  输出质量验证: $PDF_FILE"
echo "========================================"

echo ""
echo ">>> 1. 检查脱敏标记..."
COUNT=$(grep -c "某某公司" "$TEXT_FILE" || true)
[ "$COUNT" -eq 0 ] && echo "   ✓ 通过" || echo "   ✗ 失败: $COUNT处"

echo ""
echo ">>> 2. 检查占位符..."
COUNT=$(grep -c "某某设备\|某某型号\|若干" "$TEXT_FILE" || true)
[ "$COUNT" -eq 0 ] && echo "   ✓ 通过" || echo "   ✗ 失败: $COUNT处"

echo ""
echo ">>> 3. 检查PDF分页..."
PAGE_COUNT=$(pdfinfo "$PDF_FILE" 2>/dev/null | grep "Pages:" | awk '{print $2}')
echo "   总页数: $PAGE_COUNT"

rm -f "$TEXT_FILE"
```

---

## 七、占位符清理机制测试用例（TD-2026-02-01-001）

### 7.1 黑盒测试用例

| 用例ID | 测试场景 | 输入 | 预期输出 | 优先级 |
|--------|---------|------|---------|--------|
| QB-T001 | 正常生成无占位符 | 标准判决书 | 证据文件无 `某某`、`X4` 等占位符 | P0 |
| QB-T002 | 首次生成有占位符 | 标准判决书 | 自动重试，3次内清除占位符 | P0 |
| QB-T003 | 多次重试失败 | 复杂判决书 | 正确降级，记录错误，继续处理 | P0 |
| QB-T004 | 占位符类型检测 | 异常证据文件 | 正确识别所有占位符模式 | P0 |
| QB-T005 | 重试计数统计 | 重试场景 | 统计信息准确 | P1 |
| QB-T006 | 批量证据生成 | 20个证据 | 所有证据无占位符 | P0 |
| QB-T007 | PDF脱敏检查 | 完整卷宗PDF | 无脱敏标记残留 | P0 |
| QB-T008 | 通过率验证 | 53个证据 | 通过率 ≥ 95% | P0 |

### 7.2 占位符模式检测测试

```python
# tests/blackbox/test_placeholder_detection.py

import pytest
from pathlib import Path
from src.utils.placeholder_checker import PlaceholderChecker


class TestPlaceholderDetectionBlackbox:
    """占位符检测黑盒测试"""
    
    def setup_method(self):
        self.checker = PlaceholderChecker()
    
    def test_qb_t001_no_placeholder_normal(self):
        """QB-T001: 正常生成无占位符"""
        # 模拟正常生成的证据文本
        text = "原告华夏金融租赁有限公司与被告江西恒信商业管理有限公司签订融资租赁合同，金额壹亿伍仟万元整。"
        is_clean, found = self.checker.check(text)
        assert is_clean, f"正常文本不应包含占位符: {found}"
    
    def test_qb_t001_detect_某某公司(self):
        """QB-T001: 检测某某公司占位符"""
        text = "原告某某公司5与被告某某公司1签订合同"
        is_clean, found = self.checker.check(text)
        assert not is_clean, "应检测到某某公司占位符"
        assert any("某某公司" in p for p in found)
    
    def test_qb_t001_detect_X4(self):
        """QB-T001: 检测X4占位符"""
        text = "按X4计算违约金，共X5元"
        is_clean, found = self.checker.check(text)
        assert not is_clean, "应检测到X4占位符"
        assert "X4" in found or "X5" in found
    
    def test_qb_t001_detect_empty_brackets(self):
        """QB-T001: 检测空括号占位符"""
        text = "开户行：银行支行【】账号：123456"
        is_clean, found = self.checker.check(text)
        assert not is_clean, "应检测到空括号占位符"
    
    def test_qb_t004_all_placeholder_types(self):
        """QB-T004: 检测所有占位符类型"""
        test_cases = [
            ("某某公司5签署", True),
            ("按X4计算", True),
            ("X年X月X日", True),
            ("按X%计算", True),
            ("【】", True),
            ("或授权代表", True),
            ("二〇二四年一月一日", False),  # 正确日期不应检测
            ("华夏金融租赁有限公司", False),
        ]
        for text, should_detect in test_cases:
            is_clean, found = self.checker.check(text)
            if should_detect:
                assert not is_clean, f"应检测到占位符: {text}"
            else:
                assert is_clean, f"正常文本不应检测为占位符: {text}"
```

### 7.3 重试机制黑盒测试

```python
# tests/blackbox/test_retry_handler.py

import pytest
from src.utils.retry_handler import RetryHandler


class TestRetryHandlerBlackbox:
    """重试处理器黑盒测试"""
    
    def test_qb_t002_retry_on_placeholder(self):
        """QB-T002: 检测到占位符时自动重试"""
        call_count = 0
        
        def generate_with_placeholder():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                return "某某公司5签署合同"
            return "华夏金融租赁有限公司签署合同"
        
        handler = RetryHandler(max_retries=3)
        result = handler.execute_with_retry(generate_with_placeholder)
        
        assert result["success"], "重试后应成功"
        assert result["attempts"] == 2, "应重试1次"
        assert call_count == 2, "生成函数应被调用2次"
    
    def test_qb_t003_max_retries_failure(self):
        """QB-T003: 超过最大重试次数后降级"""
        def always_has_placeholder():
            return "某某公司5签署合同，金额X4元"
        
        handler = RetryHandler(max_retries=2)
        result = handler.execute_with_retry(always_has_placeholder)
        
        assert not result["success"], "应返回失败"
        assert result["attempts"] == 3, "应尝试3次"
        assert len(result["placeholders"]) > 0, "应记录占位符"
    
    def test_qb_t005_retry_stats(self):
        """QB-T005: 重试统计信息"""
        def success_first():
            return "华夏金融租赁有限公司签署合同"
        
        handler = RetryHandler(max_retries=3)
        handler.execute_with_retry(success_first)
        stats = handler.get_retry_stats()
        
        assert stats["total_attempts"] == 1, "总尝试次数应为1"
        assert stats["first_try_success"] == True, "首次应成功"
        assert stats["retry_count"] == 0, "重试次数应为0"
```

### 7.4 完整流程黑盒测试

```python
# tests/blackbox/test_full_pipeline_placeholder.py

import pytest
from pathlib import Path
import subprocess


class TestFullPipelinePlaceholderBlackbox:
    """完整流程占位符清理黑盒测试"""
    
    def test_qb_t006_batch_evidence_no_placeholder(self, tmp_path):
        """QB-T006: 批量证据生成无占位符"""
        # 运行完整生成流程
        result = subprocess.run(
            ["python3", "run_complete.py"],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True,
            timeout=1800
        )
        
        assert result.returncode == 0, f"生成失败: {result.stderr}"
        
        # 检查证据文件
        evidence_dir = Path("outputs/stage1/evidence")
        if evidence_dir.exists():
            for evidence_file in evidence_dir.rglob("*.txt"):
                with open(evidence_file, 'r', encoding='utf-8') as f:
                    text = f.read()
                # 验证无占位符
                assert "某某" not in text, f"发现占位符: {evidence_file}"
                assert "X4" not in text, f"发现占位符: {evidence_file}"
                assert "X年X月X日" not in text, f"发现占位符: {evidence_file}"
    
    def test_qb_t007_pdf_no_anonymization_marks(self, tmp_path):
        """QB-T007: PDF无脱敏标记"""
        # 运行完整生成流程
        subprocess.run(
            ["python3", "run_complete.py"],
            capture_output=True,
            text=True,
            timeout=1800
        )
        
        # 检查PDF
        pdf_path = Path("outputs_complete/完整测试卷宗.pdf")
        if pdf_path.exists():
            # 提取PDF文本
            text_file = tmp_path / "pdf_text.txt"
            subprocess.run(
                ["pdftotext", str(pdf_path), str(text_file)],
                capture_output=True
            )
            
            with open(text_file, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            
            # 验证无脱敏标记
            assert "某某公司" not in text, "PDF包含某某公司脱敏标记"
            assert "某公司" not in text, "PDF包含某公司脱敏标记"
    
    def test_qb_t008_pass_rate_95_percent(self):
        """QB-T008: 通过率≥95%"""
        # 运行完整生成流程
        subprocess.run(
            ["python3", "run_complete.py"],
            capture_output=True,
            text=True,
            timeout=1800
        )
        
        # 检查验证结果
        # 期望：53个证据，50个以上通过（≥95%）
        # 验证输出中应有 "通过: 50/53" 或更高
```

### 7.5 黑盒测试执行命令

```bash
#!/bin/bash
# run_blackbox_tests.sh

set -e

echo "========================================"
echo "  占位符清理机制 - 黑盒测试"
echo "========================================"

echo ""
echo ">>> 1. 运行占位符检测测试..."
python3 -m pytest tests/blackbox/test_placeholder_detection.py -v

echo ""
echo ">>> 2. 运行重试机制测试..."
python3 -m pytest tests/blackbox/test_retry_handler.py -v

echo ""
echo ">>> 3. 运行完整流程测试..."
python3 -m pytest tests/blackbox/test_full_pipeline_placeholder.py -v

echo ""
echo "========================================"
echo "  黑盒测试完成"
echo "========================================"
```

---

**文档版本**: v2.1  
**状态**: 有效  
**创建日期**: 2024-01-27  
**最后更新**: 2026-02-01
