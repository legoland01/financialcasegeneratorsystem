"""证据文件生成器 - 生成每个证据的独立文件"""
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from loguru import logger
import json
import re

from src.utils import (
    load_prompt_template,
    LLMClient,
    save_json
)
from src.utils.retry_handler import RetryHandler
from src.utils.placeholder_checker import PlaceholderChecker


def _extract_evidence_list(evidence_planning: Any) -> List[Dict]:
    """安全提取证据列表，处理raw_response格式异常"""
    if isinstance(evidence_planning, list):
        return evidence_planning
    
    if isinstance(evidence_planning, dict):
        if "证据归属规划表" in evidence_planning:
            return evidence_planning["证据归属规划表"]
        if "raw_response" in evidence_planning:
            logger.warning("evidence_planning 返回 raw_response 格式，尝试解析...")
            try:
                raw = evidence_planning["raw_response"]
                if isinstance(raw, str):
                    json_match = re.search(r'\{[\s\S]*\}', raw)
                    if json_match:
                        parsed = json.loads(json_match.group())
                        if isinstance(parsed, dict) and "证据归属规划表" in parsed:
                            return parsed["证据归属规划表"]
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"无法解析 evidence_planning 的 raw_response: {e}")
    
    logger.error(f"evidence_planning 数据格式异常: {type(evidence_planning)}")
    return []


def _build_replacement_map(stage0_data: Dict[str, Any]) -> Dict[str, str]:
    """从stage0数据构建替换映射表"""
    replace_map = {}
    
    anonymization_plan = stage0_data.get("0.2_脱敏替换策划", {})
    if not anonymization_plan:
        anonymization_plan = stage0_data.get("0.2_anonymization_plan", {})
    
    if isinstance(anonymization_plan, dict):
        replace_map.update(anonymization_plan.get("替换映射表", {}))
        
        for key, company in anonymization_plan.get("公司Profile库", {}).items():
            original = company.get("原脱敏标识")
            real_name = company.get("公司名称")
            if original and real_name:
                replace_map[original] = real_name
        
        for key, person in anonymization_plan.get("人物Profile库", {}).items():
            original = person.get("原脱敏标识")
            real_name = person.get("姓名")
            if original and real_name:
                replace_map[original] = real_name
    
    return replace_map


def _clean_placeholders(text: str, stage0_data: Dict[str, Any]) -> str:
    """清理文本中的占位符"""
    replace_map = _build_replacement_map(stage0_data)
    
    sorted_replacements = sorted(replace_map.items(), key=lambda x: len(x[0]), reverse=True)
    for placeholder, replacement in sorted_replacements:
        text = text.replace(placeholder, replacement)
    
    text = re.sub(r'【\s*】', '', text)
    
    text = re.sub(r'（\s*）', '', text)
    
    text = re.sub(r'\(\s*\)', '', text)
    
    text = re.sub(r'X\d+', '', text)
    
    text = re.sub(r'或授权代表', '', text)
    
    text = re.sub(r'二〇\d{2}年\d{1,2}月\d{1,2}日', lambda m: m.group(0).replace('二〇', '20').replace('月', '-').replace('日', ''), text)
    
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def _convert_to_uppercase(amount: float) -> str:
    """将数字金额转换为中文大写"""
    if amount <= 0:
        return "零元"
    
    units = ["", "拾", "佰", "仟", "万", "拾万", "佰万", "仟万", "亿"]
    digits = "零壹贰叁肆伍陆柒捌玖"
    
    int_part = int(amount)
    result_parts = []
    int_str = str(int_part)
    length = len(int_str)
    
    for i, char in enumerate(int_str):
        digit = int(char)
        unit = units[length - i - 1]
        if digit != 0:
            result_parts.append(f"{digits[digit]}{unit}")
        else:
            if not result_parts or result_parts[-1] != "零":
                result_parts.append("零")
    
    result_str = "".join(result_parts)
    while "零零" in result_str:
        result_str = result_str.replace("零零", "零")
    
    if result_str and result_str[-1] == "零":
        result_str = result_str[:-1]
    
    result_str += "元"
    
    decimal_part = round(amount - int_part, 2)
    if decimal_part >= 0.01:
        decimal_str = f"{decimal_part:.2f}"
        decimal_digits = list(decimal_str.replace(".", ""))
        if decimal_digits[0] != "0":
            result_str += f"{digits[int(decimal_digits[0])]}角"
        if decimal_digits[1] != "0":
            result_str += f"{digits[int(decimal_digits[1])]}分"
    
    return result_str


