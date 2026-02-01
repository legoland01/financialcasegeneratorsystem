# 金融案件证据集生成系统 - 产品需求文档

**文档版本**: v2.3
**状态**: 有效
**创建日期**: 2024-01-27
**最后更新**: 2026-02-01

---

## 一、文档演进历史

| 版本 | 日期 | 主要变更 |
|------|------|---------|
| v1.0 | 2024-01-26 | 初始版本，特定案件设计 |
| v2.0 | 2024-01-27 | 通用框架设计，完全自动化 |
| v2.1 | 2026-01-28 | 更新验证命令、修正日期错误 |
| v2.2 | 2026-01-31 | 添加占位符后处理、质量保障体系 |
| v2.3 | 2026-02-01 | 添加多模态质量检测、清理文档结构 |

> 详细变更记录请查看 [CHANGELOG.md](CHANGELOG.md)

---

## 二、系统概述

### 2.1 设计目标

自动生成符合中国法院要求的**通用金融案件**证据集PDF文档。

### 2.2 核心设计理念

```
判决书 → 诉求 → 合同 → 附件 → 证据集
              ↓
        完全自动生成
```

### 2.3 设计原则

| 原则 | 说明 |
|------|------|
| 通用化 | 支持各类金融案件（融资租赁、借贷、担保等） |
| 配置驱动 | 案件类型、证据模板、字段映射均可配置 |
| 自动化 | 所有数据自动生成，无需人工准备 |
| 可扩展 | 新证据类型只需添加配置，不改核心代码 |

---

## 三、系统架构

### 3.1 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                      EvidenceGenerator                          │
│                                                                 │
│  ├── render_contract(title, content) → PDF元素列表             │
│  ├── render_table(title, headers, rows) → PDF元素列表          │
│  ├── post_process_evidence() → 占位符清理                      │
│  └── validate_evidence_quality() → 质量验证                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      DataGenerator                              │
│  ├── template_libraries/ 公司名称、设备名称、地址等模板库       │
│  ├── data_fields_schema.json 所有字段类型与生成规则             │
│  ├── anonymization_plan.json 反脱敏映射表                       │
│  └── placeholder_rules.json 占位符识别与替换规则                │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 数据流

```
原始材料（判决书）
    ↓
Stage 0: 理解交易结构（LLM提取结构化信息）
    ├── 提取诉讼请求
    ├── 确定需要的合同类型
    └── 生成合同上下文
    ↓
Stage 1: 生成证据（LLM生成合同+模板生成附件）
    ├── 生成合同正文
    ├── 根据合同类型确定需要的附件
    └── 自动生成附件数据
    ↓
Stage 1.5: 占位符后处理 [v2.2新增]
    ├── 识别占位符模式
    ├── 从配置文件自动填充
    └── 验证数据完整性
    ↓
Stage 2: 渲染PDF
    ├── 合同格式渲染器
    ├── 表格格式渲染器
    └── 智能分页控制器
    ↓
Stage 2.5: 质量验证 [v2.2新增]
    ├── 验证脱敏标记已清除
    ├── 验证证据ID唯一性
    └── 输出验证报告
    ↓
输出: 完整证据集.pdf
```

---

## 四、证据类型与格式映射

### 4.1 证据类型分类

| 类型 | 定义 | 示例 |
|------|------|------|
| 合同 | 当事人之间签订的协议文件 | 转让合同、融资租赁合同、抵押合同 |
| 凭证/单据 | 支付、交付、评估等证明文件 | 付款回单、租金凭证、评估报告 |
| 文书 | 司法机关出具的文书 | 执行证书、执行裁定书 |

### 4.2 格式要求

| 类型 | 格式要求 |
|------|---------|
| 合同 | 标准合同格式，含签署栏 |
| 表格 | PDF表格（斑马纹、表头灰底） |
| 凭证 | 银行/机构标准格式 |

---

## 五、数据准备系统

### 5.1 模板库结构

```
template_libraries/
├── company_names.json      # 公司名称库
├── equipment_names.json    # 设备名称库
├── locations.json          # 地址库
└── bank_accounts.json      # 银行账户库
```

### 5.2 占位符规则

```json
{
  "patterns": [
    {"pattern": "某某公司[0-9]*", "replacement": "从company_names.json随机选择"},
    {"pattern": "X年X月X日", "replacement": "从key_numbers.json提取"},
    {"pattern": "人民币[0-9]+元", "replacement": "从key_numbers.json提取"}
  ]
}
```

---

## 六、Prompt设计原则

### 6.1 核心原则

1. **必须使用真实信息** - 禁止使用占位符
2. **上下文完整** - 提供完整的当事人、金额、时间信息
3. **格式规范** - 符合法律文书标准格式

### 6.2 当事人信息格式

