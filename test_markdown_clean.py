#!/usr/bin/env python3
"""测试markdown清理功能"""
import re

# 从stage1_service.py复制的clean_markdown函数
def clean_markdown(text: str) -> str:
    """清理markdown符号，生成纯文本"""
    # 去除代码块
    text = re.sub(r'```json\s*[\s\S]*?\s*```', '', text)
    text = re.sub(r'```\s*[\s\S]*?\s*```', '', text)
    text = re.sub(r'```[^`]*```', '', text)
    text = re.sub(r'~~~[^~]*~~~', '', text)

    # 去除行内代码
    text = re.sub(r'`([^`\n]+)`', r'\1', text)

    # 去除加粗
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)

    # 去除删除线
    text = re.sub(r'~~([^~]+)~~', r'\1', text)

    # 去除标题
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)

    # 去除引用
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)

    # 处理无序列表
    text = re.sub(r'^[-*+]\s+', '· ', text, flags=re.MULTILINE)

    # 处理有序列表
    text = re.sub(r'^(\d+)\.\s+', r'\1. ', text, flags=re.MULTILINE)

    # 处理任务列表
    text = re.sub(r'^-\s*\[\s*\]\s+', '□ ', text, flags=re.MULTILINE)
    text = re.sub(r'^-\s*\[x\]\s+', '■ ', text, flags=re.MULTILINE)

    # 处理分隔线
    text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)

    # 去除链接格式
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)

    # 去除HTML标签
    text = re.sub(r'<[^>]+>', '', text)

    # 去除多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()

# 测试markdown清理
test_text = """
**民事起诉状**

**原告：** 上海金信融资租赁有限公司

### 诉讼请求

1.  请求法院判令被告支付欠款
2.  请求法院判令被告支付利息

**事实与理由：**
- 原告与被告于2021年签订合同
- 被告未按约定履行还款义务

```
{
  "test": "data"
}
```
"""

result = clean_markdown(test_text)
print('=' * 60)
print('清理后的文本')
print('=' * 60)
print(result)
print()
print('=' * 60)
print('验证结果')
print('=' * 60)
print(f"包含**: {'**' in result}")
print(f"包含#标题: {'#' in result}")
print(f"包含反引号: {'`' in result}")
print(f"包含代码块: {'```' in result}")
print(f"包含删除线: {'~~' in result}")

# 测试真实文件
print()
print('=' * 60)
print('测试真实文件')
print('=' * 60)

test_files = [
    'outputs/stage1/民事起诉状.txt',
    'outputs/stage1/原告程序性文件.txt',
    'outputs/stage2/民事答辩状.txt',
    'outputs/stage2/被告程序性文件.txt'
]

for f in test_files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        print(f"\n=== {f} ===")
        print(f"文件大小: {len(content)} 字符")
        print(f"包含**: {'**' in content}")
        print(f"包含#标题: {'#' in content}")
        print(f"包含反引号: {'`' in content}")
        print(f"包含代码块: {'```' in content}")
    except FileNotFoundError:
        print(f"\n=== {f} ===")
        print("文件不存在")
