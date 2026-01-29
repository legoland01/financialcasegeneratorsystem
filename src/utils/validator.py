"""
自动验证模块 - 对生成的内容进行自动化验证
"""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class QualityValidator:
    """质量验证器 - 自动检查生成内容的质量"""

    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.issues: List[Dict] = []
        self.warnings: List[str] = []

    def reset(self):
        """重置验证状态"""
        self.issues = []
        self.warnings = []

    def check_de_anonymization(self, text: str) -> bool:
        """
        检查脱敏标记

        Returns:
            bool: True表示通过
        """
        placeholders = [
            "某某",
            "某某公司",
            "某某律师事务所",
            "某某公证处",
            "长江某",
            "华鑫某",
        ]

        found = []
        for p in placeholders:
            if p in text:
                found.append(p)

        # 检查单独的 XXXX（排除 "第XXXXXXX号" 这种证照编号格式）
        import re
        # 匹配独立的 XXXX 或 XXXXXXXX，而不是 "第XXXXXXX号" 这种格式
        standalone_xxxx = re.findall(r'(?<!第)X{4,}(?!号)', text)
        if standalone_xxxx:
            found.extend([f"X{len(x)}" for x in standalone_xxxx])

        if found:
            self.issues.append({
                "type": "脱敏标记",
                "severity": "error",
                "message": f"发现脱敏标记: {found}"
            })
            return False

        return True

    def check_markdown_format(self, text: str) -> bool:
        """
        检查Markdown格式

        Returns:
            bool: True表示通过
        """
        # 检查Markdown表格
        if "|" in text and ":---" in text:
            self.issues.append({
                "type": "Markdown表格",
                "severity": "error",
                "message": "发现Markdown表格格式，应该使用PDF真实表格"
            })
            return False

        # 检查代码块
        if "```" in text:
            self.issues.append({
                "type": "代码块",
                "severity": "warning",
                "message": "发现代码块标记，可能需要清理"
            })

        return True

    def check_clause_reference_format(self, text: str) -> bool:
        """
        检查条款引用格式
        例如 "第一条 第1.2款" 不应该被断开成多行

        Returns:
            bool: True表示通过
        """
        issues = []

        # 检测断开的条款引用模式
        lines = text.split('\n')

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 模式: 行末为 " 第"（如 "第一条 第"、"第四条 第"）
            # 后面有多个空行，然后是条款号
            if stripped.endswith(' 第'):
                # 查找下一个非空行
                j = i + 1
                while j < len(lines) and lines[j].strip() == '':
                    j += 1

                if j < len(lines):
                    following_line = lines[j].strip()
                    # 下一行以数字开头（条款号）
                    if re.match(r'^\d+\.\d+款', following_line) or re.match(r'^\d+款', following_line):
                        issues.append(f"条款引用断开: '{stripped}' -> '{following_line}'")

        if issues:
            self.issues.append({
                "type": "条款引用格式",
                "severity": "warning",
                "message": f"发现{len(issues)}处条款引用断开: {issues[:3]}"
            })
            return False

        return True

    def check_equipment_list(self, key_numbers: Dict) -> bool:
        """
        检查设备清单

        Returns:
            bool: True表示通过
        """
        rental = key_numbers.get("租赁物清单", [])

        if len(rental) == 0:
            self.issues.append({
                "type": "设备清单",
                "severity": "error",
                "message": "设备清单为空"
            })
            return False

        if len(rental) < 5:
            self.warnings.append(f"设备清单仅{len(rental)}项，建议至少5项")

        # 检查金额
        total = sum(item.get("评估价值", 0) for item in rental)
        if total == 0:
            self.issues.append({
                "type": "设备金额",
                "severity": "error",
                "message": "设备评估价值为0"
            })
            return False

        # 检查与合同金额一致性
        contract_amount = key_numbers.get("合同基础金额", {}).get("原合同金额", {}).get("数值", 0)
        if contract_amount and total != contract_amount:
            self.warnings.append(
                f"设备清单合计({total:,})与合同金额({contract_amount:,})不一致"
            )

        return True

    def check_collateral_list(self, key_numbers: Dict) -> bool:
        """
        检查抵押物清单

        Returns:
            bool: True表示通过
        """
        collateral = key_numbers.get("抵押物清单", [])

        if len(collateral) == 0:
            self.warnings.append("抵押物清单为空")

        return True

    def check_rent_plan(self, key_numbers: Dict) -> bool:
        """
        检查租金支付计划

        Returns:
            bool: True表示通过
        """
        rent_plan = key_numbers.get("租金支付计划", [])

        if len(rent_plan) < 12:
            self.warnings.append(f"租金支付计划仅{len(rent_plan)}期，建议至少12期")

        return True

    def check_evidence_completeness(self, evidence_dir: Path, expected_count: int) -> bool:
        """
        检查证据文件完整性

        Args:
            evidence_dir: 证据目录
            expected_count: 期望的证据数量

        Returns:
            bool: True表示通过
        """
        if not evidence_dir.exists():
            self.issues.append({
                "type": "证据目录",
                "severity": "error",
                "message": f"证据目录不存在: {evidence_dir}"
            })
            return False

        evidence_files = list(evidence_dir.glob("**/*.txt"))
        actual_count = len(evidence_files)

        if actual_count < expected_count:
            self.issues.append({
                "type": "证据数量",
                "severity": "error",
                "message": f"证据数量不足: 期望{expected_count}个，实际{actual_count}个"
            })
            return False

        if actual_count > expected_count:
            self.warnings.append(f"证据数量超出期望: 期望{expected_count}个，实际{actual_count}个")

        return True

    def check_evidence_content(self, evidence_file: Path) -> Tuple[bool, Dict]:
        """
        检查单个证据文件的内容质量

        Returns:
            Tuple[通过状态, 检查结果]
        """
        result = {
            "file": str(evidence_file),
            "passed": True,
            "checks": []
        }

        content = evidence_file.read_text(encoding='utf-8')
        char_count = len(content)

        # 检查长度
        if char_count < 100:
            result["checks"].append({
                "item": "长度",
                "status": "warning",
                "detail": f"内容较短({char_count}字符)"
            })
        else:
            result["checks"].append({
                "item": "长度",
                "status": "pass",
                "detail": f"{char_count}字符"
            })

        # 检查真实名称
        has_company = "有限公司" in content or "公司" in content
        result["checks"].append({
            "item": "公司名称",
            "status": "pass" if has_company else "warning",
            "detail": "包含公司名称" if has_company else "未发现公司名称"
        })

        # 检查日期
        has_dates = bool(re.search(r'202[0-9]', content))
        result["checks"].append({
            "item": "日期",
            "status": "pass" if has_dates else "warning",
            "detail": "包含日期" if has_dates else "未发现日期"
        })

        # 检查金额
        has_amounts = "元" in content and ("000" in content or "万" in content or "亿" in content)
        result["checks"].append({
            "item": "金额",
            "status": "pass" if has_amounts else "warning",
            "detail": "包含金额" if has_amounts else "未发现金额"
        })

        # 检查脱敏
        passed = self.check_de_anonymization(content)
        result["checks"].append({
            "item": "脱敏",
            "status": "pass" if passed else "fail",
            "detail": "无脱敏标记" if passed else "发现脱敏标记"
        })

        if not passed:
            result["passed"] = False

        # 检查条款引用格式
        clause_passed = self.check_clause_reference_format(content)
        result["checks"].append({
            "item": "条款引用",
            "status": "pass" if clause_passed else "warning",
            "detail": "条款引用格式正确" if clause_passed else "发现条款引用被断开"
        })

        return result["passed"], result

    def check_all_evidence(self, evidence_dir: Path) -> Dict:
        """
        检查所有证据文件

        Returns:
            Dict: 检查结果汇总
        """
        if not evidence_dir.exists():
            return {"passed": False, "message": "证据目录不存在"}

        evidence_files = list(evidence_dir.glob("**/*.txt"))
        results = {
            "total": len(evidence_files),
            "passed": 0,
            "failed": 0,
            "details": []
        }

        for f in evidence_files:
            passed, detail = self.check_evidence_content(f)
            results["details"].append(detail)
            if passed:
                results["passed"] += 1
            else:
                results["failed"] += 1

        results["passed_ratio"] = f"{results['passed']}/{results['total']}"
        return results

    def fix_rent_schedule_dates(self, key_numbers: Dict) -> Dict:
        """
        修复租金支付计划中的无效日期（如2021-13-26 -> 2022-01-26）

        Args:
            key_numbers: 关键数字数据

        Returns:
            修复后的数据
        """
        rent_plan = key_numbers.get("租金支付计划", [])
        rent_arrangement = key_numbers.get("租金安排", {})
        start_date_str = rent_arrangement.get("租金期限", {}).get("起始日期", "2021-02-26")

        if not rent_plan:
            return key_numbers

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            start_date = datetime(2021, 2, 26)

        fixed_count = 0
        for item in rent_plan:
            date_str = item.get("应付日期", "")
            if not date_str:
                continue

            try:
                parts = date_str.split("-")
                if len(parts) != 3:
                    continue

                year = int(parts[0])
                month = int(parts[1])
                day = int(parts[2])

                if 1 <= month <= 12:
                    continue

                period = item.get("期数", 1)

                target_year = start_date.year + (start_date.month + period - 1) // 12
                target_month = (start_date.month + period - 1) % 12 + 1
                target_day = min(day, self._get_month_days(target_year, target_month))

                new_date = f"{target_year:04d}-{target_month:02d}-{target_day:02d}"
                item["应付日期"] = new_date
                fixed_count += 1

            except (ValueError, IndexError, TypeError):
                continue

        if fixed_count > 0:
            self.warnings.append(f"已修复 {fixed_count} 个无效日期")

        return key_numbers

    def _get_month_days(self, year: int, month: int) -> int:
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

    def validate_key_numbers(self, key_numbers: Dict) -> bool:
        """
        验证关键数字数据

        Returns:
            bool: True表示通过所有检查
        """
        all_passed = True

        # 检查设备清单
        if not self.check_equipment_list(key_numbers):
            all_passed = False

        # 检查抵押物清单
        if not self.check_collateral_list(key_numbers):
            all_passed = False

        # 检查租金计划
        if not self.check_rent_plan(key_numbers):
            all_passed = False

        return all_passed

    def generate_report(self) -> str:
        """生成验证报告"""
        lines = []

        if not self.issues and not self.warnings:
            return "✅ 所有验证通过！"

        lines.append("=" * 60)
        lines.append("验证报告")
        lines.append("=" * 60)

        if self.issues:
            lines.append("\n❌ 错误:")
            for issue in self.issues:
                lines.append(f"  - [{issue['type']}] {issue['message']}")

        if self.warnings:
            lines.append("\n⚠️ 警告:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")

        lines.append("\n" + "=" * 60)
        lines.append("结论: " + ("✅ 通过" if not self.issues else "❌ 存在错误"))
        lines.append("=" * 60)

        return "\n".join(lines)

    def print_report(self):
        """打印验证报告"""
        print(self.generate_report())


