"""状态自动更新模块。"""
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import yaml
import logging

logger = logging.getLogger(__name__)


@dataclass
class StateUpdateConfig:
    """状态更新配置"""
    state_file: str = "state/project_state.yaml"
    auto_commit: bool = False


class StateUpdater:
    """状态更新器"""

    def __init__(self, project_path: str = ".", config: Optional[StateUpdateConfig] = None):
        """
        初始化状态更新器

        Args:
            project_path: 项目根目录路径
            config: 配置（可选）
        """
        self.project_path = Path(project_path)
        self.config = config or StateUpdateConfig()
        self.state_file = self.project_path / self.config.state_file

    def load_state(self) -> Dict[str, Any]:
        """加载状态文件"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}

    def save_state(self, state: Dict[str, Any]) -> None:
        """保存状态文件"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            yaml.dump(state, f, allow_unicode=True)

    def _update_timestamp(self, state: Dict[str, Any]) -> None:
        """更新时间戳"""
        state['updated_at'] = datetime.now().isoformat()

    def update_test_stats(self, blackbox_cases: int = None,
                          blackbox_passed: int = None,
                          whitebox_passed: int = None,
                          test_type: str = "blackbox") -> bool:
        """
        更新测试统计信息

        Args:
            blackbox_cases: 黑盒测试用例总数
            blackbox_passed: 黑盒测试通过数
            whitebox_passed: 白盒测试通过数
            test_type: 测试类型

        Returns:
            bool: 是否更新成功
        """
        state = self.load_state()

        if 'test' not in state:
            state['test'] = {}

        test = state['test']

        if blackbox_cases is not None:
            test['blackbox_cases'] = blackbox_cases
        if blackbox_passed is not None:
            test['blackbox_passed'] = blackbox_passed
        if whitebox_passed is not None:
            test['whitebox_passed'] = whitebox_passed

        test['test_type'] = test_type

        # 计算通过率
        if blackbox_cases and blackbox_passed is not None:
            test['pass_rate'] = round(blackbox_passed / blackbox_cases * 100, 2)

        # 如果有用例，设置状态为进行中
        if blackbox_cases and blackbox_cases > 0:
            test['status'] = 'in_progress'

            # 如果全部通过，设置状态为通过
            if blackbox_passed is not None and blackbox_passed >= blackbox_cases:
                test['status'] = 'passed'

        test['last_updated'] = datetime.now().isoformat()
        state['test'] = test
        self._update_timestamp(state)

        self.save_state(state)
        logger.info(f"✓ 测试统计已更新: 用例={blackbox_cases}, 通过={blackbox_passed}")
        return True

    def update_development_status(self, status: str, branch: str = None,
                                   current_milestone: str = None) -> bool:
        """
        更新开发状态

        Args:
            status: 状态 (pending/in_progress/completed)
            branch: 分支名称
            current_milestone: 当前里程碑

        Returns:
            bool: 是否更新成功
        """
        state = self.load_state()

        if 'development' not in state:
            state['development'] = {}

        dev = state['development']
        dev['status'] = status

        if branch:
            dev['branch'] = branch
        if current_milestone:
            dev['current_milestone'] = current_milestone

        dev['last_updated'] = datetime.now().isoformat()
        state['development'] = dev
        self._update_timestamp(state)

        self.save_state(state)
        logger.info(f"✓ 开发状态已更新: {status}")
        return True

    def update_deployment_status(self, status: str, version: str = None) -> bool:
        """
        更新部署状态

        Args:
            status: 状态 (pending/in_progress/completed)
            version: 版本号

        Returns:
            bool: 是否更新成功
        """
        state = self.load_state()

        if 'deployment' not in state:
            state['deployment'] = {}

        deploy = state['deployment']
        deploy['status'] = status

        if version:
            deploy['version'] = version

        deploy['last_updated'] = datetime.now().isoformat()
        state['deployment'] = deploy
        self._update_timestamp(state)

        self.save_state(state)
        logger.info(f"✓ 部署状态已更新: {status}")
        return True

    def set_phase(self, phase: str) -> bool:
        """
        设置当前阶段

        Args:
            phase: 阶段名称

        Returns:
            bool: 是否更新成功
        """
        state = self.load_state()
        old_phase = state.get('phase', 'unknown')

        state['phase'] = phase
        self._update_timestamp(state)

        self.save_state(state)
        logger.info(f"✓ 阶段已从 {old_phase} 更新为 {phase}")
        return True

    def mark_development_complete(self, branch: str = None) -> Dict[str, Any]:
        """
        标记开发完成，自动推进到测试阶段

        Args:
            branch: 分支名称

        Returns:
            Dict: 更新结果
        """
        self.update_development_status("completed", branch=branch)

        return {
            "development_status": "completed",
            "suggested_phase": "testing",
            "action": "运行 'oc-collab advance' 或 'oc-collab auto' 推进阶段"
        }

    def mark_test_complete(self, blackbox_cases: int, blackbox_passed: int) -> Dict[str, Any]:
        """
        标记测试完成

        Args:
            blackbox_cases: 用例总数
            blackbox_passed: 通过数

        Returns:
            Dict: 更新结果
        """
        self.update_test_stats(blackbox_cases, blackbox_passed)

        passed_all = blackbox_passed >= blackbox_cases

        if passed_all:
            return {
                "test_status": "passed",
                "pass_rate": round(blackbox_passed / blackbox_cases * 100, 2),
                "suggested_action": "可以运行 'oc-collab advance' 推进到部署阶段"
            }
        else:
            return {
                "test_status": "in_progress",
                "pass_rate": round(blackbox_passed / blackbox_cases * 100, 2),
                "failed_cases": blackbox_cases - blackbox_passed,
                "suggested_action": "请修复失败的测试用例后重试"
            }

    def get_status_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
        state = self.load_state()

        return {
            "phase": state.get('phase', 'unknown'),
            "test": state.get('test', {}),
            "development": state.get('development', {}),
            "deployment": state.get('deployment', {}),
            "metadata": state.get('metadata', {})
        }

    def print_status(self) -> None:
        """打印状态摘要"""
        summary = self.get_status_summary()

        print("\n" + "=" * 50)
        print("项目状态摘要")
        print("=" * 50)
        print(f"当前阶段: {summary['phase']}")
        print()

        test = summary['test']
        print("测试状态:")
        print(f"  状态: {test.get('status', 'unknown')}")
        print(f"  用例数: {test.get('blackbox_cases', 0)}")
        print(f"  通过数: {test.get('blackbox_passed', 0)}")
        print(f"  通过率: {test.get('pass_rate', 0)}%")
        print()

        dev = summary['development']
        print("开发状态:")
        print(f"  状态: {dev.get('status', 'unknown')}")
        print(f"  分支: {dev.get('branch', 'unknown')}")
        print(f"  里程碑: {dev.get('current_milestone', 'unknown')}")
        print()

        print("=" * 50)


def create_state_updater(project_path: str = ".") -> StateUpdater:
    """创建状态更新器的便捷函数"""
    return StateUpdater(project_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        updater = create_state_updater()

        if command == "status":
            updater.print_status()

        elif command == "complete-dev":
            result = updater.mark_development_complete()
            print(result)

        elif command == "test":
            if len(sys.argv) >= 4:
                cases = int(sys.argv[2])
                passed = int(sys.argv[3])
                result = updater.mark_test_complete(cases, passed)
                print(result)
            else:
                print("用法: python state_updater.py test <用例数> <通过数>")

        elif command == "set-phase":
            if len(sys.argv) >= 3:
                updater.set_phase(sys.argv[2])
            else:
                print("用法: python state_updater.py set-phase <阶段名>")

        else:
            print(f"未知命令: {command}")
            print("可用命令: status, complete-dev, test, set-phase")
    else:
        print("项目状态自动更新工具")
        print("用法:")
        print("  python state_updater.py status        # 查看状态")
        print("  python state_updater.py complete-dev  # 标记开发完成")
        print("  python state_updater.py test 100 95   # 更新测试统计")
        print("  python state_updater.py set-phase testing  # 设置阶段")
