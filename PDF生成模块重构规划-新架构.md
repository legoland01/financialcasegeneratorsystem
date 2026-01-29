# 金融案件测试数据生成系统 - PDF生成模块重构规划

## 规划背景

### 当前问题分析

#### 问题1：证据包生成方式不当 ⚠️

**当前方式**：
```
outputs/stage1/
├── 原告证据包_证据组1.txt      # 一个大文件，包含4个证据
├── 原告证据包_证据组2.txt      # 一个大文件，包含2个证据
└── 民事起诉状.txt
```

**问题**：
- ❌ 多个证据混在一个文件里
- ❌ 格式混杂（合同、凭证、文书都在一起）
- ❌ 难以分离和单独使用
- ❌ 难以维护和修改

#### 问题2：PDF生成复杂度过高 ⚠️

**当前方式**：
- 从大的txt文件中读取所有内容
- 用正则表达式分离不同证据
- 清理markdown符号
- 判断每个证据的类型
- 按类型应用不同格式

**问题**：
- ❌ 逻辑复杂，容易出错
- ❌ 正则表达式很难准确
- ❌ 不同证据格式难以统一处理
- ❌ 难以验证和调试

#### 问题3："头疼医头脚疼医脚" ⚠️

**表现**：
- 为了解决一个复杂处理，引入更多复杂处理
- 文件内容转换：txt → JSON → 正则提取 → PDF
- 格式清理：markdown → 清理后的文本 → PDF
- 每一步都可能引入新问题

### 用户建议的优秀方案

#### 核心思想

**每个证据单独一个文件，PDF生成时直接读取**

#### 方案优势

1. ✅ **文件结构清晰**
   ```
   outputs/stage1/evidence/
   ├── 证据组1_转让合同.txt
   ├── 证据组1_公证书.txt
   ├── 证据组1_付款回单.txt
   ├── 证据组2_融资租赁合同.txt
   └── ...
   ```

2. ✅ **PDF生成简单**
   - 读取证据归属规划表
   - 根据规划表找到每个证据文件
   - 直接读取并插入PDF
   - 不需要复杂的文本分离

3. ✅ **易于维护**
   - 每个证据文件可以独立查看和修改
   - 增删证据不影响其他文件
   - 可以单独测试每个证据

4. ✅ **类型处理简单**
   - 合同类文件：直接插入，不需要额外处理
   - 凭证类文件：直接插入
   - 文书类文件：直接插入
   - 表格类文件：可能需要特殊处理，但范围更小

---

## 新架构设计

### 文件结构重构

#### 阶段0：判决书解析
```
outputs/stage0/
├── 0.1_structured_extraction.json
├── 0.2_anonymization_plan.json
├── 0.3_transaction_reconstruction.json
├── 0.4_key_numbers.json
├── 0.5_evidence_planning.json     # 证据归属规划表
└── evidence_index.json             # 证据索引（新增）
```

#### 阶段1：原告起诉包
```
outputs/stage1/
├── metadata.json                   # 元数据（文件列表）
├── complaint.txt                  # 民事起诉状（保留）
├── procedural_files.txt           # 程序性文件（保留）
└── evidence/                      # 证据目录（新增）
    ├── 证据组1/
    │   ├── E001_转让合同.txt
    │   ├── E002_公证书.txt
    │   ├── E003_付款回单.txt
    │   └── E004_资产评估报告.txt
    ├── 证据组2/
    │   ├── E005_融资租赁合同.txt
    │   └── E006_公证书.txt
    └── ...
```

#### 阶段2：被告答辩包
```
outputs/stage2/
├── metadata.json                   # 元数据
├── answer.txt                      # 民事答辩状
├── procedural_files.txt           # 程序性文件
└── evidence/                      # 证据目录
    └── ...
```

### 证据文件命名规范

#### 命名规则

```
格式：{证据组编号}_{证据序号}_{证据名称简写}.{扩展名}

示例：
证据组1_E001_转让合同.txt
证据组1_E002_公证书.txt
证据组1_E003_付款回单.txt
证据组2_E005_融资租赁合同.txt
```

