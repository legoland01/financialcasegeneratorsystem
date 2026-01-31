"""占位符检测器"""
import re
from typing import List, Tuple
from loguru import logger


class PlaceholderChecker:
    """检测文本中的占位符模式"""

    def __init__(self):
        self.patterns = [
            (r'某某\w*', '某某开头占位符'),
            (r'某\w{1,3}', '某开头短占位符'),
            (r'X\d+', 'X+数字占位符'),
            (r'X年X月X日', '日期占位符'),
            (r'[X×]\d+%', '百分比占位符'),
            (r'[X×]\d+', '数字占位符'),
            (r'【\s*】', '方括号占位符'),
            (r'（\s*）', '圆括号占位符'),
            (r'\(\s*\)', '英文圆括号占位符'),
            (r'或授权代表', '签名占位符'),
            (r'二〇\d{2}年\d{1,2}月\d{1,2}日', '未填充日期'),
        ]

    def check(self, text: str) -> Tuple[bool, List[str]]:
        found = []
        for pattern, _ in self.patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                placeholder = str(match)
                if placeholder not in found:
                    found.append(placeholder)
        return len(found) == 0, found

    def check_file(self, file_path: str) -> Tuple[bool, List[str]]:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return self.check(text)

    def get_placeholder_count(self, text: str) -> int:
        _, placeholders = self.check(text)
        return len(placeholders)

    def has_any_placeholder(self, text: str) -> bool:
        is_clean, _ = self.check(text)
        return not is_clean
