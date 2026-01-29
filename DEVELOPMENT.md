# 开发规范

**新项目请先阅读此文档**

---

## 必须先读

| 文档 | 说明 |
|------|------|
| [docs/开发规范.md](docs/开发规范.md) | 通用开发规范（适用于所有项目） |
| [开发交接清单.md](开发交接清单.md) | 本项目交接checklist（必须签字确认） |
| [项目经验记录.md](项目经验记录.md) | 本项目专属经验教训 |

---

## 文档索引

### 需求文档

| 文档 | 说明 |
|------|------|
| [需求文档.md](需求文档.md) | 功能需求总览 |
| [v2.0功能保留清单.md](docs/v2.0功能保留清单.md) | 必须保留的功能 + 必须解决的问题 |

### 测试文档

| 文档 | 说明 |
|------|------|
| [v2.0完整测试清单.md](docs/v2.0完整测试清单.md) | 验收标准 + 测试命令 |
| [测试计划.md](docs/TEST_PLAN.md) | 测试方案 |
| [测试报告_2026-01-27.md](docs/测试报告_2026-01-27.md) | 测试报告（按日期命名） |

### 规范文档

| 文档 | 说明 |
|------|------|
| [docs/开发规范.md](docs/开发规范.md) | **通用开发规范**（适用于所有项目） |
| [docs/问题记录.md](docs/问题记录.md) | 问题记录（含解决方案） |
| [项目经验记录.md](项目经验记录.md) | **本项目专属经验教训** |

### 历史文档

| 文档 | 说明 |
|------|------|
| [CHANGELOG.md](CHANGELOG.md) | 版本变更记录 |
| [docs/v1_history/](docs/v1_history/) | v1.0历史文档 |

---

## 快速开始

### 新加入项目

1. 阅读 [docs/开发规范.md](docs/开发规范.md) 了解通用开发流程
2. 阅读 [开发交接清单.md](开发交接清单.md) 并签字确认
3. 阅读 [项目经验记录.md](项目经验记录.md) 了解本项目的教训
4. 按 [v2.0完整测试清单.md](docs/v2.0完整测试清单.md) 中的验收标准开发

### 遇到问题

1. 查 [docs/问题记录.md](docs/问题记录.md) 看以前有没有解决过
2. 查 [项目经验记录.md](项目经验记录.md) 看本项目的教训
3. 查 [CHANGELOG.md](CHANGELOG.md) 看历史版本

---

## 通用规范 vs 项目专属记录

| 类型 | 文档 | 内容 |
|------|------|------|
| **通用规范** | [docs/开发规范.md](docs/开发规范.md) | 适用于所有项目的规范 |
| **项目专属** | [项目经验记录.md](项目经验记录.md) | 本项目的教训和经验 |

---

## 入口点说明

### 推荐使用: run_complete.py

统一入口脚本，包含完整流程和自动验证：

```bash
# 完整流程（默认）
python3 run_complete.py

# 仅验证
python3 run_complete.py --verify

# 仅Stage0
python3 run_complete.py --stage0

# Stage0 + Stage1
python3 run_complete.py --stage1

# Stage0 + Stage1 + PDF生成
python3 run_complete.py --stage2
```

### 旧脚本（已废弃）

| 脚本 | 状态 | 说明 |
|------|------|------|
| `run_full_regeneration.py` | 废弃 | 使用 `run_complete.py` 替代 |
| `generate_pdf.py` | 废弃 | 使用 `run_complete.py --stage2` 替代 |
| `validate_outputs.py` | 保留 | 可独立运行验证（仅验证，不生成） |

### 独立验证脚本

```bash
# 独立验证（不重新生成）
python3 validate_outputs.py
```

---

## 关键链接

- GitHub Issues: 报告Bug或提出需求
- Pull Requests: 提交代码审查
- Wiki: 团队知识库（可选）

---

**更新日期**: 2026-01-27
**版本**: v1.1
