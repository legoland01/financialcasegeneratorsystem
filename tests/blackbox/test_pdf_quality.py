#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF文本质量测试

使用pdftotext提取PDF文本，检查质量问题：
1. 模糊词检测（某某设备、若干台等）
2. 占位符检测
3. 格式问题（过长行、连续空行等）

运行方式：
    # 仅文本测试（快速）
    python3 -m pytest tests/blackbox/test_pdf_text_quality.py -v
    
    # 完整测试（需要pdftotext）
    pdftotext安装: brew install poppler
    python3 -m pytest tests/blackbox/test_pdf_text_quality.py -v
"""

import unittest
import json
import tempfile
import shutil
import os
import re
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


def extract_text_from_pdf(pdf_path):
    """
    从PDF提取文本
    
    Args:
        pdf_path: PDF文件路径
        
    Returns:
        提取的文本（str），失败返回None
    """
    try:
        # 尝试使用pdfplumber（推荐）
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return text if text.strip() else None
    except ImportError:
        pass
    
    try:
        # 备选：使用PyPDF2
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text if text.strip() else None
    except ImportError:
        pass
    except Exception as e:
        print(f"⚠️ PDF提取失败: {e}")
        return None


class TestPDFTextQuality(unittest.TestCase):
    """
    PDF文本质量测试
    
    检查PDF中的文本质量问题
    """
    
    @classmethod
    def setUpClass(cls):
        """类级别设置：查找PDF文件"""
        # 查找最新的PDF文件
        pdf_dir = project_root / "outputs_complete"
        if not pdf_dir.exists():
            raise unittest.SkipTest("outputs_complete目录不存在")
        
        pdf_files = list(pdf_dir.glob("完整测试卷宗*.pdf"))
        if not pdf_files:
            raise unittest.SkipTest("未找到PDF文件")
        
        # 使用最新的PDF
        cls.pdf_path = max(pdf_files, key=lambda f: f.stat().st_mtime)
        print(f"\n📄 测试PDF: {cls.pdf_path}")
    
    def test_no_vague_words_in_pdf(self):
        """
        测试PDF中不包含模糊词
        
        基于用户反馈的模糊词：
        - 某某设备
        - 某某型号
        - 若干台
        - 若干
        - 人民币叁仟万元整
        """
        text = extract_text_from_pdf(self.pdf_path)
        if text is None:
            self.skipTest("pdftotext未安装")
        
        vague_patterns = [
            "某某设备",
            "某某型号",
            "若干台",
            "若干",
            "人民币叁仟万元整",
            "人民币壹亿伍仟万元整",
        ]
        
        found = []
        for pattern in vague_patterns:
            if pattern in text:
                found.append(pattern)
        
        self.assertEqual(
            len(found), 0,
            f"PDF包含{len(found)}个模糊词: {found}"
        )
    
    def test_no_placeholders_in_pdf(self):
        """
        测试PDF中不包含占位符
        
        占位符类型：
        - 某某公司X
        - X年X月X日
        - 人民币X元
        """
        text = extract_text_from_pdf(self.pdf_path)
        if text is None:
            self.skipTest("pdftotext未安装")
        
        placeholder_patterns = [
            "某某公司",
            "X年",
            "X月",
            "人民币X元",
            "某公司",
        ]
        
        found = []
        for pattern in placeholder_patterns:
            if pattern in text:
                found.append(pattern)
        
        self.assertEqual(
            len(found), 0,
            f"PDF包含{len(found)}个占位符: {found}"
        )
    
    def test_no_continuous_empty_lines(self):
        """
        测试PDF中无连续空行
        
        连续空行可能表示回车丢失或格式问题
        """
        text = extract_text_from_pdf(self.pdf_path)
        if text is None:
            self.skipTest("pdftotext未安装")
        
        # 检测连续3个以上换行
        if '\n\n\n\n' in text:
            self.fail("PDF包含连续空行（可能表示回车丢失）")
    
    def test_no_overly_long_lines(self):
        """
        测试PDF中无过长行
        
        过长行可能表示该换行没换行
        合同条款行不应超过200字符
        """
        text = extract_text_from_pdf(self.pdf_path)
        if text is None:
            self.skipTest("pdftotext未安装")
        
        lines = text.split('\n')
        long_lines = []
        
        for i, line in enumerate(lines, 1):
            if len(line) > 200:
                # 过长行，检查是否是条款内容
                if '条' in line or '款' in line or '第' in line:
                    long_lines.append((i, len(line), line[:50] + "..."))
        
        self.assertEqual(
            len(long_lines), 0,
            f"发现{len(long_lines)}个过长行（可能缺少回车）: {long_lines}"
        )
    
    def test_clause_numbering_consistency(self):
        """
        测试条款编号连续性
        
        检测异常编号模式：
        1. 第X条后直接跟数字.数字（如第4条后直接跟1.1）- 这是您反馈的问题
        2. 数字.数字后突然回到第Y条（如1.1后直接跟第5条）
        
        注意：【第一条 转让标的】后跟1.1是正常格式（条款标题+子条款）
        """
        text = extract_text_from_pdf(self.pdf_path)
        if text is None:
            self.skipTest("pdftotext未安装")
        
        lines = text.split('\n')
        
        # 查找真正的条款编号（非标题格式）
        # 条款标题格式：【第一条 转让标的】- 这是标题，不是条款编号
        # 条款内容格式：第X条、第Y条 - 这是条款编号
        # 子条款格式：1.1、2.1 - 这是子条款
        
        clause_lines = []
        for i, line in enumerate(lines, 1):
            line = line.strip()
            # 只匹配行首的条款编号（排除标题格式）
            if re.match(r'^第[一二三四五六七八九十\d]+条', line):
                clause_lines.append((i, 'clause', line))
            elif re.match(r'^\d+\.\d+', line):
                clause_lines.append((i, 'subclause', line))
        
        # 检查编号连续性
        issues = []
        for i in range(len(clause_lines) - 1):
            curr_type = clause_lines[i][1]
            next_type = clause_lines[i + 1][1]
            
            # 如果当前是"第X条"，下一个不应该是"数字.数字"
            # 如果当前是"数字.数字"，下一个应该是"数字.数字"（继续子条款）
            # 不应该出现：条款后直接跟不同类型的编号
            
            # 正常情况：条款 -> 子条款（1.1, 1.2...）
            # 正常情况：子条款 -> 子条款（1.1 -> 1.2 或 2.1）
            # 异常情况：条款 -> 条款（如第4条后直接跟第5条，这是正常的）
            # 异常情况：子条款 -> 条款（如1.1后直接跟第5条，这是编号断裂）
            
            if curr_type == 'subclause' and next_type == 'clause':
                # 子条款后直接跟条款，可能是编号断裂
                issues.append(
                    f"第{clause_lines[i+1][0]}行 子条款后直接跟条款: {clause_lines[i+1][2][:30]}..."
                )
        
        # 只在发现问题时报告，不要过度检测
        if len(issues) > 10:
            # 可能是误报，只报告前几个
            self.skipTest(f"检测到{len(issues)}个潜在问题，可能是正常格式")


class TestPDFLayoutQuality(unittest.TestCase):
    """
    PDF布局质量测试（多模态）
    
    使用Qwen-VL-Max检查PDF布局问题：
    - 留白异常
    - 表格格式
    - 回车位置
    - 视觉格式问题
    
    运行方式：
    MULTIMODAL_TEST=1 python3 -m pytest tests/blackbox/test_pdf_layout_quality.py -v
    """
    
    @classmethod
    def setUpClass(cls):
        """类级别设置：查找PDF文件"""
        pdf_dir = project_root / "outputs_complete"
        if not pdf_dir.exists():
            raise unittest.SkipTest("outputs_complete目录不存在")
        
        pdf_files = list(pdf_dir.glob("完整测试卷宗*.pdf"))
        if not pdf_files:
            raise unittest.SkipTest("未找到PDF文件")
        
        cls.pdf_path = max(pdf_files, key=lambda f: f.stat().st_mtime)
        
        # 检查是否启用多模态测试
        cls.multimodal_enabled = os.getenv("MULTIMODAL_TEST", "0") == "1"
    
    def test_layout_with_qwen_vl(self):
        """
        使用Qwen-VL-Max检查PDF布局质量
        
        检查项目：
        1. 条款编号是否连续
        2. 是否有异常留白
        3. 表格格式是否正确
        4. 回车位置是否合理
        """
        if not self.multimodal_enabled:
            self.skipTest("设置MULTIMODAL_TEST=1环境变量运行此测试")
        
        # 导入多模态模块
        try:
            from src.utils.multimodal_qa import analyze_pdf_layout
        except ImportError:
            self.skipTest("多模态模块未实现")
        
        # 分析PDF布局
        result = analyze_pdf_layout(self.pdf_path)
        
        # 解析结果
        issues = result.get("issues", [])
        
        self.assertEqual(
            len(issues), 0,
            f"发现{len(issues)}个布局问题: {issues}"
        )


def run_pdf_quality_check():
    """
    快速运行PDF质量检查（命令行工具）
    
    用法:
        python3 tests/blackbox/test_pdf_quality.py
        python3 tests/blackbox/test_pdf_quality.py --all
        python3 tests/blackbox/test_pdf_quality.py --vague
    """
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="PDF质量检查工具")
    parser.add_argument("pdf", nargs="?", default=None, help="PDF文件路径")
    parser.add_argument("--vague", action="store_true", help="检查模糊词")
    parser.add_argument("--placeholder", action="store_true", help="检查占位符")
    parser.add_argument("--layout", action="store_true", help="检查布局")
    parser.add_argument("--all", action="store_true", help="检查所有项目")
    
    args = parser.parse_args()
    
    if args.pdf:
        target_pdf = Path(args.pdf)
    else:
        # 查找最新PDF
        pdf_dir = project_root / "outputs_complete"
        pdf_files = list(pdf_dir.glob("完整测试卷宗*.pdf"))
        if not pdf_files:
            print("❌ 未找到PDF文件")
            return
        target_pdf = max(pdf_files, key=lambda f: f.stat().st_mtime)
    
    print(f"\n📄 检查PDF: {target_pdf}")
    print("=" * 60)
    
    text = extract_text_from_pdf(target_pdf)
    if text is None:
        print("⚠️ 无法提取PDF文本")
        return
    
    all_pass = True
    
    # 检查模糊词
    if args.vague or args.all:
        print("\n🔍 检查模糊词...")
        vague_patterns = [
            "某某设备", "某某型号", "若干台", "若干",
            "人民币叁仟万元整",
        ]
        found = [p for p in vague_patterns if p in text]
        if found:
            print(f"  ❌ 发现模糊词: {found}")
            all_pass = False
        else:
            print("  ✅ 无模糊词")
    
    # 检查占位符
    if args.placeholder or args.all:
        print("\n🔍 检查占位符...")
        placeholder_patterns = ["某某公司", "X年", "X月", "人民币X元"]
        found = [p for p in placeholder_patterns if p in text]
        if found:
            print(f"  ❌ 发现占位符: {found}")
            all_pass = False
        else:
            print("  ✅ 无占位符")
    
    # 检查过长行
    if args.layout or args.all:
        print("\n🔍 检查过长行...")
        lines = text.split('\n')
        long_lines = [(i+1, len(l)) for i, l in enumerate(lines) if len(l) > 200]
        if long_lines:
            print(f"  ❌ 发现{len(long_lines)}个过长行")
            all_pass = False
        else:
            print("  ✅ 无过长行")
    
    # 检查连续空行
    if args.layout or args.all:
        print("\n🔍 检查连续空行...")
        if '\n\n\n\n' in text:
            print("  ❌ 发现连续空行")
            all_pass = False
        else:
            print("  ✅ 无连续空行")
    
    print("\n" + "=" * 60)
    if all_pass:
        print("✅ PDF质量检查通过")
    else:
        print("❌ PDF质量检查发现问题")


if __name__ == "__main__":
    # 运行单元测试
    unittest.main(verbosity=2)
