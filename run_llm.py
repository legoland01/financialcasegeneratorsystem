#!/usr/bin/env python3
"""
金融案件完整证据生成系统 v4 - LLM生成版
使用大语言模型生成差异化、高质量的证据内容
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

from loguru import logger

from src.utils.prompt_templates import build_prompt, get_evidence_type_for_id
from src.utils.llm_generator import create_generator, LLMGenerator
import json
import re


def parse_args():
    parser = argparse.ArgumentParser(
        description='金融案件完整证据生成 v4 - LLM生成版',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--provider', type=str, default='mock',
                        choices=['openai', 'anthropic', 'deepseek', 'mock'],
                        help='LLM provider')
    parser.add_argument('--model', type=str, default='gpt-4',
                        help='Model name')
    parser.add_argument('--api-key', type=str, default=None,
                        help='API key')
    parser.add_argument('--base-url', type=str, default=None,
                        help='API base URL')
    return parser.parse_args()


def main():
    args = parse_args()
    
    output_dir = Path("outputs_llm")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.remove()
    logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}")
    logger.add(output_dir / "run.log", rotation="10MB", encoding="utf-8")
    
    logger.info("=" * 60)
    logger.info("金融案件证据生成系统 v4 - LLM生成版")
    logger.info("=" * 60)
    
    # 使用SiliconFlow DeepSeek配置（性价比高）
    logger.info("使用SiliconFlow DeepSeek-V3.2 API")
    logger.info("API: https://api.siliconflow.cn/v1")
    
    # 初始化LLM生成器（使用用户配置）
    generator = create_generator({
        "provider": "deepseek",  # SiliconFlow兼容OpenAI API
        "model": "deepseek-ai/DeepSeek-V3.2",
        "api_key": "sk-fjephnssumhgkxhakpxlfrqayiuckkyogvwkchqutqolqilk",
        "base_url": "https://api.siliconflow.cn/v1",
    })
    
    data = {
        "原告": "东方国际融资租赁有限公司",
        "原告信用代码": "91310000MA1FL3L123",
        "原告地址": "中国（上海）自由贸易试验区世纪大道100号",
        "原告法人": "周明远",
        "被告": "江西昌盛商业管理有限公司",
        "被告信用代码": "91360121MA35L8T456",
        "被告地址": "江西省南昌市南昌县莲塘镇向阳路199号",
        "被告法人": "吴建华",
        "被告二": "南昌长风房地产开发有限公司",
        "被告二信用代码": "91360103MA35H7U789",
        "被告二地址": "江西省南昌市西湖区抚生路369号",
        "被告二法人": "张立军",
        "被告三": "深圳前海恒信担保有限公司",
        "被告三信用代码": "91440300MA5FQ2K012",
        "被告三地址": "广东省深圳市福田区福田街道福华一路6号",
        "被告三法人": "李伟",
        "合同金额": 150000000,
        "已付租金": 40155653.92,
        "未付租金": 120467622.06,
        "逾期利息": 31198572,
        "保证金": 4500000,
        "律师费": 200000,
        "公证费": 273000,
        "保全保险费": 121663.17,
        "咨询服务费": 4650000,
        "利率": 0.061,
        "租赁期限": 24,
        "签订日期": "2021-02-24",
        "交付日期": "2021-02-26",
        "案号": "（2024）沪74民初721号",
        "公证编号": "（2021）沪长证经字第XXXX号",
        "执行证书编号": "（2021）沪长证执字第XXXX号",
        "执行裁定编号": "（2022）沪0112执12719号",
        "抵押登记编号": "赣（2021）南昌市不动产证明第1234567号",
    }
    
    # Step 1: 由LLM动态生成租赁物清单
    logger.info("生成租赁物清单（LLM动态生成）...")
    prompt = build_prompt("equipment_list", data)
    equipment_content = generator.generate(prompt, "equipment_list")
    
    # 解析JSON
    try:
        equipment_list = json.loads(equipment_content)
        if isinstance(equipment_list, list) and len(equipment_list) > 0:
            data["租赁物清单"] = equipment_list
            logger.info(f"  生成 {len(equipment_list)} 项设备")
        else:
            raise ValueError("生成的租赁物不是有效列表")
    except Exception as e:
        logger.warning(f"解析租赁物JSON失败，使用默认清单: {e}")
        # 默认清单
        data["租赁物清单"] = [
            {"序号": 1, "名称": "多联机中央空调系统", "规格型号": "VRV VIII代", "数量": "10套", "存放地点": data['被告地址'], "评估价值": 45000000},
            {"序号": 2, "名称": "冷水机组", "规格型号": "离心式RF1-5000", "数量": "2套", "存放地点": data['被告地址'], "评估价值": 12000000},
            {"序号": 3, "名称": "电梯设备", "规格型号": "曳引式客梯KONIA-1000", "数量": "4台", "存放地点": data['被告地址'], "评估价值": 8000000},
        ]
    
    # 抵押物清单（固定）
    data["抵押物清单"] = [
        {"序号": 1, "名称": "商业房产及土地使用权", "不动产权证号": "赣（2021）南昌市不动产权第0789012号", "地址": data['被告二地址'], "建筑面积": 15000, "评估价值": 80000000, "产权人": data['被告二']},
    ]
    
    plaintiff_dir = output_dir / "原告起诉包"
    plaintiff_dir.mkdir(exist_ok=True)
    
    # 保存关键数据（供PDF生成使用）
    key_numbers = {
        "租赁物清单": data["租赁物清单"],
        "抵押物清单": data["抵押物清单"],
    }
    with open(plaintiff_dir / "key_numbers.json", 'w', encoding='utf-8') as f:
        json.dump(key_numbers, f, ensure_ascii=False, indent=2)
    logger.info(f"  key_numbers.json ({len(data['租赁物清单'])}项设备)")
    
    logger.info("生成原告证据包...")
    _generate_plaintiff_package_v4(plaintiff_dir, data, generator)
    
    defendant_dir = output_dir / "被告答辩包"
    defendant_dir.mkdir(exist_ok=True)
    
    logger.info("生成被告证据包...")
    _generate_defendant_package_v4(defendant_dir, data, generator)
    
    court_dir = output_dir / "法院审理包"
    court_dir.mkdir(exist_ok=True)
    
    logger.info("生成法院文件包...")
    _generate_court_package_v4(court_dir, data, generator)
    
    logger.info("\n" + "=" * 60)
    logger.success("完成!")
    logger.info("=" * 60)
    
    all_files = list(output_dir.glob("**/*"))
    txt_files = [f for f in all_files if f.is_file() and f.suffix == '.txt']
    logger.info(f"\n共生成 {len(txt_files)} 个证据文件")
    
    for f in sorted(txt_files)[:25]:
        rel = f.relative_to(output_dir)
        logger.info(f"  {rel}")
    if len(txt_files) > 25:
        logger.info(f"  ... 还有 {len(txt_files) - 25} 个文件")


def _generate_plaintiff_package_v4(p_dir, data, generator: LLMGenerator):
    p_dir.mkdir(exist_ok=True)
    
    evidence_index = {
        "证据总数": 0,
        "证据组数": 0,
        "证据列表": [],
        "证据组列表": []
    }
    
    evidence_groups = []
    
    # ========== 证据组1：主合同履行证据组 ==========
    group1_dir = p_dir / "证据组1"
    group1_dir.mkdir(exist_ok=True)
    
    group1_evidence = [
        ("E001", "转让合同及公证书", "transfer_contract"),
        ("E002", "融资租赁合同（售后回租）及公证书", "finance_lease_contract"),
        ("E009", "资产评估报告及租赁物照片", "assessment_report"),
        ("E010", "付款回单", "payment_receipt"),
        ("E017", "设备转让价款支付凭证", "payment_receipt"),
    ]
    
    logger.info(f"  证据组1: 5个证据 (使用LLM生成)")
    
    for eid, name, evidence_type in group1_evidence:
        logger.info(f"    - 生成 {eid}: {name}")
        
        # 构建提示词
        prompt = build_prompt(evidence_type, data)
        
        # 调用LLM生成
        content = generator.generate(prompt, evidence_type)
        
        # 保存文件
        filepath = group1_dir / f"证据组1_{eid}_{name}.txt"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        file_type = "凭证/单据" if evidence_type == "payment_receipt" else "合同"
        evidence_index["证据列表"].append({
            "证据ID": eid,
            "证据组": 1,
            "证据名称": f"《{name}》",
            "证据名称简写": name,
            "文件类型": file_type,
            "归属方": "原告",
            "文件路径": str(filepath),
            "生成方式": "LLM",
        })
    
    evidence_groups.append({
        "组编号": 1,
        "组名称": "主合同履行证据组",
        "证据数量": len(group1_evidence),
        "证明目的": "证明原被告之间转让租赁物所有权、建立融资租赁关系的基础事实"
    })
    
    # ========== 证据组2：抵押担保证据组 ==========
    group2_dir = p_dir / "证据组2"
    group2_dir.mkdir(exist_ok=True)
    
    group2_evidence = [
        ("E003", "抵押合同（单位）及抵押登记证书、股东决定、公证书", "guarantee_contract"),
        ("E004", "抵押物登记证书", "mortgage_certificate"),
        ("E005", "抵押人股东决定", "shareholder_decision"),
    ]
    
    logger.info(f"  证据组2: 3个证据 (使用LLM生成)")
    
    for eid, name, evidence_type in group2_evidence:
        logger.info(f"    - 生成 {eid}: {name}")
        
        prompt = build_prompt(evidence_type, data)
        content = generator.generate(prompt, evidence_type)
        
        filepath = group2_dir / f"证据组2_{eid}_{name}.txt"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        file_type = "凭证/单据" if evidence_type == "mortgage_certificate" else "合同"
        evidence_index["证据列表"].append({
            "证据ID": eid,
            "证据组": 2,
            "证据名称": f"《{name}》",
            "证据名称简写": name,
            "文件类型": file_type,
            "归属方": "原告",
            "文件路径": str(filepath),
            "生成方式": "LLM",
        })
    
    evidence_groups.append({
        "组编号": 2,
        "组名称": "抵押担保证据组",
        "证据数量": len(group2_evidence),
        "证明目的": "证明被告二提供抵押担保的事实及担保范围，以及担保合同已办理公证"
    })
    
    # ========== 证据组3：保证担保证据组 ==========
    group3_dir = p_dir / "证据组3"
    group3_dir.mkdir(exist_ok=True)
    
    group3_evidence = [
        ("E006", "保证合同（单位）及股东决定、公证书", "guarantee_contract"),
        ("E007", "保证人股东决定", "shareholder_decision"),
    ]
    
    logger.info(f"  证据组3: 2个证据 (使用LLM生成)")
    
    for eid, name, evidence_type in group3_evidence:
        logger.info(f"    - 生成 {eid}: {name}")
        
        prompt = build_prompt(evidence_type, data)
        content = generator.generate(prompt, evidence_type)
        
        filepath = group3_dir / f"证据组3_{eid}_{name}.txt"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        file_type = "凭证/单据" if evidence_type == "shareholder_decision" else "合同"
        evidence_index["证据列表"].append({
            "证据ID": eid,
            "证据组": 3,
            "证据名称": f"《{name}》",
            "证据名称简写": name,
            "文件类型": file_type,
            "归属方": "原告",
            "文件路径": str(filepath),
            "生成方式": "LLM",
        })
    
    evidence_groups.append({
        "组编号": 3,
        "组名称": "保证担保证据组",
        "证据数量": len(group3_evidence),
        "证明目的": "证明被告三提供连带责任保证的事实及担保范围，以及担保合同已办理公证"
    })
    
    # ========== 证据组4：前置执行程序证据组 ==========
    group4_dir = p_dir / "证据组4"
    group4_dir.mkdir(exist_ok=True)
    
    group4_evidence = [
        ("E008", "执行证书", "execution_certificate"),
        ("E011", "咨询服务合同及支付凭证", "consulting_contract"),
        ("E012", "保证金支付凭证", "deposit_proof"),
    ]
    
    logger.info(f"  证据组4: 3个证据 (使用LLM生成)")
    
    for eid, name, evidence_type in group4_evidence:
        logger.info(f"    - 生成 {eid}: {name}")
        
        prompt = build_prompt(evidence_type, data)
        content = generator.generate(prompt, evidence_type)
        
        filepath = group4_dir / f"证据组4_{eid}_{name}.txt"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        file_type = "文书" if evidence_type == "execution_certificate" else "合同/凭证"
        evidence_index["证据列表"].append({
            "证据ID": eid,
            "证据组": 4,
            "证据名称": f"《{name}》",
            "证据名称简写": name,
            "文件类型": file_type,
            "归属方": "原告",
            "文件路径": str(filepath),
            "生成方式": "LLM",
        })
    
    evidence_groups.append({
        "组编号": 4,
        "组名称": "前置执行程序证据组",
        "证据数量": len(group4_evidence),
        "证明目的": "证明原告曾通过公证债权文书方式主张权利，以及后续执行程序被驳回的事实"
    })
    
    # ========== 证据组5：实现债权费用证据组 ==========
    group5_dir = p_dir / "证据组5"
    group5_dir.mkdir(exist_ok=True)
    
    group5_evidence = [
        ("E010", "委托代理合同", "attorney_contract"),
        ("E011", "律师费支付凭证、发票", "payment_receipt"),
        ("E012", "诉讼财产保全责任保险相关材料", "insurance_policy"),
        ("E016", "公证费支付凭证及发票", "payment_receipt"),
    ]
    
    logger.info(f"  证据组5: 4个证据 (使用LLM生成)")
    
    for eid, name, evidence_type in group5_evidence:
        logger.info(f"    - 生成 {eid}: {name}")
        
        prompt = build_prompt(evidence_type, data)
        content = generator.generate(prompt, evidence_type)
        
        filepath = group5_dir / f"证据组5_{eid}_{name}.txt"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        evidence_index["证据列表"].append({
            "证据ID": eid,
            "证据组": 5,
            "证据名称": f"《{name}》",
            "证据名称简写": name,
            "文件类型": "合同/凭证",
            "归属方": "原告",
            "文件路径": str(filepath),
            "生成方式": "LLM",
        })
    
    evidence_groups.append({
        "组编号": 5,
        "组名称": "实现债权费用证据组",
        "证据数量": len(group5_evidence),
        "证明目的": "证明原告为实现本案债权实际支出了律师费、公证费、保全保险费等费用"
    })
    
    # ========== 证据组6：租金支付记录证据组 ==========
    group6_dir = p_dir / "证据组6"
    group6_dir.mkdir(exist_ok=True)
    
    group6_evidence = [
        ("E013", "租金支付记录", "rent_record"),
        ("E014", "租金逾期记录", "rent_record"),
        ("E015", "逾期利息计算表", "interest_calculation"),
    ]
    
    logger.info(f"  证据组6: 3个证据 (使用LLM生成)")
    
    for eid, name, evidence_type in group6_evidence:
        logger.info(f"    - 生成 {eid}: {name}")
        
        prompt = build_prompt(evidence_type, data)
        content = generator.generate(prompt, evidence_type)
        
        filepath = group6_dir / f"证据组6_{eid}_{name}.txt"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        evidence_index["证据列表"].append({
            "证据ID": eid,
            "证据组": 6,
            "证据名称": f"《{name}》",
            "证据名称简写": name,
            "文件类型": "凭证/单据",
            "归属方": "原告",
            "文件路径": str(filepath),
            "生成方式": "LLM",
        })
    
    evidence_groups.append({
        "组编号": 6,
        "组名称": "租金支付记录证据组",
        "证据数量": len(group6_evidence),
        "证明目的": "证明被告租金支付情况及逾期利息计算依据"
    })
    
    # 保存索引
    evidence_index["证据总数"] = len(evidence_index["证据列表"])
    evidence_index["证据组数"] = len(evidence_groups)
    evidence_index["证据组列表"] = evidence_groups
    
    with open(p_dir / "evidence_index.json", 'w', encoding='utf-8') as f:
        json.dump(evidence_index, f, ensure_ascii=False, indent=2)
    
    # 生成起诉状（使用模板）
    complaint = _make_complaint_v2(data)
    with open(p_dir / "民事起诉状.txt", 'w', encoding='utf-8') as f:
        f.write(complaint)
    
    logger.info(f"  民事起诉状.txt")
    logger.info(f"  evidence_index.json")


def _generate_defendant_package_v4(d_dir, data, generator: LLMGenerator):
    d_dir.mkdir(exist_ok=True)
    
    evidence_index = {
        "证据总数": 3,
        "证据组数": 1,
        "证据列表": [],
        "证据组列表": [{
            "组编号": 1,
            "组名称": "被告抗辩证据组",
            "证据数量": 3,
            "证明目的": "证明被告已部分履行付款义务，且因经营困难非恶意拖欠"
        }]
    }
    
    group1_dir = d_dir / "证据组1"
    group1_dir.mkdir(exist_ok=True)
    
    evidence = [
        ("D001", "还款凭证及银行流水", "payment_receipt"),
        ("D002", "保证金收据", "deposit_proof"),
        ("D003", "经营困难证明材料", "shareholder_decision"),
    ]
    
    logger.info(f"  证据组1: 3个证据 (使用LLM生成)")
    
    for eid, name, evidence_type in evidence:
        logger.info(f"    - 生成 {eid}: {name}")
        
        prompt = build_prompt(evidence_type, data)
        content = generator.generate(prompt, evidence_type)
        
        filepath = group1_dir / f"证据组1_{eid}_{name}.txt"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        evidence_index["证据列表"].append({
            "证据ID": eid,
            "证据组": 1,
            "证据名称": f"《{name}》",
            "证据名称简写": name,
            "文件类型": "凭证",
            "归属方": "被告",
            "文件路径": str(filepath),
            "生成方式": "LLM",
        })
    
    with open(d_dir / "evidence_index.json", 'w', encoding='utf-8') as f:
        json.dump(evidence_index, f, ensure_ascii=False, indent=2)
    
    defense = _make_defense_v2(data)
    with open(d_dir / "民事答辩状.txt", 'w', encoding='utf-8') as f:
        f.write(defense)
    
    logger.info(f"  民事答辩状.txt")


def _generate_court_package_v4(c_dir, data, generator: LLMGenerator):
    c_dir.mkdir(exist_ok=True)
    
    # 庭审笔录（模板）
    transcript = _make_court_transcript_v2(data)
    with open(c_dir / "庭审笔录.txt", 'w', encoding='utf-8') as f:
        f.write(transcript)
    
    # 判决书（模板）
    judgment = _make_judgment_v2(data)
    with open(c_dir / "判决书.txt", 'w', encoding='utf-8') as f:
        f.write(judgment)
    
    # 程序性文件
    proc_dir = c_dir / "程序性文件"
    proc_dir.mkdir(exist_ok=True)
    
    files = [
        ("送达回证.txt", _make_court_receipt(data)),
        ("诉讼费收据.txt", _make_court_fee(data)),
        ("审理报告.txt", _make_court_report(data)),
    ]
    
    for name, content in files:
        with open(proc_dir / name, 'w', encoding='utf-8') as f:
            f.write(content)
    
    logger.info(f"  庭审笔录.txt")
    logger.info(f"  判决书.txt")
    logger.info(f"  程序性文件/ 3个文件")


# =============== 起诉状（模板） ===============
def _make_complaint_v2(data):
    return f"""民事起诉状

