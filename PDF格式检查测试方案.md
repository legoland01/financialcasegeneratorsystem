# PDF格式检查测试方案

**创建日期**: 2026-01-25
**版本**: v2.0
**最后更新**: 2026-01-26
**目的**: 检查生成PDF文件的格式规范性和数据完整性，验证反脱敏修复

---

## 0. 反脱敏修复验证（新增）

### Test D1: 证据文件反脱敏验证

**测试目的**: 验证证据文件在保存前已正确执行反脱敏

**检查命令**:
```bash
# 1. 检查证据文件中的占位符
echo "=== 证据文件占位符检查 ==="
grep -r "某某公司" outputs/stage1/evidence_new/evidence/ 2>/dev/null | wc -l
grep -r "周某" outputs/stage1/evidence_new/evidence/ 2>/dev/null | grep -v "原告周某" | wc -l
grep -r "（此处填写" outputs/stage1/evidence_new/evidence/ 2>/dev/null | wc -l
grep -r "【填写" outputs/stage1/evidence_new/evidence/ 2>/dev/null | wc -l

# 2. 验证证据文件包含真实名称
echo ""
echo "=== 证据文件真实名称检查 ==="
grep -r "上海富隆融资租赁" outputs/stage1/evidence_new/evidence/ 2>/dev/null | wc -l
grep -r "周文斌" outputs/stage1/evidence_new/evidence/ 2>/dev/null | wc -l
grep -r "南昌昌茂商业管理" outputs/stage1/evidence_new/evidence/ 2>/dev/null | wc -l
```

**验证标准**:
| 检查项 | 修复前 | 修复后 |
|--------|--------|--------|
| "某某公司X" 占位符 | >0 | 0 |
| "周某"（非原告） | >0 | 0 |
| "（此处填写" | >0 | 0 |
| "上海富隆融资租赁" | 0 | >0 |
| "周文斌" | 0 | >0 |

---

### Test D2: PDF文件反脱敏验证

**测试目的**: 验证PDF文件中的脱敏名称已正确替换

**检查命令**:
```bash
python3 -c "
import PyPDF2
from pathlib import Path

pdf_path = Path('outputs/完整测试卷宗_简化版.pdf')
reader = PyPDF2.PdfReader(pdf_path)
full_text = ''
for page in reader.pages:
    full_text += page.extract_text() + '\n'

print('=== PDF反脱敏验证 ===')

# 检查脱敏名称（修复后应为0）
anonymized_names = ['某某公司', '某某人物', '某某机构', '某某公证处', '某某律师事务所']
for name in anonymized_names:
    if name in full_text:
        count = full_text.count(name)
        print(f'❌ 脱敏名称仍存在 \"{name}\": {count} 处')
    else:
        print(f'✅ 无脱敏名称 \"{name}\"')

# 检查真实名称（修复后应>0）
real_names = ['上海富隆融资租赁', '周文斌', '南昌昌茂', '上海嘉华律师事务所', '上海中诚公证处']
for name in real_names:
    if name in full_text:
        print(f'✅ 真实名称存在 \"{name}\"')
    else:
        print(f'❌ 真实名称缺失 \"{name}\"')
"
```

**验证标准**:
| 检查项 | 修复前 | 修复后 |
|--------|--------|--------|
| "某某公司X" | >10 | 0 |
| "某某公证处" | >0 | 0 |
| "上海富隆融资租赁" | 0 | >0 |
| "上海中诚公证处" | 0 | >0 |

---

### Test D3: 标准答案集验证

**测试目的**: 验证标准答案集JSON格式正确且数据完整

**检查命令**:
```bash
python3 -c "
import json

# 检查JSON格式
print('=== 标准答案集JSON格式验证 ===')
try:
    with open('outputs/标准答案集.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print('✅ JSON格式正确')
except json.JSONDecodeError as e:
    print(f'❌ JSON格式错误: {e}')

# 检查数据完整性
print()
print('=== 数据完整性检查 ===')
key_fields = ['审判长', '审判员', '原告', '被告', '计算基数', '起算日期', '截止日期', '滞纳金总额']
for field in key_fields:
    if field in str(data):
        print(f'✅ 字段存在 \"{field}\"')
    else:
        print(f'❌ 字段缺失 \"{field}\"')

# 检查是否有'未知'或'计算基数'
print()
print('=== 异常值检查 ===')
if '未知' in str(data):
    print('❌ 存在\"未知\"值')
else:
    print('✅ 无\"未知\"值')

if '计算基数' in str(data):
    print('❌ 存在原始键名\"计算基数\"')
else:
    print('✅ 无原始键名')
"
```

