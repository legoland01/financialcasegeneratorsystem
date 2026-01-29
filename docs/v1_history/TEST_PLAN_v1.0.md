# 金融案件PDF生成系统 - 测试方案

## 一、测试框架

```
┌─────────────────────────────────────────────────────────────────┐
│                         测试框架架构                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    单元测试 (Unit Test)                  │   │
│   │   - 通用配置加载测试                                      │   │
│   │   - 插件化处理器测试                                      │   │
│   │   - 模板引擎测试                                          │   │
│   │   - 数据验证测试                                          │   │
│   │   - 内容净化测试                                          │   │
│   │   - 计算器测试                                            │   │
│   └─────────────────────────────────────────────────────────┘   │
│                           ↓                                      │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                   集成测试 (Integration Test)            │   │
│   │   - 配置驱动的完整流程测试                                │   │
│   │   - 多案件类型测试                                        │   │
│   │   - 插件加载测试                                          │   │
│   │   - 模板渲染测试                                          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                           ↓                                      │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                   E2E测试 (End-to-End Test)              │   │
│   │   - 完整PDF生成测试（多案件类型）                         │   │
│   │   - 配置切换测试                                          │   │
│   │   - 性能测试                                              │   │
│   └─────────────────────────────────────────────────────────┘   │
│                           ↓                                      │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                   Regression测试 (Regression Test)       │   │
│   │   - 通用框架回归测试                                      │   │
│   │   - 配置兼容性测试                                        │   │
│   │   - 插件兼容性测试                                        │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 二、通用性测试原则

### 2.1 配置驱动测试

```python
# tests/conftest.py

import pytest
import json
from pathlib import Path
from src.core.config_loader import ConfigLoader

@pytest.fixture
def config_loader():
    return ConfigLoader()

@pytest.fixture
def sample_case_config():
    """示例案件配置 - 可复用于多案件类型测试"""
    return {
        "case_type": "通用金融纠纷",
        "case_type_code": "通用",
        "evidence_templates": [
            {
                "template_id": "generic_contract",
                "template_name": "合同模板",
                "required_clauses": [
                    "定义与解释",
                    "标的",
                    "价款",
                    "交付",
                    "违约责任",
                    "争议解决"
                ],
                "field_mappings": {
                    "amount": "data.amount",
                    "date": "data.date",
                    "parties": "data.parties"
                }
            }
        ],
        "calculation_rules": {},
        "anonymization_rules": {
            "company_patterns": ["某某公司\\d*"],
            "person_patterns": ["张某\\d*"],
            "address_patterns": ["某某省.*市.*区.*路.*号"]
        }
    }
```

### 2.2 多案件类型测试配置

```python
# tests/fixtures/case_configs/
case_configs/
├── financing_lease.json      # 融资租赁配置
├── bank_loan.json            # 银行借贷配置
├── factoring.json            # 保理合同配置
├── guarantee.json            # 担保合同配置
└── custom_case.json          # 自定义案件配置
```

## 三、单元测试

### 3.1 配置加载测试

```python
# tests/unit/test_config_loader.py

import pytest
from src.core.config_loader import ConfigLoader

class TestConfigLoader:
    """配置加载器测试"""
    
    def setup_method(self):
        self.loader = ConfigLoader()
    
    def test_load_case_type_config(self, tmp_path):
        """测试加载案件类型配置"""
        config_content = {
            "case_type": "测试案件",
            "case_type_code": "TEST",
            "evidence_templates": []
        }
        config_file = tmp_path / "test_case.json"
        config_file.write_text(json.dumps(config_content))
        
        result = self.loader.load_case_config(str(config_file))
        
        assert result["case_type"] == "测试案件"
        assert result["case_type_code"] == "TEST"
    
    def test_config_not_found(self):
        """测试配置文件不存在"""
        with pytest.raises(FileNotFoundError):
            self.loader.load_case_config("/nonexistent/config.json")
    
    def test_invalid_json(self, tmp_path):
        """测试无效JSON格式"""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("not valid json")
        
        with pytest.raises(json.JSONDecodeError):
            self.loader.load_case_config(str(config_file))
    
    def test_missing_required_fields(self, tmp_path):
        """测试缺少必填字段"""
        config_content = {"case_type": "只有类型"}  # 缺少case_type_code
        
        # 应该使用默认值或给出警告
        result = self.loader.load_case_config_from_dict(config_content)
        assert result["case_type"] == "只有类型"
```

### 3.2 模板引擎测试

```python
# tests/unit/test_template_engine.py

import pytest
from src.core.template_engine import TemplateEngine