原告：{data['原告']}
统一社会信用代码：{data['原告信用代码']}
住所地：{data['原告地址']}
法定代表人：{data['原告法人']}，职务：董事长

委托代理人：左安平，上海华通律师事务所律师
委托代理人：蔡晓薇，上海华通律师事务所律师

被告一：{data['被告']}
统一社会信用代码：{data['被告信用代码']}
住所地：{data['被告地址']}
法定代表人：{data['被告法人']}，职务：执行董事兼总经理

被告二：{data['被告二']}
统一社会信用代码：{data['被告二信用代码']}
住所地：{data['被告二地址']}
法定代表人：{data['被告二法人']}，职务：执行董事兼总经理

被告三：{data['被告三']}
统一社会信用代码：{data['被告三信用代码']}
住所地：{data['被告三地址']}
法定代表人：{data['被告三法人']}，职务：董事长

诉讼请求：

1. 判令被告一{data['被告']}立即向原告支付未付租金人民币{data['未付租金']:,.2f}元；

2. 判令被告一{data['被告']}向原告支付截至2024年2月24日产生的逾期利息人民币{data['逾期利息']:,.2f}元（已扣除保证金人民币{data['保证金']:,}元），并以未付租金人民币{data['未付租金']:,.2f}元为基数，自2024年2月25日起按每日万分之五的利率计算至实际清偿之日止的逾期利息；

