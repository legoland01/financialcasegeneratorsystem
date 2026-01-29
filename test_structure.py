"""测试脚本 - 验证项目结构"""
import sys
from pathlib import Path

# 添加src到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from loguru import logger


def test_project_structure():
    """测试项目结构"""
    logger.info("开始测试项目结构...")
    
    base_dir = Path(__file__).parent
    
    # 检查必需的目录
    required_dirs = [
        "src",
        "src/api",
        "src/services",
        "src/services/stage0",
        "src/services/stage1",
        "src/services/stage2",
        "src/services/stage3",
        "src/models",
        "src/utils",
        "prompts",
        "schemas",
        "quality_control",
        "tests",
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
        else:
            logger.success(f"✓ 目录存在: {dir_path}")
    
    if missing_dirs:
        logger.error(f"✗ 缺失目录: {', '.join(missing_dirs)}")
        return False
    
    # 检查必需的文件
    required_files = [
        "main.py",
        "config.py",
        "requirements.txt",
        "pyproject.toml",
        "README.md",
        "prompts/stage0/0.1_结构化提取.md",
        "prompts/stage0/0.2_脱敏替换策划.md",
        "prompts/stage0/0.3_交易结构重构.md",
        "prompts/stage0/0.4_关键数字提取.md",
        "prompts/stage0/0.5_证据归属规划.md",
        "prompts/stage1/1.1_起诉状生成.md",
        "prompts/stage1/1.2_证据包生成.md",
        "prompts/stage1/1.3_程序文件生成.md",
        "prompts/stage2/2.1_答辩状生成.md",
        "prompts/stage2/2.2_证据包生成.md",
        "prompts/stage2/2.3_程序文件生成.md",
        "prompts/stage3/3.1_庭审笔录生成.md",
        "prompts/stage3/3.2_判决书脱敏替换.md",
        "schemas/stage0_output_schema.json",
        "schemas/profile_library_schema.json",
        "schemas/evidence_planning_schema.json",
        "quality_control/automated_rules.json",
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = base_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)
        else:
            logger.success(f"✓ 文件存在: {file_path}")
    
    if missing_files:
        logger.error(f"✗ 缺失文件: {', '.join(missing_files)}")
        return False
    
    logger.success("项目结构测试通过！")
    return True


def test_imports():
    """测试模块导入"""
    logger.info("开始测试模块导入...")
    
    try:
        from src.utils import load_prompt_template, LLMClient
        logger.success("✓ src.utils 导入成功")
    except Exception as e:
        logger.error(f"✗ src.utils 导入失败: {e}")
        return False
    
    try:
        from src.services import Stage0Service, Stage1Service, Stage2Service, Stage3Service
        logger.success("✓ src.services 导入成功")
    except Exception as e:
        logger.error(f"✗ src.services 导入失败: {e}")
        return False
    
    try:
        from src.api import app
        logger.success("✓ src.api 导入成功")
    except Exception as e:
        logger.error(f"✗ src.api 导入失败: {e}")
        return False
    
    logger.success("模块导入测试通过！")
    return True


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("金融案件测试数据生成系统 - 测试脚本")
    logger.info("=" * 50)
    
    structure_ok = test_project_structure()
    print()
    
    imports_ok = test_imports()
    print()
    
    if structure_ok and imports_ok:
        logger.success("=" * 50)
        logger.success("所有测试通过！")
        logger.success("=" * 50)
        sys.exit(0)
    else:
        logger.error("=" * 50)
        logger.error("测试失败！请检查上述错误信息。")
        logger.error("=" * 50)
        sys.exit(1)