def validate_pdf(pdf_path: Path) -> Dict:
    """
    验证PDF文件

    Args:
        pdf_path: PDF文件路径

    Returns:
        Dict: 验证结果
    """
    result = {
        "passed": True,
        "checks": []
    }

    if not pdf_path.exists():
        result["passed"] = False
        result["checks"].append({
            "name": "文件存在",
            "passed": False,
            "detail": "文件不存在"
        })
        return result

    result["checks"].append({
        "name": "文件存在",
        "passed": True,
        "detail": f"大小: {pdf_path.stat().st_size / 1024:.0f}KB"
    })

    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(str(pdf_path))
        text = "".join([p.extract_text() or "" for p in reader.pages])

        # 脱敏检查
        # 真正的脱敏标记：某某、某某公司、长江某等
        # 排除：第XXXXXXX号（正常的证照编号格式）
        deanon_markers = []
        for marker in ["某某", "某公司", "长江某", "华某"]:
            if marker in text:
                deanon_markers.append(marker)

        # 检查独立的 XXXX 标记（排除 "第XXXXXXX号" 这种正常的证照编号）
        # 正常证照号格式：第XXXXXXXX号（7-10个X）
        # 脱敏标记格式：单独的 XXXX 或 XXXXXXXX
        certificate_pattern = r'第X{7,10}号'
        text_without_certs = re.sub(certificate_pattern, '[证照编号]', text)

        # 检查剩余文本中的 XXXX
        remaining_xxxx = re.findall(r'X{4,}', text_without_certs)
        if remaining_xxxx:
            deanon_markers.extend([f"X{len(x)}" for x in remaining_xxxx])

        passed = len(deanon_markers) == 0

        result["checks"].append({
            "name": "脱敏标记",
            "passed": passed,
            "detail": f"无脱敏标记" if passed else f"发现脱敏标记: {deanon_markers}"
        })
        if not passed:
            result["passed"] = False

        # Markdown表格检查
        has_markdown = "|" in text and ":---" in text
        result["checks"].append({
            "name": "Markdown表格",
            "passed": not has_markdown,
            "detail": "无Markdown表格" if not has_markdown else "发现Markdown表格"
        })
        if has_markdown:
            result["passed"] = False

        # 页数
        result["checks"].append({
            "name": "页数",
            "passed": True,
            "detail": f"{len(reader.pages)}页"
        })

    except Exception as e:
        result["passed"] = False
        result["checks"].append({
            "name": "PDF读取",
            "passed": False,
            "detail": str(e)[:50]
        })

    return result


if __name__ == "__main__":
    import sys

    # 示例用法
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
        if target.is_file() and target.suffix == ".pdf":
            result = validate_pdf(target)
            print(f"PDF验证结果: {'✅ 通过' if result['passed'] else '❌ 失败'}")
            for check in result["checks"]:
                status = "✅" if check["passed"] else "❌"
                print(f"  {status} {check['name']}: {check['detail']}")
        elif target.is_dir():
            validator = QualityValidator()
            results = validator.check_all_evidence(target)
            print(f"证据验证: {results['passed']}/{results['total']} 通过")
            for detail in results["details"][:3]:
                status = "✅" if detail["passed"] else "❌"
                print(f"  {status} {detail['file'][-30:]}")
    else:
        print("用法: python3 validator.py <pdf文件或证据目录>")