#### 编号规则

- **证据组编号**：组1、组2、组3...
- **证据序号**：E001、E002、E003...（全局唯一）
- **证据名称简写**：转让合同、公证书、付款回单等
- **扩展名**：.txt（统一为文本格式，便于阅读和编辑）

### 元数据文件

#### evidence_index.json（新增）

```json
{
  "证据总数": 24,
  "证据组数": 6,
  "证据列表": [
    {
      "证据ID": "E001",
      "证据组": 1,
      "证据组名称": "租赁物转让关系证据组",
      "证据名称": "《转让合同》",
      "证据名称简写": "转让合同",
      "文件类型": "合同类",
      "归属方": "原告",
      "文件路径": "outputs/stage1/evidence/证据组1_E001_转让合同.txt",
      "页面数": 1,
      "文件大小": 12345
    },
    {
      "证据ID": "E002",
      "证据组": 1,
      "证据组名称": "租赁物转让关系证据组",
      "证据名称": "（2021）XXX证经字第1643号公证书",
      "证据名称简写": "公证书",
      "文件类型": "文书类",
      "归属方": "原告",
      "文件路径": "outputs/stage1/evidence/证据组1_E002_公证书.txt",
      "页面数": 1,
      "文件大小": 5678
    }
  ],
  "证据组列表": [
    {
      "组编号": 1,
      "组名称": "租赁物转让关系证据组",
      "证据数量": 3,
      "证明目的": "证明原告与被告某某公司1之间就租赁物买卖达成合意并已实际履行"
    }
  ]
}
```

#### metadata.json（阶段1/阶段2）

```json
{
  "阶段": 1,
  "生成时间": "2026-01-21 18:00:00",
  "证据总数": 15,
  "证据目录": "evidence/",
  "证据索引文件": "evidence_index.json",
  "主文件": {
    "民事起诉状": "complaint.txt",
    "程序性文件": "procedural_files.txt"
  },
  "文件统计": {
    "合同类": 3,
    "凭证类": 4,
    "文书类": 5,
    "表格类": 3
  }
}
```

---

## 重构步骤

### 步骤1：修改证据包生成逻辑

#### 1.1 修改阶段1服务

**文件**：`src/services/stage1/stage1_service.py`

**修改前**：
```python
# 生成一个大的txt文件，包含所有证据
evidence_package = self.generate_evidence_package(stage0_data, evidence_group_index=1)
# 输出：outputs/stage1/原告证据包_证据组1.txt（包含多个证据）
```

**修改后**：
```python
# 生成每个证据的独立文件
evidence_files = self.generate_evidence_files(stage0_data)

# 生成证据索引
evidence_index = self.generate_evidence_index(evidence_files, stage0_data)

# 保存证据索引
evidence_index_path = self.output_dir / "stage1" / "evidence_index.json"
save_json(evidence_index, str(evidence_index_path))

# 生成元数据
metadata = self.generate_metadata(evidence_files, stage0_data)
metadata_path = self.output_dir / "stage1" / "metadata.json"
save_json(metadata, str(metadata_path))
```

#### 1.2 修改阶段2服务

**文件**：`src/services/stage2/stage2_service.py`

**修改**：同阶段1

### 步骤2：实现证据文件生成

#### 2.1 新建证据文件生成器

**文件**：`src/services/evidence_file_generator.py`