3. 判令被告一{data['被告']}向原告支付本案实现债权的费用（公证费{data['公证费']:,}元、律师费{data['律师费']:,}元、保全保险费{data['保全保险费']:,.2f}元）合计人民币{data['公证费']+data['律师费']+data['保全保险费']:,.2f}元；

4. 判令原告有权对被告二{data['被告二']}名下抵押物【不动产登记证明编号：{data['抵押登记编号']}】以折价或以拍卖、变卖方式所得价款，在上述第1、2、3项诉讼请求范围内享有优先受偿权；

5. 判令被告三{data['被告三']}对上述第1、2、3项债务承担连带清偿责任；

6. 判令本案全部诉讼费用（包括但不限于案件受理费、保全费等）由三被告共同承担。

事实与理由：

{data['签订日期']}，原告（作为出租人）与被告一（作为承租人）签署了《转让合同》及《融资租赁合同（售后回租）》，约定：原告以人民币{data['合同金额']:,}元的价格向被告一购买其所有的"某某商场设备及附属设施"作为租赁物，再将该租赁物出租给被告一使用；租赁期限为{data['租赁期限']}个月，自{data['交付日期']}起至2024年2月24日止；租金总额为人民币160,623,496.08元，年利率为{data['利率']*100:.2f}%；若被告一逾期支付租金，则需按未付租金的每日万分之五支付逾期利息。