```
甲方（出租人/转让方）：
  公司名称：从0.2_脱敏替换策划.companyProfileLib提取
  统一社会信用代码：91310000MA1XXXXXXX
  法定代表人：XXX
  地址：XXX

乙方（承租人/受让方）：
  公司名称：XXX
  统一社会信用代码：XXX
  ...
```

### 6.3 金额信息格式

```
合同金额：人民币壹亿伍仟万元整（¥150,000,000.00）
```

---

## 七、Prompt构建策略（v2.2新增）

### 7.1 问题背景

v1.0系统使用JSON数据模板，LLM无法正确提取公司名称，导致生成内容包含大量占位符。

### 7.2 解决方案

**核心原则**：不是"生成后替换"，而是"生成时提供完整上下文"

### 7.3 Prompt构建流程

```
Step 1: 分析目标内容类型（合同/文书/凭证）
Step 2: 提取涉及的公司、金额、时间
Step 3: 从Profile库查询完整信息
Step 4: 直接在Prompt中列出具体信息
Step 5: 明确禁止使用占位符
Step 6: 生成证据
```

### 7.4 接口设计

```python
class PromptBuilder:
    def build_evidence_prompt(self, evidence: Dict, evidence_type: str) -> str:
        """构建证据生成的完整Prompt"""
        
    def _extract_involved_companies(self, evidence: Dict, profiles: Dict) -> List[Dict]:
        """提取涉及的公司信息"""
        
    def _extract_amount_info(self, evidence: Dict, key_numbers: Dict) -> Dict:
        """提取金额信息"""
        
    def _build_party_info_section(self, companies: List[Dict]) -> str:
        """构建当事人信息section"""
        
    def _assemble_prompt(self, ...) -> str:
        """组装完整Prompt"""
```

---

## 八、PDF格式规范

### 8.1 分页规则

| 元素 | 要求 |
|------|------|
| 每份证据 | 必须另起一页 |
| 封面（可选） | 不计页码或标"I" |
| 页码位置 | 统一（底部居中） |

### 8.2 字体规范

| 类型 | 字号 | 字体 |
|------|------|------|
| 合同标题 | 18 | SimHei |
| 合同正文 | 12 | SimSun |
| 表格标题 | 14 | SimHei |
| 表格内容 | 10 | SimSun |

### 8.3 表格样式

- 表头背景：浅灰（#D3D3D3）
- 斑马纹：偶数行浅灰
- 边框：黑色0.5pt
- 对齐：居中

---

## 九、质量保障体系（v2.2新增）

### 9.1 证据质量等级

| 等级 | 定义 | 要求 |
|------|------|------|
| P0-可用 | 内容完整，无占位符 | 可用于生产环境 |
| P1-基本可用 | 内容基本完整，有少量非关键占位符 | 需人工检查 |
| P2-不可用 | 有关键占位符或数据不一致 | 禁止生成PDF |

### 9.2 质量检查项

| 检查项 | 要求 | 处理 |
|--------|------|------|
| 脱敏标记检查 | 不含 `某某`、`某公司` | ❌ 失败，阻止生成PDF |
| 完整性检查 | 所有必需字段有值 | ❌ 失败，阻止生成PDF |
| 金额一致性检查 | 合同金额与租赁物清单合计一致 | ❌ 失败，阻止生成PDF |

### 9.3 质量验证命令

```bash
# 完整运行（含质量验证）
python3 run_complete.py

# 分阶段运行
python3 run_complete.py --stage0 --judgment <path>
python3 run_complete.py --stage1 --judgment <path>
python3 run_complete.py --stage2 --judgment <path>

# 验证输出质量
python3 validate_outputs.py outputs/
```

### 9.4 质量报告示例

```json
{
  "report_time": "2026-01-31 20:49:42",
  "evidence_count": 33,
  "quality_summary": {
    "passed": 3,
    "failed": 30,
    "pass_rate": "9%"
  },
  "issues": [
    {
      "type": "placeholder_detected",
      "file": "证据组4_E005_执行证书.txt",
      "pattern": "X年月日",
      "count": 5
    }
  ],
  "recommendation": "当前系统不可用于生产环境，需修复占位符问题"
}
```

---

## 十、当前实现范围

### 10.1 核心功能

| 组件 | 功能 | 优先级 | 状态 |
|------|------|--------|------|
| DataGenerator | 数据自动生成 | P0 | ✅ |
| DynamicPromptBuilder | 动态Prompt构建 | P0 | ✅ |
| EvidenceRenderer.render_contract | 合同渲染 | P0 | ✅ |
| EvidenceRenderer.render_table | 表格渲染 | P0 | ✅ |
| SmartPaginator | 智能分页 | P0 | ✅ |
| PostProcessor | 占位符后处理 | P0 | ✅ |
| QualityValidator | 质量验证 | P0 | ✅ |