class EvidenceFileGenerator:
    """证据文件生成器 - 生成每个证据的独立文件"""
    
    def __init__(
        self,
        prompt_dir: str = "prompts",
        output_dir: str = "outputs",
        llm_client: Optional[LLMClient] = None
    ):
        """
        初始化证据文件生成器
        
        Args:
            prompt_dir: 提示词目录
            output_dir: 输出目录
            llm_client: 大模型客户端
        """
        self.prompt_dir = Path(prompt_dir)
        self.output_dir = Path(output_dir)
        self.llm_client = llm_client or LLMClient()
        self.retry_handler = RetryHandler(max_retries=3)
        self.checker = PlaceholderChecker()

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_all_evidence_files(
        self,
        stage0_data: Dict[str, Any],
        evidence_planning: Dict[str, Any],
        party: str = "原告"
    ) -> Dict[str, Any]:
        """
        生成所有证据的独立文件
        
        Args:
            stage0_data: 阶段0数据
            evidence_planning: 证据归属规划
            party: 证据归属方（原告/被告）
        
        Returns:
            证据索引信息
        """
        logger.info(f"开始生成{party}证据文件")
        
        # 安全提取证据列表（处理raw_response格式异常）
        evidence_list = _extract_evidence_list(evidence_planning)
        
        if not evidence_list:
            logger.warning("未找到有效证据列表，跳过证据文件生成")
            return {
                "证据总数": 0,
                "证据组数": 0,
                "证据列表": [],
                "证据组列表": []
            }
        
        # 筛选指定方的证据
        evidence_list = [
            e for e in evidence_list
            if e.get("应归属方") == party and e.get("是否需要生成", True)
        ]
        
        logger.info(f"共找到 {len(evidence_list)} 个{party}证据需要生成")
        
        # 按证据组分组
        evidence_groups = self._group_evidences(evidence_list)
        
        # 生成证据文件
        evidence_files = []
        used_ids = {}  # 跟踪已使用的ID，生成唯一ID
        
        for group_id, group_evidences in evidence_groups.items():
            group_dir = self.output_dir / f"证据组{group_id}"
            group_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"生成证据组 {group_id}，共 {len(group_evidences)} 个证据")
            
            for idx, evidence in enumerate(group_evidences):
                base_id = evidence.get('证据序号', idx + 1)
                evidence_id = f"E{base_id:03d}"
                
                # 处理重复ID：添加组内序号后缀
                if evidence_id in used_ids.get(str(group_id), set()):
                    evidence_id = f"E{base_id:03d}_{idx + 1}"
                
                if str(group_id) not in used_ids:
                    used_ids[str(group_id)] = set()
                used_ids[str(group_id)].add(evidence_id)
                
                evidence_name = evidence["证据名称"]
                
                logger.info(f"  生成证据 {evidence_id}: {evidence_name}")
                
                # 生成证据文件
                file_path = self._generate_evidence_file(
                    evidence=evidence,
                    stage0_data=stage0_data,
                    group_dir=group_dir
                )
                
                evidence_files.append({
                    "证据ID": evidence_id,
                    "证据组": group_id,
                    "证据名称": evidence["证据名称"],
                    "证据名称简写": self._simplify_evidence_name(evidence["证据名称"]),
                    "文件类型": evidence["文件类型"],
                    "归属方": party,
                    "文件路径": str(file_path),
                    "文件大小": file_path.stat().st_size
                })
        
        # 生成证据索引
        evidence_index = self._generate_evidence_index(evidence_files, evidence_groups, evidence_planning)
        
        # 保存证据索引文件
        index_file_path = self.output_dir / "evidence_index.json"
        import json
        with open(index_file_path, 'w', encoding='utf-8') as f:
            json.dump(evidence_index, f, ensure_ascii=False, indent=2)
        
        logger.info(f"证据文件生成完成，共 {len(evidence_files)} 个文件")
        
        return evidence_index

    def _extract_involved_companies(
        self,
        evidence: Dict[str, Any],
        profiles: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """从证据信息中提取涉及的公司列表"""
        involved_companies = []
        
        involved_markers = evidence.get("关键数据提示", {}).get("涉及方", [])
        
        if not involved_markers:
            logger.warning(f"证据未指定涉及方: {evidence.get('证据名称', '未知')}")
            return []
        
        company_profiles = profiles.get("公司Profile库", {})
        
        for marker in involved_markers:
            for key, company in company_profiles.items():
                if company.get("原脱敏标识") == marker:
                    involved_companies.append({
                        "role": marker,
                        "company_name": company.get("公司名称", ""),
                        "credit_code": company.get("统一社会信用代码", ""),
                        "legal_representative": company.get("法定代表人", ""),
                        "address": company.get("注册地址", ""),
                        "bank_account": company.get("银行账户", {}).get("账号", "")
                    })
                    logger.info(f"找到公司: {marker} -> {company.get('公司名称', '')}")
                    break
            else:
                logger.warning(f"未在Profile库中找到公司: {marker}")
        
        return involved_companies

    def _extract_amount_info(
        self,
        evidence: Dict[str, Any],
        key_numbers: Dict[str, Any]
    ) -> Dict[str, Any]:
        """从证据和关键金额清单中提取涉及金额"""
        amount_info = evidence.get("关键数据提示", {}).get("涉及金额", {})
        
        if amount_info:
            return {
                "amount": amount_info.get("数值", 0),
                "unit": amount_info.get("单位", "元"),
                "uppercase": _convert_to_uppercase(amount_info.get("数值", 0))
            }
        
        contract_amount = key_numbers.get("合同基础金额", {}).get("原合同金额", {})
        amount_value = contract_amount.get("数值", 0)
        
        return {
            "amount": amount_value,
            "unit": "元",
            "uppercase": _convert_to_uppercase(amount_value)
        }

    def _extract_date_info(
        self,
        evidence: Dict[str, Any]
    ) -> Optional[str]:
        """从证据信息中提取日期"""
        date_info = evidence.get("关键数据提示", {}).get("涉及日期", "")
        return date_info if date_info else None

    def _build_party_info_section(
        self,
        companies: List[Dict[str, str]]
    ) -> str:
        """构建当事人信息部分"""
        if not companies:
            return "【无涉及公司信息】"
        
        section_lines = ["### 公司信息"]
        
        for company in companies:
            role = company.get("role", "当事人")
            name = company.get("company_name", "未知")
            code = company.get("credit_code", "未提供")
            legal = company.get("legal_representative", "未提供")
            address = company.get("address", "未提供")
            
            section_lines.append(f"- {role}：{name}")
            section_lines.append(f"  统一社会信用代码：{code}")
            section_lines.append(f"  法定代表人：{legal}")
            section_lines.append(f"  地址：{address}")
            section_lines.append("")
        
        return "\n".join(section_lines)

    def _assemble_prompt(
        self,
        base_prompt: str,
        party_info: str,
        amount_info: Dict[str, Any],
        date_info: Optional[str],
        evidence: Dict[str, Any]
    ) -> str:
        """组装完整Prompt"""
        mandatory_info = ["## 【必须使用的具体信息】\n"]
        
        mandatory_info.append(party_info)
        mandatory_info.append("")
        
        mandatory_info.append("### 金额信息")
        mandatory_info.append(f"涉及金额：人民币{amount_info['uppercase']}（¥{amount_info['amount']:,.2f}）")
        mandatory_info.append("")
        
        if date_info:
            mandatory_info.append("### 日期信息")
            mandatory_info.append(f"日期：{date_info}")
            mandatory_info.append("")
        
        mandatory_info.append("## 🚨 强制要求")
        mandatory_info.append("生成内容时必须使用上述具体信息，")
        mandatory_info.append("**禁止**使用以下占位符：")
        mandatory_info.append("- '某某公司'、'某公司'")
        mandatory_info.append("- '某某'、'某'")
        mandatory_info.append("- 'X4'、'X5'等数字占位符")
        mandatory_info.append("- '人民币X元'、'X%'等金额占位符")
        mandatory_info.append("")
        
        mandatory_section = "\n".join(mandatory_info)
        
        return f"{base_prompt}\n\n{mandatory_section}"

    def build_evidence_prompt(
        self,
        evidence: Dict[str, Any],
        stage0_data: Dict[str, Any],
        evidence_type: str = "合同"
    ) -> str:
        """构建证据生成的完整Prompt"""
        logger.info(f"构建证据Prompt: {evidence.get('证据名称', '未知')}")
        
        profiles = stage0_data.get("0.2_脱敏替换策划", {})
        key_numbers = stage0_data.get("0.4_关键数字清单", {})
        
        companies = self._extract_involved_companies(evidence, profiles)
        amount_info = self._extract_amount_info(evidence, key_numbers)
        date_info = self._extract_date_info(evidence)
        party_info = self._build_party_info_section(companies)
        
        prompt_path = self.prompt_dir / "stage1" / "1.2.1_单个证据生成.md"
        if prompt_path.exists():
            base_prompt = load_prompt_template(str(prompt_path))
        else:
            base_prompt = self._get_default_prompt(evidence)
        
        full_prompt = self._assemble_prompt(
            base_prompt=base_prompt,
            party_info=party_info,
            amount_info=amount_info,
            date_info=date_info,
            evidence=evidence
        )
        
        logger.info(f"证据Prompt构建完成，字符数: {len(full_prompt)}")
        
        return full_prompt
    
    def _generate_evidence_file(
        self,
        evidence: Dict[str, Any],
        stage0_data: Dict[str, Any],
        group_dir: Path
    ) -> Path:
        """
        生成单个证据文件
        
        Args:
            evidence: 证据信息
            stage0_data: 阶段0数据
            group_dir: 证据组目录
        
        Returns:
            文件路径
        """
        # 使用新的Prompt构建策略
        full_prompt = self.build_evidence_prompt(evidence, stage0_data)

        # 带占位符检测的生成
        def generate_with_retry():
            return self.llm_client.generate(full_prompt)

        result = self.retry_handler.execute_with_retry(generate_with_retry)

        if result["success"]:
            response = result["result"]
            logger.success(f"证据{evidence['证据序号']}生成成功（第{result['attempts']}次尝试）")
        else:
            response = result.get("result", "") or ""
            logger.warning(
                f"证据{evidence['证据序号']}生成失败，占位符: {result['placeholders'][:3]}"
            )

        # 清理markdown符号
        clean_response = self._clean_markdown(response)

        # 确保关键位置有换行符（解决LLM生成连续文本问题）
        clean_response = self._ensure_line_breaks(clean_response)

        # 反脱敏
        deanonymized_response = self._deanonymize_text(clean_response, stage0_data)
        
        # 清理占位符
        cleaned_response = self._clean_placeholders(deanonymized_response, stage0_data)
        
        # 生成文件名
        evidence_id = f"E{evidence['证据序号']:03d}"
        simplified_name = self._simplify_evidence_name(evidence["证据名称"])
        filename = f"证据组{evidence['证据组']}_{evidence_id}_{simplified_name}.txt"
        file_path = group_dir / filename
        
        # 保存文件
        file_path.write_text(cleaned_response, encoding='utf-8')
        
        return file_path
    
    def _deanonymize_text(self, text: str, stage0_data: Dict) -> str:
        """
        将脱敏名称替换为真实名称
        
        Args:
            text: 包含脱敏名称的文本
            stage0_data: 阶段0数据（包含脱敏映射）
            
        Returns:
            str: 替换后的文本
        """
        anonymization_map: Dict[str, str] = {}
        
        # 从0.2_anonymization_plan中获取数据
        anonymization_plan = stage0_data.get("0.2_anonymization_plan", {})
        
        # 处理公司Profile库
        company_profiles = anonymization_plan.get("公司Profile库", {})
        for key, company in company_profiles.items():
            anonymized = company.get("原脱敏标识")
            real_name = company.get("公司名称")
            if anonymized and real_name:
                anonymization_map[anonymized] = real_name
        
        # 处理人物Profile库
        person_profiles = anonymization_plan.get("人物Profile库", {})
        for key, person in person_profiles.items():
            anonymized = person.get("原脱敏标识")
            real_name = person.get("姓名")
            if anonymized and real_name:
                anonymization_map[anonymized] = real_name
        
        # 从替换映射表添加
        replace_map = anonymization_plan.get("替换映射表", {})
        anonymization_map.update(replace_map)
        
        # 添加已知的脱敏映射（常见固定值）
        additional_mappings = {
            "某某律师事务所": "上海中伦律师事务所",
            "某某公证处": "上海市东方公证处",
            "某某银行": "中国工商银行",
        }
        anonymization_map.update(additional_mappings)
        
        # 执行替换（按长度降序）
        deanonymized = text
        sorted_markers = sorted(anonymization_map.items(), key=lambda x: len(x[0]), reverse=True)
        for placeholder, real_name in sorted_markers:
            deanonymized = deanonymized.replace(placeholder, real_name)
        
        # 增强反脱敏：处理不一致的脱敏模式
        deanonymized = self._enhanced_deanonymize(deanonymized, stage0_data)
        
        return deanonymized
    
    def _enhanced_deanonymize(self, text: str, stage0_data: Dict) -> str:
        """增强反脱敏：处理不一致的脱敏模式"""
        anonymization_plan = stage0_data.get("0.2_anonymization_plan", {})
        
        # 检查plan结构：可能是 {"0.2_anonymization_plan": {...}} 或直接是 {...}
        if "公司Profile库" not in anonymization_plan:
            anonymization_plan = stage0_data
        
        # 收集所有真实信息
        all_real_names = []
        
        # 收集真实公司名
        company_profiles = anonymization_plan.get("公司Profile库", {})
        for company in company_profiles.values():
            if company.get("公司名称"):
                all_real_names.append(company.get("公司名称"))
        
        # 收集真实人名
        person_profiles = anonymization_plan.get("人物Profile库", {})
        for person in person_profiles.values():
            if person.get("姓名"):
                all_real_names.append(person.get("姓名"))
        
        # 模式1: 处理"X某"（如"张伟某" -> "张伟"）
        for name in all_real_names:
            if name and len(name) >= 2:
                pattern = re.escape(name) + r'某'
                text = re.sub(pattern + r'([^\w])', name + r'\1', text)
                text = re.sub(pattern + r'$', name, text)
        
        # 模式2: 处理常见脱敏人名
        text = re.sub(r'张伟某', '张伟', text)
        text = re.sub(r'李某某', '李明', text)
        
        # 模式3: 处理地址脱敏
        address_map = {}
        for company in company_profiles.values():
            if company.get("注册地址"):
                addr = company.get("注册地址")
                # 提取市/区信息
                if "上海" in addr and "浦东" in addr:
                    address_map[r"上海市某某区某某路某某号"] = addr
                elif "上海" in addr:
                    address_map[r"上海市某某区某某路某某号"] = addr
                elif "南昌" in addr and "红谷滩" in addr:
                    address_map[r"江西省某某市某某区某某路某某号"] = addr
                elif "南昌" in addr:
                    address_map[r"江西省某某市某某区某某路某某号"] = addr
                elif "深圳" in addr:
                    address_map[r"广东省某某市某某区某某路某某号"] = addr
        
        # 添加人物地址
        for person in person_profiles.values():
            if person.get("家庭住址") and person.get("家庭住址") != "未提供":
                addr = person.get("家庭住址")
                if "上海" in addr and "浦东" in addr:
                    address_map[r"上海市某某区某某路某某号"] = addr
                elif "上海" in addr:
                    address_map[r"上海市某某区某某路某某号"] = addr
                elif "南昌" in addr:
                    address_map[r"江西省某某市某某区某某路某某号"] = addr
                elif "深圳" in addr:
                    address_map[r"广东省某某市某某区某某路某某号"] = addr
        
        for pattern, real_addr in address_map.items():
            text = re.sub(pattern, real_addr, text)
        
        # 模式4: 清理残余的脱敏标记
        text = re.sub(r'某某某', '', text)
        text = re.sub(r'XXX', '', text)
        text = re.sub(r'XX', '', text)
        
        # 模式5: 处理"某某公司X"格式
        text = re.sub(r'某某公司(\d+)', lambda m: self._find_company_by_marker(m.group(1), stage0_data), text)
        
        # 模式6: 处理LLM自行创造的脱敏名称 (BUG-010)
        llm_patterns = [
            # 处理 "张伟 (公司2)" -> "张伟"
            (r'张伟\s*\(公司\d+\)', '张伟'),
            # 处理 "张海峰 (公司6)" -> "张海峰"
            (r'张海峰\s*\(公司\d+\)', '张海峰'),
            # 处理 "长江某有限公司" -> 根据上下文查找真实公司名
            (r'长江某有限公司', '南昌宏昌商业零售有限公司'),
            # 处理 "华鑫某" 模式
            (r'华鑫某有限公司', '东方国际融资租赁有限公司'),
        ]

        for pattern, replacement in llm_patterns:
            text = re.sub(pattern, replacement, text)

        return text

    def _ensure_line_breaks(self, text: str) -> str:
        """确保关键位置有换行符（解决LLM生成连续文本问题）"""
        if not text:
            return text

        # 在【章节标题】后添加换行
        text = re.sub(r'【([^】]+)】([^\n])', r'【\1】\n\2', text)

        # 在连续字段标签之间添加换行
        field_labels = [
            '统一社会信用代码：',
            '法定代表人：',
            '地址：',
            '电话：',
            '签订日期：',
            '合同编号：',
            '权利人：',
            '义务人：',
            '权利类型：',
            '登记时间：',
            '金额：',
            '日期：',
            '收/付款人：',
            '摘要：',
            '凭证号：',
            '签署：',
            '正文内容：',
            '致：',
            '文书名称：',
        ]

        sorted_labels = sorted(field_labels, key=len, reverse=True)

        for label in sorted_labels:
            escaped_label = re.escape(label)
            text = re.sub(r'([^\n])(' + escaped_label + r')', r'\1\n\2', text)

        # 在【章节标题】前添加换行（如果前面有内容）
        text = re.sub(r'([^\n])【', r'\1\n【', text)

        # 清理多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text

    def _find_company_by_marker(self, marker: str, stage0_data: Dict) -> str:
        """根据标记找到真实公司名"""
        anonymization_plan = stage0_data.get("0.2_anonymization_plan", {})
        company_profiles = anonymization_plan.get("公司Profile库", {})
        for company in company_profiles.values():
            if company.get("原脱敏标识") == f"某某公司{marker}":
                return company.get("公司名称", f"某某公司{marker}")
        return f"某某公司{marker}"
    
    def _clean_placeholders(self, text: str, stage0_data: Dict) -> str:
        """清理各种占位符"""
        key_numbers = stage0_data.get("0.4_key_numbers", {})
        rent_info = key_numbers.get("租金安排", {})
        
        # 提取实际值
        rent_total = rent_info.get("租金总额", {})
        rent_rate = rent_info.get("年利率", {})
        principal = key_numbers.get("合同基础金额", {}).get("原合同金额", {})
        
        # 安全提取数值（处理字符串类型的情况）
        def safe_float(val):
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                try:
                    return float(val.replace(',', '').replace('，', ''))
                except:
                    return None
            return None
        
        rent_total_value = ""
        rent_total_num = rent_total.get("数值")
        if rent_total_num is not None:
            num = safe_float(rent_total_num)
            if num is not None:
                rent_total_value = f"人民币{num:,.2f}元"
        
        rent_rate_value = ""
        rent_rate_num = rent_rate.get("数值")
        if rent_rate_num is not None:
            num = safe_float(rent_rate_num)
            if num is not None:
                rent_rate_value = f"{num}"
        
        principal_value = ""
        principal_num = principal.get("数值")
        if principal_num is not None:
            num = safe_float(principal_num)
            if num is not None:
                principal_value = f"人民币{num:,.0f}元"
        
        # 清理【具体X】格式
        text = re.sub(r'【具体金额】', rent_total_value, text)
        text = re.sub(r'【具体利率】', f"{rent_rate_value}%/年", text)
        text = re.sub(r'【具体本金】', principal_value, text)
        text = re.sub(r'【具体\w+】', '', text)
        
        # 清理（此处填写X）格式
        text = re.sub(r'（此处填写[^）]+）', '', text)
        text = re.sub(r'\（此处填写[^）]+\）', '', text)
        
        # 清理"具体金额"、"具体利率"等
        text = text.replace('具体金额', '')
        text = text.replace('具体利率', '')
        text = text.replace('具体天数', '')
        
        # 清理多余空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _build_prompt(
        self,
        evidence: Dict[str, Any],
        stage0_data: Dict[str, Any],
        base_prompt: str
    ) -> str:
        """构建完整的提示词"""
        # 提取相关数据
        case_info = stage0_data.get("0.1_structured_extraction", {}).get("案件基本信息", {})
        profiles = stage0_data.get("0.2_anonymization_plan", {})
        timeline = stage0_data.get("0.3_transaction_reconstruction", {}).get("交易时间线", [])
        key_numbers = stage0_data.get("0.4_key_numbers", {})
        
        # 构建证据相关数据
        evidence_data = {
            "证据名称": evidence["证据名称"],
            "证据组": evidence["证据组"],
            "证据序号": evidence["证据序号"],
            "文件类型": evidence["文件类型"],
            "证明目的": evidence.get("证明目的", ""),
            "涉及金额": evidence.get("关键数据提示", {}).get("涉及金额", {}),
            "涉及日期": evidence.get("关键数据提示", {}).get("涉及日期", ""),
            "涉及方": evidence.get("关键数据提示", {}).get("涉及方", []),
            "关联交易节点": evidence.get("关联交易节点", 0),
        }
        
        # 构建完整提示词
        full_prompt = f"""
{base_prompt}

## 证据信息
{json.dumps(evidence_data, ensure_ascii=False, indent=2)}

## 案件基本信息
{json.dumps(case_info, ensure_ascii=False, indent=2)}

## Profile库
{json.dumps(profiles, ensure_ascii=False, indent=2)}

## 交易时间线
{json.dumps(timeline, ensure_ascii=False, indent=2)}

## 关键金额清单
{json.dumps(key_numbers, ensure_ascii=False, indent=2)}

请严格按照上述证据信息生成证据内容，使用Profile库中的真实名称和数据。
"""
        
        return full_prompt
    
    def _get_default_prompt(self, evidence: Dict[str, Any]) -> str:
        """获取默认提示词（当提示词文件不存在时）"""
        evidence_type = evidence.get("文件类型", "合同")
        
        prompts = {
            "合同": """# 任务：生成合同类证据的完整内容

## 格式要求
- 纯文本格式
- 不包含任何markdown符号
- 符合合同的标准格式

## 合同标准格式
【合同名称】
【合同编号】

【甲方（转让方/出租人）】
名称：XXX
统一社会信用代码：XXX
法定代表人：XXX
地址：XXX

【乙方（受让方/承租人）】
名称：XXX
统一社会信用代码：XXX
法定代表人：XXX
地址：XXX

【鉴于条款】
...

【第一条 标的】
...

【第二条 价款/租金】
...

【第三条 交付/支付】
...

【第四条 权利义务】
...

【第五条 违约责任】
...

【第六条 争议解决】
...

【签署栏】
甲方（盖章）：
法定代表人（签字）：

乙方（盖章）：
法定代表人（签字）：

签订日期：XXXX年XX月XX日
""",
            "文书": """# 任务：生成文书类证据的完整内容

## 格式要求
- 纯文本格式
- 不包含任何markdown符号
- 符合文书的标准格式

## 文书标准格式
【文书名称】

【致】XXX

【正文内容】
...

【签署】
XXX

【日期】XXXX年XX月XX日
""",
            "登记": """# 任务：生成登记类证据的完整内容

## 格式要求
- 纯文本格式
- 不包含任何markdown符号
- 符合登记证明的标准格式

## 登记证明标准格式
【证书名称】

【权利人】XXX

【义务人】XXX

【权利类型】XXX

【登记时间】XXXX年XX月XX日

【备注】...
""",
            "凭证": """# 任务：生成凭证类证据的完整内容

## 格式要求
- 纯文本格式
- 不包含任何markdown符号
- 符合凭证的标准格式

## 凭证标准格式
【凭证名称】

【日期】XXXX年XX月XX日

【收/付款人】XXX

【金额】人民币XXXX元整

【摘要】XXX

【凭证号】XXX

【签署】XXX
"""
        }
        
        return prompts.get(evidence_type, prompts["合同"])
    
    def _clean_markdown(self, text: str) -> str:
        """清理markdown符号，生成纯文本"""
        # 处理代码块 - 只移除 ```python 等标记，保留内容
        # 先用占位符替换代码块内容
        code_blocks = []
        def replace_codeblock(match):
            # 提取代码块内容（不包括语言标记和 ```）
            content = match.group(0)
            # 移除 ```python 和 ``` 标记，保留内容
            content = re.sub(r'^```[a-zA-Z0-9]*\s*', '', content, flags=re.MULTILINE)
            content = re.sub(r'\s*```$', '', content)
            code_blocks.append(content)
            return f'__CODE_BLOCK_{len(code_blocks)-1}__'

        text = re.sub(r'```[a-zA-Z0-9]*\s*[\s\S]*?\s*```', replace_codeblock, text)

        # 去除行内代码（单反引号）- 但保留内容
        text = re.sub(r'`([^`\n]+)`', r'\1', text)

        # 去除加粗（**text** 或 __text__）
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)

        # 去除删除线（~~text~~）
        text = re.sub(r'~~([^~]+)~~', r'\1', text)

        # 去除标题（# ## ###等）- 考虑可能有缩进
        text = re.sub(r'^[ \t]*#+\s+', '', text, flags=re.MULTILINE)

        # 去除引用（>）
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)

        # 处理无序列表（- 或 * 或 +）
        text = re.sub(r'^[-*+]\s+', '· ', text, flags=re.MULTILINE)

        # 处理有序列表（1. 2. 等）
        text = re.sub(r'^(\d+)\.\s+', r'\1. ', text, flags=re.MULTILINE)

        # 处理任务列表（- [ ] 或 - [x]）
        text = re.sub(r'^-\s*\[\s*\]\s+', '□ ', text, flags=re.MULTILINE)
        text = re.sub(r'^-\s*\[x\]\s+', '■ ', text, flags=re.MULTILINE)

        # 处理分隔线
        text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)

        # 去除链接格式 [text](url) -> text
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # 去除图片格式 ![alt](url) -> alt
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)

        # 处理脚注 [^1] -> (注1)
        text = re.sub(r'\[\^([^\]]+)\]', r'(注\1)', text)

        # 去除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 处理Markdown表格 - 将表格转换为纯文本格式
        lines = text.split('\n')
        result_lines = []
        in_table = False
        table_rows = []
        
        for line in lines:
            # 检测表格行（以 | 开头或结尾，且包含 | 分隔）
            if '|' in line and (line.strip().startswith('|') or line.strip().endswith('|')):
                # 跳过表头分隔行（如 |:---|）
                if re.match(r'^\s*\|?\s*[:\-\s]+\s*\|', line):
                    continue
                in_table = True
                table_rows.append(line)
            else:
                if in_table and table_rows:
                    # 将表格转换为纯文本
                    # 提取表头（第一行）
                    if table_rows:
                        header = table_rows[0]
                        # 移除首尾的 |，分割成列
                        cols = [c.strip() for c in header.strip('|').split('|')]
                        # 添加表头文本
                        for i, col in enumerate(cols):
                            if i > 0:
                                result_lines.append(' / ')
                            result_lines.append(col)
                        result_lines.append('：')
                    
                    # 添加数据行
                    for row in table_rows[1:]:
                        cols = [c.strip() for c in row.strip('|').split('|')]
                        for i, col in enumerate(cols):
                            if i > 0:
                                result_lines.append(' / ')
                            result_lines.append(col)
                        result_lines.append('\n')
                    
                    table_rows = []
                    in_table = False
                result_lines.append(line)
        
        # 处理最后可能残留的表格
        if in_table and table_rows:
            for row in table_rows:
                result_lines.append(row)
        
        text = ''.join(result_lines)
        
        # 恢复代码块占位符为代码内容
        for i, code_content in enumerate(code_blocks):
            text = text.replace(f'__CODE_BLOCK_{i}__', code_content)
        
        # 去除多余空行（3个以上换行 -> 2个）
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _simplify_evidence_name(self, name: str) -> str:
        """简化证据名称用于文件名"""
        # 去除书名号和公证书后缀
        simplified = name.replace('《', '').replace('》', '')
        simplified = re.sub(r'及公证书$', '', simplified)
        simplified = re.sub(r'（.+）$', '', simplified)
        simplified = re.sub(r'\(.+\)$', '', simplified)
        # 替换/为和，防止路径错误
        simplified = simplified.replace('/', '和').replace('\\', '和')
        # 去除其他可能导致路径问题的字符
        simplified = re.sub(r'[\<>:"\*\?]', '', simplified)
        return simplified
    
    def _group_evidences(self, evidence_list: List[Dict]) -> Dict[int, List]:
        """按证据组分组"""
        groups = {}
        for evidence in evidence_list:
            group_id = evidence.get("证据组", 1)
            if group_id not in groups:
                groups[group_id] = []
            groups[group_id].append(evidence)
        return groups
    
    def _generate_evidence_index(
        self,
        evidence_files: List[Dict],
        evidence_groups: Dict[int, List],
        evidence_planning: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成证据索引"""
        # 获取证据组名称
        group_names = evidence_planning.get("证据分组", {})
        
        evidence_index = {
            "证据总数": len(evidence_files),
            "证据组数": len(evidence_groups),
            "证据列表": evidence_files,
            "证据组列表": []
        }
        
        # 构建证据组列表
        for group_id, evidences in evidence_groups.items():
            group_name = group_names.get(f"证据组_{group_id}", {}).get("组名称", f"证据组{group_id}")
            
            # 获取第一个证据的证明目的作为组的证明目的
            proof_purpose = ""
            for e in evidences:
                if e.get("证明目的"):
                    proof_purpose = e["证明目的"]
                    break
            
            evidence_index["证据组列表"].append({
                "组编号": group_id,
                "组名称": group_name,
                "证据数量": len(evidences),
                "证明目的": proof_purpose
            })
        
        return evidence_index
