"""模式管理器 - 防止Mock/Real混淆 (EXE-002)

EXE-002 问题: Mock/Real模式混淆
解决方案: 要求明确声明运行模式，未声明则阻塞运行
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum
from loguru import logger
import sys


class RunMode(Enum):
    """运行模式"""
    MOCK = "mock"
    REAL = "real"
    AUTO = "auto"

    @classmethod
    def from_string(cls, mode: str) -> 'RunMode':
        """从字符串解析运行模式"""
        mode_lower = mode.lower()
        for m in cls:
            if m.value == mode_lower:
                return m
        raise ValueError(f"未知的运行模式: {mode}，可选值: mock, real, auto")

    def is_real(self) -> bool:
        """是否真实运行模式"""
        return self == RunMode.REAL

    def is_mock(self) -> bool:
        """是否模拟运行模式"""
        return self == RunMode.MOCK


@dataclass
class ModeConfig:
    """模式配置"""
    mode: RunMode
    use_cache: bool = True
    cache_dir: str = "outputs"
    fresh: bool = False

    def should_use_cache(self) -> bool:
        """是否使用缓存"""
        return self.use_cache and not self.fresh

    def should_clear_cache(self) -> bool:
        """是否清除缓存"""
        return self.fresh


class ModeManager:
    """模式管理器

    功能:
    - 要求明确声明运行模式
    - 管理Mock/Real模式的切换
    - 记录模式切换历史
    - 提供模式相关的约束检查
    """

    _instance: Optional['ModeManager'] = None
    _mode: Optional[RunMode] = None
    _mode_history: list = field(default_factory=list)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._mode is None:
            self._mode = RunMode.AUTO

    @classmethod
    def reset(cls):
        """重置模式管理器（用于测试）"""
        cls._instance = None
        cls._mode = None
        cls._mode_history = []

    def set_mode(self, mode: RunMode, reason: str = ""):
        """
        设置运行模式

        Args:
            mode: 运行模式
            reason: 设置原因
        """
        old_mode = self._mode
        self._mode = mode

        entry = {
            "from": old_mode.value if old_mode else None,
            "to": mode.value,
            "reason": reason,
        }
        self._mode_history.append(entry)

        logger.info(f"运行模式已切换: {old_mode.value if old_mode else '未设置'} -> {mode.value} {reason}")

    def get_mode(self) -> RunMode:
        """
        获取当前运行模式

        Returns:
            RunMode: 当前运行模式

        Raises:
            ModeNotDeclaredError: 模式未声明时抛出
        """
        if self._mode is None or self._mode == RunMode.AUTO:
            raise ModeNotDeclaredError(
                "运行模式未明确声明。请使用 --mode mock 或 --mode real 指定运行模式。"
            )
        return self._mode

    def assert_mode(self, expected_mode: RunMode):
        """
        断言当前模式为期望模式

        Args:
            expected_mode: 期望的运行模式

        Raises:
            ModeMismatchError: 模式不匹配时抛出
        """
        current_mode = self.get_mode()
        if current_mode != expected_mode:
            raise ModeMismatchError(
                f"运行模式不匹配: 当前为 {current_mode.value}，但需要 {expected_mode.value}"
            )

    def require_real_mode(self):
        """要求使用真实模式，如果不是则抛出异常"""
        mode = self.get_mode()
        if mode == RunMode.MOCK:
            raise ModeMismatchError(
                "当前为Mock模式，不允许执行此操作。请使用 --mode real 切换到真实模式。"
            )

    def require_mock_mode(self):
        """要求使用Mock模式，如果不是则抛出异常"""
        mode = self.get_mode()
        if mode == RunMode.REAL:
            raise ModeMismatchError(
                "当前为Real模式，不允许执行此操作。请使用 --mode mock 切换到Mock模式。"
            )

    def parse_args(self, args: Dict[str, Any]) -> ModeConfig:
        """
        从命令行参数解析模式配置

        Args:
            args: 命令行参数字典

        Returns:
            ModeConfig: 模式配置
        """
        mode_str = args.get('mode', 'auto')
        use_cache = args.get('use_cache', True)
        fresh = args.get('fresh', False)
        cache_dir = args.get('cache_dir', 'outputs')

        mode = RunMode.from_string(mode_str) if mode_str != 'auto' else RunMode.AUTO

        self.set_mode(mode, reason="命令行参数")

        return ModeConfig(
            mode=mode,
            use_cache=use_cache,
            cache_dir=cache_dir,
            fresh=fresh
        )

    def get_mode_history(self) -> list:
        """获取模式切换历史"""
        return self._mode_history.copy()

    def is_mode_declared(self) -> bool:
        """检查模式是否已声明"""
        return self._mode is not None and self._mode != RunMode.AUTO


class ModeNotDeclaredError(Exception):
    """模式未声明异常"""
    pass


class ModeMismatchError(Exception):
    """模式不匹配异常"""
    pass


def require_mode_declaration():
    """
    检查模式是否已声明的便捷函数

    Raises:
        ModeNotDeclaredError: 模式未声明时抛出
    """
    manager = ModeManager()
    manager.get_mode()


def create_mode_config_from_args(**kwargs) -> ModeConfig:
    """
    从参数创建模式配置的便捷函数

    Args:
        **kwargs: 参数

    Returns:
        ModeConfig: 模式配置
    """
    manager = ModeManager()
    return manager.parse_args(kwargs)