### 10.2 待实现功能

| 功能 | 预估工时 |
|------|---------|
| MultimodalQA多模态质量检测 | 11小时 |

---

## 十一、输入输出

### 11.1 输入

```
输入: (2024)沪74民初XXX号.pdf
```

### 11.2 输出

```
outputs/
├── stage0/
│   ├── 0.1_结构化提取.json
│   ├── 0.2_脱敏替换策划.json
│   ├── 0.3_交易结构重构.json
│   ├── 0.4_关键数字清单.json
│   └── 0.5_证据归属规划.json
├── stage1/
│   ├── 民事起诉状.txt
│   ├── plaintiff_package.json
│   └── evidence/
│       ├── evidence_index.json
│       ├── 证据组1/
│       ├── 证据组2/
│       └── ...
├── stage2/
│   └── quality_report.json          [新增] 质量验证报告
└── outputs_complete/
    └── 完整测试卷宗.pdf
```

---

## 十二、配置文档

### 12.1 配置文件结构

```
config/
├── evidence_format_schema.json   # 证据格式定义
├── data_fields_schema.json       # 字段类型定义
├── placeholder_rules.json        # 占位符规则定义
└── template_libraries/           # 模板库
    ├── company_names.json
    ├── equipment_names.json
    └── locations.json
```

### 12.2 案件类型配置

```json
// config/case_types/financing_lease.json
{
  "case_type": "融资租赁纠纷",
  "required_contracts": [
    {"type": "融资租赁合同", "attachments": ["租赁物清单", "租金支付计划"]},
    {"type": "抵押合同", "attachments": ["抵押物清单"]}
  ]
}
```

---

## 十三、多模态质量检测（v2.3新增）

### 13.1 背景

PDF生成存在布局质量问题，需要多模态模型检测：

| 问题类型 | 示例 | 当前检测方法 |
|---------|------|-------------|
| 文本问题 | 某某设备、若干台 | pdftotext + 正则 ✅ |
| **布局问题** | 留白、回车、表格、编号断裂 | **需要多模态** ❌ |

### 13.2 功能需求

| 需求编号 | 功能描述 | 优先级 |
|---------|---------|--------|
| MR-001 | 使用Qwen-VL-Max分析PDF布局 | P0 |
| MR-002 | 检测条款编号连续性 | P0 |
| MR-003 | 检测异常留白 | P1 |
| MR-004 | 检测回车位置正确性 | P1 |

### 13.3 技术方案

| 组件 | 选择 | 理由 |
|------|------|------|
| 多模态模型 | Qwen-VL-Max | SiliconFlow可用 |
| PDF处理 | PyMuPDF | PDF转图片 |
| API | SiliconFlow | 用户指定 |

### 13.4 运行方式

```bash
# 环境变量设置
export SILICONFLOW_API_KEY="your-api-key"
export MULTIMODAL_TEST=1

# 运行多模态测试
python3 -m pytest tests/blackbox/test_pdf_quality.py::TestPDFLayoutQuality -v
```

---

## 十四、附录

### 14.1 相关文档

| 文档 | 说明 |
|------|------|
| [TEST_PLAN.md](TEST_PLAN.md) | 测试方案 |
| [开发规范.md](开发规范.md) | 通用开发规范 |
| [问题记录.md](问题记录.md) | 问题记录 |
| [需求变更记录.md](需求变更记录.md) | 需求变更记录 |
| [CHANGELOG.md](CHANGELOG.md) | 变更日志 |
| [详细设计_TD-2026-01-27-001.md](详细设计_TD-2026-01-27-001.md) | 详细设计文档 |
| [详细设计评审_TD-2026-01-27-001.md](详细设计评审_TD-2026-01-27-001.md) | 设计评审记录 |
| [需求评审_RR-2026-02-01-001_Prompt构建策略v2.md](需求评审_RR-2026-02-01-001_Prompt构建策略v2.md) | Prompt策略评审 |
| [需求评审_RR-2026-02-01-002_多模态质量检测.md](需求评审_RR-2026-02-01-002_多模态质量检测.md) | 多模态评审 |

### 14.2 验证命令

```bash
# 完整运行
python3 run_complete.py --all --judgment <path_to_judgment>

# 分阶段运行
python3 run_complete.py --stage0 --judgment <path>
python3 run_complete.py --stage1 --judgment <path>
python3 run_complete.py --stage2 --judgment <path>

# 验证输出质量
python3 validate_outputs.py outputs/

# 检查数据生成
python3 -c "from src.utils.data_generator import DataGenerator; ..."
```

---

**文档版本**: v2.3
**状态**: 有效
**创建日期**: 2024-01-27
**最后更新**: 2026-02-01
