#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新架构证据生成专用脚本
专门用于运行新架构的证据生成，每个证据独立文件
"""

import sys
import json
from pathlib import Path

# 添加src到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from loguru import logger
from src.services.evidence_file_generator import EvidenceFileGenerator
from src.services.stage0.stage0_service import Stage0Service
from src.services.stage1.stage1_service import Stage1Service
from src.utils import LLMClient

def run_new_architecture_generation():
    """运行新架构证据生成"""
    logger.info("🚀 开始新架构证据生成流程")
    
    try:
        # 步骤1: 运行阶段0分析（如果还没有结果）
        stage0_dir = Path("outputs/stage0")
        if not (stage0_dir / "0.5_evidence_planning.json").exists():
            logger.info("📋 执行阶段0分析...")
            stage0_service = Stage0Service()
            
            # 使用测试判决书
            judgment_path = Path("测试用判决书/(2024)沪74民初245号.pdf")
            if not judgment_path.exists():
                # 尝试其他可能的路径
                judgment_path = Path("/Users/liuzhen/Documents/河广/Product Development/chatGPT/Digital Law/Digital court/金融法院/法官数字助手/案卷材料样例/融资租赁/(2024)沪74民初721号/OpenCode Trial/测试用判决书/(2024)沪74民初245号.pdf")
            
            if judgment_path.exists():
                stage0_result = stage0_service.run_all(str(judgment_path))
                logger.info("✅ 阶段0分析完成")
            else:
                logger.error("❌ 未找到判决书文件")
                return False
        else:
            logger.info("📋 阶段0数据已存在，跳过分析")
        
        # 步骤2: 构建完整的阶段0数据结构
        logger.info("📂 加载阶段0数据...")
        stage0_data = {
            "0.1_structured_extraction": json.loads((stage0_dir / "0.1_structured_extraction.json").read_text()),
            "0.2_anonymization_plan": json.loads((stage0_dir / "0.2_anonymization_plan.json").read_text()),
            "0.3_transaction_reconstruction": json.loads((stage0_dir / "0.3_transaction_reconstruction.json").read_text()),
            "0.4_key_numbers": json.loads((stage0_dir / "0.4_key_numbers.json").read_text()),
            "0.5_evidence_planning": json.loads((stage0_dir / "0.5_evidence_planning.json").read_text())
        }
        
        logger.info(f"✅ 阶段0数据加载成功，包含 {len(stage0_data)} 个部分")
        
        # 步骤3: 使用新架构生成证据文件
        logger.info("📄 开始新架构证据生成...")
        
        # 设置输出目录
        evidence_output_dir = Path("outputs/stage1/evidence_new")
        evidence_output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化证据生成器
        evidence_generator = EvidenceFileGenerator(
            prompt_dir="prompts",
            output_dir=str(evidence_output_dir),
            llm_client=LLMClient()  # 使用默认配置
        )
        
        # 生成所有证据文件（使用新架构）
        evidence_index = evidence_generator.generate_all_evidence_files(
            stage0_data=stage0_data,
            evidence_planning=stage0_data["0.5_evidence_planning"],
            party="原告"
        )
        
        # 保存证据索引
        evidence_index_path = evidence_output_dir / "evidence_index.json"
        with open(evidence_index_path, 'w', encoding='utf-8') as f:
            json.dump(evidence_index, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 新架构证据生成完成!")
        logger.info(f"   总证据数: {evidence_index.get('证据总数', 0)} 个")
        logger.info(f"   证据组数: {evidence_index.get('证据组数', 0)} 组")
        logger.info(f"   证据索引: {evidence_index_path}")
        logger.info(f"   证据文件: {evidence_output_dir}/evidence/")
        
        # 验证生成结果
        evidence_files = list(evidence_output_dir.glob("evidence/**/*.txt"))
        logger.info(f"   实际生成文件数: {len(evidence_files)} 个")
        
        if len(evidence_files) == evidence_index.get('证据总数', 0):
            logger.info("✅ 文件数量验证通过")
        else:
            logger.warning("⚠️  文件数量验证失败")
        
        # 显示部分文件结构
        logger.info("📁 生成的文件结构预览:")
        for i, file_path in enumerate(evidence_files[:5]):  # 只显示前5个
            relative_path = file_path.relative_to(evidence_output_dir)
            logger.info(f"   {relative_path}")
        if len(evidence_files) > 5:
            logger.info(f"   ... 还有 {len(evidence_files) - 5} 个文件")
        
        logger.info("🎉 新架构证据生成流程完成!")
        return True
        
    except Exception as e:
        logger.error(f"❌ 新架构证据生成失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """主函数"""
    logger.info("🔧 金融案件测试数据生成系统 - 新架构专用运行脚本")
    logger.info("===============================================")
    
    success = run_new_architecture_generation()
    
    if success:
        logger.info("✅ 新架构运行成功完成!")
        logger.info("📄 请查看以下输出文件:")
        logger.info("   - outputs/stage1/evidence_new/evidence_index.json")
        logger.info("   - outputs/stage1/evidence_new/evidence/证据组*/")
        logger.info("📖 详细使用说明请参考: 金融案件测试数据生成方案/新软件运行指南.md")
    else:
        logger.error("❌ 新架构运行失败，请查看错误信息")
        sys.exit(1)

if __name__ == "__main__":
    main()