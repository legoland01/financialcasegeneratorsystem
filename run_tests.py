#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行器
运行所有测试套件
"""

import unittest
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

def run_all_tests():
    """运行所有测试"""
    print("🧪 开始运行所有测试...")
    print("=" * 50)
    
    # 测试套件列表
    test_suites = [
        # 单元测试
        "tests.unit.test_evidence_file_generator",
        
        # 功能测试
        "tests.functional.test_new_architecture",
        "tests.functional.test_file_structure",
        
        # 集成测试
        "tests.integration.test_complete_workflow",
    ]
    
    results = []
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    for test_suite in test_suites:
        print(f"\n📋 运行测试套件: {test_suite}")
        print("-" * 40)
        
        try:
            # 导入测试模块
            module_name = test_suite.replace(".", "_")
            test_module = __import__(module_name, fromlist=[''])
            
            # 创建测试套件
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(test_module)
            
            # 运行测试
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(suite)
            
            # 记录结果
            total_tests += result.testsRun
            total_failures += len(result.failures)
            total_errors += len(result.errors)
            
            results.append({
                "suite": test_suite,
                "tests": result.testsRun,
                "failures": len(result.failures),
                "errors": len(result.errors),
                "success": len(result.failures) == 0 and len(result.errors) == 0
            })
            
            if result.wasSuccessful():
                print(f"✅ {test_suite} - 通过")
            else:
                print(f"❌ {test_suite} - 失败")
                
        except Exception as e:
            print(f"💥 运行测试套件 {test_suite} 时出错: {e}")
            total_errors += 1
            results.append({
                "suite": test_suite,
                "tests": 0,
                "failures": 0,
                "errors": 1,
                "success": False
            })
    
    # 输出总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print("=" * 50)
    
    for result in results:
        status = "✅ 通过" if result["success"] else "❌ 失败"
        print(f"{status} | {result['suite']}")
        print(f"      测试数: {result['tests']}")
        if result["failures"] > 0:
            print(f"      失败数: {result['failures']}")
        if result["errors"] > 0:
            print(f"      错误数: {result['errors']}")
        print()
    
    print(f"总计: {total_tests} 个测试, {total_failures} 个失败, {total_errors} 个错误")
    
    if total_failures == 0 and total_errors == 0:
        print("🎉 所有测试通过!")
        return True
    else:
        print("💥 存在测试失败!")
        return False

def run_specific_tests(test_pattern):
    """运行特定测试"""
    print(f"🧪 运行特定测试: {test_pattern}")
    print("=" * 50)
    
    try:
        # 使用unittest的发现功能
        loader = unittest.TestLoader()
        suite = loader.discover(
            start_dir="tests",
            pattern=test_pattern,
            top_level_dir="."
        )
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except Exception as e:
        print(f"💥 运行测试时出错: {e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 运行特定测试
        test_pattern = sys.argv[1]
        success = run_specific_tests(test_pattern)
    else:
        # 运行所有测试
        success = run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()