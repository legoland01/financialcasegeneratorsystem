# Bug Report & 反思文档

## 一、Bug清单

---

### Bug #001: evidence_index.json 文件路径全部指向最后一个证据

| 属性 | 内容 |
|------|------|
| **严重程度** | P0 - 阻断性缺陷 |
| **发现时间** | 2026-01-27 23:30 |
| **影响范围** | 原告证据索引文件完全失效 |
| **触发条件** | 每次运行生成系统必然触发 |

**问题现象：**
```
证据索引中所有证据的"文件路径"字段都指向同一个文件：
"outputs_complete/原告起诉包/证据组1/证据组1_E012_租金支付凭证.txt"

实际应该分别是：
- E001 -> 证据组1_E001_转让合同及公证书.txt
- E002 -> 证据组1_E002_融资租赁合同（售后回租）及公证书.txt
- ...
- E012 -> 证据组1_E012_租金支付凭证.txt
```

**根本原因：**
```python
# 错误代码结构
for eid, name, content in group1_evidence:
    filepath = group1_dir / f"证据组1_{eid}_{name}.txt"  # ← 每次循环更新filepath
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
# ↑ filepath在循环内更新 ✓

evidence_groups.append({...})  # ← 循环外代码

for eid, name, _ in group1_evidence:  # ← 独立的循环
    evidence_index["证据列表"].append({
        "文件路径": str(filepath)  # ← filepath始终指向最后一次赋值的E012
    })
```

**解决方案：**
```python
# 正确代码结构
for eid, name, content in group1_evidence:
    filepath = group1_dir / f"证据组1_{eid}_{name}.txt"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 在循环内部立即记录索引
    evidence_index["证据列表"].append({
        "证据ID": eid,
        "文件路径": str(filepath)  # ← 现在指向正确的文件
    })

evidence_groups.append({...})
```

**修复文件：** `run_complete.py:126-148`

---

### Bug #002: LSP报错 "filepath" is possibly unbound (5处)

| 属性 | 内容 |
|------|------|
| **严重程度** | P1 - 编译警告 |
| **发现时间** | 2026-01-27 23:30 |
| **影响范围** | 5处变量未绑定警告 |

**问题现象：**
```
ERROR [173:25] "filepath" is possibly unbound
ERROR [206:25] "filepath" is possibly unbound
ERROR [240:25] "filepath" is possibly unbound
ERROR [274:25] "filepath" is possibly unbound
ERROR [307:25] "filepath" is possibly unbound
```

**根本原因：**
在修复Bug #001时，删除了循环外的`for eid, name, _ in group1_evidence`循环，但保留了其他证据组（Group 2-6）的类似代码结构，导致：
1. 部分代码残留了旧的循环结构
2. `evidence_groups.append`被错误地移到了循环前面
3. filepath变量在某些代码路径中未被赋值就被使用

**解决方案：**
统一所有证据组的代码模式，将索引记录完全移到循环内部：
```python
for eid, name, content in groupN_evidence:
    filepath = groupN_dir / f"证据组N_{eid}_{name}.txt"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    evidence_index["证据列表"].append({
        "证据ID": eid,
        "文件路径": str(filepath)
    })

evidence_groups.append({...})
```

**修复文件：** `run_complete.py:153-184` (Group 2), `run_complete.py:186-214` (Group 3), 等

---

### Bug #003: 文件类型(证据类型)全部错误

| 属性 | 内容 |
|------|------|
| **严重程度** | P2 - 数据错误 |
| **发现时间** | 2026-01-27 23:30 |
| **影响范围** | 证据索引中"文件类型"字段不准确 |

**问题现象：**
```
E009 资产评估报告 -> "合同"  ← 错误，应该是"凭证/单据"
E010 付款回单 -> "合同"     ← 错误，应该是"凭证/单据"
E012 租金支付凭证 -> "合同" ← 错误，应该是"凭证/单据"
```

**根本原因：**
硬编码了所有证据的文件类型为"合同"，未根据证据ID区分：
```python
# 错误代码
for eid, name, _ in group1_evidence:
    evidence_index["证据列表"].append({
        "文件类型": "合同"  # ← 全部设为"合同"
    })
```

**解决方案：**
```python
# 正确代码
file_type = "凭证/单据" if eid in ["E009", "E010", "E012"] else "合同"
evidence_index["证据列表"].append({
    "文件类型": file_type
})
```

**修复文件：** `run_complete.py:131`

---

## 二、根本原因分析

### 2.1 代码结构问题

| 问题 | 分析 |
|------|------|
| **循环嵌套逻辑混乱** | 证据组循环和索引记录循环分离，导致变量作用域问题 |
| **重复代码模式** | 6个证据组几乎完全相同的代码，未提取公共函数 |
| **缺乏防御性编程** | 没有验证生成的路径是否正确对应 |

**为什么会出现：**
- 编码时急于求成，没有先设计整体结构
- 复制粘贴代码时忘记调整变量作用域
- 缺少单元测试覆盖关键路径

---

### 2.2 需求传承问题

#### 问题表现：

**需求文档 vs 代码实现不一致：**

