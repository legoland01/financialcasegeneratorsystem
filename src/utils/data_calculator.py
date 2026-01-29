from datetime import datetime, timedelta
from typing import List, Dict, Optional
import math


class DataCalculator:
    """数据计算器 - 根据边界条件计算详细数据"""

    def __init__(self):
        """初始化数据计算器"""
        pass

    def calculate_rent_schedule(
        self,
        principal: float,
        annual_rate: float,
        periods: int,
        start_date: str,
        payment_day: int = 24,
        paid_periods: int = 2
    ) -> List[Dict]:
        """
        计算租金支付计划（等额本息）

        Args:
            principal: 本金（融资金额）
            annual_rate: 年利率
            periods: 期数
            start_date: 开始日期 (YYYY-MM-DD)
            payment_day: 每月支付日（默认24日）
            paid_periods: 已付期数（默认2期）
        Returns:
            租金支付计划列表
        """
        if principal <= 0:
            raise ValueError("本金必须大于0")

        if periods <= 0:
            raise ValueError("期数必须大于0")

        if annual_rate < 0:
            raise ValueError("利率不能为负")

        monthly_rate = annual_rate / 12

        if monthly_rate > 0:
            monthly_payment = principal * (
                monthly_rate * (1 + monthly_rate) ** periods
            ) / ((1 + monthly_rate) ** periods - 1)
        else:
            monthly_payment = principal / periods

        start = datetime.strptime(start_date, "%Y-%m-%d")
        remaining_principal = principal
        total_interest = 0
        total_principal = 0

        schedule = []

        for i in range(1, periods + 1):
            interest = remaining_principal * monthly_rate
            principal_payment = monthly_payment - interest

            if i == periods:
                principal_payment = remaining_principal
                monthly_payment = principal_payment + interest

            remaining_principal -= principal_payment
            total_interest += interest
            total_principal += principal_payment

            payment_date = self._calculate_payment_date(start, i, payment_day)

            schedule.append({
                "期数": i,
                "应付日期": payment_date.strftime("%Y-%m-%d"),
                "租金金额": round(monthly_payment, 2),
                "本金金额": round(principal_payment, 2),
                "利息金额": round(interest, 2),
                "剩余本金": round(remaining_principal, 2),
                "支付状态": "已付" if i <= paid_periods else "未付"
            })

        return schedule

    def _calculate_payment_date(
        self,
        start_date: datetime,
        period: int,
        payment_day: int
    ) -> datetime:
        """计算支付日期"""
        target_year = start_date.year + (start_date.month + period - 1) // 12
        target_month = (start_date.month + period - 1) % 12 + 1

        day = min(payment_day, self._get_month_days(target_year, target_month))

        try:
            return datetime(target_year, target_month, day)
        except ValueError:
            return datetime(target_year, target_month, self._get_month_days(target_year, target_month))

    def _get_month_days(self, year: int, month: int) -> int:
        """获取月份天数"""
        if month in [1, 3, 5, 7, 8, 10, 12]:
            return 31
        elif month in [4, 6, 9, 11]:
            return 30
        else:
            if self._is_leap_year(year):
                return 29
            else:
                return 28

    def _is_leap_year(self, year: int) -> bool:
        """判断闰年"""
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    def calculate_equipment_allocation(
        self,
        total_value: int,
        equipment_count: int,
        min_value_ratio: float = 0.05,
        max_value_ratio: float = 0.15
    ) -> List[int]:
        """
        分配设备价值

        Args:
            total_value: 总价值
            equipment_count: 设备数量
            min_value_ratio: 最小价值比例
            max_value_ratio: 最大价值比例
        Returns:
            各设备价值列表
        """
        if total_value <= 0:
            raise ValueError("总价值必须大于0")

        if equipment_count <= 0:
            raise ValueError("设备数量必须大于0")

        if min_value_ratio <= 0 or max_value_ratio <= 0:
            raise ValueError("比例必须为正数")

        if min_value_ratio > max_value_ratio:
            raise ValueError("最小比例不能大于最大比例")

        allocation = []
        remaining_value = total_value

        for i in range(equipment_count):
            if i == equipment_count - 1:
                value = remaining_value
            else:
                max_value = int(remaining_value * max_value_ratio)
                min_value = int(remaining_value * min_value_ratio)
                value = self._random_int_in_range(min_value, max_value)
                remaining_value -= value

            allocation.append(max(value, 1))

        return allocation

    def _random_int_in_range(self, min_val: int, max_val: int) -> int:
        """在范围内生成随机整数"""
        if min_val > max_val:
            min_val, max_val = max_val, min_val
        if min_val == max_val:
            return min_val
        return __import__('random').randint(min_val, max_val)

    def calculate_installment_details(
        self,
        principal: float,
        annual_rate: float,
        periods: int
    ) -> Dict:
        """
        计算分期付款详情

        Args:
            principal: 本金
            annual_rate: 年利率
            periods: 期数
        Returns:
            分期付款详情
        """
        monthly_rate = annual_rate / 12

        if monthly_rate > 0:
            monthly_payment = principal * (
                monthly_rate * (1 + monthly_rate) ** periods
            ) / ((1 + monthly_rate) ** periods - 1)
            total_payment = monthly_payment * periods
            total_interest = total_payment - principal
        else:
            monthly_payment = principal / periods
            total_payment = principal
            total_interest = 0

        return {
            "月供金额": round(monthly_payment, 2),
            "总还款额": round(total_payment, 2),
            "总利息": round(total_interest, 2),
            "期数": periods,
            "年利率": annual_rate,
            "月利率": round(monthly_rate, 6)
        }

    def calculate_early_repayment(
        self,
        original_principal: float,
        annual_rate: float,
        periods: int,
        start_date: str,
        early_repayment_period: int,
        prepayment_amount: float
    ) -> Dict:
        """
        计算提前还款详情

        Args:
            original_principal: 原始本金
            annual_rate: 年利率
            periods: 总期数
            start_date: 开始日期
            early_repayment_period: 提前还款期数
            prepayment_amount: 提前还款金额
        Returns:
            提前还款详情
        """
        monthly_rate = annual_rate / 12

        rent_schedule = self.calculate_rent_schedule(
            principal=original_principal,
            annual_rate=annual_rate,
            periods=early_repayment_period,
            start_date=start_date
        )

        remaining_principal = 0
        for item in rent_schedule:
            remaining_principal = item.get("剩余本金", 0)

        if prepayment_amount > remaining_principal:
            prepayment_amount = remaining_principal

        settlement_amount = prepayment_amount + remaining_principal * 0.01

        return {
            "提前还款期数": early_repayment_period,
            "剩余本金": round(remaining_principal, 2),
            "提前还款金额": round(prepayment_amount, 2),
            "违约金": round(remaining_principal * 0.01, 2),
            "结清金额": round(settlement_amount, 2),
            "还款后状态": "已结清"
        }

    def format_currency(self, amount: float) -> str:
        """格式化货币"""
        return f"¥{amount:,.2f}"

    def format_percentage(self, rate: float, decimals: int = 2) -> str:
        """格式化百分比"""
        return f"{rate * 100:.{decimals}f}%"
