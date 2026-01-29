import json
import random
from pathlib import Path
from typing import List, Dict, Optional


class TemplateLibrary:
    """模板库 - 提供自动生成所需的模板数据"""

    def __init__(self, template_dir: str = "config/template_libraries"):
        """
        初始化模板库

        Args:
            template_dir: 模板目录
        """
        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.company_names: List[Dict] = []
        self.equipment_names: List[Dict] = []
        self.locations: List[Dict] = []
        self._load_templates()

    def _load_templates(self):
        """加载所有模板数据"""
        company_names_path = self.template_dir / "company_names.json"
        if company_names_path.exists():
            try:
                with open(company_names_path, 'r', encoding='utf-8') as f:
                    self.company_names = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.company_names = self._get_default_company_names()
        else:
            self.company_names = self._get_default_company_names()
            self._save_template(company_names_path, self.company_names)

        equipment_names_path = self.template_dir / "equipment_names.json"
        if equipment_names_path.exists():
            try:
                with open(equipment_names_path, 'r', encoding='utf-8') as f:
                    self.equipment_names = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.equipment_names = self._get_default_equipment_names()
        else:
            self.equipment_names = self._get_default_equipment_names()
            self._save_template(equipment_names_path, self.equipment_names)

        locations_path = self.template_dir / "locations.json"
        if locations_path.exists():
            try:
                with open(locations_path, 'r', encoding='utf-8') as f:
                    self.locations = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.locations = self._get_default_locations()
        else:
            self.locations = self._get_default_locations()
            self._save_template(locations_path, self.locations)

    def _save_template(self, path: Path, data: list):
        """保存模板数据"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _get_default_company_names(self) -> List[Dict]:
        """获取默认公司名称模板"""
        return [
            {
                "脱敏标识": "某某公司1",
                "公司名称": "江西昌盛商业管理有限公司",
                "信用代码": "91360121MA1XXXXXX",
                "法定代表人": "张伟",
                "注册地址": "江西省南昌市红谷滩区XX路XX号",
                "联系电话": "0791-88888888"
            },
            {
                "脱敏标识": "某某公司2",
                "公司名称": "杭州恒通贸易有限公司",
                "信用代码": "91330100MA2XXXXXX",
                "法定代表人": "李明",
                "注册地址": "浙江省杭州市西湖区XX路XX号",
                "联系电话": "0571-88888888"
            },
            {
                "脱敏标识": "某某公司3",
                "公司名称": "深圳创投科技有限公司",
                "信用代码": "91440300MA3XXXXXX",
                "法定代表人": "王强",
                "注册地址": "广东省深圳市南山区XX路XX号",
                "联系电话": "0755-88888888"
            },
            {
                "脱敏标识": "某某公司4",
                "公司名称": "北京华夏融资租赁有限公司",
                "信用代码": "91110000MA4XXXXXX",
                "法定代表人": "赵敏",
                "注册地址": "北京市朝阳区XX路XX号",
                "联系电话": "010-88888888"
            },
            {
                "脱敏标识": "某某公司5",
                "公司名称": "东方国际融资租赁有限公司",
                "信用代码": "91310000MA1FL3L123",
                "法定代表人": "周明远",
                "注册地址": "中国（上海）自由贸易试验区世纪大道100号",
                "联系电话": "021-88888888"
            },
            {
                "脱敏标识": "某某公司6",
                "公司名称": "广州金桥担保有限公司",
                "信用代码": "91440000MA5XXXXXX",
                "法定代表人": "陈华",
                "注册地址": "广东省广州市天河区XX路XX号",
                "联系电话": "020-88888888"
            },
            {
                "脱敏标识": "某某公司7",
                "公司名称": "成都新光实业集团有限公司",
                "信用代码": "91510000MA6XXXXXX",
                "法定代表人": "刘洋",
                "注册地址": "四川省成都市高新区XX路XX号",
                "联系电话": "028-88888888"
            },
            {
                "脱敏标识": "某某公司8",
                "公司名称": "武汉长江实业股份有限公司",
                "信用代码": "91420000MA7XXXXXX",
                "法定代表人": "黄伟",
                "注册地址": "湖北省武汉市江岸区XX路XX号",
                "联系电话": "027-88888888"
            }
        ]

    def _get_default_equipment_names(self) -> List[Dict]:
        """获取默认设备名称模板"""
        return [
            {"名称": "多联机中央空调系统", "规格型号": "VRV VIII代"},
            {"名称": "冷水机组", "规格型号": "离心式RF1-5000"},
            {"名称": "电梯设备", "规格型号": "曳引式客梯KONIA-1000"},
            {"名称": "配电变压器", "规格型号": "SCB13-2500/10"},
            {"名称": "消防水泵", "规格型号": "XBD15/40"},
            {"名称": "监控系统", "规格型号": "DS-7700系列"},
            {"名称": "门禁系统", "规格型号": "DS-K2600系列"},
            {"名称": "停车场管理系统", "规格型号": "速通闸机ST-600"},
            {"名称": "新风换气系统", "规格型号": "热回收新风机组HRB-5000"},
            {"名称": "地暖热水锅炉", "规格型号": "冷凝式锅炉CGB-2"},
            {"名称": "空气源热泵", "规格型号": "商用热水机组RS-10"},
            {"名称": "光伏发电设备", "规格型号": "单晶硅组件GCL-450W"},
            {"名称": "储能电池系统", "规格型号": "磷酸铁锂电池500kWh"},
            {"名称": "充电桩设备", "规格型号": "直流快充桩60kW"},
            {"名称": "LED显示屏", "规格型号": "室内P2.5全彩屏"},
            {"名称": "会议音响系统", "规格型号": "专业扩声系统Bose"},
            {"名称": "智能照明系统", "规格型号": "DALI控制系统"},
            {"名称": "楼宇自控系统", "规格型号": "BACnet协议控制器"},
            {"名称": "给排水设备", "规格型号": "不锈钢水箱50m³"},
            {"名称": "燃气锅炉", "规格型号": "真空热水锅炉ZKB-2"}
        ]

    def _get_default_locations(self) -> List[Dict]:
        """获取默认地址模板"""
        return [
            {"地址": "南昌市红谷滩区XX广场A座"},
            {"地址": "杭州市西湖区XX大厦B座"},
            {"地址": "深圳市南山区XX科技园C栋"},
            {"地址": "北京市朝阳区XX中心D座"},
            {"地址": "上海市浦东新区XX大厦E栋"},
            {"地址": "广州市天河区XX广场F座"},
            {"地址": "成都市高新区XX大厦G栋"},
            {"地址": "武汉市江岸区XX广场H座"},
            {"地址": "南京市鼓楼区XX中心I座"},
            {"地址": "西安市雁塔区XX大厦J栋"}
        ]

    def generate_equipment_list(
        self,
        count: int,
        total_value: int,
        random_seed: Optional[int] = None
    ) -> List[Dict]:
        """
        生成设备清单

        Args:
            count: 设备数量
            total_value: 总评估价值
            random_seed: 随机种子（用于确定性生成）
        Returns:
            设备列表
        """
        if random_seed is not None:
            random.seed(random_seed)

        if not self.equipment_names:
            raise ValueError("设备模板库为空")

        if not self.locations:
            raise ValueError("地址模板库为空")

        if count <= 0:
            raise ValueError("设备数量必须大于0")

        if total_value <= 0:
            raise ValueError("总评估价值必须大于0")

        equipment_list = []
        remaining_value = total_value

        for i in range(count):
            if i == count - 1:
                value = remaining_value
            else:
                max_value = int(remaining_value * 0.15)
                min_value = int(max_value * 0.3)
                value = random.randint(min_value, max_value)
                remaining_value -= value

            equipment_name = random.choice(self.equipment_names)

            equipment = {
                "序号": i + 1,
                "设备名称": equipment_name["名称"],
                "规格型号": equipment_name.get("规格型号", f"Model-{random.randint(100, 999)}"),
                "数量": f"{random.randint(1, 10)}套",
                "存放地点": random.choice(self.locations)["地址"],
                "评估价值": value,
                "数据来源": "模板生成"
            }
            equipment_list.append(equipment)

        return equipment_list

    def generate_bank_account(self, bank_code: str = "1502211009") -> str:
        """生成随机银行账号"""
        suffix = random.randint(10000000, 99999999)
        return f"{bank_code}{suffix}"

    def get_company_profile(self, marker: str) -> Optional[Dict]:
        """
        获取公司Profile

        Args:
            marker: 脱敏标识（如"某某公司1"）
        Returns:
            公司信息字典
        """
        for company in self.company_names:
            if company.get("脱敏标识") == marker:
                return company
        return None

    def get_random_company(self, exclude_markers: List[str] = None) -> Dict:
        """
        获取随机公司

        Args:
            exclude_markers: 排除的脱敏标识列表
        Returns:
            公司信息字典
        """
        if exclude_markers is None:
            exclude_markers = []

        available = [c for c in self.company_names if c.get("脱敏标识") not in exclude_markers]
        if available:
            return random.choice(available)
        return self.company_names[0] if self.company_names else {}

    def get_random_location(self) -> str:
        """获取随机地址"""
        if self.locations:
            return random.choice(self.locations)["地址"]
        return ""

    def reload_templates(self):
        """重新加载模板数据"""
        self._load_templates()
