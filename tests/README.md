# 测试文件整理和创建计划

## 📋 当前测试文件状态

### 已存在的测试文件
1. `test_new_architecture.py` - 新架构测试（已验证）
2. `test_with_judgment_improved.py` - 改进的判决书测试
3. `test_pdf_generator.py` - PDF生成器测试
4. `test_config.py` - 配置测试
5. 其他各种测试脚本（部分过时）

### 缺少的测试文件
1. 系统性测试套件
2. 单元测试文件
3. 集成测试文件
4. 性能测试文件

## 🎯 需要创建的测试文件

### 1. 单元测试
- `tests/unit/test_stage0_service.py`
- `tests/unit/test_stage1_service.py`
- `tests/unit/test_stage2_service.py`
- `tests/unit/test_stage3_service.py`
- `tests/unit/test_evidence_file_generator.py`
- `tests/unit/test_pdf_generator.py`

### 2. 集成测试
- `tests/integration/test_full_workflow.py`
- `tests/integration/test_new_architecture_workflow.py`
- `tests/integration/test_pdf_generation_workflow.py`

### 3. 系统测试
- `tests/system/test_complete_generation.py`
- `tests/system/test_error_handling.py`
- `tests/system/test_performance.py`

### 4. 功能测试
- `tests/functional/test_evidence_generation.py`
- `tests/functional/test_file_structure.py`
- `tests/functional/test_data_consistency.py`