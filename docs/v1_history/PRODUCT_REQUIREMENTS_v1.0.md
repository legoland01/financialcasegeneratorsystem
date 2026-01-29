# 金融案件PDF生成系统 - 产品要求文档

## 一、概述

本文档描述**通用金融案件PDF生成系统**的产品要求。

**设计原则**:
- 框架通用化：支持各类金融案件（融资租赁、借贷、担保、保理等）
- 配置驱动：通过配置文件定义案件类型、证据模板、字段映射
- 可扩展性：新案件类型只需添加配置，无需修改核心代码
- 插件化：表格渲染、脱敏处理、内容净化等作为可插拔模块

## 二、系统目标

自动生成符合中国法院要求的**通用金融案件**卷宗PDF文档，包括：
- 民事起诉状
- 证据材料（各类合同、协议、清单、凭证等）
- 程序性文件
- 被告答辩材料
- 法院审理材料

**支持的案件类型（示例）**:
```
├── 融资租赁纠纷
├── 金融借款合同纠纷
├── 民间借贷纠纷
├── 保理合同纠纷
├── 担保合同纠纷
├── 票据纠纷
└── 其他金融纠纷（可配置）
```

## 三、问题追踪清单

### 3.1 问题分类（通用框架问题）

| ID | 问题 | 严重性 | 状态 | 根本原因 | 修复方案 |
|---|------|--------|------|---------|---------|
| BUG-001 | 脱敏替换不完整 | 🔴 高 | 待修复 | 反脱敏逻辑不通用 | 增强_deanonymize方法 |
| BUG-002 | 特定字段未使用 | 🔴 高 | 待修复 | 字段映射不灵活 | 配置驱动的字段引用 |
| BUG-003 | Markdown表格残留 | 🔴 高 | 待修复 | 表格解析器不完整 | 重写MarkdownTableParser |
| BUG-004 | 数据计算错误 | 🔴 高 | 待修复 | 计算逻辑硬编码 | 插件化的计算器 |
| BUG-005 | 合同模板不完整 | 🔴 高 | 待修复 | 模板缺少必备条款 | 模板库+条款库 |
| BUG-006 | 内容污染残留 | 🔴 高 | 待修复 | 后处理未清理 | 添加_content_cleaner |

### 3.2 统计

- 总计: 6个通用Bug
- 已修复: 0个
- 待修复: 6个
- P0阻塞: 6个

## 四、对开发团队的要求

### 4.1 通用性设计要求

```
================================================================================
                          通用性设计要求
================================================================================

【P0 - 框架必须通用】
1. 不能硬编码任何特定案件类型
   ❌ "融资租赁合同"  →  ✓ 案件类型从配置文件读取
   ❌ "设备转让协议"  →  ✓ 协议类型从配置文件读取
   ❌ "租赁物清单"    →  ✓ 清单名称从配置文件读取

2. 不能硬编码任何特定字段
   ❌ "某某公司"      →  ✓ 公司名从脱敏映射读取
   ❌ "多联机中央空调" →  ✓ 设备名从key_numbers读取
   ❌ "150,000,000"   →  ✓ 金额从数据源读取

3. 不能硬编码任何特定条款
   ❌ "第一条 转让标的" →  ✓ 条款从模板库读取
   ❌ "租金支付计划"    →  ✓ 计划表从数据生成

【P1 - 框架必须可配置】
4. 案件类型必须可配置
   - 通过 JSON/YAML 配置文件定义案件类型
   - 新增案件类型只需添加配置，无需修改代码
   
5. 证据模板必须可配置
   - 通过模板文件定义证据格式
   - 模板支持变量替换、条件渲染
   
6. 字段映射必须可配置
   - 通过映射表定义字段对应关系
   - 支持自定义字段验证规则

【P2 - 框架必须可扩展】
7. 支持插件化扩展
   - 表格渲染器可替换
   - 脱敏处理器可扩展
   - 内容净化器可定制
   
8. 支持自定义计算器
   - 租金计算器可配置
   - 利息计算器可配置
   - 违约金计算器可配置

================================================================================
                          代码设计红线
================================================================================

【P0 - 阻塞问题】
1. 任何硬编码特定案件内容 → 拒绝合并
2. 任何硬编码特定字段值   → 拒绝合并
3. 任何硬编码特定合同条款 → 拒绝合并

【P1 - 严重问题】
4. 未使用配置驱动的功能   → 必须重构
5. 未预留扩展点的设计     → 必须重构
6. 未考虑多案件类型的场景 → 必须重构

================================================================================
```