**验证标准**:
| 检查项 | 修复前 | 修复后 |
|--------|--------|--------|
| JSON格式 | Python字典格式 | 有效JSON |
| "计算基数: 未知" | 存在 | 不存在 |
| "起算日期: 未知" | 存在 | 不存在 |
| Python字典标记`{` | 存在 | 不存在 |

---

## 一、PDF文件清单

### 1.1 完整测试卷宗PDF

| 文件名 | 大小 | 页数 | 生成时间 | 状态 |
|--------|------|------|----------|------|
| 完整测试卷宗_简化版.pdf | 426KB | 30 | 2026-01-25 | ⚠️ 需检查 |
| 完整测试卷宗_最终版.pdf | 562KB | - | 2026-01-22 | 旧版本 |
| 完整测试卷宗_最新.pdf | 602KB | - | 2026-01-23 | 旧版本 |

### 1.2 标准答案集PDF

| 文件名 | 大小 | 页数 | 生成时间 | 状态 |
|--------|------|------|----------|------|
| 标准答案集.pdf | 194KB | 6 | 2026-01-25 | ⚠️ 需检查 |
| 标准答案集_新.pdf | 103KB | - | 2026-01-22 | 旧版本 |

---

## 二、测试项目

### Test P1: 完整测试卷宗格式检查

#### P1.1 占位符检查

**测试目的**: 检查PDF中是否包含占位符

**检查命令**:
```bash
python3 -c "
import PyPDF2
from pathlib import Path

pdf_path = Path('outputs/完整测试卷宗_简化版.pdf')
reader = PyPDF2.PdfReader(pdf_path)

# 提取所有文本
full_text = ''
for page in reader.pages:
    full_text += page.extract_text() + '\n'

# 检查占位符
placeholders = [
    '（此处填写',
    '【填写',
    '【请填写',
    '（略）',
    '【】',
    'XXX',
    '具体金额',
    '具体合同编号',
    'XXXX年XX月XX日'
]

print('=== 占位符检查结果 ===')
found_placeholders = []
for placeholder in placeholders:
    if placeholder in full_text:
        count = full_text.count(placeholder)
        found_placeholders.append((placeholder, count))
        print(f'❌ 发现占位符 \"{placeholder}\": {count} 处')

if not found_placeholders:
    print('✅ 无占位符')

print()
print(f'总页数: {len(reader.pages)}')
print(f'总字符数: {len(full_text)}')
"
```

**预期结果**: 
- ❌ 应发现占位符（当前状态）
- ✅ 修复后应无占位符

---

#### P1.2 数据完整性检查

**测试目的**: 检查关键数据是否完整

**检查命令**:
```bash
python3 -c "
import PyPDF2
from pathlib import Path

pdf_path = Path('outputs/完整测试卷宗_简化版.pdf')
reader = PyPDF2.PdfReader(pdf_path)
full_text = reader.pages[0].extract_text()  # 目录页

# 检查关键信息
checks = {
    '案号': '（2024）沪74民初',
    '法院': '上海金融法院',
    '证据组数': '证据组',
}

print('=== 数据完整性检查 ===')
for name, pattern in checks.items():
    if pattern in full_text:
        print(f'✅ {name}: 存在')
    else:
        print(f'❌ {name}: 缺失')
"
```

**预期结果**:
- ✅ 案号: 应存在
- ✅ 法院: 应存在
- ✅ 证据组列表: 应存在

---

#### P1.3 脱敏一致性检查

**测试目的**: 检查公司名称脱敏是否一致

