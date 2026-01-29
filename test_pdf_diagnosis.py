#!/usr/bin/env python3
"""测试PDF生成问题"""
import sys
import traceback
from pathlib import Path

# 添加src到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# 设置环境变量
import os
os.environ["OPENAI_API_KEY"] = "sk-fjephnssumhgkxhakpxlfrqayiuckkyogvwkchqutqolqilk"
os.environ["OPENAI_API_BASE"] = "https://api.siliconflow.cn/v1"
os.environ["OPENAI_MODEL"] = "deepseek-ai/DeepSeek-V3.2"

def test_pdf_generation():
    """测试PDF生成"""
    try:
        print("=" * 60)
        print("PDF生成问题诊断")
        print("=" * 60)
        
        # 加载阶段0数据
        print("1. 加载阶段0数据...")
        from src.utils import load_json
        
        stage0_file = Path("outputs/stage0/0.1_structured_extraction.json")
        if not stage0_file.exists():
            print(f"❌ 阶段0文件不存在: {stage0_file}")
            return False
        
        stage0_data = load_json(str(stage0_file))
        print(f"✅ 阶段0数据加载成功，包含 {len(stage0_data)} 个字段")
        
        # 加载证据索引
        print("\n2. 加载证据索引...")
        evidence_index_file = Path("outputs/stage1/evidence/evidence_index.json")
        if not evidence_index_file.exists():
            print(f"❌ 证据索引文件不存在: {evidence_index_file}")
            return False
        
        evidence_index = load_json(str(evidence_index_file))
        print(f"✅ 证据索引加载成功，包含 {evidence_index.get('证据总数', 0)} 个证据")
        
        # 加载起诉状
        print("\n3. 加载起诉状...")
        complaint_file = Path("outputs/stage1/民事起诉状.txt")
        if not complaint_file.exists():
            print(f"❌ 起诉状文件不存在: {complaint_file}")
            return False
        
        complaint_text = complaint_file.read_text(encoding='utf-8')
        print(f"✅ 起诉状加载成功，长度: {len(complaint_text)} 字符")
        
        # 加载程序性文件
        print("\n4. 加载程序性文件...")
        procedural_file = Path("outputs/stage1/原告程序性文件.txt")
        if procedural_file.exists():
            procedural_text = procedural_file.read_text(encoding='utf-8')
            print(f"✅ 程序性文件加载成功，长度: {len(procedural_text)} 字符")
        else:
            procedural_text = ""
            print("⚠️ 程序性文件不存在，使用空字符串")
        
        # 测试PDF生成器
        print("\n5. 测试PDF生成器...")
        from src.utils.pdf_generator_simple import PDFGeneratorSimple
        
        output_path = Path("outputs/test_诊断PDF.pdf")
        pdf_generator = PDFGeneratorSimple(str(output_path), stage0_data)
        
        # 尝试生成PDF
        try:
            pdf_generator.generate_complete_docket(
                stage0_data=stage0_data,
                evidence_index=evidence_index,
                complaint_text=complaint_text,
                procedural_text=procedural_text
            )
            print(f"✅ PDF生成成功: {output_path}")
            
            if output_path.exists():
                file_size = output_path.stat().st_size
                print(f"✅ PDF文件大小: {file_size} 字节")
            
            return True
            
        except Exception as e:
            print(f"❌ PDF生成失败: {e}")
            print("详细错误:")
            traceback.print_exc()
            return False
            
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_pdf_generation()
    if success:
        print("\n🎉 PDF生成测试成功！")
    else:
        print("\n💥 PDF生成测试失败！")
    
    sys.exit(0 if success else 1)