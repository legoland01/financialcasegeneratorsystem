"""重试处理器"""
from typing import Callable, Any, Dict, List
from loguru import logger
from src.utils.placeholder_checker import PlaceholderChecker


class RetryHandler:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.checker = PlaceholderChecker()
        self.retry_count = 0
        self.retry_history: List[Dict] = []

    def execute_with_retry(
        self,
        generate_func: Callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        self.retry_count = 0
        self.retry_history = []

        for attempt in range(self.max_retries + 1):
            self.retry_count = attempt

            try:
                result = generate_func(*args, **kwargs)
                is_clean, placeholders = self.checker.check(result)

                retry_info = {
                    "attempt": attempt + 1,
                    "success": is_clean,
                    "placeholders": placeholders,
                    "has_result": result is not None
                }
                self.retry_history.append(retry_info)

                if is_clean:
                    logger.success(f"生成成功，第{attempt + 1}次尝试")
                    return {
                        "success": True,
                        "result": result,
                        "attempts": attempt + 1,
                        "placeholders": [],
                        "error": None
                    }
                else:
                    logger.warning(
                        f"尝试 {attempt + 1}/{self.max_retries + 1} 失败，"
                        f"占位符: {placeholders[:3]}..."
                    )

            except Exception as e:
                logger.error(f"尝试 {attempt + 1} 异常: {e}")
                self.retry_history.append({
                    "attempt": attempt + 1,
                    "success": False,
                    "placeholders": [],
                    "error": str(e),
                    "has_result": False
                })

        logger.error(f"重试 {self.max_retries + 1} 次后仍失败")
        return {
            "success": False,
            "result": self.retry_history[-1].get("result"),
            "attempts": self.max_retries + 1,
            "placeholders": self.retry_history[-1].get("placeholders", []),
            "error": "超过最大重试次数"
        }

    def get_retry_stats(self) -> Dict[str, Any]:
        total = len(self.retry_history)
        first_success = total > 0 and self.retry_history[0].get("success", False)
        return {
            "total_attempts": total,
            "first_try_success": first_success,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "history": self.retry_history
        }
