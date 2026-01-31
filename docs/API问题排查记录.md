# 问题排查与修复记录

> 本文档记录系统开发过程中遇到的问题及解决方案，避免重复踩坑。

---

## 1. SiliconFlow API 问题

### 1.1 API Key Invalid 错误

**问题描述**
```
Error code: 401 - Api key is invalid
```

**排查过程**
1. 使用curl测试API连接
2. 检查API端点配置

**根本原因**
- **错误端点**: `https://api.siliconflow.com/v1`
- **正确端点**: `https://api.siliconflow.cn/v1`

**解决方案**
```env
OPENAI_API_BASE=https://api.siliconflow.cn/v1
```

---

## 2. 证据目录重复创建问题

### 2.1 问题描述
证据文件生成到重复目录: `outputs/stage1/evidence/evidence/证据组X/`

### 2.2 排查过程
```bash
# 发现重复目录
ls outputs/stage1/evidence/
# → evidence/ (重复)
# → 证据组1/ (正确)

tree outputs/stage1/evidence/
# → evidence/evidence/证据组1/  (错误)
```

### 2.3 根本原因
`evidence_file_generator.py` 第72行:
```python
group_dir = self.output_dir / f"evidence/证据组{group_id}"
```
`self.output_dir` 已指向 `outputs/stage1/evidence`，又加了 `evidence/` 前缀。

### 2.4 解决方案
```python
# 修复后
group_dir = self.output_dir / f"证据组{group_id}"
```

**修复文件**: `src/services/evidence_file_generator.py:72`

---

## 3. 入口脚本逻辑问题

### 3.1 问题描述
`python3 run_complete.py` 无法生成完整卷宗

**原逻辑**:
| 命令 | Stage 0 | Stage 1 | PDF |
|------|---------|---------|-----|
| `run_complete.py` | ✅ | ❌ | ✅* |
| `run_complete.py --stage0` | ✅ | ❌ | ❌ |
| `run_complete.py --stage1` | ✅ | ✅ | ❌ |

*PDF需要evidence_index.json，但默认流程不运行Stage 1

### 3.2 排查过程
1. 运行 `python3 run_complete.py --no-verify`
2. 检查输出目录，发现缺少证据文件
3. 手动运行Stage 1后PDF才生成

### 3.3 解决方案
修改 `run_complete.py` 逻辑:

```python
# 修复后逻辑
# Stage0 - 始终运行
# Stage1 - 默认运行（除非指定 --stage0）
# PDF - 默认运行（除非指定 --stage0）
```

**修复文件**: `run_complete.py` (约410-450行)

---

## 4. fix_key_numbers() 调用时机问题

### 4.1 问题描述
LLM生成的 `0.4_key_numbers.json` 缺少设备清单，导致金额验证失败

**现象**:
```
设备总额: 0元
合同金额: 150,000,000元
❌ 金额不一致!
```

### 4.2 排查过程
1. 检查 `0.4_key_numbers.json` 内容
2. 发现缺少 `租赁物清单` 字段
3. 追踪 `fix_key_numbers()` 调用时机

### 4.3 根本原因
```python
# 原代码 (第410-412行)
fix_key_numbers()  # Stage 0之前调用
fix_evidence_index()

# 运行Stage 0...
stage0_result = run_stage0(judgment_text)

# fix_key_numbers() 保存的数据被LLM结果覆盖
```

### 4.4 解决方案
删除Stage 0之前的 `fix_key_numbers()` 调用，只在Stage 1之后调用:
```python
# 删除第410-412行
# fix_key_numbers()
# fix_evidence_index()

# Stage0 - 始终运行
logger.info("\n运行Stage0...")
stage0_result = run_stage0(judgment_text)

# ... Stage1 ...

# 修复数据 (Stage 1之后)
fix_key_numbers()
fix_evidence_index()
```

**修复文件**: `run_complete.py` 第410-412行

---

## 5. 证据索引路径问题

### 5.1 问题描述
PDF生成失败: `证据索引不存在: outputs_complete/原告起诉包/evidence_index.json`

### 5.2 排查过程
```bash
find outputs -name "evidence_index.json"
# → outputs/stage1/evidence/evidence_index.json
```

### 5.3 根本原因
`fix_evidence_index()` 函数路径错误:
```python
# 原代码 (第154行)
evidence_dir = Path("outputs/stage1/evidence/evidence")  # 错误!
```

### 5.4 解决方案
```python
# 修复后
evidence_dir = Path("outputs/stage1/evidence")
```

**修复文件**: `run_complete.py` 第154行

---

## 6. 超时问题

### 6.1 问题描述
命令执行超时，证据生成被中断

**原因**: 13-21个证据文件需要10-15分钟

### 6.2 解决方案
1. 增加LLM客户端超时时间
2. 不要手动中断长时间运行的命令

```python
# 使用1200秒超时
llm_client = LLMClient(timeout=1200.0)
```

---

## 7. 快速排查清单

遇到问题时，按以下顺序检查：

| 步骤 | 检查项 | 命令 |
|------|--------|------|
| 1 | 查看日志 | `python3 run_complete.py 2>&1` |
| 2 | 检查目录结构 | `tree outputs/stage1/evidence/` |
| 3 | 检查索引文件 | `cat outputs/stage1/evidence/evidence_index.json` |
| 4 | 验证数据 | `python3 -c "import json; print(json.load(open('outputs/stage0/0.4_key_numbers.json')).keys())"` |
| 5 | API测试 | `curl -X POST "https://api.siliconflow.cn/v1/chat/completions"` |

---

## 8. 相关文件

| 文件 | 说明 |
|------|------|
| `.env` | API配置 |
| `src/utils/llm.py` | LLM客户端 |
| `src/services/evidence_file_generator.py` | 证据生成器 |
| `src/services/stage1/stage1_service.py` | Stage 1服务 |
| `run_complete.py` | 入口脚本 |
| `docs/测试报告_*.md` | 测试报告 |

---

## 9. 更新日志

| 日期 | 更新内容 |
|------|----------|
| 2026-01-29 | 首次记录API问题 |
| 2026-01-29 | 补充证据目录重复问题 |
| 2026-01-29 | 补充入口脚本逻辑问题 |
| 2026-01-29 | 补充fix_key_numbers调用时机问题 |
| 2026-01-29 | 补充证据索引路径问题 |