**功能**：
```python
class EvidenceFileGenerator:
    """证据文件生成器 - 生成每个证据的独立文件"""

    def __init__(self, llm_client, output_dir):
        self.llm_client = llm_client
        self.output_dir = output_dir / "evidence"

    def generate_all_evidence_files(self, stage0_data, evidence_planning):
        """
        生成所有证据的独立文件

        Returns:
            证据文件列表
        """
        evidence_files = []

        # 按证据组分组
        evidence_groups = self._group_evidences(evidence_planning)

        # 为每个证据生成文件
        for group_id, evidence_list in evidence_groups.items():
            group_dir = self.output_dir / f"证据组{group_id}"
            group_dir.mkdir(parents=True, exist_ok=True)

            for evidence in evidence_list:
                file_path = self._generate_evidence_file(
                    evidence,
                    stage0_data,
                    group_dir
                )
                evidence_files.append(file_path)

        return evidence_files

    def _generate_evidence_file(self, evidence, stage0_data, group_dir):
        """
        生成单个证据文件

        Returns:
            文件路径
        """
        # 加载提示词
        prompt_path = self.prompt_dir / "stage1" / "1.2.1_单个证据生成.md"
        prompt = load_prompt_template(str(prompt_path))

        # 构建完整提示词
        full_prompt = f"""
{prompt}

证据信息：
{json.dumps(evidence, ensure_ascii=False, indent=2)}

阶段0数据：
{self._get_relevant_stage0_data(evidence, stage0_data)}

请按照证据类型（{evidence['文件类型']}）的标准格式，生成完整的证据内容。
不要包含任何markdown符号，只生成纯文本内容。
"""

        # 调用大模型
        response = self.llm_client.generate(full_prompt)

        # 清理markdown符号
        clean_response = self._clean_markdown(response)

        # 生成文件名
        evidence_id = f"E{evidence['证据序号']:03d}"
        filename = f"证据组{evidence['证据组']}_{evidence_id}_{evidence['证据名称简写']}.txt"
        file_path = group_dir / filename

        # 保存文件
        file_path.write_text(clean_response, encoding='utf-8')

        return file_path

    def _clean_markdown(self, text):
        """清理markdown符号"""
        # 去除所有markdown符号
        text = re.sub(r'```json\s*[\s\S]*?\s*```', '', text)
        text = re.sub(r'```\s*[\s\S]*?\s*```', '', text)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^-\s+', '• ', text, flags=re.MULTILINE)
        text = re.sub(r'^(\d+)\.\s+', r'\1. ', text, flags=re.MULTILINE)

        return text.strip()

    def _generate_evidence_index(self, evidence_files, stage0_data):
        """生成证据索引"""
        # 从0.5读取证据归属规划
        evidence_planning = stage0_data.get("0.5_证据归属规划", {})

        # 构建证据索引
        evidence_index = {
            "证据总数": len(evidence_files),
            "证据组数": len(set([f"证据组{e.get('证据组')}" for f in evidence_files])),
            "证据列表": [],
            "证据组列表": []
        }

        # 添加每个证据的信息
        for file_path in evidence_files:
            # 从文件名解析信息
            filename = file_path.stem
            parts = filename.split('_')

            evidence_id = parts[1]  # E001
            group_id = int(parts[0].replace('证据组', ''))  # 1
            evidence_name_simplified = parts[2]  # 转让合同

            # 从证据归属规划表查找详细信息
            evidence_info = self._find_evidence_info(
                group_id,
                evidence_id,
                evidence_planning
            )

            # 添加到索引
            evidence_index["证据列表"].append({
                "证据ID": evidence_id,
                "证据组": group_id,
                "证据名称": evidence_info.get("证据名称", ""),
                "证据名称简写": evidence_name_simplified,
                "文件类型": evidence_info.get("文件类型", ""),
                "归属方": evidence_info.get("应归属方", ""),
                "文件路径": str(file_path),
                "页面数": 1,  # 暂时固定为1
                "文件大小": file_path.stat().st_size
            })

        # 构建证据组列表
        evidence_groups = {}
        for evidence in evidence_planning.get("证据归属规划表", []):
            group_id = evidence.get("证据组")
            if group_id not in evidence_groups:
                evidence_groups[group_id] = {
                    "组编号": group_id,
                    "组名称": evidence_planning.get("证据分组", {}).get(f"证据组_{group_id}", {}).get("组名称", ""),
                    "证据数量": 0,
                    "证明目的": ""
                }
            evidence_groups[group_id]["证据数量"] += 1

        evidence_index["证据组列表"] = list(evidence_groups.values())

        return evidence_index
```

### 步骤3：重构PDF生成器

#### 3.1 新建简化版PDF生成器