同日，为担保《融资租赁合同》项下债权的实现，原告与被告二签署了《抵押合同（单位）》，被告二以其名下的土地使用权及在建建筑物【不动产登记证明编号：{data['抵押登记编号']}】为被告一的全部债务提供抵押担保，并依法办理了抵押登记。原告亦与被告三签署了《保证合同（单位）》，被告三为被告一的全部债务提供连带责任保证担保。上述主合同及担保合同均办理了公证。

{data['交付日期']}，原告依约向被告一支付了设备转让款（即融资本金）人民币{data['合同金额']:,}元，履行了主要付款义务。同日，《转让合同》项下租赁物的所有权转移至原告名下，并由被告一继续占有使用，租赁期正式开始。被告一在合同履行初期支付了前两期租金。

然而，自第三期租金起，被告一开始出现逾期支付租金的情况，且经原告多次催告后仍未履行。截至2024年2月24日租赁期届满，被告一已累计拖欠租金本金人民币{data['未付租金']:,.2f}元，并由此产生了巨额逾期利息。根据合同约定，被告一还应承担原告为实现债权而支出的公证费、律师费、保全保险费等费用。

原告曾依据经公证的债权文书向法院申请强制执行，但相关申请被驳回，原告只得通过诉讼方式维护自身合法权益。

