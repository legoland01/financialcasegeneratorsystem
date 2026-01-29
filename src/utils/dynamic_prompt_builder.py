from pathlib import Path
from typing import Dict, Any, Optional

from context_injector import ContextInjector
from template_renderer import TemplateRenderer


class DynamicPromptBuilder:
    """动态Prompt构建器 - 注入上下文并渲染模板"""

    def __init__(
        self,
        template_dir: str = "config/evidence_templates",
        default_template: str = "contract_template.md"
    ):
        """
        初始化动态Prompt构建器

        Args:
            template_dir: 证据模板目录
            default_template: 默认模板
        """
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.context_injector = ContextInjector()
        self.template_renderer = TemplateRenderer()
        self.default_template = default_template

    def build_prompt(
        self,
        task_type: str,
        boundary_conditions: Dict[str, Any],
        deanonymization_context: Dict[str, Any],
        template_name: Optional[str] = None
    ) -> str:
        """
        构建完整的Prompt

        Args:
            task_type: 任务类型 (e.g., "生成融资租赁合同")
            boundary_conditions: 边界条件
            deanonymization_context: 反脱敏上下文
            template_name: 模板文件名
        Returns:
            完整的Prompt字符串
        """
        template = self._load_template(template_name)

        context = self.context_injector.inject(
            boundary_conditions=boundary_conditions,
            deanonymization_context=deanonymization_context
        )

        prompt = self.template_renderer.render(
            template=template,
            task_type=task_type,
            context=context
        )

        return prompt

    def build_contract_prompt(
        self,
        boundary_conditions: Dict[str, Any],
        deanonymization_context: Dict[str, Any],
        contract_type: str = "融资租赁合同"
    ) -> str:
        """
        构建合同生成Prompt

        Args:
            boundary_conditions: 边界条件
            deanonymization_context: 反脱敏上下文
            contract_type: 合同类型
        Returns:
            合同生成Prompt
        """
        return self.build_prompt(
            task_type=f"生成{contract_type}",
            boundary_conditions=boundary_conditions,
            deanonymization_context=deanonymization_context,
            template_name="contract_template.md"
        )

    def build_table_prompt(
        self,
        boundary_conditions: Dict[str, Any],
        deanonymization_context: Dict[str, Any],
        table_type: str = "租赁物清单"
    ) -> str:
        """
        构建表格生成Prompt

        Args:
            boundary_conditions: 边界条件
            deanonymization_context: 反脱敏上下文
            table_type: 表格类型
        Returns:
            表格生成Prompt
        """
        return self.build_prompt(
            task_type=f"生成{table_type}",
            boundary_conditions=boundary_conditions,
            deanonymization_context=deanonymization_context,
            template_name="table_template.md"
        )

    def _load_template(self, template_name: Optional[str] = None) -> str:
        """加载模板"""
        if template_name is None:
            template_name = self.default_template

        template_path = self.template_dir / template_name

        if template_path.exists():
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except (IOError, UnicodeDecodeError):
                pass

        return self._get_default_template(template_name)

    def _get_default_template(self, template_name: str) -> str:
        """获取默认模板"""
        if template_name == "contract_template.md":
            return self._get_default_contract_template()
        elif template_name == "table_template.md":
            return self._get_default_table_template()
        else:
            return self._get_default_generic_template()

    def _get_default_contract_template(self) -> str:
        """获取默认合同模板"""
        return """# 任务：{task_type}

## 当事人信息
**出租人**：
  - 公司名称：{parties_出租人_公司名称}
  - 统一社会信用代码：{parties_出租人_信用代码}
  - 法定代表人：{parties_出租人_法定代表人}
  - 注册地址：{parties_出租人_注册地址}
  - 联系电话：{parties_出租人_联系电话}

**承租人**：
  - 公司名称：{parties_承租人_公司名称}
  - 统一社会信用代码：{parties_承租人_信用代码}
  - 法定代表人：{parties_承租人_法定代表人}
  - 注册地址：{parties_承租人_注册地址}
  - 联系电话：{parties_承租人_联系电话}

## 案件关键数据
- 合同金额：{boundary_conditions_合同金额}元
- 签订日期：{boundary_conditions_签订日期}
- 租赁期限：{boundary_conditions_租赁期}个月
- 年利率：{boundary_conditions_利率}

## 生成要求
请根据以上信息生成一份完整的融资租赁合同，包含以下条款：
1. 租赁物条款
2. 租赁期限和租金支付条款
3. 租赁物的交付和验收条款
4. 租赁物的维修和保养条款
5. 违约责任条款
6. 争议解决条款

请直接生成合同正文内容，使用真实的公司名称和金额，不需要使用占位符。
"""

    def _get_default_table_template(self) -> str:
        """获取默认表格模板"""
        return """# 任务：{task_type}

## 案件关键数据
- 设备数量：{boundary_conditions_设备数量}
- 设备总价值：{boundary_conditions_合同金额}元

## 生成要求
请根据以上信息生成一份详细的设备清单表格，包含以下列：
1. 序号
2. 设备名称
3. 规格型号
4. 数量
5. 存放地点
6. 评估价值

请直接生成表格内容，使用真实的数据，不需要使用占位符。
表格格式请使用Markdown表格。
"""

    def _get_default_generic_template(self) -> str:
        """获取默认通用模板"""
        return """# 任务：{task_type}

## 边界条件
```
{boundary_conditions}
```

## 反脱敏上下文
```
{deanonymization_context}
```

## 生成要求
请根据以上信息完成指定任务。
请直接生成内容，使用真实数据，不需要使用占位符。
"""

    def add_template(
        self,
        name: str,
        content: str,
        overwrite: bool = False
    ) -> bool:
        """
        添加自定义模板

        Args:
            name: 模板名称
            content: 模板内容
            overwrite: 是否覆盖已存在的模板
        Returns:
            是否成功
        """
        template_path = self.template_dir / name

        if template_path.exists() and not overwrite:
            return False

        try:
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except IOError:
            return False

    def list_templates(self) -> list:
        """列出所有模板"""
        if not self.template_dir.exists():
            return []

        templates = []
        for file_path in self.template_dir.glob("*.md"):
            templates.append(file_path.name)

        return templates