**文件**：`src/utils/pdf_generator_simple.py`

**核心思想**：
- 不做复杂的内容分离和清理
- 直接读取证据文件内容
- 直接插入PDF

**主要方法**：
```python
class PDFGeneratorSimple:
    """简化版PDF生成器"""

    def __init__(self, output_path):
        self.output_path = Path(output_path)
        self._setup_pdf()

    def _setup_pdf(self):
        """初始化PDF文档"""
        # 注册中文字体
        self._register_chinese_fonts()

        # 初始化PDF文档
        self.doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=A4,
            rightMargin=2.5*cm,
            leftMargin=2.5*cm,
            topMargin=2.5*cm,
            bottomMargin=2.5*cm
        )

        # 初始化样式
        self.styles = getSampleStyleSheet()
        self._setup_styles()

        # 存储PDF内容
        self.elements = []

    def generate_complete_docket_from_files(self, evidence_index_path, stage0_data, stage1_data, stage2_data):
        """从证据索引文件生成完整卷宗PDF"""
        # 读取证据索引
        evidence_index = json.loads(Path(evidence_index_path).read_text(encoding='utf-8'))

        # 添加封面
        self._add_cover()

        # 添加目录
        self._add_table_of_contents(evidence_index)

        # 添加阶段1内容
        self._add_stage1_from_files(stage1_data, evidence_index)

        # 添加阶段2内容
        self._add_stage2_from_files(stage2_data, evidence_index)

        # 添加阶段3内容
        self._add_stage3_from_files(stage0_data)

        # 生成PDF
        self.doc.build(self.elements)

    def _add_stage1_evidence(self, evidence_index):
        """添加阶段1证据 - 从证据文件直接读取"""
        evidence_list = evidence_index["证据列表"]
        plaintiff_evidence = [e for e in evidence_list if e["归属方"] == "原告"]

        # 按证据组分组
        evidence_groups = {}
        for evidence in plaintiff_evidence:
            group_id = evidence["证据组"]
            if group_id not in evidence_groups:
                evidence_groups[group_id] = []
            evidence_groups[group_id].append(evidence)

        # 为每个证据组添加标题和证据
        for group_id in sorted(evidence_groups.keys()):
            group_name = f"证据组{group_id}"

            # 添加证据组标题
            self.add_title(group_name, level=2)
            self.add_spacer()

            # 添加每个证据
            for evidence in evidence_groups[group_id]:
                # 添加证据标题
                self.add_title(f"证据{evidence['证据ID']}：{evidence['证据名称']}", level=3)

                # 直接读取证据文件内容
                evidence_file_path = Path(evidence["文件路径"])
                evidence_content = evidence_file_path.read_text(encoding='utf-8')

                # 直接添加到PDF（不需要任何处理）
                self.add_paragraph(evidence_content)

                self.add_spacer()

    def add_paragraph(self, text):
        """添加段落"""
        # 不做任何清理，直接添加
        paragraph = Paragraph(text, self.styles['ChineseBody'])
        self.elements.append(paragraph)
```

#### 3.2 保留原有PDF生成器

**文件**：`src/utils/pdf_generator.py`

**操作**：不删除，保留作为备份

---

## 新提示词

### 提示词1.2.1：单个证据生成

**文件**：`prompts/stage1/1.2.1_单个证据生成.md`

**内容**：
```markdown
# 任务：生成单个证据文件的完整内容

## 任务背景
本任务负责根据证据信息，生成单个证据文件的完整内容。
生成的证据文件应该是纯文本格式，不包含任何markdown符号。

## 输入参数

- 证据信息（JSON格式）
- 阶段0相关数据

## 输出要求

### 格式要求
- 纯文本格式
- 不包含任何markdown符号（```、**、#、`、>、-等）
- 符合证据类型的标准格式

### 证据类型格式