原告认为，原告与被告一之间的融资租赁法律关系合法有效，原告已全面履行合同义务。被告一逾期支付租金的行为已构成根本违约，依法应承担支付全部未付租金、逾期利息及实现债权费用的违约责任。被告二、被告三作为担保人，应依法在其担保范围内承担相应的抵押担保责任和连带保证责任。

为维护原告的合法权益，根据《中华人民共和国民法典》第七百五十二条、《最高人民法院关于审理融资租赁合同纠纷案件适用法律问题的解释》等相关法律规定，特向贵院提起诉讼，请求依法支持原告的全部诉讼请求。

此致
上海金融法院

具状人：{data['原告']}
日期：2024年X月X日

附件：
1. 本起诉状副本1份
2. 原告营业执照副本复印件1份
3. 被告工商登记信息3份
4. 证据材料6组（详见证据清单）
"""


def _make_defense_v2(data):
    return f"""民事答辩状

答辩人：{data['被告']}
统一社会信用代码：{data['被告信用代码']}
住所地：{data['被告地址']}
法定代表人：{data['被告法人']}，职务：执行董事兼总经理

被答辩人：{data['原告']}
统一社会信用代码：{data['原告信用代码']}
住所地：{data['原告地址']}

答辩人对被答辩人的起诉有异议，答辩如下：