**检查命令**:
```bash
python3 -c "
import PyPDF2
from pathlib import Path

pdf_path = Path('outputs/完整测试卷宗_简化版.pdf')
reader = PyPDF2.PdfReader(pdf_path)

# 检查第1页（起诉状）和第8页（证据文件）
for page_num in [0, 7]:  # 第1页和第8页
    if page_num < len(reader.pages):
        page_text = reader.pages[page_num].extract_text()
        
        print(f'\\n--- 第{page_num+1}页 ---')
        
        # 统计脱敏名称使用情况
        real_names = ['上海富隆', '南昌昌茂', '江西立信', '深圳前海']
        anonymized = ['某某公司']
        
        for name in real_names:
            if name in page_text:
                print(f'❌ 发现真实名称: {name}')
        
        for name in anonymized:
            count = page_text.count(name)
            if count > 0:
                print(f'✅ 使用脱敏名称: \"{name}\" ({count}处)')
"
```

**预期结果**:
- ✅ 起诉状应使用真实公司名称
- ✅ 证据文件应使用脱敏名称（某某公司1、某某公司5等）
- ⚠️ 当前可能存在混用问题

---

#### P1.4 证据文件格式检查

**测试目的**: 检查证据文件的格式规范性

**检查命令**:
```bash
python3 -c "
import PyPDF2
from pathlib import Path

pdf_path = Path('outputs/完整测试卷宗_简化版.pdf')
reader = PyPDF2.PdfReader(pdf_path)

# 检查证据文件部分（第8-20页）
print('=== 证据文件格式检查 ===')

for i in range(7, min(20, len(reader.pages))):  # 第8-20页
    page_text = reader.pages[i].extract_text()
    if not page_text:
        continue
    
    # 检查合同格式
    if '合同编号' in page_text:
        # 检查合同编号格式
        import re
        contract_ids = re.findall(r'合同编号[：:]\s*[\w\-]+', page_text)
        if contract_ids:
            print(f'✅ 第{i+1}页: 发现合同编号 - {contract_ids[0]}')
        
        # 检查方括号和圆括号混用
        brackets = {'【': page_text.count('【'), '】': page_text.count('【'),
                   '(': page_text.count('('), ')': page_text.count(')')}
        
        if brackets['【'] != brackets['【']:
            print(f'⚠️ 第{i+1}页: 方括号不匹配')
        
        if brackets['('] != brackets[')']:
            print(f'⚠️ 第{i+1}页: 圆括号不匹配')
"
```

**预期结果**:
- ✅ 合同编号格式正确
- ⚠️ 可能存在括号不匹配问题

---

### Test P2: 标准答案集格式检查

#### P2.1 JSON格式检查

**测试目的**: 检查标准答案集是否正确格式化

**检查命令**:
```bash
python3 -c "
import PyPDF2
from pathlib import Path

pdf_path = Path('outputs/标准答案集.pdf')
reader = PyPDF2.PdfReader(pdf_path)

print('=== JSON格式检查 ===')

# 检查第2页的合议庭信息
if len(reader.pages) > 1:
    page_text = reader.pages[1].extract_text()
    
    # 检查是否包含Python字典格式
    if \"{'\" in page_text or \"':\" in page_text:
        print('❌ 发现Python字典格式（未正确格式化）')
        print('示例: {\"审判长\": \"朱瑞\"...}')
        
        # 查找具体位置
        lines = page_text.split('\\n')
        for j, line in enumerate(lines):
            if '审判长' in line or '审判员' in line:
                print(f'  位置: 第{j+1}行')
    else:
        print('✅ 未发现未格式化的JSON')
"
```

**预期结果**:
- ❌ 当前存在JSON格式问题（Python字典格式直接输出）
- ✅ 修复后应无此问题

---

#### P2.2 关键数据检查

**测试目的**: 检查关键计算数据是否完整