#### 合同类
```
【合同名称】
【合同编号】

【甲方（出租人）】
名称：XXX
统一社会信用代码：XXX
法定代表人：XXX
地址：XXX

【乙方（承租人）】
名称：XXX
统一社会信用代码：XXX
法定代表人：XXX
地址：XXX

【第一条 租赁物】
...

【第二条 转让价款】
...

【签署栏】
甲方（盖章）：
法定代表人（签字）：

乙方（盖章）：
法定代表人（签字）：

签订日期：XXXX年XX月XX日
```

#### 凭证类
```
【凭证名称】

【日期】XXXX年XX月XX日

【收/付款人】XXX

【金额】人民币XXXX元整

【摘要】XXX

【凭证号】XXX

【签署】XXX
```

#### 文书类
```
【文书名称】

【致】XXX

【正文内容】...

【签署】
XXX
【日期】XXXX年XX月XX日
```

## 执行步骤

1. 读取证据信息
2. 读取阶段0相关数据（Profile库、关键金额等）
3. 根据证据类型选择对应的标准格式
4. 使用Profile库中的真实名称和数据
5. 生成完整的证据内容
6. 清理所有markdown符号
7. 确保格式符合证据类型规范

## 质量控制

- [ ] 纯文本格式
- [ ] 无markdown符号
- [ ] 数据与Profile库一致
- [ ] 格式符合证据类型规范
- [ ] 内容完整
```

---

## 文件组织对比

### 当前方式（复杂）

```
outputs/stage1/
├── 民事起诉状.txt
├── 原告证据包_证据组1.txt      # 大文件，4个证据混在一起
│   ├── ```json
│   ├── 证据1
│   ├── 证据2
│   ├── ...
│   └── 需要复杂处理分离
└── 原告程序性文件.txt
```

**问题**：
- ❌ 证据混杂，难以分离
- ❌ PDF生成需要复杂的文本处理
- ❌ 难以维护和调试

### 新方式（简单）

```
outputs/stage1/
├── metadata.json                  # 元数据
├── evidence_index.json           # 证据索引
├── 民事起诉状.txt
├── 原告程序性文件.txt
└── evidence/                     # 证据目录
    ├── 证据组1/
    │   ├── E001_转让合同.txt      # 独立文件
    │   ├── E002_公证书.txt
    │   ├── E003_付款回单.txt
    │   └── E004_资产评估报告.txt
    ├── 证据组2/
    │   ├── E005_融资租赁合同.txt
    │   └── E006_公证书.txt
    └── ...
```

**优势**：
- ✅ 每个证据独立，易于维护
- ✅ PDF生成直接读取文件，无需复杂处理
- ✅ 文件结构清晰
- ✅ 易于扩展和修改

---

## 实施计划

### 阶段1：重构证据包生成（2-3小时）

**任务1.1**：创建证据文件生成器
- [ ] 创建 `src/services/evidence_file_generator.py`
- [ ] 实现 `generate_all_evidence_files` 方法
- [ ] 实现 `_generate_evidence_file` 方法
- [ ] 实现 `_clean_markdown` 方法
- [ ] 实现 `_generate_evidence_index` 方法

**任务1.2**：修改阶段1服务
- [ ] 修改 `run_all` 方法
- [ ] 移除旧的证据包生成逻辑
- [ ] 集成新的证据文件生成器
- [ ] 生成 `evidence_index.json`
- [ ] 生成 `metadata.json`

**任务1.3**：修改阶段2服务
- [ ] 同阶段1的修改

### 阶段2：创建简化版PDF生成器（2-3小时）

**任务2.1**：创建简化版PDF生成器
- [ ] 创建 `src/utils/pdf_generator_simple.py`
- [ ] 实现基础PDF初始化
- [ ] 实现中文字体注册
- [ ] 实现基础样式设置

**任务2.2**：实现证据添加逻辑
- [ ] 实现 `_add_stage1_evidence` 方法
- [ ] 实现直接读取证据文件并添加
- [ ] 不做任何文本处理，直接插入PDF

**任务2.3**：实现完整卷宗生成
- [ ] 实现 `generate_complete_docket_from_files` 方法
- [ ] 从 `evidence_index.json` 读取证据列表
- [ ] 按证据组组织PDF内容