一、关于未付租金金额

被答辩人主张的未付租金金额计算有误。答辩人已实际支付租金人民币{data['已付租金']:,.2f}元，另支付保证金人民币{data['保证金']:,}元。保证金应当在计算未付租金时予以扣除。

二、关于逾期利息

被答辩人主张的逾期利息计算标准过高，应当按照合同约定的正常利率计算，而非按照逾期利率计算。

三、关于经营困难

答辩人因近年来市场环境变化及疫情影响，经营确实出现困难。答辩人一直在积极筹措资金，努力偿还欠款，并非恶意拖欠。

四、关于担保责任

答辩人对抵押担保和保证担保的事实无异议，但请求法院在判决时考虑答辩人的实际困难。

综上，请求法院依法查明事实，驳回被答辩人不合理的诉讼请求。

此致
上海金融法院

答辩人：{data['被告']}
日期：2024年X月X日
"""


def _make_court_transcript_v2(data):
    return f"""庭审笔录

案号：{data['案号']}
案由：融资租赁合同纠纷
开庭时间：2024年X月X日 14:00
开庭地点：上海金融法院第X法庭
审判长：XXX
审判员：XXX
书记员：XXX

原告：{data['原告']}
委托代理人：左安平（律师）、蔡晓薇（律师）

被告一：{data['被告']}
委托代理人：XXX（律师）

