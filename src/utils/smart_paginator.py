from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EvidenceElement:
    """证据元素"""
    evidence_id: str
    title: str
    content: str
    element_type: str = "text"
    page_break_after: bool = True


@dataclass
class PDFElement:
    """PDF元素"""
    element_type: str
    content: Any
    style: Optional[Dict[str, Any]] = None
    page_break_after: bool = False


class SmartPaginator:
    """智能分页控制器"""

    def __init__(
        self,
        page_width: float = 595.0,
        page_height: float = 842.0,
        margin_left: float = 72.0,
        margin_right: float = 72.0,
        margin_top: float = 72.0,
        margin_bottom: float = 72.0
    ):
        """
        初始化智能分页控制器

        Args:
            page_width: 页面宽度（points，默认A4: 595）
            page_height: 页面高度（points，默认A4: 842）
            margin_left: 左边距
            margin_right: 右边距
            margin_top: 上边距
            margin_bottom: 下边距
        """
        self.page_width = page_width
        self.page_height = page_height
        self.margin_left = margin_left
        self.margin_right = margin_right
        self.margin_top = margin_top
        self.margin_bottom = margin_bottom

        self.elements: List[PDFElement] = []
        self.current_page = 0
        self.evidence_count = 0
        self._page_break_count = 0

    def add_evidence(
        self,
        evidence_id: str,
        elements: List[PDFElement],
        start_new_page: bool = True
    ) -> int:
        """
        添加证据（自动分页）

        Args:
            evidence_id: 证据ID
            elements: PDF元素列表
            start_new_page: 是否新起一页
        Returns:
            证据所在页码
        """
        if start_new_page and self.elements:
            self.elements.append(PDFElement(
                element_type="page_break",
                content=None,
                page_break_after=False
            ))
            self._page_break_count += 1

        for element in elements:
            self.elements.append(element)
            if element.page_break_after:
                self.elements.append(PDFElement(
                    element_type="page_break",
                    content=None,
                    page_break_after=False
                ))
                self._page_break_count += 1

        self.evidence_count += 1
        self.current_page = self._calculate_page_count()

        return self.current_page

    def add_element(
        self,
        element: PDFElement,
        check_page_break: bool = True
    ) -> int:
        """
        添加单个元素

        Args:
            element: PDF元素
            check_page_break: 是否检查分页
        Returns:
            当前页码
        """
        if check_page_break and self._needs_page_break(element):
            self.elements.append(PDFElement(
                element_type="page_break",
                content=None,
                page_break_after=False
            ))
            self._page_break_count += 1

        self.elements.append(element)

        return self._calculate_page_count()

    def _needs_page_break(self, element: PDFElement) -> bool:
        """检查是否需要分页"""
        if element.element_type == "page_break":
            return False

        if element.element_type in ["title", "table_title"]:
            return True

        return False

    def _calculate_page_count(self) -> int:
        """计算页码"""
        base_pages = 1
        return base_pages + self._page_break_count

    def build_pdf(self, doc_elements: List[PDFElement] = None) -> Dict[str, Any]:
        """
        构建PDF文档结构

        Args:
            doc_elements: 文档元素列表（如果为None则使用内部元素）
        Returns:
            PDF文档结构
        """
        if doc_elements is None:
            doc_elements = self.elements

        structure = {
            "page_info": {
                "width": self.page_width,
                "height": self.page_height,
                "margins": {
                    "left": self.margin_left,
                    "right": self.margin_right,
                    "top": self.margin_top,
                    "bottom": self.margin_bottom
                }
            },
            "elements": doc_elements,
            "statistics": {
                "total_elements": len(doc_elements),
                "total_pages": self._calculate_page_count(),
                "evidence_count": self.evidence_count,
                "page_breaks": self._page_break_count
            },
            "generated_at": datetime.now().isoformat()
        }

        return structure

    def get_page_content(self, page_num: int) -> List[PDFElement]:
        """
        获取指定页面的内容

        Args:
            page_num: 页码（从1开始）
        Returns:
            页面元素列表
        """
        if page_num < 1:
            return []

        current_page = 0
        page_elements = []
        in_page = False

        for element in self.elements:
            if element.element_type == "page_break":
                current_page += 1
                in_page = False
                continue

            if current_page + 1 == page_num:
                in_page = True
                page_elements.append(element)

        return page_elements

    def reset(self):
        """重置分页器"""
        self.elements = []
        self.current_page = 0
        self.evidence_count = 0
        self._page_break_count = 0

    def set_page_size(
        self,
        width: float,
        height: float,
        margin_left: float = None,
        margin_right: float = None,
        margin_top: float = None,
        margin_bottom: float = None
    ):
        """
        设置页面大小

        Args:
            width: 页面宽度
            height: 页面高度
            margin_left: 左边距（可选）
            margin_right: 右边距（可选）
            margin_top: 上边距（可选）
            margin_bottom: 下边距（可选）
        """
        self.page_width = width
        self.page_height = height

        if margin_left is not None:
            self.margin_left = margin_left
        if margin_right is not None:
            self.margin_right = margin_right
        if margin_top is not None:
            self.margin_top = margin_top
        if margin_bottom is not None:
            self.margin_bottom = margin_bottom

    def insert_page_break(self, position: int = None) -> bool:
        """
        插入分页符

        Args:
            position: 插入位置（如果为None则插入到末尾）
        Returns:
            是否成功
        """
        page_break = PDFElement(
            element_type="page_break",
            content=None,
            page_break_after=False
        )

        if position is None:
            self.elements.append(page_break)
        elif 0 <= position <= len(self.elements):
            self.elements.insert(position, page_break)
        else:
            return False

        self._page_break_count += 1
        return True

    def add_cover_page(
        self,
        title: str,
        subtitle: str = "",
        case_no: str = ""
    ) -> int:
        """
        添加封面页

        Args:
            title: 标题
            subtitle: 副标题
            case_no: 案号
        Returns:
            封面页页码
        """
        cover_elements = [
            PDFElement(
                element_type="title",
                content=title,
                style={
                    "font_size": 24,
                    "font_name": "SimHei",
                    "alignment": "center",
                    "text_color": "#000000"
                }
            ),
            PDFElement(
                element_type="text",
                content=subtitle,
                style={
                    "font_size": 14,
                    "font_name": "SimSun",
                    "alignment": "center",
                    "space_after": 50
                }
            )
        ]

        if case_no:
            cover_elements.append(PDFElement(
                element_type="text",
                content=f"案号：{case_no}",
                style={
                    "font_size": 12,
                    "font_name": "SimSun",
                    "alignment": "center"
                }
            ))

        return self.add_evidence(
            evidence_id="cover",
            elements=cover_elements,
            start_new_page=False
        )