| 需求文档 | 实际实现 |
|----------|----------|
| 证据组1包含5个证据 | ✅ 正确 |
| 证据组2包含1个证据 | ✅ 正确 |
| E001-E012的证据ID | ✅ 正确 |
| 证据组1的证明目的 | ✅ 正确 |
| 证据ID顺序：E001, E002, E009, E010, E012 | ✅ 正确 |
| **证据文件类型分类** | ❌ 未实现 |
| **文件路径与证据ID一一对应** | ❌ Bug |

**质疑：**

1. **需求文档缺少关键字段定义**
   - `docs/PRODUCT_REQUIREMENTS.md` 没有明确定义"文件类型"字段的取值规则
   - 没有定义evidence_index.json中"文件路径"字段的格式要求

2. **需求文档没有定义Evidence Item的分类标准**
   - 哪些证据是"合同"？
   - 哪些证据是"凭证/单据"？
   - 哪些证据是"文书"？
   - 需求中没有明确说明

3. **前序版本的evidence_index.json没有作为标准参考**
   - `outputs/stage1/evidence/evidence_index.json` 文件存在
   - 但没有将其作为新版本的输入规范
   - 导致新版本需要"重新发明轮子"

---

### 2.3 测试覆盖不足

| 测试场景 | 覆盖状态 |
|----------|----------|
| 生成文件数量 | ✅ 验证了22个文件 |
| 文件名格式 | ✅ 验证了命名规范 |
| **evidence_index.json内容正确性** | ❌ 未验证 |
| **文件路径与实际文件对应** | ❌ 未验证 |
| **证据类型分类正确性** | ❌ 未验证 |

**为什么没有测试：**
- 没有编写验证脚本
- 依赖人工检查
- 没有自动化断言

---

## 三、改进建议

### 3.1 需求层面

1. **补充Evidence Item分类规范**
   ```markdown
   ## 证据文件类型分类
   
   | 类型 | 定义 | 示例 |
   |------|------|------|
   | 合同 | 当事人之间签订的协议文件 | 转让合同、融资租赁合同、抵押合同 |
   | 凭证/单据 | 支付、交付、评估等证明文件 | 付款回单、租金凭证、评估报告 |
   | 文书 | 司法机关出具的文书 | 执行证书、执行裁定书 |
   | 合同/凭证 | 兼具合同和凭证性质 | 委托代理合同、咨询服务合同 |
   ```

2. **定义evidence_index.json的Schema**
   ```json
   {
     "type": "object",
     "properties": {
       "证据列表": {
         "type": "array",
         "items": {
           "properties": {
             "文件路径": {"type": "string", "pattern": ".*E[0-9]{3}.*"}
           }
         }
       }
     }
   }
   ```

3. **将前序版本输出作为Golden Standard**
   - 明确要求新版本输出必须与旧版本结构完全一致
   - 提供diff工具验证差异

---

### 3.2 代码层面

1. **提取公共函数**
   ```python
   def _generate_evidence_group(p_dir, group_num, evidence_list, group_info):
       """生成证据组及索引记录的公共函数"""
       group_dir = p_dir / f"证据组{group_num}"
       group_dir.mkdir(exist_ok=True)
       
       evidence_items = []
       for eid, name, content in evidence_list:
           filepath = group_dir / f"证据组{group_num}_{eid}_{name}.txt"
           with open(filepath, 'w', encoding='utf-8') as f:
               f.write(content)
           
           file_type = _get_file_type(eid)
           evidence_items.append({
               "证据ID": eid,
               "文件路径": str(filepath),
               "文件类型": file_type
           })
       
       return evidence_items
   ```

2. **增加断言验证**
   ```python
   def _validate_evidence_index(evidence_index, output_dir):
       """验证evidence_index的正确性"""
       for item in evidence_index["证据列表"]:
           filepath = Path(item["文件路径"])
           assert filepath.exists(), f"文件不存在: {filepath}"
           assert item["证据ID"] in filepath.name, f"ID与文件名不匹配: {item}"
   ```

---

### 3.3 测试层面

1. **自动化验证脚本**
   ```python
   def test_evidence_index_consistency():
       with open("outputs_complete/原告起诉包/evidence_index.json") as f:
           index = json.load(f)
       
       for item in index["证据列表"]:
           filepath = Path(item["文件路径"])
           assert filepath.exists(), f"Missing: {item['文件路径']}"
           assert item["证据ID"] in filepath.name
       
       print("✓ evidence_index.json consistency verified")
   ```

2. **回归测试**
   - 对比新旧版本的evidence_index.json结构
   - 对比生成的证据文件数量
   - 验证关键字段的取值

---

## 四、结论

### 4.1 经验教训

| 教训 | 行动项 |
|------|--------|
| 循环变量作用域容易出错 | 将相关操作集中在同一循环内 |
| 重复代码容易遗漏 | 提取公共函数 |
| 需求文档不完整会导致实现偏差 | 补充Schema和分类规范 |
| 缺少测试会导致低级错误 | 增加断言和验证脚本 |

### 4.2 致谢

感谢用户提出这个要求。代码写得匆忙，确实出现了不应该出现的bug。写下这份文档有助于团队避免类似问题再次发生。

---

**文档创建时间：** 2026-01-27 23:35
**文档作者：** OpenCode Assistant