被告二：{data['被告二']}
委托代理人：XXX（律师）

被告三：{data['被告三']}
委托代理人：XXX（律师）

审：宣布开庭，核对当事人身份。
原告出庭人员身份已核实。
被告一出庭人员身份已核实。
被告二出庭人员身份已核实。
被告三出庭人员身份已核实。

审：告知当事人诉讼权利义务。
（告知过程略）

审：原告陈述诉讼请求。
原代：宣读诉讼请求（详见起诉状）。

审：被告一答辩。
被代一：答辩意见如下（详见答辩状）。

审：被告二答辩。
被代二：对原告起诉的事实无异议，但请求法院依法判决。

审：被告三答辩。
被代三：对担保事实无异议，请求法院依法判决。

审：法庭举证质证。
（举证质证过程略）

审：法庭调查。
（法庭调查过程略）

审：法庭辩论。
原代：坚持诉讼请求。
被代一：请求驳回不合理部分。

审：最后陈述。
原代：坚持诉讼请求。
被代一：请求法庭依法判决。

审：休庭，本案择日宣判。
以上记录经当事人核对无误后签字。

原告：XXX
被告一：XXX
被告二：XXX
被告三：XXX
审判长：XXX
书记员：XXX
"""


def _make_judgment_v2(data):
    return f"""民事判决书

{data['案号']}

原告：{data['原告']}
被告：{data['被告']}
被告：{data['被告二']}
被告：{data['被告三']}

原告{data['原告']}与被告{data['被告']}、{data['被告二']}、{data['被告三']}融资租赁合同纠纷一案，本院于2024年X月X日立案后，依法适用普通程序，公开开庭进行了审理。本案现已审理终结。