**检查命令**:
```bash
python3 -c "
import PyPDF2
from pathlib import Path

pdf_path = Path('outputs/标准答案集.pdf')
reader = PyPDF2.PdfReader(pdf_path)

print('=== 关键数据检查 ===')

# 读取第6页（计算过程）
if len(reader.pages) > 5:
    page_text = reader.pages[5].extract_text()
    
    # 检查\"未知\"出现次数
    unknown_count = page_text.count('未知')
    if unknown_count > 0:
        print(f'❌ 发现{unknown_count}个\"未知\"数据项')
        
        # 显示包含\"未知\"的行
        lines = page_text.split('\\n')
        for j, line in enumerate(lines):
            if '未知' in line:
                print(f'  第{j+1}行: {line.strip()[:80]}')
    else:
        print('✅ 无\"未知\"数据项')
    
    # 检查0.00元的项目
    zero_count = page_text.count('0.00 元')
    if zero_count > 0:
        print(f'⚠️ 发现{zero_count}个金额为0.00元的项目')
"
```

**预期结果**:
- ❌ 当前存在"未知"数据（计算基数、起算日期等）
- ⚠️ 金额为0.00元（诉讼费用等）

---

#### P2.3 表格完整性检查

**测试目的**: 检查表格数据是否完整

**检查命令**:
```bash
python3 -c "
import PyPDF2
from pathlib import Path

pdf_path = Path('outputs/标准答案集.pdf')
reader = PyPDF2.PdfReader(pdf_path)

print('=== 表格完整性检查 ===')

# 读取第5页（表格）
if len(reader.pages) > 4:
    page_text = reader.pages[4].extract_text()
    
    # 检查表格行
    table_sections = [
        '合同基础金额',
        '租金安排',
        '租金支付计划',
        '违约相关金额',
        '诉讼费用',
        '判决金额',
        '关键时间点'
    ]
    
    for section in table_sections:
        if section in page_text:
            # 提取该部分内容
            start = page_text.find(section)
            end = page_text.find('\\n\\n', start)  # 下一个空行
            if end == -1:
                end = len(page_text)
            
            section_text = page_text[start:end]
            lines = section_text.split('\\n')
            
            # 统计空行或仅有标题的行
            empty_rows = [line for line in lines if line.strip() == '' or len(line.strip()) < 10]
            if len(empty_rows) > 2:
                print(f'⚠️ {section}: 发现{len(empty_rows)}个可能为空的行')
            else:
                print(f'✅ {section}: 格式正常')
        else:
            print(f'❌ {section}: 未找到')
"
```

**预期结果**:
- ⚠️ 表格数据可能不完整
- ✅ 修复后应有完整数据

---

## 三、性能检查

### Test P3: PDF生成性能

#### P3.1 文件大小检查

**测试目的**: 检查PDF文件大小是否合理

**检查命令**:
```bash
python3 -c "
from pathlib import Path

print('=== PDF文件大小检查 ===')

pdf_files = [
    '完整测试卷宗_简化版.pdf',
    '标准答案集.pdf'
]

for filename in pdf_files:
    filepath = Path(f'outputs/{filename}')
    if filepath.exists():
        size_kb = filepath.stat().st_size / 1024
        size_mb = size_kb / 1024
        
        print(f'{filename}:')
        print(f'  大小: {size_kb:.2f} KB ({size_mb:.2f} MB)')
        
        # 评估大小合理性
        if '完整测试卷宗' in filename:
            if size_mb > 1:
                print('  状态: ⚠️ 文件过大（超过1MB）')
            elif size_mb > 0.5:
                print('  状态: ✅ 大小合理（0.5-1MB）')
            else:
                print('  状态: ⚠️ 文件过小（低于0.5MB）')
        elif '标准答案集' in filename:
            if size_kb > 200:
                print('  状态: ⚠️ 文件过大（超过200KB）')
            elif size_kb > 50:
                print('  状态: ✅ 大小合理（50-200KB）')
            else:
                print('  状态: ⚠️ 文件过小（低于50KB）')
"
```

**预期结果**:
- 完整测试卷宗: 0.5-1MB 合理
- 标准答案集: 50-200KB 合理

---

## 四、测试结果汇总表

