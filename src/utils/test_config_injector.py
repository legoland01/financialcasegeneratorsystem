"""
测试配置注入器 - 用于错误注入测试

该模块实现了测试配置功能，支持：
- 错误注入（multiply, add, replace操作）
- 复合错误配置
- 数据验证

Author: OpenCode AI
Date: 2026-01-27
"""

import copy
from typing import Dict, Any, Optional, List


class TestConfigInjector:
    """测试配置注入器 - 用于错误注入测试"""
    
    def __init__(self):
        """初始化测试配置注入器"""
        pass
    
    def apply(
        self,
        data: Dict[str, Any],
        test_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        应用测试配置（错误注入）
        
        Args:
            data: 原始数据
            test_config: 测试配置
                {
                    "enabled": true,
                    "description": "测试描述",
                    "errors": [
                        {
                            "target": "boundary_conditions.合同金额",
                            "operation": "multiply",  // multiply, add, replace
                            "value": 1.1  // 操作值
                        }
                    ]
                }
        Returns:
            修改后的数据
        """
        if not test_config or not test_config.get('enabled', False):
            return data
        
        result = self._deep_copy(data)
        
        for error in test_config.get('errors', []):
            target = error.get('target')
            operation = error.get('operation')
            value = error.get('value')
            
            if target and operation:
                self._apply_error(result, target, operation, value)
        
        return result
    
    def _apply_error(
        self,
        data: Dict[str, Any],
        target: str,
        operation: str,
        value: float
    ):
        """
        应用单个错误
        
        Args:
            data: 目标数据字典
            target: 目标路径（如 "boundary_conditions.合同金额"）
            operation: 操作类型（multiply, add, replace）
            value: 操作值
        """
        # 解析路径
        parts = target.split('.')
        current = data
        
        # 导航到目标父节点
        for part in parts[:-1]:
            if part in current:
                current = current[part]
            else:
                return  # 目标路径不存在
        
        # 获取最终目标字段
        final_field = parts[-1]
        if final_field not in current:
            return
        
        # 获取原始值
        original_value = current[final_field]
        
        # 计算新值
        if isinstance(original_value, (int, float)):
            if operation == 'multiply':
                new_value = original_value * value
            elif operation == 'add':
                new_value = original_value + value
            elif operation == 'replace':
                new_value = value
            else:
                new_value = original_value
            
            current[final_field] = new_value
        elif operation == 'replace':
            current[final_field] = value
    
    def _deep_copy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """深拷贝字典"""
        return copy.deepcopy(data)
    
    def validate_test_config(self, test_config: Dict[str, Any]) -> List[str]:
        """
        验证测试配置
        
        Args:
            test_config: 测试配置
        Returns:
            错误列表（空表示配置有效）
        """
        errors = []
        
        if not isinstance(test_config, dict):
            return ["test_config必须是字典"]
        
        if not test_config.get('enabled', False):
            return []  # 未启用，不需要验证
        
        errors_path = test_config.get('errors', [])
        if not isinstance(errors_path, list):
            return ["errors必须是列表"]
        
        for i, error in enumerate(errors_path):
            if not isinstance(error, dict):
                errors.append(f"errors[{i}]必须是字典")
                continue
            
            if 'target' not in error:
                errors.append(f"errors[{i}]缺少target字段")
            
            if 'operation' not in error:
                errors.append(f"errors[{i}]缺少operation字段")
            
            if 'value' not in error:
                errors.append(f"errors[{i}]缺少value字段")
            
            valid_operations = ['multiply', 'add', 'replace']
            if error.get('operation') not in valid_operations:
                errors.append(f"errors[{i}]operation必须是 {', '.join(valid_operations)} 之一")
        
        return errors
    
    def create_test_config(
        self,
        description: str = "",
        errors: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        创建测试配置
        
        Args:
            description: 测试描述
            errors: 错误配置列表
        Returns:
            测试配置字典
        """
        return {
            "enabled": True,
            "description": description,
            "errors": errors or []
        }
    
    def add_error(
        self,
        test_config: Dict[str, Any],
        target: str,
        operation: str,
        value: float
    ) -> Dict[str, Any]:
        """
        添加错误到测试配置
        
        Args:
            test_config: 现有测试配置
            target: 目标路径
            operation: 操作类型
            value: 操作值
        Returns:
            更新后的测试配置
        """
        if 'errors' not in test_config:
            test_config['errors'] = []
        
        test_config['errors'].append({
            "target": target,
            "operation": operation,
            "value": value
        })
        
        return test_config


# 测试代码
if __name__ == "__main__":
    import json
    
    # 创建测试注入器
    injector = TestConfigInjector()
    
    # 原始数据
    data = {
        "boundary_conditions": {
            "合同金额": 150000000,
            "利率": 0.061,
            "签订日期": "2021-02-24",
            "设备数量": 62
        },
        "generated_data": {
            "租金支付计划": [
                {"期数": 1, "租金金额": 19455520.96}
            ]
        }
    }
    
    # 测试场景1: 合同金额+10%
    test_config1 = injector.create_test_config(
        description="测试合同金额+10%",
        errors=[
            {
                "target": "boundary_conditions.合同金额",
                "operation": "multiply",
                "value": 1.1
            }
        ]
    )
    
    result1 = injector.apply(data, test_config1)
    print("测试场景1 - 合同金额+10%:")
    print(f"  原始金额: {data['boundary_conditions']['合同金额']}")
    print(f"  修改后: {result1['boundary_conditions']['合同金额']}")
    
    # 测试场景2: 利率改为8%
    test_config2 = injector.create_test_config(
        description="测试利率改为8%",
        errors=[
            {
                "target": "boundary_conditions.利率",
                "operation": "replace",
                "value": 0.08
            }
        ]
    )
    
    result2 = injector.apply(data, test_config2)
    print("\n测试场景2 - 利率改为8%:")
    print(f"  原始利率: {data['boundary_conditions']['利率']}")
    print(f"  修改后: {result2['boundary_conditions']['利率']}")
    
    # 测试场景3: 复合错误
    test_config3 = {
        "enabled": True,
        "description": "复合错误测试",
        "errors": [
            {
                "target": "boundary_conditions.合同金额",
                "operation": "multiply",
                "value": 1.1
            },
            {
                "target": "boundary_conditions.利率",
                "operation": "replace",
                "value": 0.08
            },
            {
                "target": "boundary_conditions.设备数量",
                "operation": "replace",
                "value": 100
            }
        ]
    }
    
    result3 = injector.apply(data, test_config3)
    print("\n测试场景3 - 复合错误:")
    print(f"  合同金额: {result3['boundary_conditions']['合同金额']}")
    print(f"  利率: {result3['boundary_conditions']['利率']}")
    print(f"  设备数量: {result3['boundary_conditions']['设备数量']}")
    
    # 验证配置
    print("\n配置验证:")
    errors = injector.validate_test_config(test_config3)
    print(f"  验证结果: {'通过' if not errors else errors}")
    
    # 测试配置2 - 无效配置
    invalid_config = {
        "enabled": True,
        "errors": [
            {
                "operation": "invalid_operation",  # 无效操作
                "value": 1.1
            }
        ]
    }
    errors = injector.validate_test_config(invalid_config)
    print(f"  无效配置验证: {errors}")