原告诉称：{data['签订日期']}，原告与被告一签订《融资租赁合同》，约定原告以人民币{data['合同金额']:,}元的价格向被告一购买设备，再将该设备出租给被告一使用。合同签订后，原告依约支付了设备转让款，但被告一未按期支付租金。被告二、被告三提供担保。故原告诉至本院，请求判令被告一支付未付租金人民币{data['未付租金']:,.2f}元及逾期利息，被告二、被告三承担担保责任。

被告一辩称：对融资租赁事实无异议，但未付租金金额计算有误，且逾期利息计算标准过高。

被告二辩称：对抵押担保事实无异议。

被告三辩称：对保证担保事实无异议。

经审理查明：{data['签订日期']}，原告与被告一签订《融资租赁合同》，约定原告以人民币{data['合同金额']:,}元的价格向被告一购买设备，租赁期限{data['租赁期限']}个月，年利率{data['利率']*100:.2f}%等。同日，原告与被告二签订《抵押合同》，被告二以其名下房产提供抵押担保；原告与被告三签订《保证合同》，被告三提供连带责任保证。上述合同均办理了公证。原告依约支付了设备转让款，被告一未按期支付租金。

本院认为：原告与被告一签订的《融资租赁合同》系双方真实意思表示，合法有效。原告依约支付了融资金额，被告一未按期支付租金，构成违约。被告二、被告三作为担保人，应承担担保责任。

判决如下：

一、被告{data['被告']}于本判决生效之日起十五日内向原告支付未付租金人民币{data['未付租金']:,.2f}元；

二、被告{data['被告']}于本判决生效之日起十五日内向原告支付逾期利息人民币{data['逾期利息']:,.2f}元（暂计至2024年2月24日），并继续计算至实际清偿之日止；

三、被告{data['被告']}于本判决生效之日起十五日内向原告支付实现债权费用人民币{data['公证费']+data['律师费']+data['保全保险费']:,.2f}元；

四、原告有权对被告{data['被告二']}名下抵押物【不动产登记证明编号：{data['抵押登记编号']}】以折价或以拍卖、变卖方式所得价款，在上述第一、二、三项范围内享有优先受偿权；

五、被告{data['被告三']}对上述第一、二、三项债务承担连带清偿责任；

六、驳回原告其他诉讼请求。

案件受理费人民币XXX元，由被告负担。

如不服本判决，可在判决书送达之日起十五日内向本院递交上诉状。

审 判 长：XXX
审 判 员：XXX
人民陪审员：XXX

2024年X月X日
"""


def _make_court_receipt(data):
    return f"""送达回证

收件人：{data['被告']}
送达文书：起诉状副本、举证通知书、应诉通知书
送达日期：2024年X月X日
送达方式：邮寄送达
送达地址：{data['被告地址']}
收件人签名：XXX
代收人签名：XXX

备注：
1. 起诉状副本1份
2. 举证通知书1份
3. 应诉通知书1份
4. 民事案件举证须知1份
5. 诉讼费用预交通知书1份
"""


def _make_court_fee(data):
    return f"""诉讼费收据

案号：{data['案号']}
案由：融资租赁合同纠纷
付款人：{data['原告']}
金额：人民币XXX元
日期：2024年X月X日

收费项目：
- 案件受理费：XXX元
- 保全申请费：XXX元

收款单位：上海金融法院
"""


def _make_court_report(data):
    return f"""审理报告

案号：{data['案号']}
案由：融资租赁合同纠纷
原告：{data['原告']}
被告：{data['被告']}、{data['被告二']}、{data['被告三']}

一、案件基本情况
原告与被告一于{data['签订日期']}签订《融资租赁合同》，合同金额{data['合同金额']:,}元。被告二提供抵押担保，被告三提供保证担保。

二、案件争议焦点
1. 未付租金金额的认定
2. 逾期利息计算标准的确定
3. 担保责任的承担范围

三、案件事实
详见判决书

四、处理意见
详见判决书

五、承办人意见
同意合议庭意见

承办人：XXX
日期：2024年X月X日
"""


if __name__ == "__main__":
    main()
