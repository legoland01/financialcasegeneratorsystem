from typing import Dict, Any, List, Optional


class ContextInjector:
    """上下文注入器 - 将边界条件和反脱敏上下文合并"""

    def __init__(self):
        """初始化上下文注入器"""
        pass

    def inject(
        self,
        boundary_conditions: Dict[str, Any],
        deanonymization_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        注入所有上下文

        Args:
            boundary_conditions: 边界条件
            deanonymization_context: 反脱敏上下文
        Returns:
            合并后的上下文字典
        """
        parties = self._expand_party_info(
            boundary_conditions=boundary_conditions,
            deanonymization_context=deanonymization_context
        )

        context = {
            "boundary_conditions": boundary_conditions,
            "deanonymization_context": deanonymization_context,
            "parties": parties,
            "data_sources": self._extract_data_sources(boundary_conditions)
        }

        return context

    def _expand_party_info(
        self,
        boundary_conditions: Dict[str, Any],
        deanonymization_context: Dict[str, Any]
    ) -> Dict[str, Dict[str, str]]:
        """
        展开当事人信息

        Args:
            boundary_conditions: 边界条件
            deanonymization_context: 反脱敏上下文
        Returns:
            当事人信息字典
        """
        parties = {}
        company_profiles = deanonymization_context.get("公司Profile库", {})
        person_profiles = deanonymization_context.get("人物Profile库", {})

        if "当事人" in boundary_conditions:
            for role, marker in boundary_conditions["当事人"].items():
                if marker in company_profiles:
                    parties[role] = company_profiles[marker]
                elif marker in person_profiles:
                    parties[role] = person_profiles[marker]
                else:
                    parties[role] = {
                        "脱敏标识": marker,
                        "公司名称": f"公司（{marker}）",
                        "信用代码": "",
                        "法定代表人": "",
                        "注册地址": "",
                        "联系电话": ""
                    }

        return parties

    def _extract_data_sources(self, boundary_conditions: Dict[str, Any]) -> Dict[str, str]:
        """提取数据来源"""
        data_source = boundary_conditions.get("数据来源", "未知")
        return {
            "边界条件来源": data_source,
            "生成时间": self._get_current_time()
        }

    def _get_current_time(self) -> str:
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def inject_party_context(
        self,
        role: str,
        marker: str,
        deanonymization_context: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        注入单个当事人上下文

        Args:
            role: 当事人角色
            marker: 脱敏标识
            deanonymization_context: 反脱敏上下文
        Returns:
            当事人详细信息
        """
        company_profiles = deanonymization_context.get("公司Profile库", {})
        person_profiles = deanonymization_context.get("人物Profile库", {})

        if marker in company_profiles:
            profile = company_profiles[marker]
            profile["角色"] = role
            return profile
        elif marker in person_profiles:
            profile = person_profiles[marker]
            profile["角色"] = role
            return profile

        return {
            "脱敏标识": marker,
            "角色": role,
            "原始标识": marker
        }

    def format_party_for_prompt(self, role: str, party_info: Dict[str, str]) -> str:
        """
        格式化当事人信息用于Prompt

        Args:
            role: 当事人角色
            party_info: 当事人信息
        Returns:
            格式化的字符串
        """
        lines = [f"**{role}**"]

        if "公司名称" in party_info:
            lines.append(f"  - 公司名称：{party_info['公司名称']}")
        if "信用代码" in party_info:
            lines.append(f"  - 统一社会信用代码：{party_info['信用代码']}")
        if "法定代表人" in party_info:
            lines.append(f"  - 法定代表人：{party_info['法定代表人']}")
        if "注册地址" in party_info:
            lines.append(f"  - 注册地址：{party_info['注册地址']}")
        if "联系电话" in party_info:
            lines.append(f"  - 联系电话：{party_info['联系电话']}")
        if "姓名" in party_info:
            lines.append(f"  - 姓名：{party_info['姓名']}")
        if "身份证" in party_info:
            lines.append(f"  - 身份证号：{party_info['身份证']}")

        return "\n".join(lines)
