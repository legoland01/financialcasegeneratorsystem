"""约束注册表 - 统一管理所有约束 (DOC-005)

DOC-005 问题: 质量门禁机制缺失
解决方案: 约束注册表统一管理所有约束，失败则阻塞下一阶段
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Union
from enum import Enum
from loguru import logger


class ConstraintResult(Enum):
    """约束检查结果"""
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    WARN = "warn"


@dataclass
class Constraint:
    """约束定义"""
    name: str
    check_fn: Callable[[], ConstraintResult]
    description: str
    blocking: bool = True
    retry_on_fail: bool = False
    max_retries: int = 1
    on_pass_action: Optional[Callable[[], None]] = None
    on_fail_action: Optional[Callable[[], None]] = None
    enabled: bool = True


@dataclass
class ConstraintCheckResult:
    """约束检查结果"""
    constraint_name: str
    result: ConstraintResult
    message: str = ""
    duration_ms: float = 0.0
    error: Optional[str] = None

    def is_pass(self) -> bool:
        return self.result == ConstraintResult.PASS

    def is_blocking_fail(self) -> bool:
        return self.result == ConstraintResult.FAIL and self.constraint.blocking


class ConstraintRegistry:
    """约束注册表

    功能:
    - 注册和管理约束
    - 按阶段分组约束
    - 执行约束检查
    - 生成约束检查报告
    - 失败时阻塞流程
    """

    _instance: Optional['ConstraintRegistry'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.constraints: Dict[str, Constraint] = {}
            self.stage_constraints: Dict[str, List[str]] = {}
            self._initialized = True
            self._check_history: List[ConstraintCheckResult] = []

    @classmethod
    def reset(cls):
        """重置注册表（用于测试）"""
        cls._instance = None

    def register(
        self,
        constraint: Constraint,
        stage: Optional[str] = None,
    ) -> 'ConstraintRegistry':
        """
        注册约束

        Args:
            constraint: 约束定义
            stage: 所属阶段

        Returns:
            self: 支持链式调用
        """
        self.constraints[constraint.name] = constraint

        if stage:
            if stage not in self.stage_constraints:
                self.stage_constraints[stage] = []
            self.stage_constraints[stage].append(constraint.name)

        logger.debug(f"已注册约束: {constraint.name}")
        return self

    def register_check(
        self,
        name: str,
        check_fn: Callable[[], bool],
        description: str,
        stage: Optional[str] = None,
        blocking: bool = True,
        error_message: str = "检查失败",
    ) -> 'ConstraintRegistry':
        """
        注册简单约束检查

        Args:
            name: 约束名称
            check_fn: 检查函数，返回True表示通过
            description: 约束描述
            stage: 所属阶段
            blocking: 是否阻塞
            error_message: 失败时的错误信息

        Returns:
            self: 支持链式调用
        """
        def wrapped_check() -> ConstraintResult:
            try:
                if check_fn():
                    return ConstraintResult.PASS
                else:
                    return ConstraintResult.FAIL
            except Exception as e:
               AIL

        constraint return ConstraintResult.F = Constraint(
            name=name,
            check_fn=wrapped_check,
            description=description,
            blocking=blocking,
        )
        constraint.error_message = error_message

        return self.register(constraint, stage)

    def unregister(self, name: str) -> bool:
        """注销约束"""
        if name in self.constraints:
            del self.constraints[name]
            for stage_constraints in self.stage_constraints.values():
                if name in stage_constraints:
                    stage_constraints.remove(name)
            return True
        return False

    def get_constraint(self, name: str) -> Optional[Constraint]:
        """获取约束"""
        return self.constraints.get(name)

    def get_stage_constraints(self, stage: str) -> List[Constraint]:
        """获取阶段约束"""
        constraint_names = self.stage_constraints.get(stage, [])
        return [self.constraints[n] for n in constraint_names if n in self.constraints]

    def check(
        self,
        constraint_name: str,
        raise_on_blocking: bool = True,
    ) -> ConstraintCheckResult:
        """
        执行约束检查

        Args:
            constraint_name: 约束名称
            raise_on_blocking: 阻塞性失败是否抛出异常

        Returns:
            ConstraintCheckResult: 检查结果
        """
        import time

        constraint = self.constraints.get(constraint_name)
        if constraint is None:
            result = ConstraintCheckResult(
                constraint_name=constraint_name,
                result=ConstraintResult.FAIL,
                message=f"约束不存在: {constraint_name}",
            )
            self._check_history.append(result)
            return result

        if not constraint.enabled:
            result = ConstraintCheckResult(
                constraint_name=constraint_name,
                result=ConstraintResult.SKIP,
                message=f"约束已禁用: {constraint_name}",
            )
            self._check_history.append(result)
            return result

        start_time = time.time()
        try:
            result_value = constraint.check_fn()
            duration_ms = (time.time() - start_time) * 1000

            if isinstance(result_value, bool):
                result_value = ConstraintResult.PASS if result_value else ConstraintResult.FAIL

            result = ConstraintCheckResult(
                constraint_name=constraint_name,
                result=result_value,
                message=self._get_result_message(result_value, constraint),
                duration_ms=duration_ms,
            )

            if result_value == ConstraintResult.PASS and constraint.on_pass_action:
                constraint.on_pass_action()
            elif result_value == ConstraintResult.FAIL and constraint.on_fail_action:
                constraint.on_fail_action()

        except Exception as e:
            result = ConstraintCheckResult(
                constraint_name=constraint_name,
                result=ConstraintResult.FAIL,
                message=f"约束执行错误: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e),
            )

        self._check_history.append(result)

        if raise_on_blocking and result.is_blocking_fail():
            raise ConstraintViolationError(
                f"约束检查失败: {constraint_name} - {result.message}"
            )

        return result

    def check_stage(
        self,
        stage: str,
        raise_on_blocking: bool = True,
    ) -> List[ConstraintCheckResult]:
        """
        执行阶段所有约束检查

        Args:
            stage: 阶段名称
            raise_on_blocking: 阻塞性失败是否抛出异常

        Returns:
            List[ConstraintCheckResult]: 检查结果列表
        """
        results = []
        constraints = self.get_stage_constraints(stage)

        logger.info(f"开始执行阶段 {stage} 的约束检查，共 {len(constraints)} 个约束")

        for constraint in constraints:
            result = self.check(constraint.name, raise_on_blocking=raise_on_blocking)
            results.append(result)

        return results

    def check_all(self, raise_on_blocking: bool = True) -> List[ConstraintCheckResult]:
        """
        执行所有约束检查

        Args:
            raise_on_blocking: 阻塞性失败是否抛出异常

        Returns:
            List[ConstraintCheckResult]: 检查结果列表
        """
        results = []
        for name in self.constraints:
            result = self.check(name, raise_on_blocking=raise_on_blocking)
            results.append(result)
        return results

    def _get_result_message(
        self,
        result: ConstraintResult,
        constraint: Constraint,
    ) -> str:
        """获取结果消息"""
        if result == ConstraintResult.PASS:
            return f"约束检查通过: {constraint.description}"
        elif result == ConstraintResult.FAIL:
            return getattr(constraint, 'error_message', f"约束检查失败: {constraint.description}")
        elif result == ConstraintResult.WARN:
            return f"约束警告: {constraint.description}"
        elif result == ConstraintResult.SKIP:
            return f"约束跳过: {constraint.description}"
        return ""

    def verify_all(self) -> bool:
        """
        验证所有约束，返回是否全部通过

        Returns:
            bool: 是否全部通过
        """
        results = self.check_all(raise_on_blocking=False)
        failed = [r for r in results if r.result == ConstraintResult.FAIL]

        if failed:
            logger.error(f"约束验证失败: {len(failed)}/{len(results)} 个约束未通过")
            for r in failed:
                logger.error(f"  - {r.constraint_name}: {r.message}")
            return False

        logger.success(f"所有约束验证通过: {len(results)}/{len(results)}")
        return True

    def get_check_history(self) -> List[ConstraintCheckResult]:
        """获取检查历史"""
        return self._check_history.copy()

    def clear_history(self):
        """清空检查历史"""
        self._check_history.clear()

    def print_report(self):
        """打印约束检查报告"""
        print("\n" + "=" * 60)
        print("约束检查报告")
        print("=" * 60)

        if not self._check_history:
            print("暂无检查记录")
            print("=" * 60 + "\n")
            return

        passed = sum(1 for r in self._check_history if r.result == ConstraintResult.PASS)
        failed = sum(1 for r in self._check_history if r.result == ConstraintResult.FAIL)
        skipped = sum(1 for r in self._check_history if r.result == ConstraintResult.SKIP)

        print(f"总检查数: {len(self._check_history)}")
        print(f"  - 通过: {passed}")
        print(f"  - 失败: {failed}")
        print(f"  - 跳过: {skipped}")
        print()

        if failed:
            print("失败约束:")
            for r in self._check_history:
                if r.result == ConstraintResult.FAIL:
                    print(f"  - {r.constraint_name}: {r.message}")

        print("=" * 60 + "\n")


class ConstraintViolationError(Exception):
    """约束违反异常"""
    pass


def get_registry() -> ConstraintRegistry:
    """获取约束注册表实例"""
    return ConstraintRegistry()


def register_constraint(
    name: str,
    check_fn: Callable[[], bool],
    description: str,
    stage: Optional[str] = None,
    blocking: bool = True,
) -> ConstraintRegistry:
    """
    注册约束的便捷函数

    Args:
        name: 约束名称
        check_fn: 检查函数
        description: 约束描述
        stage: 所属阶段
        blocking: 是否阻塞

    Returns:
        ConstraintRegistry: 约束注册表
    """
    registry = get_registry()
    return registry.register_check(
        name=name,
        check_fn=check_fn,
        description=description,
        stage=stage,
        blocking=blocking,
    )
