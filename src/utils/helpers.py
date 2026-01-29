"""工具函数"""
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


def load_prompt_template(prompt_path: str, params: Optional[Dict[str, Any]] = None) -> str:
    """
    加载提示词模板并注入参数
    
    Args:
        prompt_path: 提示词文件路径
        params: 参数字典
    
    Returns:
        替换参数后的提示词内容
    """
    prompt_file = Path(prompt_path)
    if not prompt_file.exists():
        raise FileNotFoundError(f"提示词文件不存在: {prompt_path}")
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if params:
        for key, value in params.items():
            content = content.replace(f"{{{key}}}", str(value))
    
    return content


def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    加载JSON Schema
    
    Args:
        schema_path: Schema文件路径
    
    Returns:
        Schema字典
    """
    schema_file = Path(schema_path)
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema文件不存在: {schema_path}")
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_company_names(text: str) -> list[str]:
    """
    从文本中提取公司名称
    
    Args:
        text: 输入文本
    
    Returns:
        公司名称列表
    """
    pattern = r'([^。\n]{2,20})(公司|集团|企业|集团|有限公司|股份有限公司)'
    matches = re.findall(pattern, text)
    companies = [match[0] + match[1] for match in matches]
    return list(set(companies))


def extract_person_names(text: str) -> list[str]:
    """
    从文本中提取人名
    
    Args:
        text: 输入文本
    
    Returns:
        人名列表
    """
    pattern = r'([^\s。,\n]{2,4})(原告|被告|法定代表人|代理人|审判长|审判员|书记员)'
    matches = re.findall(pattern, text)
    names = [match[0] for match in matches]
    return list(set(names))


def extract_amounts(text: str) -> list[dict]:
    """
    从文本中提取金额
    
    Args:
        text: 输入文本
    
    Returns:
        金额列表,每个金额包含数值和单位
    """
    pattern = r'([\d,]+\.?\d*)\s*(元|万元|美元|欧元|日元|港币)'
    matches = re.findall(pattern, text)
    amounts = []
    for match in matches:
        try:
            value = float(match[0].replace(',', ''))
            amounts.append({
                '数值': value,
                '单位': match[1]
            })
        except ValueError:
            continue
    return amounts


def extract_dates(text: str) -> list[str]:
    """
    从文本中提取日期
    
    Args:
        text: 输入文本
    
    Returns:
        日期列表(YYYY-MM-DD格式)
    """
    patterns = [
        r'(\d{4})年(\d{1,2})月(\d{1,2})日',
        r'(\d{4})-(\d{1,2})-(\d{1,2})',
        r'(\d{4})/(\d{1,2})/(\d{1,2})',
    ]
    
    dates = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            year, month, day = match
            dates.append(f"{year}-{month.zfill(2)}-{day.zfill(2)}")
    
    return list(set(dates))


def format_amount(amount: float, unit: str = "元") -> str:
    """
    格式化金额
    
    Args:
        amount: 金额数值
        unit: 单位
    
    Returns:
        格式化后的金额字符串
    """
    if unit == "万元":
        return f"{amount:.2f}万元"
    elif unit == "元":
        return f"{amount:.2f}元"
    else:
        return f"{amount}{unit}"


def validate_json_structure(data: dict, schema: dict) -> tuple[bool, list[str]]:
    """
    验证JSON数据结构是否符合schema
    
    Args:
        data: 待验证的数据
        schema: Schema定义
    
    Returns:
        (是否通过, 错误消息列表)
    """
    errors = []
    
    def validate_recursive(data: Any, schema: Any, path: str = ""):
        if isinstance(schema, dict):
            if "type" in schema:
                expected_type = schema["type"]
                if expected_type == "string" and not isinstance(data, str):
                    errors.append(f"{path}: 期望字符串, 实际为{type(data).__name__}")
                elif expected_type == "number" and not isinstance(data, (int, float)):
                    errors.append(f"{path}: 期望数字, 实际为{type(data).__name__}")
                elif expected_type == "integer" and not isinstance(data, int):
                    errors.append(f"{path}: 期望整数, 实际为{type(data).__name__}")
                elif expected_type == "boolean" and not isinstance(data, bool):
                    errors.append(f"{path}: 期望布尔值, 实际为{type(data).__name__}")
                elif expected_type == "array" and not isinstance(data, list):
                    errors.append(f"{path}: 期望数组, 实际为{type(data).__name__}")
                elif expected_type == "object" and not isinstance(data, dict):
                    errors.append(f"{path}: 期望对象, 实际为{type(data).__name__}")
            
            if "required" in schema and isinstance(data, dict):
                for field in schema["required"]:
                    if field not in data:
                        errors.append(f"{path}: 缺少必填字段 '{field}'")
            
            if "properties" in schema and isinstance(data, dict):
                for key, value in data.items():
                    if key in schema["properties"]:
                        validate_recursive(value, schema["properties"][key], f"{path}.{key}")
    
    validate_recursive(data, schema)
    return len(errors) == 0, errors


def save_json(data: Any, output_path: str) -> None:
    """
    保存数据为JSON文件
    
    Args:
        data: 要保存的数据
        output_path: 输出文件路径
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(input_path: str) -> Any:
    """
    加载JSON文件
    
    Args:
        input_path: 输入文件路径
    
    Returns:
        加载的数据
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_llm_json_response(response: str) -> Any:
    """
    解析LLM返回的JSON，处理各种格式问题
    
    Args:
        response: LLM返回的文本
    
    Returns:
        解析后的JSON对象或None
    """
    # 方法1: 直接尝试解析
    try:
        return json.loads(response.strip())
    except:
        pass
    
    # 方法2: 提取Markdown代码块中的JSON
    json_match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', response)
    if json_match:
        try:
            return json.loads(json_match.group(1).strip())
        except:
            pass
    
    # 方法3: 提取大括号内的JSON
    json_match = re.search(r'\{[\s\S]*\}', response, re.DOTALL)
    if json_match:
        json_str = json_match.group()
        try:
            # 修复缩进问题
            json_str = re.sub(r'\n\s{0,2}(\S)', r'\n    \1', json_str)
            # 修复多余逗号
            json_str = re.sub(r',\s*([\}\]])', r'\1', json_str)
            return json.loads(json_str)
        except:
            pass
    
    # 方法4: 尝试提取所有大括号内容，找到最外层的
    brace_count = 0
    start = -1
    for i, char in enumerate(response):
        if char == '{':
            if brace_count == 0:
                start = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start != -1:
                try:
                    json_str = response[start:i+1]
                    # 修复缩进问题
                    json_str = re.sub(r'\n\s{0,2}(\S)', r'\n    \1', json_str)
                    # 修复多余逗号
                    json_str = re.sub(r',\s*([\}\]])', r'\1', json_str)
                    return json.loads(json_str)
                except:
                    pass
    
    logger.error("无法解析LLM返回的JSON")
    return None
