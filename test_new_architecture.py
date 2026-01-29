#!/usr/bin/env python3
"""测试新架构功能：证据文件生成和PDF生成"""

import json
import os
from pathlib import Path
from loguru import logger
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.services.evidence_file_generator import EvidenceFileGenerator
from src.utils.pdf_generator_simple import PDFGeneratorSimple
from src.utils import load_json


def test_evidence_file_generator():
    """测试证据文件生成器"""
    logger.info("=" * 60)
    logger.info("测试1: 证据文件生成器")
    logger.info("=" * 60)
    
    # 加载阶段0数据
    stage0_dir = project_root / "outputs" / "stage0"
    stage0_data = {}
    
    for f in stage0_dir.glob("*.json"):
        key = f.stem
        with open(f, 'r', encoding='utf-8') as file:
            stage0_data[key] = json.load(file)
    
    logger.info(f"加载了 {len(stage0_data)} 个阶段0数据文件")
    
    # 加载证据规划
    evidence_planning = stage0_data.get("0.5_evidence_planning", {})
    
    if not evidence_planning:
        logger.error("未找到证据归属规划数据")
        return False
    
    # 创建证据文件生成器
    output_dir = project_root / "outputs_new" / "stage1"
    generator = EvidenceFileGenerator(
        prompt_dir=str(project_root / "prompts"),
        output_dir=str(output_dir)
    )
    
    # 生成原告证据文件
    evidence_index = generator.generate_all_evidence_files(
        stage0_data=stage0_data,
        evidence_planning=evidence_planning,
        party="原告"
    )
    
    # 保存证据索引
    index_path = output_dir / "evidence_index.json"
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(evidence_index, f, ensure_ascii=False, indent=2)
    
    logger.success(f"证据索引已保存: {index_path}")
    
    # 验证生成的证据文件
    evidence_dir = output_dir / "evidence"
    if evidence_dir.exists():
        evidence_files = list(evidence_dir.rglob("*.txt"))
        logger.info(f"共生成 {len(evidence_files)} 个证据文件")
        
        for f in evidence_files[:5]:  # 显示前5个
            logger.info(f"  - {f.name} ({f.stat().st_size} bytes)")
        
        if len(evidence_files) > 5:
            logger.info(f"  ... 等共 {len(evidence_files)} 个文件")
    
    # 验证证据索引内容
    logger.info(f"证据索引: {evidence_index['证据总数']} 个证据, {evidence_index['证据组数']} 个证据组")
    
    # 验证证据组
    for group in evidence_index.get("证据组列表", []):
        logger.info(f"  证据组{group['组编号']}: {group['组名称']} ({group['证据数量']}个证据)")
    
    logger.success("证据文件生成测试通过")
    return True


def test_pdf_generator():
    """测试PDF生成器"""
    logger.info("=" * 60)
    logger.info("测试2: PDF生成器")
    logger.info("=" * 60)
    
    # 加载阶段0数据
    stage0_dir = project_root / "outputs" / "stage0"
    stage0_data = {}
    
    for f in stage0_dir.glob("*.json"):
        key = f.stem
        with open(f, 'r', encoding='utf-8') as file:
            stage0_data[key] = json.load(file)
    
    # 加载证据索引
    output_dir = project_root / "outputs_new" / "stage1"
    index_path = output_dir / "evidence_index.json"
    
    if not index_path.exists():
        logger.error(f"证据索引文件不存在: {index_path}")
        return False
    
    with open(index_path, 'r', encoding='utf-8') as f:
        evidence_index = json.load(f)
    
    # 创建PDF生成器
    pdf_path = project_root / "outputs_new" / "完整测试卷宗_新架构.pdf"
    pdf_generator = PDFGeneratorSimple(str(pdf_path), stage0_data)
    
    # 读取起诉状和程序性文件
    complaint_path = project_root / "outputs" / "stage1" / "民事起诉状.txt"
    procedural_path = project_root / "outputs" / "stage1" / "原告程序性文件.txt"
    
    complaint_text = ""
    if complaint_path.exists():
        complaint_text = complaint_path.read_text(encoding='utf-8')
        logger.info(f"加载起诉状: {len(complaint_text)} 字符")
    
    procedural_text = ""
    if procedural_path.exists():
        procedural_text = procedural_path.read_text(encoding='utf-8')
        logger.info(f"加载程序性文件: {len(procedural_text)} 字符")
    
    # 生成PDF
    pdf_generator.generate_complete_docket(
        stage0_data=stage0_data,
        evidence_index=evidence_index,
        complaint_text=complaint_text,
        procedural_text=procedural_text
    )
    
    # 验证PDF文件
    if pdf_path.exists():
        logger.success(f"PDF已生成: {pdf_path} ({pdf_path.stat().st_size} bytes)")
    else:
        logger.error("PDF文件未生成")
        return False
    
    logger.success("PDF生成测试通过")
    return True


