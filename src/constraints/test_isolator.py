"""测试隔离器 - 防止缓存重用导致测试失效 (EXE-003)

EXE-003 问题: 中间结果重用导致测试无效
解决方案: 提供--fresh参数强制清除缓存，支持测试隔离
"""

from dataclasses import dataclass, field
from typing import Optional, List, Set
from pathlib import Path
from enum import Enum
from loguru import logger
import shutil
import os


class IsolationLevel(Enum):
    """隔离级别"""
    NONE = "none"
    OUTPUT = "output"
    CACHE = "cache"
    FULL = "full"


@dataclass
class IsolationConfig:
    """隔离配置"""
    level: IsolationLevel
    dirs_to_clean: List[str] = field(default_factory=list)
    files_to_clean: List[str] = field(default_factory=list)
    dry_run: bool = False

    def should_clean_output(self) -> bool:
        """是否清除输出目录"""
        return self.level in [IsolationLevel.OUTPUT, IsolationLevel.FULL]

    def should_clean_cache(self) -> bool:
        """是否清除缓存"""
        return self.level in [IsolationLevel.CACHE, IsolationLevel.FULL]


class TestIsolator:
    """测试隔离器

    功能:
    - 管理测试隔离级别
    - 清除缓存和输出目录
    - 跟踪被清除的文件
    - 提供隔离状态报告
    """

    _instance: Optional['TestIsolator'] = None
    _cleaned_paths: Set[str] = field(default_factory=set)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._cleaned_paths = set()

    @classmethod
    def reset(cls):
        """重置隔离器状态（用于测试）"""
        cls._instance = None

    def isolate(
        self,
        level: IsolationLevel = IsolationLevel.FULL,
        output_dir: str = "outputs",
        cache_dir: Optional[str] = None,
        dry_run: bool = False
    ) -> IsolationConfig:
        """
        执行隔离操作

        Args:
            level: 隔离级别
            output_dir: 输出目录
            cache_dir: 缓存目录
            dry_run: 干运行模式（不实际执行）

        Returns:
            IsolationConfig: 隔离配置
        """
        config = IsolationConfig(
            level=level,
            dirs_to_clean=[],
            files_to_clean=[],
            dry_run=dry_run
        )

        if level == IsolationLevel.NONE:
            logger.info("隔离级别: 无")
            return config

        if level == IsolationLevel.FULL:
            config.dirs_to_clean.extend([output_dir])
            if cache_dir:
                config.dirs_to_clean.append(cache_dir)

        elif level == IsolationLevel.OUTPUT:
            config.dirs_to_clean.append(output_dir)

        elif level == IsolationLevel.CACHE and cache_dir:
            config.dirs_to_clean.append(cache_dir)

        for dir_path in config.dirs_to_clean:
            self._clean_directory(dir_path, dry_run)
            config.dirs_to_clean[config.dirs_to_clean.index(dir_path)] = dir_path

        logger.info(f"隔离级别: {level.value}，清除目录: {config.dirs_to_clean}")

        return config

    def _clean_directory(self, dir_path: str, dry_run: bool = False):
        """清除目录"""
        path = Path(dir_path)

        if not path.exists():
            logger.debug(f"目录不存在，跳过: {dir_path}")
            return

        if dry_run:
            logger.info(f"[干运行] 将清除目录: {dir_path}")
            return

        try:
            shutil.rmtree(dir_path)
            self._cleaned_paths.add(dir_path)
            logger.info(f"已清除目录: {dir_path}")
        except Exception as e:
            logger.error(f"清除目录失败: {dir_path}, 错误: {e}")

    def clean_output_dir(self, output_dir: str = "outputs", dry_run: bool = False) -> List[str]:
        """
        清除输出目录

        Args:
            output_dir: 输出目录路径
            dry_run: 干运行模式

        Returns:
            List[str]: 被清除的路径列表
        """
        config = self.isolate(
            level=IsolationLevel.OUTPUT,
            output_dir=output_dir,
            dry_run=dry_run
        )
        return config.dirs_to_clean

    def clean_cache_dir(self, cache_dir: str, dry_run: bool = False) -> List[str]:
        """
        清除缓存目录

        Args:
            cache_dir: 缓存目录路径
            dry_run: 干运行模式

        Returns:
            List[str]: 被清除的路径列表
        """
        if dry_run:
            logger.info(f"[干运行] 将清除缓存目录: {cache_dir}")
            return [cache_dir]

        path = Path(cache_dir)
        if path.exists():
            try:
                shutil.rmtree(cache_dir)
                self._cleaned_paths.add(cache_dir)
                logger.info(f"已清除缓存目录: {cache_dir}")
                return [cache_dir]
            except Exception as e:
                logger.error(f"清除缓存目录失败: {cache_dir}, 错误: {e}")
        return []

    def get_cleaned_paths(self) -> Set[str]:
        """获取被清除的路径"""
        return self._cleaned_paths.copy()

    def create_fresh_config(
        self,
        output_dir: str = "outputs",
        cache_dir: Optional[str] = None
    ) -> IsolationConfig:
        """
        创建完全隔离配置（相当于 --fresh）

        Args:
            output_dir: 输出目录
            cache_dir: 缓存目录

        Returns:
            IsolationConfig: 隔离配置
        """
        return self.isolate(
            level=IsolationLevel.FULL,
            output_dir=output_dir,
            cache_dir=cache_dir
        )

    def check_cache_exists(self, output_dir: str = "outputs") -> bool:
        """检查缓存是否存在"""
        return Path(output_dir).exists()

    def warn_if_cache_exists(self, output_dir: str = "outputs"):
        """如果缓存存在则发出警告"""
        if self.check_cache_exists(output_dir):
            logger.warning(
                f"检测到缓存目录存在: {output_dir}。\n"
                f"如需使用缓存结果，请添加 --use-cache。\n"
                f"如需清除缓存重新运行，请添加 --fresh。"
            )

    def parse_args(self, args: Dict) -> IsolationConfig:
        """
        从命令行参数解析隔离配置

        Args:
            args: 命令行参数字典

        Returns:
            IsolationConfig: 隔离配置
        """
        fresh = args.get('fresh', False)
        use_cache = args.get('use_cache', True)
        output_dir = args.get('output_dir', 'outputs')

        if fresh:
            level = IsolationLevel.FULL
            logger.info("检测到 --fresh 参数，将清除所有缓存重新运行")
        elif not use_cache:
            level = IsolationLevel.OUTPUT
            logger.info("检测到 --no-cache 参数，将清除输出目录")
        else:
            level = IsolationLevel.NONE
            self.warn_if_cache_exists(output_dir)

        return self.isolate(level=level, output_dir=output_dir)


class CacheWarning:
    """缓存警告"""

    @staticmethod
    def show(output_dir: str = "outputs"):
        """显示缓存警告"""
        if Path(output_dir).exists():
            logger.warning(
                f"⚠️  检测到缓存目录存在: {output_dir}\n"
                f"    继续使用缓存结果可能会导致测试结果不准确。\n"
                f"    如需重新运行，请添加 --fresh 参数清除缓存。"
            )


def create_isolator() -> TestIsolator:
    """创建隔离器的便捷函数"""
    return TestIsolator()


def setup_test_isolation(
    fresh: bool = False,
    use_cache: bool = True,
    output_dir: str = "outputs"
) -> IsolationConfig:
    """
    设置测试隔离的便捷函数

    Args:
        fresh: 是否完全清除
        use_cache: 是否使用缓存
        output_dir: 输出目录

    Returns:
        IsolationConfig: 隔离配置
    """
    isolator = create_isolator()

    if fresh:
        level = IsolationLevel.FULL
    elif not use_cache:
        level = IsolationLevel.OUTPUT
    else:
        level = IsolationLevel.NONE

    return isolator.isolate(level=level, output_dir=output_dir)
