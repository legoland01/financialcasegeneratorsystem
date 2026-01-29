import re
from typing import Dict, Any, List, Optional


class TemplateRenderer:
    """模板渲染器 - 渲染Prompt模板"""

    def __init__(self):
        """初始化模板渲染器"""
        pass

    def render(
        self,
        template: str,
        task_type: str,
        context: Dict[str, Any]
    ) -> str:
        """
        渲染模板

        Args:
            template: 模板字符串
            task_type: 任务类型
            context: 上下文字典
        Returns:
            渲染后的Prompt
        """
        flat_context = self._flatten_context(context)

        rendered = self._safe_format(template, task_type=task_type, **flat_context)

        rendered = self._post_process(rendered, context)

        return rendered

    def _safe_format(self, template: str, **kwargs) -> str:
        """安全格式化，处理缺失的键"""
        import re

        def replace_match(match):
            full_key = match.group(1)
            if full_key in kwargs:
                return str(kwargs[full_key])
            return f"[{full_key}]"

        pattern = r'\{([^{}]+)\}'
        return re.sub(pattern, replace_match, template)

    def _flatten_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """将嵌套字典展平为单层"""
        flat = {}

        def flatten(obj: Any, prefix: str = ""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{prefix}_{key}" if prefix else key
                    flatten(value, new_key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_key = f"{prefix}_{i}" if prefix else str(i)
                    flatten(item, new_key)
            else:
                if prefix:
                    flat[prefix] = obj

        flatten(context)
        return flat

    def _safe_get(self, context: Dict[str, Any], key: str, default: str = "") -> str:
        """安全获取上下文值"""
        return context.get(key, default)

    def _post_process(
        self,
        rendered: str,
        context: Dict[str, Any]
    ) -> str:
        """后处理渲染结果"""
        rendered = self._remove_empty_placeholders(rendered)
        rendered = self._format_numbers(rendered)
        rendered = self._clean_whitespace(rendered)
        return rendered

    def _remove_empty_placeholders(self, text: str) -> str:
        """移除空占位符"""
        pattern = r'\{[^{}]*_None\}'
        return re.sub(pattern, '', text)

    def _format_numbers(self, text: str) -> str:
        """格式化数字"""
        def format_number(match):
            number_str = match.group(1).replace(',', '')
            try:
                number = float(number_str)
                if number == int(number):
                    return f"{int(number):,}"
                return f"{number:,.2f}"
            except ValueError:
                return match.group(0)

        pattern = r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)'
        return re.sub(pattern, format_number, text)

    def _clean_whitespace(self, text: str) -> str:
        """清理空白字符"""
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines]
        return '\n'.join([line for line in cleaned_lines if line])

    def render_table(
        self,
        headers: List[str],
        rows: List[List[Any]],
        context: Dict[str, Any]
    ) -> str:
        """
        渲染表格

        Args:
            headers: 表头
            rows: 数据行
            context: 上下文
        Returns:
            渲染后的表格字符串
        """
        col_widths = self._calculate_column_widths(headers, rows)
        separator = self._create_table_separator(col_widths)

        lines = []
        lines.append(separator)
        header_line = self._create_table_row(headers, col_widths)
        lines.append(header_line)
        lines.append(separator)

        for row in rows:
            row_line = self._create_table_row(row, col_widths)
            lines.append(row_line)
            lines.append(separator)

        return '\n'.join(lines)

    def _calculate_column_widths(
        self,
        headers: List[str],
        rows: List[List[Any]]
    ) -> List[int]:
        """计算列宽"""
        col_widths = [len(str(h)) for h in headers]

        for row in rows:
            for i, cell in enumerate(row):
                cell_len = len(str(cell))
                if cell_len > col_widths[i]:
                    col_widths[i] = cell_len

        return [max(w, 3) for w in col_widths]

    def _create_table_separator(self, col_widths: List[int]) -> str:
        """创建表格分隔符"""
        parts = []
        for width in col_widths:
            parts.append('-' * (width + 2))
        return '+' + '+'.join(parts) + '+'

    def _create_table_row(
        self,
        cells: List[Any],
        col_widths: List[int]
    ) -> str:
        """创建表格行"""
        parts = []
        for i, cell in enumerate(cells):
            cell_str = str(cell)
            width = col_widths[i]
            parts.append(f" {cell_str:<{width}} ")
        return '|' + '|'.join(parts) + '|'

    def render_list(
        self,
        items: List[str],
        context: Dict[str, Any],
        bullet: str = "-"
    ) -> str:
        """
        渲染列表

        Args:
            items: 项目列表
            context: 上下文
            bullet: 项目符号
        Returns:
            渲染后的列表字符串
        """
        flat_context = self._flatten_context(context)
        rendered_items = []

        for item in items:
            rendered_item = item.format(**flat_context) if isinstance(item, str) else item
            rendered_items.append(f"{bullet} {rendered_item}")

        return '\n'.join(rendered_items)

    def render_section(
        self,
        title: str,
        content: str,
        context: Dict[str, Any],
        level: int = 2
    ) -> str:
        """
        渲染章节

        Args:
            title: 标题
            content: 内容
            context: 上下文
            level: 标题级别
        Returns:
            渲染后的章节字符串
        """
        markers = ['#', '##', '###', '####', '#####']
        level = min(level, len(markers))
        header = markers[level - 1]

        rendered_content = content.format(**self._flatten_context(context))

        return f"{header} {title}\n\n{rendered_content}"

    def extract_variables(self, template: str) -> List[str]:
        """提取模板中的变量"""
        pattern = r'\{([^{}]+)\}'
        matches = re.findall(pattern, template)
        return list(set(matches))