def test_file_structure():
    """测试文件结构是否符合新架构规范"""
    logger.info("=" * 60)
    logger.info("测试3: 文件结构验证")
    logger.info("=" * 60)
    
    output_dir = project_root / "outputs_new" / "stage1"
    
    # 检查必要文件
    checks = [
        ("证据索引文件", output_dir / "evidence_index.json"),
        ("证据目录", output_dir / "evidence"),
        ("PDF文件", output_dir.parent / "完整测试卷宗_新架构.pdf"),
    ]
    
    for name, path in checks:
        if path.exists():
            logger.success(f"✓ {name} 存在: {path}")
        else:
            logger.error(f"✗ {name} 不存在: {path}")
            return False
    
    # 检查证据文件命名规范
    evidence_dir = output_dir / "evidence"
    if evidence_dir.exists():
        txt_files = list(evidence_dir.rglob("*.txt"))
        logger.info(f"共 {len(txt_files)} 个证据文件")
        
        # 验证命名规范: 证据组{组号}_{证据ID}_{证据名称简写}.txt
        import re
        pattern = re.compile(r'^证据组(\d+)_E(\d{3})_.+\.txt$')
        
        valid_count = 0
        for f in txt_files:
            if re.match(r'^证据组\d+_E\d{3}_.+\.txt$', f.name):
                valid_count += 1
            else:
                logger.warning(f"  文件命名不符合规范: {f.name}")
        
        logger.info(f"  {valid_count}/{len(txt_files)} 个文件命名符合规范")
    
    logger.success("文件结构验证测试通过")
    return True


def main():
    """主测试函数"""
    logger.remove()
    logger.add(sys.stdout, level="INFO")
    
    logger.info("")
    logger.info("=" * 60)
    logger.info("新架构功能测试")
    logger.info("=" * 60)
    logger.info("")
    
    results = []
    
    # 测试1: 证据文件生成器
    try:
        results.append(("证据文件生成器", test_evidence_file_generator()))
    except Exception as e:
        logger.error(f"证据文件生成器测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("证据文件生成器", False))
    
    logger.info("")
    
    # 测试2: PDF生成器
    try:
        results.append(("PDF生成器", test_pdf_generator()))
    except Exception as e:
        logger.error(f"PDF生成器测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("PDF生成器", False))
    
    logger.info("")
    
    # 测试3: 文件结构验证
    try:
        results.append(("文件结构验证", test_file_structure()))
    except Exception as e:
        logger.error(f"文件结构验证测试失败: {e}")
        import traceback
        traceback.print_exc()
        results.append(("文件结构验证", False))
    
    # 输出测试结果汇总
    logger.info("")
    logger.info("=" * 60)
    logger.info("测试结果汇总")
    logger.info("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        logger.info(f"{status} - {name}")
        if success:
            passed += 1
        else:
            failed += 1
    
    logger.info("")
    logger.info(f"总计: {passed} 个测试通过, {failed} 个测试失败")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
