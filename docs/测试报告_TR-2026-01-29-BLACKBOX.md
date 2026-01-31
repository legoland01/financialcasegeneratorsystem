# 金融案件证据集生成系统 v2.0 - 黑盒测试报告

**测试日期**: 2026-01-29  
**测试版本**: v2.0.1  
**测试命令**: `python3 run_complete.py`  
**测试环境**: macOS + SiliconFlow API (DeepSeek-V3.2)  
**状态**: ✅ 通过

---

## 一、测试概述

### 1.1 测试目标
作为最终用户，使用单一命令生成完整卷宗，检查输出是否满足要求。

### 1.2 测试结果
| 项目 | 状态 |
|------|------|
| 单命令执行 | ✅ 通过 |
| Stage 0 | ✅ 5/5 成功 |
| Stage 1 | ✅ 21个证据 |
| PDF生成 | ✅ 完整卷宗.pdf |
| 数据一致性 | ✅ 金额一致 |

---

## 二、修复的问题

### 2.1 入口脚本修复 (BUG-ENTRY-001)

**问题**: 默认命令只运行Stage 0，不生成证据和PDF

**修复前**:
```
python3 run_complete.py           # Stage 0 → PDF (失败，缺证据文件)
python3 run_complete.py --stage1  # Stage 0+1 (无PDF)
```

**修复后**:
```
python3 run_complete.py           # 完整流程 (Stage 0 → Stage 1 → PDF)
python3 run_complete.py --stage0  # 仅Stage 0
```

**修改文件**: `run_complete.py`
- 移除Stage 0之前的`fix_key_numbers()`调用
- 调整逻辑：默认运行完整流程，`--stage0`仅运行Stage 0

### 2.2 证据目录路径修复

**问题**: 证据生成到重复目录 `evidence/evidence/证据组X/`

**修复**: `src/services/evidence_file_generator.py` 第72行
```python
# 修复前
group_dir = self.output_dir / f"evidence/证据组{group_id}"

# 修复后
group_dir = self.output_dir / f"证据组{group_id}"
```

### 2.3 证据索引路径修复

**问题**: `fix_evidence_index()`查找错误路径

**修复**: `run_complete.py` 第154行
```python
# 修复前
evidence_dir = Path("outputs/stage1/evidence/evidence")

# 修复后
evidence_dir = Path("outputs/stage1/evidence")
```

---

## 三、输出文件清单

```
outputs/
├── stage0/
│   ├── 0.1_structured_extraction.json  ✅
│   ├── 0.2_anonymization_plan.json     ✅
│   ├── 0.3_transaction_reconstruction.json  ✅
│   ├── 0.4_key_numbers.json            ✅ (设备总额1.5亿)
│   └── 0.5_evidence_planning.json      ✅
├── stage1/
│   ├── 民事起诉状.txt                   ✅
│   ├── plaintiff_package.json          ✅
│   └── evidence/
│       ├── evidence_index.json         ✅
│       ├── 证据组1/ (3个证据)           ✅
│       ├── 证据组2/ (2个证据)           ✅
│       ├── 证据组3/ (4个证据)           ✅
│       ├── 证据组4/ (3个证据)           ✅
│       ├── 证据组5/ (3个证据)           ✅
│       ├── 证据组6/ (4个证据)           ✅
│       └── 证据组7/ (2个证据)           ✅
└── outputs_complete/
    ├── 原告起诉包/
    │   ├── evidence_index.json         ✅
    │   └── key_numbers.json            ✅
    └── 完整测试卷宗.pdf                 ✅ (387 KB)
```

---

## 四、数据验证

### 4.1 金额一致性 ✅

| 项目 | 值 |
|------|-----|
| 设备总额 | 150,000,000元 |
| 合同金额 | 150,000,000元 |
| 状态 | ✅ 一致 |

### 4.2 证据统计 ✅

| 证据组 | 数量 |
|--------|------|
| 证据组1 | 3个 |
| 证据组2 | 2个 |
| 证据组3 | 4个 |
| 证据组4 | 3个 |
| 证据组5 | 3个 |
| 证据组6 | 4个 |
| 证据组7 | 2个 |
| **总计** | **21个** |

---

## 五、测试结论

| 评估项 | 结果 |
|--------|------|
| 单命令生成 | ✅ 通过 |
| Stage 0 | ✅ 5/5 成功 |
| Stage 1 | ✅ 21个证据 |
| PDF生成 | ✅ 成功 |
| 数据一致性 | ✅ 通过 |
| 整体评估 | ✅ **通过** |

---

**报告更新**: 2026-01-29  
**版本**: v2.0  
**状态**: ✅ 已修复并验证通过
