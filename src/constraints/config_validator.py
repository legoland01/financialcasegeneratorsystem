"""配置验证器 - 防止API Key配置错误 (EXE-001)

EXE-001 问题: LLM API Key配置错误重复发生
解决方案: 启动时验证配置完整性，不完整则阻塞运行
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from pathlib import Path
import os
import yaml
from loguru import logger


@dataclass
class ConfigValidationResult:
    """配置验证结果"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_config: Dict = field(default_factory=dict)

    def add_error(self, error: str):
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str):
        self.warnings.append(warning)

    def summary(self) -> str:
        lines = [f"配置验证结果: {'通过' if self.is_valid else '失败'}"]
        if self.errors:
            lines.append(f"  错误 ({len(self.errors)}):")
            for e in self.errors:
                lines.append(f"    - {e}")
        if self.warnings:
            lines.append(f"  警告 ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"    - {w}")
        return "\n".join(lines)


class ConfigValidator:
    """配置验证器

    功能:
    - 验证必需的配置项是否存在
    - 验证API Key格式是否正确
    - 验证配置文件路径是否有效
    - 提供详细的验证错误信息
    """

    REQUIRED_FIELDS = {
        'siliconflow': ['api_key', 'api_url'],
        'openai': ['api_key', 'api_url'],
        'default': ['api_key', 'api_url'],
    }

    API_KEY_PATTERN = {
        'siliconflow': r'^sk-[a-zA-Z0-9]{20,}$',
        'openai': r'^sk-[a-zA-Z0-9]{20,}$',
    }

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置验证器

        Args:
            config_path: 配置文件路径，如果为None则尝试标准位置
        """
        self.config_path = config_path
        self.config: Dict = {}
        self.custom_validators: List[Callable[[Dict], ConfigValidationResult]] = []

    def add_validator(self, validator: Callable[[Dict], ConfigValidationResult]):
        """添加自定义验证器"""
        self.custom_validators.append(validator)

    def load_config(self, path: Optional[str] = None) -> bool:
        """加载配置文件"""
        config_path = path or self.config_path
        if config_path is None:
            config_path = self._find_config_file()

        if config_path is None:
            return False

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
            logger.info(f"已加载配置文件: {config_path}")
            return True
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return False

    def _find_config_file(self) -> Optional[str]:
        """查找配置文件"""
        possible_paths = [
            'config.yaml',
            'config.yml',
            'configs/config.yaml',
            'configs/main.yaml',
            os.path.expanduser('~/.financial_case_generator/config.yaml'),
        ]

        for path in possible_paths:
            if Path(path).exists():
                return path

        return None

    def validate(self, config: Optional[Dict] = None) -> ConfigValidationResult:
        """
        验证配置

        Args:
            config: 要验证的配置，如果为None则使用已加载的配置

        Returns:
            ConfigValidationResult: 验证结果
        """
        result = ConfigValidationResult(is_valid=True)

        if config is not None:
            self.config = config
        elif not self.config:
            if not self.load_config():
                result.add_error("未找到配置文件，请指定 --config 或创建 config.yaml")
                return result

        # 验证必需字段
        self._validate_required_fields(result)

        # 验证API Key格式
        self._validate_api_key_format(result)

        # 验证配置文件存在性
        self._validate_file_paths(result)

        # 运行自定义验证器
        for validator in self.custom_validators:
            try:
                custom_result = validator(self.config)
                if not custom_result.is_valid:
                    result.is_valid = False
                    result.errors.extend(custom_result.errors)
                result.warnings.extend(custom_result.warnings)
            except Exception as e:
                result.add_error(f"自定义验证器执行失败: {e}")

        # 记录验证结果
        if result.is_valid:
            logger.success("配置验证通过")
        else:
            logger.error(f"配置验证失败: {len(result.errors)} 个错误")

        result.validated_config = self.config
        return result

    def _validate_required_fields(self, result: ConfigValidationResult):
        """验证必需字段"""
        provider = self.config.get('provider', 'default')
        required_fields = self.REQUIRED_FIELDS.get(provider, self.REQUIRED_FIELDS['default'])

        for field in required_fields:
            if field not in self.config:
                result.add_error(f"缺少必需配置项: {field} (provider: {provider})")

    def _validate_api_key_format(self, result: ConfigValidationResult):
        """验证API Key格式"""
        provider = self.config.get('provider', 'default')
        api_key = self.config.get('api_key', '')

        if not api_key:
            result.add_error("API Key为空")
            return

        # 检查是否是环境变量引用
        if api_key.startswith('${'):
            env_var = api_key[2:-1]
            env_value = os.environ.get(env_var)
            if not env_value:
                result.add_error(f"环境变量 {env_var} 未设置或为空")
                return
            api_key = env_value

        # 验证格式
        pattern = self.API_KEY_PATTERN.get(provider)
        if pattern:
            import re
            if not re.match(pattern, api_key):
                result.add_warning(
                    f"API Key格式可能不正确 (provider: {provider})"
                )

    def _validate_file_paths(self, result: ConfigValidationResult):
        """验证配置文件引用的文件路径"""
        file_fields = ['judgment_path', 'template_dir', 'output_dir']

        for field in file_fields:
            path = self.config.get(field)
            if path and not Path(path).exists():
                result.add_warning(f"配置的文件路径不存在: {field} -> {path}")

    def validate_or_raise(self, config: Optional[Dict] = None) -> Dict:
        """
        验证配置，如果不通过则抛出异常

        Args:
            config: 要验证的配置

        Returns:
            Dict: 验证通过的配置

        Raises:
            ConfigurationError: 配置验证失败时抛出
        """
        result = self.validate(config)

        if not result.is_valid:
            error_msg = f"配置验证失败:\n{result.summary()}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)

        return result.validated_config


class ConfigurationError(Exception):
    """配置错误异常"""
    pass


def validate_config_at_startup(config_path: Optional[str] = None) -> ConfigValidationResult:
    """
    启动时验证配置的便捷函数

    Args:
        config_path: 配置文件路径

    Returns:
        ConfigValidationResult: 验证结果
    """
    validator = ConfigValidator(config_path)
    return validator.validate()
