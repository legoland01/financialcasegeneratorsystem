"""阶段1服务：原告起诉包生成"""
from typing import Dict, Any, Optional, Callable
from pathlib import Path
from loguru import logger
import json
import re

from src.utils import (
    load_prompt_template,
    load_json,
    save_json,
    LLMClient,
    check_generation_result
)
from src.services.evidence_file_generator import EvidenceFileGenerator
from src.utils.placeholder_checker import PlaceholderChecker
from src.utils.retry_handler import RetryHandler


def _extract_evidence_planning(stage0_data: Dict, key: str = "0.5_证据归属规划") -> Dict:
    """安全提取证据归属规划，处理raw_response格式异常"""
    raw_data = stage0_data.get(key, {})
    
    if isinstance(raw_data, dict):
        if "证据归属规划表" in raw_data:
            return raw_data
        if "raw_response" in raw_data:
            logger.warning(f"{key} 返回 raw_response 格式，尝试解析...")
            try:
                parsed = json.loads(raw_data["raw_response"])
                if isinstance(parsed, dict) and "证据归属规划表" in parsed:
                    return parsed
            except json.JSONDecodeError:
                logger.error(f"无法解析 {key} 的 raw_response")
    
    logger.error(f"{key} 数据格式异常: {type(raw_data)}")
    return {"证据归属规划表": [], "证据分组": {}}


def clean_markdown(text: str) -> str:
    """清理markdown符号，生成纯文本"""
    # 去除代码块
    text = re.sub(r'```json\s*[\s\S]*?\s*```', '', text)
    text = re.sub(r'```\s*[\s\S]*?\s*```', '', text)
    text = re.sub(r'```[^`]*```', '', text)
    text = re.sub(r'~~~[^~]*~~~', '', text)

    # 去除行内代码
    text = re.sub(r'`([^`\n]+)`', r'\1', text)

    # 去除加粗
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)

    # 去除删除线
    text = re.sub(r'~~([^~]+)~~', r'\1', text)

    # 去除标题
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)

    # 去除引用
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)

    # 处理无序列表
    text = re.sub(r'^[-*+]\s+', '· ', text, flags=re.MULTILINE)

    # 处理有序列表
    text = re.sub(r'^(\d+)\.\s+', r'\1. ', text, flags=re.MULTILINE)

    # 处理任务列表
    text = re.sub(r'^-\s*\[\s*\]\s+', '□ ', text, flags=re.MULTILINE)
    text = re.sub(r'^-\s*\[x\]\s+', '■ ', text, flags=re.MULTILINE)

    # 处理分隔线
    text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)

    # 去除链接格式
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)

    # 去除HTML标签
    text = re.sub(r'<[^>]+>', '', text)

    # 去除多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def _generate_with_placeholder_check(
    generate_func: Callable,
    *args,
    **kwargs
) -> Dict[str, Any]:
    """
    带占位符检查的生成包装函数

    Args:
        generate_func: 生成函数
        *args, **kwargs: 生成函数参数

    Returns:
        Dict包含: success, content, attempts, placeholders, error
    """
    checker = PlaceholderChecker()
    handler = RetryHandler(max_retries=3)
    return handler.execute_with_retry(generate_func, *args, **kwargs)


