from typing import List, Dict, Any, Optional


class TableRenderer:
    """表格渲染器 - 渲染表格格式到PDF元素"""

    def __init__(self):
        """初始化表格渲染器"""
        pass

    def render(
        self,
        title: str,
        headers: List[str],
        rows: List[List[Any]]
    ) -> Dict[str, Any]:
        """
        渲染表格格式

        Args:
            title: 表格标题
            headers: 表头
            rows: 数据行
        Returns:
            渲染后的表格数据
        """
        result = {
            "title": title,
            "headers": headers,
            "rows": rows,
            "style": self._get_default_style()
        }

        return result

    def render_from_dict(
        self,
        title: str,
        data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        从字典列表渲染表格

        Args:
            title: 表格标题
            data: 字典列表
        Returns:
            渲染后的表格数据
        """
        if not data:
            return {
                "title": title,
                "headers": [],
                "rows": [],
                "style": self._get_default_style()
            }

        headers = list(data[0].keys())
        rows = [[str(item.get(h, "")) for h in headers] for item in data]

        return self.render(title, headers, rows)

    def _get_default_style(self) -> Dict[str, Any]:
        """获取默认样式"""
        return {
            "header_background": "#E0E0E0",
            "header_text_color": "#000000",
            "header_font_name": "SimHei",
            "header_font_size": 10,
            "body_font_name": "SimSun",
            "body_font_size": 9,
            "alternating_row_colors": ["#FFFFFF", "#F5F5F5"],
            "grid_color": "#000000",
            "grid_width": 0.5,
            "alignment": "center",
            "header_alignment": "center"
        }

    def format_title(self, title: str, font_size: int = 14) -> Dict[str, Any]:
        """格式化表格标题"""
        return {
            "type": "table_title",
            "text": title,
            "font_size": font_size,
            "font_name": "SimHei",
            "alignment": "left"
        }

    def format_header(self, headers: List[str]) -> Dict[str, Any]:
        """格式化表头"""
        return {
            "type": "table_header",
            "headers": headers,
            "style": self._get_default_style()
        }

    def format_row(
        self,
        row: List[Any],
        row_index: int,
        style: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """格式化数据行"""
        if style is None:
            style = self._get_default_style()

        alt_colors = style.get("alternating_row_colors", ["#FFFFFF", "#F5F5F5"])
        bg_color = alt_colors[row_index % len(alt_colors)]

        return {
            "type": "table_row",
            "data": [str(cell) for cell in row],
            "background_color": bg_color,
            "style": style
        }

    def format_cell(
        self,
        value: Any,
        row: int,
        col: int,
        style: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """格式化单元格"""
        if style is None:
            style = self._get_default_style()

        alt_colors = style.get("alternating_row_colors", ["#FFFFFF", "#F5F5F5"])
        bg_color = alt_colors[row % len(alt_colors)]

        return {
            "type": "table_cell",
            "value": str(value),
            "row": row,
            "col": col,
            "background_color": bg_color,
            "font_name": style.get("body_font_name", "SimSun"),
            "font_size": style.get("body_font_size", 9),
            "alignment": style.get("alignment", "center")
        }

    def calculate_column_widths(
        self,
        headers: List[str],
        rows: List[List[Any]],
        page_width: float = 595.0,
        margins: float = 72.0
    ) -> List[float]:
        """
        计算列宽

        Args:
            headers: 表头
            rows: 数据行
            page_width: 页面宽度（points）
            margins: 页边距（points）
        Returns:
            列宽列表
        """
        available_width = page_width - 2 * margins

        col_widths = [len(str(h)) for h in headers]

        for row in rows:
            for i, cell in enumerate(row):
                cell_len = len(str(cell))
                if cell_len > col_widths[i]:
                    col_widths[i] = cell_len

        total_chars = sum(col_widths)
        if total_chars == 0:
            return [available_width / len(headers)] * len(headers)

        col_widths = [
            (w / total_chars) * available_width
            for w in col_widths
        ]

        return col_widths

    def apply_zebra_striping(
        self,
        rows: List[List[Any]],
        odd_color: str = "#FFFFFF",
        even_color: str = "#F5F5F5"
    ) -> List[Dict[str, Any]]:
        """应用斑马纹"""
        styled_rows = []
        for i, row in enumerate(rows):
            bg_color = even_color if i % 2 == 0 else odd_color
            styled_rows.append({
                "data": [str(cell) for cell in row],
                "background_color": bg_color
            })
        return styled_rows

    def merge_cells(
        self,
        rows: List[List[Any]],
        merge_regions: List[Dict[str, int]]
    ) -> List[Dict[str, Any]]:
        """
        合并单元格

        Args:
            rows: 数据行
            merge_regions: 合并区域 [(start_row, end_row, start_col, end_col), ...]
        Returns:
            合并后的数据
        """
        from copy import deepcopy
        result = deepcopy(rows)

        for region in merge_regions:
            sr = region.get("start_row", 0)
            er = region.get("end_row", sr)
            sc = region.get("start_col", 0)
            ec = region.get("end_col", sc)

            if er >= len(result):
                er = len(result) - 1
            if ec >= len(result[0]) if result else 0:
                ec = len(result[0]) - 1 if result else 0

            value = result[sr][sc] if result and sr < len(result) else ""
            for r in range(sr, er + 1):
                for c in range(sc, ec + 1):
                    if r == sr and c == sc:
                        result[r][c] = {"value": value, "rowspan": er - sr + 1, "colspan": ec - sc + 1}
                    else:
                        result[r][c] = None

        return result
