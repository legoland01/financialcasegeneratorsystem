"""阶段3服务：法院审理包生成"""
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger
import json

from src.utils import (
    load_prompt_template,
    load_json,
    save_json,
    LLMClient,
    check_generation_result
)


class Stage3Service:
    """阶段3服务：法院审理包"""
    
    def __init__(
        self,
        prompt_dir: str = "prompts",
        schema_dir: str = "schemas",
        output_dir: str = "outputs",
        llm_client: Optional[LLMClient] = None
    ):
        """
        初始化阶段3服务
        
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
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_trial_transcript(
        self,
        stage0_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成庭审笔录
        
        Args:
            stage0_data: 阶段0数据
        
        Returns:
            生成的庭审笔录和质量检查报告
        """
        logger.info("开始生成庭审笔录")
        
        # 提取阶段0数据
        case_info = stage0_data["0.1_结构化提取"]["案件基本信息"]
        claims = stage0_data["0.1_结构化提取"]["原告诉讼请求"]
        defenses = stage0_data["0.1_结构化提取"]["被告抗辩意见"]
        court_findings = stage0_data["0.1_结构化提取"]["法院认定部分"]
        profiles = stage0_data["0.2_脱敏替换策划"]
        timeline = stage0_data["0.3_交易结构重构"]["交易时间线"]
        evidence_planning = stage0_data["0.5_证据归属规划"]
        
        # 提取争议焦点
        dispute_focus = court_findings.get("事实认定", {}).get("争议焦点", [])
        
        # 加载提示词
        prompt_path = self.prompt_dir / "stage3" / "3.1_庭审笔录生成.md"
        prompt = load_prompt_template(str(prompt_path))
        
        # 构建完整提示词
        full_prompt = f"""
{prompt}

案件基本信息：
{json.dumps(case_info, ensure_ascii=False, indent=2)}

原告诉讼请求：
{json.dumps(claims, ensure_ascii=False, indent=2)}

被告抗辩意见：
{json.dumps(defenses, ensure_ascii=False, indent=2)}

法院认定部分：
{json.dumps(court_findings, ensure_ascii=False, indent=2)}

人物Profile库：
{json.dumps(profiles.get("人物Profile库", {}), ensure_ascii=False, indent=2)}

交易时间线：
{json.dumps(timeline, ensure_ascii=False, indent=2)}

证据归属规划表：
{json.dumps(evidence_planning["证据归属规划表"], ensure_ascii=False, indent=2)}

争议焦点：
{json.dumps(dispute_focus, ensure_ascii=False, indent=2)}

请按照上述要求生成完整的庭审笔录。
"""
        
        # 调用大模型
        response = self.llm_client.generate(full_prompt)
        
        # 质量检查
        generation_result = {"content": response}
        quality_report = check_generation_result(generation_result, stage0_data)
        
        # 保存结果
        output_path = self.output_dir / "stage3" / "庭审笔录.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response)
        
        # 保存质量报告
        report_path = self.output_dir / "stage3" / "庭审笔录_质量报告.json"
        save_json(quality_report, str(report_path))
        
        logger.info(f"庭审笔录已生成并保存到 {output_path}")
        
        return {
            "content": response,
            "output_path": str(output_path),
            "quality_report": quality_report
        }
    
    def replace_anonymized_judgment(
        self,
        original_judgment: str,
        stage0_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        判决书脱敏替换
        
        Args:
            original_judgment: 原始判决书文本
            stage0_data: 阶段0数据
        
        Returns:
            替换后的判决书
        """
        logger.info("开始判决书脱敏替换")
        
        # 提取阶段0数据
        profiles = stage0_data["0.2_脱敏替换策划"]
        evidence_planning = stage0_data["0.5_证据归属规划"]
        
        # 加载提示词
        prompt_path = self.prompt_dir / "stage3" / "3.2_判决书脱敏替换.md"
        prompt = load_prompt_template(str(prompt_path))
        
        # 构建完整提示词
        full_prompt = f"""
{prompt}

原始判决书文本：
{original_judgment}

人物Profile库：
{json.dumps(profiles.get("人物Profile库", {}), ensure_ascii=False, indent=2)}

公司Profile库：
{json.dumps(profiles.get("公司Profile库", {}), ensure_ascii=False, indent=2)}

机构Profile库：
{json.dumps(profiles.get("机构Profile库", {}), ensure_ascii=False, indent=2)}

证据归属规划表：
{json.dumps(evidence_planning["证据归属规划表"], ensure_ascii=False, indent=2)}

请按照上述要求对判决书进行脱敏替换。
"""
        
        # 调用大模型
        response = self.llm_client.generate(full_prompt)
        
        # 保存结果
        output_path = self.output_dir / "stage3" / "判决书(脱敏替换).txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response)
        
        logger.info(f"判决书脱敏替换完成并保存到 {output_path}")
        
        return {
            "content": response,
            "output_path": str(output_path)
        }
    
    def run_all(
        self,
        original_judgment: str,
        stage0_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行阶段3的所有任务
        
        Args:
            original_judgment: 原始判决书文本
            stage0_data: 阶段0数据
        
        Returns:
            阶段3完整输出
        """
        logger.info("开始执行阶段3：法院审理包生成")
        
        # 生成庭审笔录
        trial_transcript = self.generate_trial_transcript(stage0_data)
        
        # 判决书脱敏替换
        replaced_judgment = self.replace_anonymized_judgment(original_judgment, stage0_data)
        
        # 整合结果
        result = {
            "庭审笔录": trial_transcript,
            "判决书脱敏替换": replaced_judgment
        }
        
        # 保存完整结果
        output_path = self.output_dir / "stage3" / "court_package.json"
        save_json(result, str(output_path))
        logger.info(f"阶段3完成，完整结果已保存到 {output_path}")
        
        return result