### 4.2 配置设计要求

```json
// 配置文件示例: config/case_types/financing_lease.json
{
  "case_type": "融资租赁纠纷",
  "case_type_code": "FL",
  "description": "融资租赁合同纠纷案件配置",
  
  "evidence_templates": [
    {
      "template_id": "transfer_contract",
      "template_name": "设备转让协议",
      "required_clauses": [
        "定义与解释",
        "转让标的", 
        "价款支付",
        "所有权转移",
        "违约责任",
        "争议解决"
      ],
      "field_mappings": {
        "transfer_price": "key_numbers.transfer_price",
        "rental_list": "key_numbers.rental_equipment",
        "collateral_list": "key_numbers.collateral_list"
      }
    },
    {
      "template_id": "lease_contract",
      "template_name": "融资租赁合同",
      "required_clauses": [
        "定义与解释",
        "租赁物",
        "租赁期限",
        "租金及支付",
        "保证金",
        "交付与验收",
        "保险",
        "维修保养",
        "违约责任",
        "争议解决"
      ],
      "field_mappings": {
        "rent_total": "key_numbers.rent_total",
        "rent_schedule": "key_numbers.rent_schedule",
        "interest_rate": "key_numbers.interest_rate"
      }
    }
  ],
  
  "calculation_rules": {
    "rent_calculation": {
      "method": "equal_installment",
      "frequency": "monthly",
      "default_periods": 12
    },
    "interest_calculation": {
      "method": "daily_rate",
      "default_rate_type": "annual"
    }
  },
  
  "anonymization_rules": {
    "company_patterns": ["某某公司\\d*", "长江某.*", "华鑫某.*"],
    "person_patterns": ["张某\\d*", "李某某"],
    "address_patterns": ["某某省.*市.*区.*路.*号"]
  }
}
```

### 4.3 代码组织要求

```
src/
├── core/                          # 核心框架（通用）
│   ├── base_generator.py          # 生成器基类
│   ├── config_loader.py           # 配置加载器
│   ├── template_engine.py         # 模板引擎
│   └── plugin_manager.py          # 插件管理器
│
├── processors/                    # 处理器（插件化）
│   ├── deanonymizer/              # 脱敏处理器
│   │   ├── base.py
│   │   ├── standard_processor.py  # 标准脱敏
│   │   └── enhanced_processor.py  # 增强脱敏（处理LLM创造的新模式）
│   │
│   ├── table_parser/              # 表格解析器
│   │   ├── base.py
│   │   ├── markdown_parser.py     # Markdown表格解析
│   │   └── html_parser.py         # HTML表格解析
│   │
│   ├── content_cleaner/           # 内容净化器
│   │   ├── base.py
│   │   ├── llm_prefix_cleaner.py  # 清理LLM响应前缀
│   │   ├── qc_report_cleaner.py   # 清理质检报告
│   │   └── test_marker_cleaner.py # 清理测试标记
│   │
│   └── calculator/                # 计算器（可配置）
│       ├── base.py
│       ├── rent_calculator.py     # 租金计算器
│       ├── interest_calculator.py # 利息计算器
│       └── penalty_calculator.py  # 违约金计算器
│
├── renderers/                     # 渲染器
│   ├── pdf_renderer.py            # PDF渲染
│   └── html_renderer.py           # HTML渲染
│
├── templates/                     # 模板库
│   ├── contracts/                 # 合同模板
│   │   ├── base_contract.md       # 合同基础模板
│   │   ├── transfer_agreement.md  # 转让协议模板
│   │   └── lease_contract.md      # 租赁合同模板
│   │
│   ├── pleadings/                 # 文书模板
│   │   ├── complaint.md           # 起诉状模板
│   │   ├── answer.md              # 答辩状模板
│   │   └── judgment.md            # 判决书模板
│   │
│   └── evidence/                  # 证据模板
│       ├── contract_evidence.md   # 合同类证据模板
│       ├── voucher_evidence.md    # 凭证类证据模板
│       └── certificate_evidence.md # 证书类证据模板
│
├── validators/                    # 验证器
│   ├── completeness_validator.py  # 完整性验证
│   ├── consistency_validator.py   # 一致性验证
│   └── format_validator.py        # 格式验证
│
└── utils/                         # 工具类
    ├── json_utils.py
    ├── date_utils.py
    └── money_utils.py
```