**任务2.4**：创建单个证据生成提示词
- [ ] 创建 `prompts/stage1/1.2.1_单个证据生成.md`
- [ ] 定义不同证据类型的格式规范
- [ ] 明确输出要求

### 阶段3：测试和验证（1-2小时）

**任务3.1**：测试证据文件生成
- [ ] 测试证据文件是否正确生成
- [ ] 验证每个证据文件的内容
- [ ] 检查 `evidence_index.json` 是否正确
- [ ] 检查文件命名是否符合规范

**任务3.2**：测试PDF生成
- [ ] 测试完整卷宗PDF是否生成
- [ ] 验证PDF内容是否完整
- [ ] 验证证据是否正确插入
- [ ] 验证格式是否正确

**任务3.3**：验证markdown清理
- [ ] 检查证据文件是否无markdown符号
- [ ] 手动打开PDF检查格式

### 阶段4：集成和优化（1小时）

**任务4.1**：集成到主执行流程
- [ ] 修改 `run_full_regeneration.py`
- [ ] 集成新的证据文件生成
- [ ] 集成新的PDF生成
- [ ] 更新命令行参数

**任务4.2**：清理旧文件
- [ ] 保留原有 `pdf_generator.py` 作为备份
- [ ] 测试新流程
- [ ] 验证功能完整性

---

## 预期效果

### 代码复杂度对比

| 任务 | 当前方式 | 新方式 | 改进 |
|------|---------|--------|------|
| 证据包生成 | 复杂（混在一起） | 简单（逐个生成） | 70% ↓ |
| PDF证据处理 | 极复杂（正则分离） | 简单（直接读取） | 90% ↓ |
| Markdown清理 | 复杂（多种格式） | 简单（单个文件） | 80% ↓ |
| 调试难度 | 困难（大文件） | 容易（小文件） | 80% ↓ |

### 文件数量对比

**阶段1（15个证据）**：
- 当前：3个文件
- 新方式：19个文件（15证据 + 4元数据）

**优势**：
- ✅ 虽然文件数增加，但每个文件都很简单
- ✅ 易于维护和查找
- ✅ 可以单独修改某个证据
- ✅ 可以单独查看某个证据

### 用户体验对比

| 维度 | 当前方式 | 新方式 |
|------|---------|--------|
| 查找证据 | 困难（在大文件中搜索） | 容易（直接打开文件） |
| 修改证据 | 困难（需定位大文件） | 容易（直接编辑文件） |
| 查看证据 | 困难（混杂内容） | 容易（独立文件） |
| PDF生成 | 复杂处理 | 简单读取 |

---

## 总体评估

### 优势

1. ✅ **架构清晰**：每个证据独立，职责明确
2. ✅ **逻辑简单**：直接读取文件，无需复杂处理
3. ✅ **易于维护**：每个文件独立，容易修改和扩展
4. ✅ **易于调试**：可以单独测试每个证据生成
5. ✅ **易于理解**：符合"分而治之"的设计原则

### 风险

1. ⚠️ **文件数量增加**：证据文件数较多（每个证据一个文件）
2. ⚠️ **需要重构**：需要重写证据生成和PDF生成的核心逻辑
3. ⚠️ **向后兼容**：可能与旧格式不兼容

### 应对

1. **文件数量增加**：这是合理的trade-off，带来的是架构的简化
2. **需要重构**：这是必要的，当前架构过于复杂
3. **向后兼容**：可以保留旧代码作为参考和备份

---

## 总结

### 核心思想

**每个证据单独一个文件，PDF生成时直接读取**

### 关键改进

1. 证据文件独立
2. 证据索引清晰
3. PDF生成简化
4. 复杂度大幅降低

### 预期时间

- 阶段1：2-3小时
- 阶段2：2-3小时
- 阶段3：1-2小时
- 阶段4：1小时

**总计**：6-9小时（约1-1.5个工作日）

### 下一步

本规划经确认后，可以交给开发会话执行重构。

---

**规划制定日期**: 2026-01-21
**规划版本**: v2.0.0
**制定人**: opencode
**审批状态**: 待确认