| 测试编号 | 测试项目 | 预期状态 | 当前状态 | 严重程度 |
|---------|---------|---------|---------|----------|
| P1.1 | 占位符检查 | 无占位符 | ❌ 有占位符 | 高 |
| P1.2 | 数据完整性 | 完整 | ⚠️ 部分完整 | 中 |
| P1.3 | 脱敏一致性 | 一致 | ⚠️ 存在混用 | 中 |
| P1.4 | 证据格式 | 规范 | ⚠️ 需优化 | 低 |
| P2.1 | JSON格式 | 正确格式化 | ❌ 未格式化 | 高 |
| P2.2 | 关键数据 | 完整 | ❌ 有"未知" | 高 |
| P2.3 | 表格完整 | 完整 | ⚠️ 部分缺失 | 中 |
| P3.1 | 文件大小 | 合理 | ✅ 合理 | 低 |

---

## 五、修复建议

### 立即修复（高优先级）

1. **占位符问题**
   - 修改证据生成模板，使用实际数据替换占位符
   - 或从0.4关键数字清单中提取数据填充

2. **JSON格式化问题**
   - 修改标准答案集生成代码，正确格式化JSON输出
   - 使用`json.dumps(..., indent=2)`格式化后输出

3. **关键数据完整性**
   - 从0.4关键数字清单中提取完整数据
   - 填充计算基数、起算日期等关键字段

### 短期修复（中优先级）

1. **脱敏一致性**
   -统一起诉状和证据文件的脱敏策略
   - 起诉状可使用真实名称
   - 证据文件应使用脱敏名称

2. **表格数据填充**
   - 从阶段0数据中提取完整表格数据
   - 填充合同金额、租金安排等

### 长期优化（低优先级）

1. **格式规范化**
   - 统一使用方括号或圆括号
   - 统一金额格式（全角/半角）

2. **性能优化**
   - 压缩PDF文件大小
   - 优化图片和表格

---

## 六、测试执行

### 执行反脱敏验证测试
```bash
# 验证证据文件
python3 -c "
import PyPDF2
from pathlib import Path

# 检查证据文件
evidence_dir = Path('outputs/stage1/evidence_new/evidence/')
if evidence_dir.exists():
    print('=== 证据文件反脱敏检查 ===')
    for md_file in evidence_dir.glob('*.md'):
        text = md_file.read_text(encoding='utf-8')
        
        # 检查占位符
        placeholders = ['某某公司', '（此处填写', '【填写']
        for p in placeholders:
            if p in text:
                print(f'❌ {md_file.name}: 包含占位符 \"{p}\"')
        
        # 检查真实名称
        real_names = ['上海富隆', '周文斌', '南昌昌茂']
        for name in real_names:
            if name in text:
                print(f'✅ {md_file.name}: 包含真实名称 \"{name}\"')
"
```

### 执行所有测试
```bash
python3 -c "
# 执行P1.1 占位符检查
exec(open('tests/check_placeholder.py').read())

# 执行P2.1 JSON格式检查
exec(open('tests/check_json_format.py').read())

# 执行P2.2 关键数据检查
exec(open('tests/check_key_data.py').read())
"
```

### 生成测试报告
```bash
python3 tests/generate_pdf_test_report.py
```

---

## 七、反脱敏修复状态

### 当前状态

| 状态项 | 状态 | 说明 |
|--------|------|------|
| 问题识别 | ✅ 完成 | 发现证据生成器缺少反脱敏 |
| 原因分析 | ✅ 完成 | 确定数据流问题 |
| 设计方案 | ✅ 完成 | 创建问题跟踪文档 |
| 代码规格 | ✅ 完成 | 创建代码修改规格说明 |
| 测试方案 | ✅ 完成 | 更新PDF格式检查测试方案 |
| 代码实现 | ⏳ 待执行 | 等待用户确认后执行 |
| 测试验证 | ⏳ 待执行 | 依赖代码实现 |

### 修复检查清单

- [ ] 创建 `src/utils/deanonymizer.py` 统一反脱敏工具类
- [ ] 修改 `src/services/evidence_file_generator.py` 添加反脱敏步骤
- [ ] 重新生成证据文件（阶段1）
- [ ] 验证证据文件不包含占位符
- [ ] 重新生成PDF文件（阶段3）
- [ ] 验证PDF文件显示真实名称
- [ ] 验证标准答案集JSON格式正确

---

**文档创建时间**: 2026-01-25
**最后更新**: 2026-01-26
**版本**: v2.0
**状态**: 待执行测试