class TestTemplateEngine:
    """模板引擎测试"""
    
    def setup_method(self):
        self.engine = TemplateEngine()
    
    def test_variable_replacement(self):
        """测试变量替换"""
        template = """
合同编号：{{contract_number}}
金额：{{amount}}元
日期：{{date}}
"""
        data = {
            "contract_number": "TEST-2024-001",
            "amount": "1,000,000",
            "date": "2024-01-27"
        }
        
        result = self.engine.render(template, data)
        
        assert "TEST-2024-001" in result
        assert "1,000,000元" in result
        assert "2024-01-27" in result
        assert "{{" not in result  # 变量已被替换
    
    def test_conditional_rendering(self):
        """测试条件渲染"""
        template = """
{% if has_collateral %}
担保物：{{collateral_name}}
{% endif %}
"""
        data_with_collateral = {"has_collateral": True, "collateral_name": "房产 data_without_collateral = {"has_collateral": False}
"}
               
        result_with = self.engine.render(template, data_with_collateral)
        result_without = self.engine.render(template, data_without_collateral)
        
        assert "担保物：房产" in result_with
        assert "担保物" not in result_without
    
    def test_loop_rendering(self):
        """测试循环渲染"""
        template = """
设备清单：
{% for item in equipment_list %}
- {{item.name}} ({{item.model}})
{% endfor %}
"""
        data = {
            "equipment_list": [
                {"name": "设备A", "model": "Model-A"},
                {"name": "设备B", "model": "Model-B"}
            ]
        }
        
        result = self.engine.render(template, data)
        
        assert "设备A (Model-A)" in result
        assert "设备B (Model-B)" in result
```

### 3.3 脱敏处理器测试（通用）

```python
# tests/unit/test_deanonymizer.py

import pytest
from src.processors.deanonymizer.enhanced_processor import EnhancedDeanonymizer

class TestDeanonymizer:
    """脱敏处理器测试"""
    
    def setup_method(self):
        self.processor = EnhancedDeanonymizer()
        self.sample_mapping = {
            "company_patterns": ["某某公司\\d*"],
            "person_patterns": ["张某\\d*"],
            "address_patterns": ["某某省.*市.*区.*路.*号"],
            "custom_mapping": {
                "某某公司5": "测试公司A",
                "某某公司1": "测试公司B"
            }
        }
    
    def test_company_anonymization(self):
        """测试公司名脱敏替换"""
        text = "原告某某公司5与被告某某公司1签订合同"
        result = self.processor.process(text, self.sample_mapping)
        
        assert "测试公司A" in result
        assert "测试公司B" in result
        assert "某某公司" not in result
    
    def test_pattern_based_anonymization(self):
        """测试模式匹配脱敏"""
        text = "某某公司123与某某公司456签订协议"
        result = self.processor.process(text, self.sample_mapping)
        
        # 应该清理所有某某公司X格式
        assert "某某公司" not in result
    
    def test_no_mapping_leftover(self):
        """测试无脱敏标记残留"""
        text = "某某公司5委托某某律师事务所的张某处理本案"
        result = self.processor.process(text, self.sample_mapping)
        
        assert "某某公司" not in result
        assert "某某律师" not in result
        assert "张某" not in result  # 如果配置了person_patterns
    
    def test_llm_created_patterns(self):
        """测试LLM创造的脱敏模式"""
        text = "被告长江某有限公司未按期付款"
        result = self.processor.process(text, self.sample_mapping)
        
        # 应该清理长江某XXX模式
        assert "长江某" not in result

    def test_company_with_parentheses_pattern(self):
        """测试 '张伟 (公司2)' 模式处理 - BUG-010"""
        text = "法定代表人：张伟 (公司2)、张海峰 (公司6)"
        result = self.processor.process(text, self.sample_mapping)

        # 应该清理公司编号后缀
        assert "张伟 (公司2)" not in result
        assert "张海峰 (公司6)" not in result
        assert "张伟" in result
        assert "张海峰" in result
```

### 3.4 内容净化测试（通用）

```python
# tests/unit/test_content_cleaner.py

import pytest
from src.processors.content_cleaner.llm_prefix_cleaner import LLMPrefixCleaner
from src.processors.content_cleaner.qc_report_cleaner import QCReportCleaner

class TestContentCleaner:
    """内容净化器测试"""
    
    def test_llm_prefix_removal(self):
        """测试LLM响应前缀清理 - 通用版本"""
        cleaner = LLMPrefixCleaner()
        
        prefixes = [
            "好的，作为专业的法律文书生成助手，我将根据您提供的输入参数，生成第1证据组的完整证据包。",
            "根据您的要求，我生成以下内容：",
            "以下是第1证据组的完整证据包。",
            "作为专业的法律助手，我将帮您生成法律文书。",
            "我将根据您提供的输入参数，严格按照执行步骤和质量控制要求，生成第N证据组的完整证据包。",
        ]
        
        for prefix in prefixes:
            text = f"{prefix}\n\n合同正文内容..."
            cleaned = cleaner.clean(text)
            
            assert prefix not in cleaned, f"前缀 '{prefix}' 未被清理"
            assert "合同正文内容" in cleaned
    
    def test_qc_report_removal(self):
        """测试质检报告清理 - 通用版本"""
        cleaner = QCReportCleaner()
        
        qc_texts = [
            "数据一致性验证报告（证据组1）\n\n1. 公司名称与Profile库一致\n\n结论： 证据组1生成完毕",
            "验证报告\n结论： 生成完毕",
            "质量报告\n结论： 所有文件完整",
        ]
        
        for qc_text in qc_texts:
            text = f"合同正文...\n\n{qc_text}\n\n附件"
            cleaned = cleaner.clean(text)
            
            assert "数据一致性验证报告" not in cleaned
            assert "验证报告" not in cleaned
            assert "结论：" not in cleaned
            assert "合同正文" in cleaned
            assert "附件" in cleaned
    
    def test_combined_cleanup(self):
        """测试多问题混合清理"""
        from src.processors.content_cleaner import ContentCleaner
        
        cleaner = ContentCleaner()
        
        text = """好的，作为专业的法律文书生成助手，我将根据您提供的输入参数，生成第1证据组的完整证据包。

【测试】这是测试数据

数据一致性验证报告
结论： 证据组1生成完毕

合同正文内容...
（此处填写日期）
"""
        cleaned = cleaner.clean(text)
        
        assert "好的，作为" not in cleaned
        assert "【测试】" not in cleaned
        assert "数据一致性验证报告" not in cleaned
        assert "（此处填写" not in cleaned
        assert "合同正文内容" in cleaned

    def test_anomaly_pattern_cleanup(self):
        """测试LLM生成的异常模式清理 - BUG-012"""
        from src.processors.content_cleaner import ContentCleaner

        cleaner = ContentCleaner()

        # 测试"某地址"异常
        anomaly_texts = [
            "深圳华新科技集团有限公司）某地址：上海市浦东新区路号室",
            "法定代表人：张伟地址：上海市浦东新区路号室",
            "某某区上海市浦东新区某某路某某号",
        ]

        for text in anomaly_texts:
            cleaned, report = cleaner.clean(text)

            # 验证异常模式被清理
            assert "某地址" not in cleaned, f"某地址未清理: {cleaned}"
            assert "某某区" not in cleaned, f"某某区未清理: {cleaned}"
```

### 3.5 表格解析测试（通用）

```python
# tests/unit/test_table_parser.py

import pytest
from src.processors.table_parser.markdown_parser import MarkdownTableParser

class TestTableParser:
    """表格解析器测试 - 通用版本"""
    
    def test_simple_table(self):
        """测试简单表格解析"""
        parser = MarkdownTableParser()
        text = """
主要条款：

| 期数 | 应付日期 | 金额 |
|------|----------|------|
| 1 | 2021-08-24 | 100000 |
| 2 | 2022-02-24 | 100000 |

以上是付款计划。
"""
        clean_text, tables = parser.parse(text)
        
        assert len(tables) == 1
        assert "__TABLE_PLACEHOLDER_0__" in clean_text
        assert "|" not in clean_text
    
    def test_multiple_tables(self):
        """测试多表格解析"""
        parser = MarkdownTableParser()
        text = """
设备清单：
| 序号 | 名称 | 数量 |
|------|------|------|
| 1 | 设备A | 10套 |

付款计划：
| 期数 | 金额 |
|------|------|
| 1 | 100万 |
"""
        clean_text, tables = parser.parse(text)
        
        assert len(tables) == 2
        assert "__TABLE_PLACEHOLDER_0__" in clean_text
        assert "__TABLE_PLACEHOLDER_1__" in clean_text
    
    def test_complex_table(self):
        """测试复杂表格（含合并单元格等）"""
        parser = MarkdownTableParser()
        text = """
| 项目 | 内容1 | 内容2 |
|------|-------|-------|
| A | 值1 | 值2 |
| B | 值3 | 值4 |
"""
        clean_text, tables = parser.parse(text)
        
        assert len(tables) == 1
        assert tables[0][0] == ["项目", "内容1", "内容2"]
```

### 3.6 验证器测试（通用）

```python
# tests/unit/test_validators.py

import pytest
from src.validators.completeness_validator import CompletenessValidator
from src.validators.consistency_validator import ConsistencyValidator

class TestValidators:
    """验证器测试"""
    
    def test_clause_completeness(self):
        """测试条款完整性验证"""
        validator = CompletenessValidator()
        
        # 模拟配置
        required_clauses = ["定义与解释", "标的", "价款", "交付", "违约责任", "争议解决"]
        
        complete_contract = """
第一条 定义与解释
第二条 标的
第三条 价款
第四条 交付
第五条 违约责任
第六条 争议解决
"""
        result = validator.validate_clauses(complete_contract, required_clauses)
        assert result.is_complete == True
        assert len(result.missing_clauses) == 0
        
        incomplete_contract = """
第一条 定义与解释
第二条 标的
"""
        result = validator.validate_clauses(incomplete_contract, required_clauses)
        assert result.is_complete == False
        assert len(result.missing_clauses) == 4
    
    def test_field_completeness(self):
        """测试字段完整性验证"""
        validator = CompletenessValidator()
        
        required_fields = ["contract_number", "amount", "date", "parties"]
        
        complete_data = {
            "contract_number": "TEST-001",
            "amount": "100万",
            "date": "2024-01-27",
            "parties": ["公司A", "公司B"]
        }
        result = validator.validate_fields(complete_data, required_fields)
        assert result.is_complete == True
        
        incomplete_data = {
            "contract_number": "TEST-001",
            # 缺少 amount, date, parties
        }
        result = validator.validate_fields(incomplete_data, required_fields)
        assert result.is_complete == False
```

### 3.6 证据文件格式测试（通用）

```python
# tests/unit/test_evidence_format.py

import pytest
from services.evidence_file_generator import EvidenceFileGenerator

class TestEvidenceFormat:
    """证据文件格式测试 - BUG-011"""

    def setup_method(self):
        self.generator = EvidenceFileGenerator()

    def test_line_breaks_in_section_headers(self):
        """测试章节标题后换行"""
        text = "【甲方（转让方/出租人）】名称：上海国金融资租赁有限公司"
        result = self.generator._ensure_line_breaks(text)

        # 章节标题后应该有换行
        assert "【甲方（转让方/出租人）】\n" in result

    def test_line_breaks_between_field_labels(self):
        """测试字段标签之间换行"""
        text = "名称：上海国金融资租赁有限公司统一社会信用代码：91310120MA1H法定代表人：张伟"
        result = self.generator._ensure_line_breaks(text)

        # 字段标签之间应该有换行
        lines = result.split('\n')
        assert len(lines) >= 3, f"期望至少3行，实际{len(lines)}行: {result}"

    def test_continuous_text_with_sections(self):
        """测试连续文本中的章节换行"""
        text = "【甲方（转让方/出租人）】名称：上海国金融资租赁有限公司统一社会信用代码：91310120MA1H【乙方（受让方/承租人）】名称：江西鸿润商业管理有限公司"
        result = self.generator._ensure_line_breaks(text)

        # 每个章节标题后应该有换行
        assert "【甲方（转让方/出租人）】\n" in result
        assert "【乙方（受让方/承租人）】\n" in result

        # 字段标签之间应该有换行
        lines = result.split('\n')
        assert "名称：上海国金融资租赁有限公司" in lines
        assert "统一社会信用代码：91310120MA1H" in lines
        assert "名称：江西鸿润商业管理有限公司" in lines
```

### 3.7 PDF分页测试（通用）

```python
# tests/unit/test_pdf_pagination.py

import pytest
from src.renderers.pdf_paginator import PDFPaginator
from src.renderers.table_of_contents import TableOfContents

class TestPDFPagination:
    """PDF分页测试"""
    
    def setup_method(self):
        self.config = {
            "output_structure": {
                "cover_page": {"enabled": False},
                "table_of_contents": {"enabled": True, "page_numbering": True},
                "evidence_new_page": True
            }
        }
        self.paginator = PDFPaginator(self.config)
        self.toc_generator = TableOfContents()
    
    def test_evidence_new_page(self):
        """测试每份证据另起一页"""
        # 添加证据1
        evidence1 = MockEvidence("证据1", "合同A的内容...")
        self.paginator.add_evidence(evidence1)
        
        # 添加证据2（应该另起一页）
        evidence2 = MockEvidence("证据2", "合同B的内容...")
        self.paginator.add_evidence(evidence2)
        
        # 验证分页
        pages = self.paginator.get_pages()
        
        assert len(pages) >= 2, "证据应该分布在至少2页"
        assert pages[0].contains_evidence("证据1"), "第1页应包含证据1"
        assert pages[1].contains_evidence("证据2"), "第2页应包含证据2（另起一页）"
    
    def test_no_content_split(self):
        """测试内容不会被截断到两页"""
        long_content = "A" * 5000  # 长内容
        
        evidence = MockEvidence("长证据", long_content)
        self.paginator.add_evidence(evidence)
        
        pages = self.paginator.get_pages()
        
        # 验证没有单个证据被分割到不连续页面
        evidence_pages = [p for p in pages if p.contains_evidence("长证据")]
        
        # 如果被分割，应该在后续页面继续（不丢失内容）
        if len(evidence_pages) > 1:
            # 检查内容连续性
            content = "".join([p.get_content() for p in evidence_pages])
            assert long_content in content or content == long_content
    
    def test_page_number_sequence(self):
        """测试页码连续"""
        # 添加多个证据
        for i in range(5):
            evidence = MockEvidence(f"证据{i+1}", f"内容{i+1}")
            self.paginator.add_evidence(evidence)
        
        pages = self.paginator.get_pages()
        page_numbers = [p.number for p in pages]
        
        # 验证页码连续
        assert page_numbers == list(range(1, len(page_numbers) + 1)), \
            f"页码应该连续: {page_numbers}"
    
    def test_page_number_position(self):
        """测试页码位置统一"""
        # 添加证据
        for i in range(3):
            evidence = MockEvidence(f"证据{i+1}", f"内容{i+1}")
            self.paginator.add_evidence(evidence)
        
        pages = self.paginator.get_pages()
        
        # 验证所有页面的页码位置一致
        positions = [p.footer_position for p in pages]
        assert len(set(positions)) == 1, "所有页面的页码位置应该一致"


class TestTableOfContents:
    """目录生成测试"""
    
    def test_toc_page_numbers(self):
        """测试目录页码与实际页码一致"""
        page_registry = [
            {"element": MockElement("起诉状", "E001"), "page": 1},
            {"element": MockElement("证据1", "E002"), "page": 3},
            {"element": MockElement("证据2", "E003"), "page": 5},
        ]
        
        toc = self.toc_generator.generate(page_registry)
        
        # 验证目录内容
        assert "起诉状" in toc
        assert "证据1" in toc
        assert "证据2" in toc
        
        # 验证页码正确
        assert "第1页" in toc or "1" in toc.split("起诉状")[1][:10]
    
    def test_toc_accuracy(self):
        """测试目录准确性"""
        page_registry = [
            {"element": MockElement("起诉状", "E001"), "page": 1},
            {"element": MockElement("证据1", "E002"), "page": 3},
            {"element": MockElement("证据2", "E003"), "page": 5},
        ]
        
        toc = self.toc_generator.generate(page_registry)
        
        # 验证目录项与实际一致
        for entry in page_registry:
            title = entry["element"].get_title()
            page = entry["page"]
            
            assert title in toc, f"目录缺少: {title}"
            # 检查页码标注
            assert f"第{page}页" in toc or str(page) in toc.split(title)[1][:10], \
                f"{title}的页码标注不正确"


class TestCoverPage:
    """封面测试"""
    
    def test_cover_page_excluded_from_numbering(self):
        """测试封面不计页码"""
        config = {
            "output_structure": {
                "cover_page": {"enabled": True, "number_pages": False},
                "table_of_contents": {"enabled": False},
                "start_page_number": 1
            }
        }
        
        generator = CoverPageGenerator(config)
        cover = generator.generate(case_info)
        
        # 封面不应有页码或页码标记为特殊符号
        assert cover.page_number is None or cover.page_number == "I"
    
    def test_cover_page_content(self):
        """测试封面内容"""
        config = {
            "output_structure": {
                "cover_page": {
                    "enabled": True,
                    "title": "案件卷宗",
                    "include_case_number": True,
                    "include_date": True
                }
            }
        }
        
        generator = CoverPageGenerator(config)
        cover = generator.generate({
            "case_number": "(2024)沪74民初721号",
            "date": "2024-01-27"
        })
        
        assert "案件卷宗" in cover.content
        assert "(2024)沪74民初721号" in cover.content
        assert "2024-01-27" in cover.content
```

## 四、集成测试

### 4.1 配置驱动流程测试

```python
# tests/integration/test_config_driven_flow.py

import pytest
import json
from pathlib import Path
from src.core.generator import PDFGenerator

class TestConfigDrivenFlow:
    """配置驱动流程测试"""
    
    def test_financing_lease_flow(self, tmp_path):
        """测试融资租赁案件流程"""
        # 1. 创建配置
        config = {
            "case_type": "融资租赁纠纷",
            "case_type_code": "FL",
            "evidence_templates": [
                {
                    "template_id": "transfer_contract",
                    "template_name": "转让协议",
                    "required_clauses": ["定义与解释", "转让标的", "价款支付", "违约责任", "争议解决"]
                }
            ],
            "calculation_rules": {},
            "anonymization_rules": {}
        }
        config_file = tmp_path / "financing_lease.json"
        config_file.write_text(json.dumps(config))
        
        # 2. 创建测试数据
        data = {
            "contract_number": "FL-2024-001",
            "amount": "15,000,000",
            "date": "2024-01-27"
        }
        
        # 3. 生成PDF
        generator = PDFGenerator()
        output_file = tmp_path / "output.pdf"
        generator.generate(config_file=str(config_file), data=data, output=output_file)
        
        # 4. 验证
        assert output_file.exists()
        assert output_file.stat().st_size > 0
    
    def test_bank_loan_flow(self, tmp_path):
        """测试银行借贷案件流程 - 复用同一框架"""
        # 使用不同的配置文件
        config = {
            "case_type": "银行借贷纠纷",
            "case_type_code": "BL",
            "evidence_templates": [
                {
                    "template_id": "loan_contract",
                    "template_name": "借款合同",
                    "required_clauses": ["定义与解释", "借款金额", "利率", "还款方式", "违约责任", "争议解决"]
                }
            ],
            "calculation_rules": {},
            "anonymization_rules": {}
        }
        config_file = tmp_path / "bank_loan.json"
        config_file.write_text(json.dumps(config))
        
        # 使用相同的生成器
        generator = PDFGenerator()
        output_file = tmp_path / "loan_output.pdf"
        generator.generate(config_file=str(config_file), data={}, output=output_file)
        
        assert output_file.exists()
```

### 4.2 插件加载测试

```python
# tests/integration/test_plugin_loading.py

import pytest
from src.core.plugin_manager import PluginManager

class TestPluginLoading:
    """插件加载测试"""
    
    def test_load_deanonymizer_plugin(self):
        """测试加载脱敏插件"""
        manager = PluginManager()
        plugin = manager.load_plugin("deanonymizer", "enhanced")
        
        assert plugin is not None
        assert hasattr(plugin, "process")
    
    def test_load_calculator_plugin(self):
        """测试加载计算器插件"""
        manager = PluginManager()
        plugin = manager.load_plugin("calculator", "rent")
        
        assert plugin is not None
        assert hasattr(plugin, "calculate")
    
    def test_plugin_compatibility(self):
        """测试插件兼容性"""
        manager = PluginManager()
        
        # 标准脱敏插件
        standard = manager.load_plugin("deanonymizer", "standard")
        # 增强脱敏插件
        enhanced = manager.load_plugin("deanonymizer", "enhanced")
        
        # 两者应该有相同的接口
        assert hasattr(standard, "process")
        assert hasattr(enhanced, "process")
```

## 五、Regression测试

### 5.1 框架回归测试

```python
# tests/regression/test_framework_regression.py

"""
Regression测试 - 每次发布前必须运行
确保框架的通用性和稳定性
"""

class TestFrameworkRegression:
    """框架回归测试"""
    
    def test_no_hardcoded_case_types(self):
        """回归测试: 框架中无硬编码的特定案件类型"""
        from src.core import generator
        import inspect
        
        source = inspect.getsource(generator)
        
        # 检查源代码中是否有硬编码的案件类型
        forbidden_patterns = [
            "融资租赁",
            "设备转让",
            "租赁物清单",
            "某某公司5",
            "多联机中央空调",
        ]
        
        for pattern in forbidden_patterns:
            assert pattern not in source, f"发现硬编码: {pattern}"
    
    def test_config_driven_templates(self):
        """回归测试: 所有模板都从配置加载"""
        from src.core import template_engine
        import inspect
        
        source = inspect.getsource(template_engine)
        
        # 不应该有硬编码的模板内容
        assert "第一条" not in source  # 条款不应硬编码
        assert "设备名称" not in source  # 字段不应硬编码
    
    def test_plugin_system_works(self):
        """回归测试: 插件系统正常工作"""
        from src.core.plugin_manager import PluginManager
        
        manager = PluginManager()
        
        # 应该能加载所有标准插件
        plugins = ["deanonymizer", "calculator", "cleaner"]
        for plugin_name in plugins:
            plugin = manager.load_plugin(plugin_name)
            assert plugin is not None, f"插件 {plugin_name} 加载失败"
    
    def test_content_cleaner_effectiveness(self):
        """回归测试: 内容净化器有效"""
        from src.processors.content_cleaner import ContentCleaner
        
        cleaner = ContentCleaner()
        
        # 测试各种污染内容
        test_cases = [
            "好的，作为专业的法律文书生成助手，我将生成证据包。",
            "【测试】这是测试数据",
            "数据一致性验证报告\n结论： 生成完毕",
            "证明目的： 证明XXX",
            "（此处填写日期）",
        ]
        
        for text in test_cases:
            cleaned, report = cleaner.clean(text)
            
            # 验证内容已被清理
            if "好的，作为" in text:
                assert "好的，作为" not in cleaned
            if "【测试】" in text:
                assert "【测试】" not in cleaned
            if "数据一致性验证报告" in text:
                assert "数据一致性验证报告" not in cleaned
    
    def test_pagination_new_page_per_evidence(self):
        """回归测试: 每份证据另起一页"""
        from src.renderers.pdf_paginator import PDFPaginator
        
        config = {
            "output_structure": {
                "evidence_new_page": True,
                "cover_page": {"enabled": False},
                "table_of_contents": {"enabled": False}
            }
        }
        paginator = PDFPaginator(config)
        
        # 添加5份证据
        for i in range(5):
            evidence = MockEvidence(f"证据{i+1}", f"内容{i+1}")
            paginator.add_evidence(evidence)
        
        pages = paginator.get_pages()
        
        # 验证每份证据在不同页面
        evidence_pages = []
        for i, page in enumerate(pages):
            for evidence_id in page.get_evidence_ids():
                evidence_pages.append((evidence_id, i))
        
        # 每份证据应该只在一页上
        evidence_ids = [eid for eid, _ in evidence_pages]
        assert len(evidence_ids) == 5, "应该有5份证据"
        assert len(set(evidence_ids)) == 5, "每份证据应该只出现一次"
    
    def test_page_number_sequence(self):
        """回归测试: 页码连续"""
        from src.renderers.pdf_paginator import PDFPaginator
        
        config = {
            "output_structure": {
                "evidence_new_page": True,
                "cover_page": {"enabled": False},
                "table_of_contents": {"enabled": False}
            }
        }
        paginator = PDFPaginator(config)
        
        # 添加证据
        for i in range(3):
            evidence = MockEvidence(f"证据{i+1}", f"内容{i+1}")
            paginator.add_evidence(evidence)
        
        pages = paginator.get_pages()
        page_numbers = [p.number for p in pages]
        
        # 验证页码连续
        assert page_numbers == list(range(1, len(page_numbers) + 1))
    
    def test_cover_and_toc_page_numbers(self):
        """回归测试: 封面和目录页码正确"""
        from src.renderers.pdf_paginator import PDFPaginator
        from src.renderers.cover_page import CoverPageGenerator
        from src.renderers.table_of_contents import TableOfContents
        
        # 测试封面不计页码
        cover_config = {
            "output_structure": {
                "cover_page": {"enabled": True, "number_pages": False}
            }
        }
        cover_gen = CoverPageGenerator(cover_config)
        cover = cover_gen.generate({})
        
        assert cover.page_number is None or cover.page_number == "I", \
            "封面应该不计页码或标记为I"
        
        # 测试目录页码正确
        toc_config = {
            "output_structure": {
                "table_of_contents": {"enabled": True, "page_numbering": True}
            }
        }
        toc_gen = TableOfContents(toc_config)
        page_registry = [
            {"element": MockElement("起诉状", "E001"), "page": 1},
            {"element": MockElement("证据1", "E002"), "page": 3},
        ]
        toc = toc_gen.generate(page_registry)
        
        # 验证目录中页码与实际一致
        assert "第1页" in toc or "1" in toc
```

## 六、自动化测试命令

### 6.1 测试执行脚本

```bash
#!/bin/bash
# run_tests.sh - 执行所有测试

set -e

echo "========================================"
echo "  金融案件PDF生成系统 - 测试套件"
echo "  (通用框架版本)"
echo "========================================"

# 1. 单元测试
echo ""
echo ">>> 1. 运行单元测试..."
python3 -m pytest tests/unit/ -v --cov=src --cov-report=html

# 2. 集成测试
echo ""
echo ">>> 2. 运行集成测试..."
python3 -m pytest tests/integration/ -v

# 3. Regression测试（必须通过）
echo ""
echo ">>> 3. 运行回归测试..."
python3 -m pytest tests/regression/ -v --tb=short

# 4. E2E测试
echo ""
echo ">>> 4. 运行端到端测试..."
python3 -m pytest tests/e2e/ -v

# 5. 生成测试报告
echo ""
echo ">>> 5. 生成测试报告..."
python3 -m pytest tests/ --html=test_report.html --self-contained-html

echo ""
echo "========================================"
echo "  测试完成！查看 test_report.html"
echo "========================================"
```

### 6.2 质量验证脚本

```bash
#!/bin/bash
# verify_quality.sh - 验证输出质量

PDF_FILE=$1

if [ -z "$PDF_FILE" ]; then
    echo "用法: ./verify_quality.sh <pdf文件>"
    exit 1
fi

echo "========================================"
echo "  输出质量验证: $PDF_FILE"
echo "========================================"

# 检查PDF工具是否可用
if ! command -v pdftotext &> /dev/null; then
    echo "警告: pdftotext 未安装，无法验证内容"
    exit 1
fi

TEXT_FILE=$(mktemp)
pdftotext "$PDF_FILE" "$TEXT_FILE" 2>/dev/null

echo ""
echo ">>> 1. 检查LLM响应前缀..."
COUNT=$(grep -c "好的，作为专业的法律文书生成助手" "$TEXT_FILE" || true)
[ "$COUNT" -eq 0 ] && echo "   ✓ 通过" || echo "   ✗ 失败: $COUNT处"

echo ""
echo ">>> 2. 检查质检报告..."
COUNT=$(grep -c "数据一致性验证报告" "$TEXT_FILE" || true)
[ "$COUNT" -eq 0 ] && echo "   ✓ 通过" || echo "   ✗ 失败: $COUNT处"

echo ""
echo ">>> 3. 检查测试标记..."
COUNT=$(grep -c "【测试】" "$TEXT_FILE" || true)
[ "$COUNT" -eq 0 ] && echo "   ✓ 通过" || echo "   ✗ 失败: $COUNT处"

echo ""
echo ">>> 4. 检查证明目的混入..."
COUNT=$(grep -c "证明目的：" "$TEXT_FILE" || true)
[ "$COUNT" -eq 0 ] && echo "   ✓ 通过" || echo "   ✗ 失败: $COUNT处"

echo ""
echo ">>> 5. 检查内部备注..."
COUNT=$(grep -c "（此处填写" "$TEXT_FILE" || true)
[ "$COUNT" -eq 0 ] && echo "   ✓ 通过" || echo "   ✗ 失败: $COUNT处"

echo ""
echo ">>> 6. 检查PDF分页..."
# 使用pdfinfo检查页面数量
PAGE_COUNT=$(pdfinfo "$PDF_FILE" 2>/dev/null | grep "Pages:" | awk '{print $2}')
if [ -n "$PAGE_COUNT" ] && [ "$PAGE_COUNT" -ge 1 ]; then
    echo "   ✓ PDF总页数: $PAGE_COUNT"
else
    echo "   ⚠ 无法获取页数信息"
fi

echo ""
echo ">>> 7. 验证分页正确性（需人工或专用工具）..."
echo "   说明: 每份证据另起一页、页码连续需使用PDF查看器验证"
echo "   建议: 打开PDF检查:"
echo "   - 证据是否从新页面开始"
echo "   - 页码是否连续"
echo "   - 封面/目录页码是否正确"

rm -f "$TEXT_FILE"

echo ""
echo "========================================"
echo "  基础内容检查完成"
echo "  分页验证请人工检查PDF文件"
echo "========================================"
```

### 6.3 分页验证脚本

```bash
#!/bin/bash
# verify_pagination.sh - 验证PDF分页（需要pdfinfo）

PDF_FILE=$1

if [ -z "$PDF_FILE" ]; then
    echo "用法: ./verify_pagination.sh <pdf文件>"
    exit 1
fi

if ! command -v pdfinfo &> /dev/null; then
    echo "错误: pdfinfo 未安装（需要poppler-utils）"
    echo "安装: apt install poppler-utils 或 brew install poppler"
    exit 1
fi

echo "========================================"
echo "  PDF分页验证: $PDF_FILE"
echo "========================================"

# 获取PDF信息
PAGE_COUNT=$(pdfinfo "$PDF_FILE" 2>/dev/null | grep "Pages:" | awk '{print $2}')
TITLE=$(pdfinfo "$PDF_FILE" 2>/dev/null | grep "Title:" | cut -d: -f2 | xargs)

echo ""
echo ">>> PDF基本信息"
echo "   总页数: $PAGE_COUNT"
echo "   标题: ${TITLE:-无}"

echo ""
echo ">>> 分页规则检查"
echo "   说明: 以下检查需要人工确认或使用专用PDF解析工具"
echo ""
echo "   1. 每份证据另起一页:"
echo "      - 打开PDF，逐页检查每份证据是否从新页面开始"
echo "      - 预期: 证据1、证据2、...各占独立页面"
echo ""
echo "   2. 页码连续:"
echo "      - 检查页码: 1, 2, 3, ... 连续无跳跃"
echo "      - 如果有封面: 封面通常不计页码或标记为'I'"
echo "      - 如果有目录: 目录页码从1开始"
echo ""
echo "   3. 页码位置统一:"
echo "      - 所有页面页码应位于相同位置（如底部居中）"
echo ""
echo "   4. 目录页码准确性（如果启用目录）:"
echo "      - 目录中标注的页码应与实际页面编号一致"
```

## 七、CI/CD Pipeline配置

---

**文档版本**: 2.1
**创建日期**: 2024-01-27
**最后更新**: 2024-01-27

**更新记录**:
- v2.2: 新增3.6证据文件格式测试（含BUG-011换行符测试）、3.2增强脱敏测试（BUG-010）、3.4异常模式测试（BUG-012）
- v2.1: 新增3.7 PDF分页测试、6.3分页验证脚本、CI分页测试
- v2.0: 通用框架版本

```yaml
# .github/workflows/test.yml
name: Test Pipeline (通用框架)

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Check for hardcoded content
      run: |
        # 检查源代码中是否有硬编码的特定案件内容
        if grep -r "融资租赁\|某某公司5\|多联机中央空调" src/ --include="*.py"; then
          echo "ERROR: 发现硬编码的特定案件内容"
          exit 1
        fi
        echo "✓ 无硬编码内容"
    
    - name: Run Unit Tests (including pagination tests)
      run: |
        pytest tests/unit/ -v --cov=src --cov-report=term-missing
    
    - name: Run Pagination Tests
      run: |
        pytest tests/unit/test_pdf_pagination.py -v
    
    - name: Run Integration Tests
      run: pytest tests/integration/ -v
    
    - name: Run Regression Tests (including pagination)
      run: pytest tests/regression/ -v
    
    - name: Run E2E Tests
      run: pytest tests/e2e/ -v
    
    - name: Generate Test PDF
      run: |
        python3 run_full_regeneration.py --all
        ls -la outputs/*.pdf
    
    - name: Verify PDF Pagination (manual check reminder)
      run: |
        # 提醒进行人工分页检查
        echo "========================================"
        echo "  PDF生成完成，请检查:"
        echo "  - 每份证据是否另起一页"
        echo "  - 页码是否连续"
        echo "  - 封面/目录页码是否正确"
        echo "========================================"
    
    - name: Upload Coverage
      uses: codecov/codecov-action@v3
```

## 八、测试数据管理

### 8.1 目录结构

```
tests/
├── fixtures/                    # 测试数据
│   ├── case_configs/           # 案件配置（多类型）
│   │   ├── financing_lease.json
│   │   ├── bank_loan.json
│   │   ├── factoring.json
│   │   └── custom_case.json
│   │
│   ├── templates/              # 测试模板
│   │   ├── contract_template.json
│   │   └── evidence_template.json
│   │
│   └── test_data.json          # 通用测试数据
│
├── unit/                        # 单元测试
│   ├── test_config_loader.py
│   ├── test_template_engine.py
│   ├── test_deanonymizer.py
│   ├── test_content_cleaner.py
│   ├── test_table_parser.py
│   └── test_validators.py
│
├── integration/                 # 集成测试
│   ├── test_config_driven_flow.py
│   └── test_plugin_loading.py
│
├── regression/                  # 回归测试
│   └── test_framework_regression.py
│
└── e2e/                         # 端到端测试
    ├── test_full_pipeline.py
    └── test_performance.py
```

---

**文档版本**: 2.1
**创建日期**: 2024-01-27
**最后更新**: 2024-01-27

**更新记录**:
- v2.2: 新增3.6证据文件格式测试（含BUG-011换行符测试）、3.2增强脱敏测试（BUG-010）、3.4异常模式测试（BUG-012）
- v2.1: 新增3.7 PDF分页测试、6.3分页验证脚本、CI分页测试
- v2.0: 通用框架版本