### 4.4 命名规范

- 函数名：snake_case (如: generate_evidence_file)
- 类名：PascalCase (如: EvidenceFileGenerator)
- 常量：UPPER_SNAKE_CASE (如: MAX_RETRY_COUNT)
- 变量：snake_case (如: evidence_list)
- 配置文件：snake_case.json (如: financing_lease.json)

### 4.5 函数要求

- 每个函数必须有类型注解 (Type Hints)
- 必须有返回值说明
- 函数长度不超过50行（除模板函数外）

## 五、功能要求

### 5.1 合同生成要求（通用）

1. **合同条款数 >= 必需要求**（根据案件类型配置）
2. **所有占位符替换完成**（某某->真实值）
3. **动态字段填充**（从配置文件读取的数据源）
4. **数据一致性**（金额、日期根据计算规则自动验证）

### 5.2 PDF生成要求（通用）

1. 无Markdown表格残留（|符号出现次数=0）
2. 所有表格正确渲染（表头有灰底、有边框）
3. 中文字体正常显示
4. 分页正确（无内容截断）
5. 文件大小合理（<10MB）

### 5.3 PDF排版要求（通用）

#### 5.3.1 分页规则

| 元素 | 分页要求 | 优先级 |
|------|---------|--------|
| **每份证据另起一页** | 每份证据必须从新页面开始，确保文档清晰、易于翻阅和归档 | 🔴 P0 |
| **封面** | 如果启用封面，从第1页开始 | 🔵 可配置 |
| **目录** | 如果启用目录，紧跟在封面后，页码从实际页码开始计算 | 🔴 P0 |
| **起诉状** | 从新页面开始（一般在封面/目录之后） | 🔴 P0 |
| **每份证据** | 每份证据必须另起一页 | 🔴 P0 |
| **证据组** | 每个证据组可以从新页面开始（可配置） | 🟢 可配置 |
| **程序性文件** | 从新页面开始 | 🔴 P0 |
| **被告答辩材料** | 从新页面开始 | 🔴 P0 |
| **法院审理材料** | 从新页面开始 | 🔴 P0 |

#### 5.3.2 页码规则

| 区域 | 页码要求 | 示例 |
|------|---------|------|
| **封面** | 有封面时，封面不计页码或单独标记 | 第Ⅰ页 |
| **目录** | 有目录时，目录页码从1开始 | 第1页 |
| **正文页码** | 从第1页开始连续编号 | 第1页、第2页... |
| **页码位置** | 统一位置（底部居中或右下角） | - |
| **页码格式** | 纯数字或"第X页"格式 | 第1页 |

#### 5.3.3 封面和目录（可选配置）

```
【配置选项】

"output_structure": {
  "cover_page": {
    "enabled": true,          // 是否启用封面
    "style": "formal",        // 封面样式：formal/simple
    "title": "案件卷宗",      // 标题
    "include_case_number": true,  // 是否包含案号
    "include_date": true      // 是否包含日期
  },
  "table_of_contents": {
    "enabled": true,          // 是否启用目录
    "page_numbering": true,   // 目录页是否计页码
    "show_page_number": true  // 是否在目录中显示页码
  }
}
```

#### 5.3.4 分页实现要求

```python
# 分页逻辑示例
class PDFPaginator:
    """PDF分页控制器"""
    
    def __init__(self, config):
        self.config = config
        self.current_page = 0
        self.elements = []
    
    def add_page_break(self):
        """添加分页符 - 每份证据必须调用此方法"""
        if self.elements:  # 如果当前页面有内容，添加分页
            self._finish_current_page()
    
    def add_evidence(self, evidence: Evidence):
        """添加证据 - 自动分页"""
        self.add_page_break()  # 确保另起一页
        self.elements.append(evidence)
    
    def _finish_current_page(self):
        """完成当前页面，准备下一页"""
        self.current_page += 1
        # 记录当前页码，供目录使用
        self.page_registry.append({
            "element": self.elements[-1],
            "page": self.current_page
        })
```

#### 5.3.5 目录生成要求

```python
class TableOfContents:
    """目录生成器"""
    
    def generate(self, page_registry: List[Dict]) -> str:
        """根据页面注册信息生成目录"""
        toc = "目  录\n" + "=" * 40 + "\n"
        
        for entry in page_registry:
            title = entry["element"].get_title()
            page_num = entry["page"]
            toc += f"{title:<30} 第{page_num}页\n"
        
        return toc
    
    def get_page_number(self, element_id: str) -> int:
        """获取指定元素的页码"""
        for entry in page_registry:
            if entry["element"].id == element_id:
                return entry["page"]
        return -1  # 未找到
```

