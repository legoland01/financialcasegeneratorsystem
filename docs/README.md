# 金融案件PDF生成系统 - 文档索引

## 文档列表

| 文档 | 版本 | 说明 |
|------|------|------|
| [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md) | v2.0 | 产品需求文档（当前有效） |
| [TEST_PLAN.md](TEST_PLAN.md) | v2.0 | 测试方案（当前有效） |
| [CHANGELOG.md](CHANGELOG.md) | - | 变更日志 |

## 文档演进历史

| 版本 | 日期 | 主要变更 |
|------|------|---------|
| [v1.0](v1_history/PRODUCT_REQUIREMENTS_v1.0.md) | 2024-01-26 | 初始版本，特定案件设计 |
| **v2.0** | **2024-01-27** | **通用框架设计，完全自动化** |

### v2.0 核心变更

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  判决书 → 诉求 → 合同 → 附件 → 证据集                        │
│                                                             │
│  所有数据自动生成，不需要人工准备                            │
│                                                             │
│  ✓ 正确？                                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**详细变更请查看 [CHANGELOG.md](CHANGELOG.md)**

## 文档结构

```
docs/
├── README.md                    # 本文档
├── PRODUCT_REQUIREMENTS.md      # 产品需求（v2.0）
├── TEST_PLAN.md                 # 测试方案（v2.0）
├── CHANGELOG.md                 # 变更日志
└── v1_history/                  # 历史版本
    ├── PRODUCT_REQUIREMENTS_v1.0.md
    ├── TEST_PLAN_v1.0.md
    └── BUG_TRACKER_v1.0.md
```

---

## 核心设计理念

### 设计方向（v2.0）

1. **完全自动化**：所有数据自动生成，不需要人工准备
2. **文档驱动**：先生成合同，合同决定需要什么附件
3. **生成时提供上下文**：Prompt中包含所有真实信息，避免LLM创造新模式
4. **可扩展渲染器**：只实现合同和表格2种核心格式，其他预留接口

### 核心功能

| 功能 | 说明 |
|------|------|
| DataGenerator | 自动生成公司名称、设备、金额、日期等数据 |
| DynamicPromptBuilder | 构建包含完整上下文的Prompt |
| render_contract() | 渲染合同格式 |
| render_table() | 渲染表格格式 |

---

## 快速开始

### 1. 阅读需求文档

[PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md) 包含：
- 系统架构
- 核心功能
- 数据准备
- PDF格式规范

### 2. 了解测试方案

[TEST_PLAN.md](TEST_PLAN.md) 包含：
- 测试框架
- 单元测试
- 集成测试
- 回归测试

### 3. 运行测试

```bash
# 运行所有测试
bash run_tests.sh

# 验证输出质量
bash verify_quality.sh outputs/完整测试卷宗_简化版.pdf
```

---

**最后更新**: 2024-01-27

