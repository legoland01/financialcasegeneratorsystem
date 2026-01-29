import json
from pathlib import Path
from collections import Counter

# 读取证据规划文件
with open('outputs/stage0/0.5_evidence_planning.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 分析证据组
evidence_table = data.get('证据归属规划表', [])

# 统计每个证据组的数量
groups = [e.get('证据组', 'unknown') for e in evidence_table]
group_counts = Counter(groups)

print('证据组分布:')
for g, c in sorted(group_counts.items()):
    print(f'  证据组{g}: {c}个证据')

print(f'\n总证据数: {len(groups)}')

# 分析归属方
owners = [e.get('应归属方', 'unknown') for e in evidence_table]
owner_counts = Counter(owners)

print('\n归属方分布:')
for owner, c in sorted(owner_counts.items()):
    print(f'  {owner}: {c}个证据')

# 显示每个证据组的详情
print('\n各证据组详情:')
for g in sorted(group_counts.keys()):
    group_items = [e for e in evidence_table if e.get('证据组') == g]
    print(f'\n证据组{g} ({len(group_items)}个证据):')
    for item in group_items:
        print(f'  {item.get("证据序号")}. {item.get("证据名称")} - {item.get("应归属方")}')