#### 5.3.6 验收检查清单

```
【分页验收】
□ 每份证据是否另起一页
  验证方法: 人工检查或自动化脚本检测
  预期: 每份证据从新页面开始

□ 分页符是否正确插入
  验证方法: 检查PDF页面边界
  预期: 无内容被截断到两页

【页码验收】
□ 封面页码是否正确（如果启用）
  验证: 封面不计页码或显示为"第Ⅰ页"

□ 目录页码是否正确（如果启用）
  验证: 目录从第1页开始

□ 正文页码是否连续
  验证: 页码1,2,3,...无跳跃

□ 页码位置是否统一
  验证: 所有页面页码位置一致

【封面/目录验收】
□ 封面信息完整（如果启用）
  验证: 包含案号、日期等必要信息

□ 目录内容准确（如果启用）
  验证: 目录项与实际内容一致

□ 目录页码与实际页码一致
  验证: 目录中标注的页码与实际页面编号一致
```

### 5.3 数据处理要求（通用）

1. 脱敏映射100%正确（支持自定义映射规则）
2. 无数据丢失
3. JSON格式正确
4. 编码统一为UTF-8

## 六、输出内容净化要求

### 6.1 P0 - 必须净化

1. **所有LLM响应前缀必须删除**
   ```
   ❌ "好的，作为专业的法律文书生成助手，我将..."
   ❌ "根据您的要求，我生成以下..."
   ❌ "以下是第1证据组的完整证据包。"
   ```

2. **所有质检报告必须分离**
   ```
   ❌ "数据一致性验证报告"
   ❌ "结论： 证据组生成完毕..."
   ```

3. **所有测试标记必须删除**
   ```
   ❌ "【测试】"
   ❌ "[TEST]"
   ❌ "（测试数据）"
   ```

### 6.2 P1 - 应该净化

4. **元数据应该分离到配置文件**
   ```
   ❌ "证明目的： ..." → 移入 evidence_index.json
   ```

5. **内部备注应该替换或删除**
   ```
   ❌ "（此处填写日期）" → 替换为实际值或删除
   ```

## 七、验收标准

### 7.1 通用性验收

| 检查项 | 验证方法 | 预期结果 |
|-------|---------|---------|
| 无硬编码案件类型 | 代码搜索 | 无特定案件名称 |
| 无硬编码字段值 | 代码搜索 | 无具体数值或名称 |
| 支持多案件类型 | 配置测试 | 可切换不同案件配置 |
| 支持自定义模板 | 模板测试 | 可加载新模板 |

### 7.2 内容净化验收

| 检查项 | 验证命令 | 预期结果 |
|-------|---------|---------|
| LLM响应前缀 | grep "好的，作为专业的法律文书生成助手" | 0 matches |
| 质检报告 | grep "数据一致性验证报告" | 0 matches |
| 测试标记 | grep "【测试】" | 0 matches |
| 证明目的混入 | grep "证明目的：" | 0 matches |
| 内部备注 | grep "（此处填写" | 0 matches |

### 7.3 内容完整性验收

| 检查项 | 验证方法 | 预期结果 |
|-------|---------|---------|
| 合同条款数 | 条款检查 | >= 配置文件要求 |
| 字段完整性 | 字段检查 | 所有变量已替换 |
| 脱敏替换 | 占位符检查 | 无脱敏标记残留 |

## 八、文档要求

### 8.1 必须提供的文档

1. API文档（接口说明、参数说明、返回值说明）
2. 配置文档（配置文件格式、案件类型配置说明）
3. 模板开发文档（如何添加新模板）
4. 插件开发文档（如何添加新处理器/计算器）
5. 部署文档（环境要求、部署步骤、配置说明）
6. 更新日志（CHANGELOG）

### 8.2 代码内文档

1. 每个文件头部必须有文件说明
2. 每个类必须有docstring
3. 每个公开函数必须有docstring
4. 复杂逻辑必须有注释说明
5. 配置项必须有注释说明

---

**文档版本**: 2.1
**创建日期**: 2024-01-27
**最后更新**: 2024-01-27

**更新记录**:
- v2.1: 新增5.3 PDF排版要求（每份证据另起一页、页码规则、封面/目录）
- v2.0: 通用框架版本，移除特定案件硬编码
