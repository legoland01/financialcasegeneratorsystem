#!/usr/bin/env python3
"""
修复0.4_key_numbers.json中的无效日期
将如"2021-13-26"之类的无效日期修复为正确的"2022-01-26"
"""
import json
from datetime import datetime
from pathlib import Path


def get_month_days(year: int, month: int) -> int:
    """获取月份天数"""
    if month in [1, 3, 5, 7, 8, 10, 12]:
        return 31
    elif month in [4, 6, 9, 11]:
        return 30
    else:
        if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
            return 29
        else:
            return 28


def fix_date(date_str: str, start_date, period: int) -> str:
    """修复单个日期"""
    try:
        parts = date_str.split("-")
        if len(parts) != 3:
            return date_str

        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])

        if 1 <= month <= 12:
            return date_str

        target_year = start_date.year + (start_date.month + period - 1) // 12
        target_month = (start_date.month + period - 1) % 12 + 1
        target_day = min(day, get_month_days(target_year, target_month))

        return f"{target_year:04d}-{target_month:02d}-{target_day:02d}"
    except (ValueError, IndexError, TypeError):
        return date_str


def main():
    data_path = Path("outputs/stage0/0.4_key_numbers.json")

    if not data_path.exists():
        print(f"❌ 文件不存在: {data_path}")
        return

    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rent_plan = data.get("租金支付计划", [])
    rent_arrangement = data.get("租金安排", {})
    start_date_str = rent_arrangement.get("租金期限", {}).get("起始日期", "2021-02-26")

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        start_date = datetime(2021, 2, 26)

    fixed_count = 0
    for item in rent_plan:
        date_str = item.get("应付日期", "")
        if not date_str:
            continue

        period = item.get("期数", 1)
        new_date = fix_date(date_str, start_date, period)

        if new_date != date_str:
            print(f"  期数{period:2d}: {date_str} -> {new_date}")
            item["应付日期"] = new_date
            fixed_count += 1

    if fixed_count > 0:
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 已修复 {fixed_count} 个无效日期")
        print(f"   文件已保存: {data_path}")
    else:
        print("✅ 无需修复，所有日期格式正确")


if __name__ == "__main__":
    main()
