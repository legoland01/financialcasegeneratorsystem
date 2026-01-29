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

**文档版本**: v2.0  
**状态**: 有效  
**创建日期**: 2024-01-27  
**最后更新**: 2024-01-27
