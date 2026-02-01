"""约束机制模块 - 防止问题重复发生

约束机制说明:
- ConfigValidator: 配置验证，防止API Key配置错误
- ModeManager: 模式管理，防止Mock/Real混淆
- TestIsolator: 测试隔离，防止缓存重用
- IssueTracker: 问题追踪，防止问题复发
- ConstraintRegistry: 约束注册表
"""

from .config_validator import ConfigValidator, ConfigValidationResult
from .mode_manager import ModeManager, RunMode
from .test_isolator import TestIsolator, IsolationLevel
from .issue_tracker import IssueTracker, IssueType, IssueSeverity
from .constraint_registry import ConstraintRegistry, ConstraintResult

__all__ = [
    'ConfigValidator',
    'ConfigValidationResult',
    'ModeManager',
    'RunMode',
    'TestIsolator',
    'IsolationLevel',
    'IssueTracker',
    'IssueType',
    'IssueSeverity',
    'ConstraintRegistry',
    'ConstraintResult',
]