class Stage1Service:
    """阶段1服务：原告起诉包"""
    
    def __init__(
        self,
        prompt_dir: str = "prompts",
        schema_dir: str = "schemas",
        output_dir: str = "outputs",
        llm_client: Optional[LLMClient] = None
    ):
        """
        初始化阶段1服务
        
        Args:
            prompt_dir: 提示词目录
            schema_dir: Schema目录
            output_dir: 输出目录
            llm_client: 大模型客户端
        """
        self.prompt_dir = Path(prompt_dir)
        self.schema_dir = Path(schema_dir)
        self.output_dir = Path(output_dir)
        self.llm_client = llm_client or LLMClient()

        # 初始化占位符检查器和重试处理器
        self.checker = PlaceholderChecker()
        self.retry_handler = RetryHandler(max_retries=3)

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_complaint(
        self,
        stage0_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成民事起诉状
        
        Args:
            stage0_data: 阶段0数据
        
        Returns:
            生成的起诉状和质量检查报告
        """
        logger.info("开始生成民事起诉状")
        
        # 提取阶段0数据
        case_info = stage0_data["0.1_结构化提取"]["案件基本信息"]
        claims = stage0_data["0.1_结构化提取"]["原告诉讼请求"]
        profiles = stage0_data["0.2_脱敏替换策划"]
        timeline = stage0_data["0.3_交易结构重构"]["交易时间线"]
        key_numbers = stage0_data["0.4_关键数字清单"]
        
        # 安全获取证据归属规划（处理raw_response格式异常）
        evidence_planning = _extract_evidence_planning(stage0_data)
        plaintiff_evidence = [
            e for e in evidence_planning.get("证据归属规划表", [])
            if e.get("应归属方") == "原告"
        ]
        
        # 加载提示词
        prompt_path = self.prompt_dir / "stage1" / "1.1_起诉状生成.md"
        prompt = load_prompt_template(str(prompt_path))
        
        # 构建完整提示词
        full_prompt = f"""
{prompt}

案件基本信息：
{json.dumps(case_info, ensure_ascii=False, indent=2)}

原告诉讼请求：
{json.dumps(claims, ensure_ascii=False, indent=2)}

人物Profile库：
{json.dumps(profiles.get("人物Profile库", {}), ensure_ascii=False, indent=2)}

公司Profile库：
{json.dumps(profiles.get("公司Profile库", {}), ensure_ascii=False, indent=2)}

交易时间线：
{json.dumps(timeline, ensure_ascii=False, indent=2)}

关键金额清单：
{json.dumps(key_numbers, ensure_ascii=False, indent=2)}

原告证据归属规划：
{json.dumps(plaintiff_evidence, ensure_ascii=False, indent=2)}

        请按照上述要求生成完整的民事起诉状。
注意：禁止使用占位符如"某某"、"某公司"、"X4"等，必须填写真实信息。
"""

        # 带占位符检测的生成
        def generate_with_retry():
            return self.llm_client.generate(full_prompt)

        result = self.retry_handler.execute_with_retry(generate_with_retry)

        if result["success"]:
            response = result["result"]
            logger.success(f"起诉状生成成功（第{result['attempts']}次尝试）")
        else:
            response = result.get("result", "") or ""
            logger.warning(
                f"起诉状生成失败，占位符: {result['placeholders'][:3]}"
            )

        # 清理markdown符号
        clean_response = clean_markdown(response)

        # 质量检查
        generation_result = {"content": clean_response}
        quality_report = check_generation_result(generation_result, stage0_data)

        # 保存结果
        output_path = self.output_dir / "stage1" / "民事起诉状.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(clean_response)
        
        # 保存质量报告
        report_path = self.output_dir / "stage1" / "民事起诉状_质量报告.json"
        save_json(quality_report, str(report_path))
        
        logger.info(f"民事起诉状已生成并保存到 {output_path}")
        
        return {
            "content": response,
            "output_path": str(output_path),
            "quality_report": quality_report
        }
    
    def generate_evidence_package(
        self,
        stage0_data: Dict[str, Any],
        evidence_group_index: int = 0
    ) -> Dict[str, Any]:
        """
        生成原告证据包（旧方法：生成合并的证据包文件）

        Args:
            stage0_data: 阶段0数据
            evidence_group_index: 证据组序号

        Returns:
            生成的证据包和质量检查报告
        """
        logger.info(f"开始生成原告证据包(证据组{evidence_group_index})")

        # 提取阶段0数据
        profiles = stage0_data["0.2_脱敏替换策划"]
        timeline = stage0_data["0.3_交易结构重构"]["交易时间线"]
        key_numbers = stage0_data["0.4_关键数字清单"]
        evidence_planning = _extract_evidence_planning(stage0_data)

        # 筛选原告证据
        plaintiff_evidence = [
            e for e in evidence_planning.get("证据归属规划表", [])
            if e.get("应归属方") == "原告"
        ]

        # 按证据组分组
        evidence_groups = {}
        for evidence in plaintiff_evidence:
            group_id = evidence.get("证据组", 1)
            if group_id not in evidence_groups:
                evidence_groups[group_id] = []
            evidence_groups[group_id].append(evidence)

        # 获取指定证据组
        if evidence_group_index not in evidence_groups:
            logger.warning(f"证据组{evidence_group_index}不存在")
            return {}

        evidence_group = evidence_groups[evidence_group_index]

        # 加载提示词
        prompt_path = self.prompt_dir / "stage1" / "1.2_证据包生成.md"
        prompt = load_prompt_template(str(prompt_path))

        # 构建完整提示词
        full_prompt = f"""
{prompt}

案件基本信息：
{json.dumps(stage0_data["0.1_结构化提取"]["案件基本信息"], ensure_ascii=False, indent=2)}

人物Profile库：
{json.dumps(profiles.get("人物Profile库", {}), ensure_ascii=False, indent=2)}

公司Profile库：
{json.dumps(profiles.get("公司Profile库", {}), ensure_ascii=False, indent=2)}

机构Profile库：
{json.dumps(profiles.get("机构Profile库", {}), ensure_ascii=False, indent=2)}

编号体系规则：
{json.dumps(profiles.get("编号体系规则", {}), ensure_ascii=False, indent=2)}

交易时间线：
{json.dumps(timeline, ensure_ascii=False, indent=2)}

关键金额清单：
{json.dumps(key_numbers, ensure_ascii=False, indent=2)}

证据归属规划表：
{json.dumps(evidence_group, ensure_ascii=False, indent=2)}

当前证据组序号：{evidence_group_index}

请按照上述要求生成该证据组的所有证据文件。
注意：禁止使用占位符如"某某"、"某公司"、"X4"等，必须填写真实信息。
"""

        # 带占位符检测的生成
        def generate_with_retry():
            return self.llm_client.generate(full_prompt)

        result = self.retry_handler.execute_with_retry(generate_with_retry)

        if result["success"]:
            response = result["result"]
            logger.success(f"证据组{evidence_group_index}生成成功（第{result['attempts']}次尝试）")
        else:
            response = result.get("result", "") or ""
            logger.error(
                f"证据组{evidence_group_index}生成失败，"
                f"已重试{result['attempts']}次，占位符: {result['placeholders'][:3]}"
            )

        # 清理markdown符号
        clean_response = clean_markdown(response)

        # 质量检查
        generation_result = {"content": clean_response}
        quality_report = check_generation_result(generation_result, stage0_data)

        # 保存结果
        output_path = self.output_dir / "stage1" / f"原告证据包_证据组{evidence_group_index}.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(clean_response)

        # 保存质量报告
        report_path = self.output_dir / "stage1" / f"原告证据包_证据组{evidence_group_index}_质量报告.json"
        save_json(quality_report, str(report_path))

        logger.info(f"原告证据包(证据组{evidence_group_index})已生成并保存到 {output_path}")

        return {
            "content": response,
            "output_path": str(output_path),
            "quality_report": quality_report
        }

    def generate_evidence_files(
        self,
        stage0_data: Dict[str, Any],
        use_new_architecture: bool = True
    ) -> Dict[str, Any]:
        """
        生成原告证据文件（新架构：生成独立的证据文件）

        Args:
            stage0_data: 阶段0数据
            use_new_architecture: 是否使用新架构（默认True）

        Returns:
            证据索引和质量检查报告
        """
        if not use_new_architecture:
            return self.generate_evidence_package(stage0_data)

        logger.info("开始使用新架构生成原告证据文件")

        evidence_planning = _extract_evidence_planning(stage0_data)
        evidence_output_dir = self.output_dir / "stage1" / "evidence"
        evidence_output_dir.mkdir(parents=True, exist_ok=True)

        evidence_generator = EvidenceFileGenerator(
            prompt_dir=str(self.prompt_dir),
            output_dir=str(evidence_output_dir),
            llm_client=self.llm_client
        )

        evidence_index = evidence_generator.generate_all_evidence_files(
            stage0_data=stage0_data,
            evidence_planning=evidence_planning,
            party="原告"
        )

        evidence_index_path = evidence_output_dir / "evidence_index.json"
        save_json(evidence_index, str(evidence_index_path))

        logger.info(f"原告证据文件生成完成，共 {evidence_index.get('证据总数', 0)} 个证据")

        return {
            "evidence_index": evidence_index,
            "output_dir": str(evidence_output_dir)
        }
    
    def generate_procedural_files(
        self,
        stage0_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成原告程序性文件
        
        Args:
            stage0_data: 阶段0数据
        
        Returns:
            生成的程序性文件和质量检查报告
        """
        logger.info("开始生成原告程序性文件")
        
        # 提取阶段0数据
        case_info = stage0_data["0.1_结构化提取"]["案件基本信息"]
        profiles = stage0_data["0.2_脱敏替换策划"]
        timeline = stage0_data["0.3_交易结构重构"]["交易时间线"]
        key_numbers = stage0_data["0.4_关键数字清单"]
        
        # 加载提示词
        prompt_path = self.prompt_dir / "stage1" / "1.3_程序文件生成.md"
        prompt = load_prompt_template(str(prompt_path))
        
        # 构建完整提示词
        full_prompt = f"""
{prompt}

案件基本信息：
{json.dumps(case_info, ensure_ascii=False, indent=2)}

人物Profile库：
{json.dumps(profiles.get("人物Profile库", {}), ensure_ascii=False, indent=2)}

公司Profile库：
{json.dumps(profiles.get("公司Profile库", {}), ensure_ascii=False, indent=2)}

交易时间线：
{json.dumps(timeline, ensure_ascii=False, indent=2)}

关键金额清单：
{json.dumps(key_numbers, ensure_ascii=False, indent=2)}

        请按照上述要求生成原告提交法院的所有程序性文件。
注意：禁止使用占位符如"某某"、"某公司"、"X4"等，必须填写真实信息。
"""

        # 带占位符检测的生成
        def generate_with_retry():
            return self.llm_client.generate(full_prompt)

        result = self.retry_handler.execute_with_retry(generate_with_retry)

        if result["success"]:
            response = result["result"]
            logger.success(f"程序性文件生成成功（第{result['attempts']}次尝试）")
        else:
            response = result.get("result", "") or ""
            logger.warning(
                f"程序性文件生成失败，占位符: {result['placeholders'][:3]}"
            )

        # 清理markdown符号
        clean_response = clean_markdown(response)

        # 质量检查
        generation_result = {"content": clean_response}
        quality_report = check_generation_result(generation_result, stage0_data)

        # 保存结果
        output_path = self.output_dir / "stage1" / "原告程序性文件.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(clean_response)
        
        # 保存质量报告
        report_path = self.output_dir / "stage1" / "原告程序性文件_质量报告.json"
        save_json(quality_report, str(report_path))
        
        logger.info(f"原告程序性文件已生成并保存到 {output_path}")
        
        return {
            "content": response,
            "output_path": str(output_path),
            "quality_report": quality_report
        }
    
    def run_all(self, stage0_data: Dict[str, Any], use_new_architecture: bool = True) -> Dict[str, Any]:
        """
        执行阶段1的所有任务

        Args:
            stage0_data: 阶段0数据
            use_new_architecture: 是否使用新架构（默认True，生成独立证据文件）

        Returns:
            阶段1完整输出
        """
        logger.info("开始执行阶段1：原告起诉包生成")

        # 生成民事起诉状
        complaint = self.generate_complaint(stage0_data)

        # 生成证据包
        logger.info("开始生成原告证据包")

        if use_new_architecture:
            evidence_result = self.generate_evidence_files(
                stage0_data=stage0_data,
                use_new_architecture=True
            )
            evidence_package_result = evidence_result.get("evidence_index", {})
        else:
            evidence_planning = _extract_evidence_planning(stage0_data)
            plaintiff_evidence = [
                e for e in evidence_planning.get("证据归属规划表", [])
                if e.get("应归属方") == "原告"
            ]
            evidence_groups = {}
            for evidence in plaintiff_evidence:
                group_id = evidence.get("证据组", 1)
                if group_id not in evidence_groups:
                    evidence_groups[group_id] = []
                evidence_groups[group_id].append(evidence)

            logger.info(f"发现 {len(evidence_groups)} 个原告证据组")

            evidence_package_result = {}
            for group_id in sorted(evidence_groups.keys()):
                logger.info(f"开始生成证据组{group_id}，包含 {len(evidence_groups[group_id])} 个证据")
                group_result = self.generate_evidence_package(
                    stage0_data,
                    evidence_group_index=group_id
                )
                evidence_package_result[f"证据组{group_id}"] = group_result

        # 生成程序性文件
        procedural_files = self.generate_procedural_files(stage0_data)

        # 整合结果
        result = {
            "民事起诉状": complaint,
            "证据包": evidence_package_result,
            "程序性文件": procedural_files,
            "使用新架构": use_new_architecture
        }

        # 保存完整结果
        output_path = self.output_dir / "stage1" / "plaintiff_package.json"
        save_json(result, str(output_path))
        logger.info(f"阶段1完成，完整结果已保存到 {output_path}")
        if use_new_architecture:
            evidence_count = evidence_package_result.get("证据总数", 0)
            logger.info(f"使用新架构，共生成 {evidence_count} 个独立证据文件")
        else:
            logger.info(f"共生成 {len(evidence_package_result)} 个证据组")

        return result
