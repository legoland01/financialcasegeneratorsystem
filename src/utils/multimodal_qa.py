#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态质量检测模块

使用Qwen-VL-Max分析PDF布局问题：
- 条款编号连续性
- 留白异常
- 表格格式
- 回车位置

依赖：
- siliconflow API密钥
- 阿里Qwen-VL-Max模型
"""

import json
import base64
import requests
from pathlib import Path
from typing import Dict, List, Optional
import os


class MultimodalQA:
    """
    多模态质量检测器
    """
    
    def __init__(self, api_key: str = None):
        """
        初始化多模态检测器
        
        Args:
            api_key: SiliconFlow API密钥，默认为环境变量SILICONFLOW_API_KEY
        """
        self.api_key = api_key or os.getenv("SILICONFLOW_API_KEY")
        self.api_url = "https://api.siliconflow.cn/v1/chat/completions"
        self.model = "Qwen/Qwen-VL-Max"
    
    def _encode_image(self, image_path: str) -> str:
        """
        将图片编码为base64
        
        Args:
            image_path: 图片路径
            
        Returns:
            base64编码的字符串
        """
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def _pdf_to_image(self, pdf_path: str, output_dir: str = None) -> str:
        """
        将PDF转换为图片（截取第一页）
        
        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录
            
        Returns:
            生成的图片路径
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            print("⚠️ PyMuPDF未安装，请安装: pip install pymupdf")
            return None
        
        pdf_doc = fitz.open(pdf_path)
        page = pdf_doc[0]  # 只截取第一页用于预览
        
        # 设置输出路径
        if output_dir is None:
            output_dir = os.path.dirname(pdf_path)
        
        output_path = os.path.join(
            output_dir,
            f"{Path(pdf_path).stem}_preview.png"
        )
        
        # 渲染为图片
        zoom = 2  # 放大2倍，提高清晰度
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        pix.save(output_path)
        
        pdf_doc.close()
        
        return output_path
    
    def analyze_pdf_layout(self, pdf_path: str) -> Dict:
        """
        分析PDF布局质量
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            {
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "API密钥未配置",
                "issues": []
            }
        
        # 转换为图片
        image_path = self._pdf_to_image(pdf_path)
        if image_path is None:
            return {
                "success": False,
                "error": "PDF转图片失败",
                "issues": []
            }
        
        # 编码图片
        base64_image = self._encode_image(image_path)
        
        # 构建提示词
        prompt = """
你是一个法律文档格式审查专家。请仔细检查这份法律合同的格式问题，特别关注：

1. **条款编号连续性**：
   - 条款编号应该是连续的（如第1条、第2条、第3条...）
   - 检测是否出现编号断裂（如第4条后突然变成1.1，或者1.1后直接跟第5条）

2. **留白异常**：
   - 检测是否存在异常的空白区域
   - 检测是否存在过长的空白行

3. **回车位置**：
   - 检测条款内容是否正常换行
   - 检测是否存在应该换行但没有换行的情况（行过长）
   - 检测是否存在不应该换行的地方被错误换行

4. **格式问题**：
   - 检测括号使用是否正确
   - 检测标点符号使用是否规范
   - 检测列表格式是否一致

请用JSON格式返回分析结果：
```json
{
    "overall_quality": "good/fair/poor",
    "issue_count": 0,
    "issues": [
        {
            "type": "clause_numbering/layout/whitespace/line_break/format",
            "severity": "high/medium/low",
            "description": "问题的详细描述",
            "location": "具体位置描述"
        }
    ],
    "summary": "格式质量的简要总结"
}
```

只返回JSON，不要返回其他内容。
"""
        
        # 调用API
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.1
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 解析响应
            content = result["choices"][0]["message"]["content"]
            
            # 提取JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            analysis = json.loads(content.strip())
            
            # 清理临时图片
            if os.path.exists(image_path):
                os.remove(image_path)
            
            return {
                "success": True,
                "analysis": analysis,
                "issues": analysis.get("issues", [])
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"API调用失败: {str(e)}",
                "issues": []
            }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON解析失败: {str(e)}, 原始响应: {content[:500]}",
                "issues": []
            }


def analyze_pdf_layout(pdf_path: str) -> Dict:
    """
    便捷函数：分析PDF布局质量
    
    Args:
        pdf_path: PDF文件路径
        
    Returns:
        分析结果字典
    """
    qa = MultimodalQA()
    return qa.analyze_pdf_layout(pdf_path)


# 测试代码
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PDF布局质量检测")
    parser.add_argument("pdf", nargs="?", default=None, help="PDF文件路径")
    parser.add_argument("--api-key", default=None, help="SiliconFlow API密钥")
    
    args = parser.parse_args()
    
    if not args.pdf:
        # 查找最新PDF
        pdf_dir = Path("outputs_complete")
        pdf_files = list(pdf_dir.glob("完整测试卷宗*.pdf"))
        if not pdf_files:
            print("❌ 未找到PDF文件")
            exit(1)
        pdf_path = str(max(pdf_files, key=lambda f: f.stat().st_mtime))
    else:
        pdf_path = args.pdf
    
    print(f"\n📄 分析PDF: {pdf_path}")
    print("=" * 60)
    
    # 使用API密钥
    api_key = args.api_key or os.getenv("SILICONFLOW_API_KEY")
    if not api_key:
        print("⚠️ 请设置SILICONFLOW_API_KEY环境变量或使用--api-key参数")
        exit(1)
    
    result = analyze_pdf_layout(pdf_path)
    
    if result["success"]:
        analysis = result["analysis"]
        print(f"\n📊 质量评估: {analysis.get('overall_quality', 'unknown')}")
        print(f"发现 {len(result['issues'])} 个问题")
        
        for issue in result["issues"][:5]:  # 只显示前5个
            print(f"\n  [{issue.get('severity', '?')}] {issue.get('type', 'unknown')}")
            print(f"    {issue.get('description', '')}")
        
        if len(result['issues']) > 5:
            print(f"\n  ... 还有 {len(result['issues']) - 5} 个问题")
        
        print(f"\n📝 总结: {analysis.get('summary', '')}")
    else:
        print(f"❌ 分析失败: {result.get('error', '未知错误')}")
