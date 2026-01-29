"""
不动产数据生成算子
功能：生成不动产信息查询结果数据
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any
from loguru import logger

from datamate.core.base_op import Mapper


class DataGenerator:
    """不动产数据生成辅助类"""

    # 国内省份列表（真实省份）
    PROVINCES = [
        "北京市",
        "天津市",
        "河北省",
        "山西省",
        "内蒙古自治区",
        "辽宁省",
        "吉林省",
        "黑龙江省",
        "上海市",
        "江苏省",
        "浙江省",
        "安徽省",
        "福建省",
        "江西省",
        "山东省",
        "河南省",
        "湖北省",
        "湖南省",
        "广东省",
        "广西壮族自治区",
        "海南省",
        "重庆市",
        "四川省",
        "贵州省",
        "云南省",
        "西藏自治区",
        "陕西省",
        "甘肃省",
        "青海省",
        "宁夏回族自治区",
        "新疆维吾尔自治区",
    ]

    # 省份与城市映射（简化版，包含主要城市）
    PROVINCE_CITIES = {
        "北京市": ["北京市"],
        "天津市": ["天津市"],
        "河北省": [
            "石家庄市",
            "唐山市",
            "秦皇岛市",
            "邯郸市",
            "邢台市",
            "保定市",
            "张家口市",
            "承德市",
            "沧州市",
            "廊坊市",
            "衡水市",
        ],
        "山西省": [
            "太原市",
            "大同市",
            "阳泉市",
            "长治市",
            "晋城市",
            "朔州市",
            "晋中市",
            "运城市",
            "忻州市",
            "临汾市",
            "吕梁市",
        ],
        "内蒙古自治区": [
            "呼和浩特市",
            "包头市",
            "乌海市",
            "赤峰市",
            "通辽市",
            "鄂尔多斯市",
            "呼伦贝尔市",
            "巴彦淖尔市",
            "乌兰察布市",
        ],
        "辽宁省": [
            "沈阳市",
            "大连市",
            "鞍山市",
            "抚顺市",
            "本溪市",
            "丹东市",
            "锦州市",
            "营口市",
            "阜新市",
            "辽阳市",
            "盘锦市",
            "铁岭市",
            "朝阳市",
            "葫芦岛市",
        ],
        "吉林省": [
            "长春市",
            "吉林市",
            "四平市",
            "辽源市",
            "通化市",
            "白山市",
            "松原市",
            "白城市",
            "延边朝鲜族自治州",
        ],
        "黑龙江省": [
            "哈尔滨市",
            "齐齐哈尔市",
            "鸡西市",
            "鹤岗市",
            "双鸭山市",
            "大庆市",
            "伊春市",
            "佳木斯市",
            "七台河市",
            "牡丹江市",
            "黑河市",
            "绥化市",
            "大兴安岭地区",
        ],
        "上海市": ["上海市"],
        "江苏省": [
            "南京市",
            "无锡市",
            "徐州市",
            "常州市",
            "苏州市",
            "南通市",
            "连云港市",
            "淮安市",
            "盐城市",
            "扬州市",
            "镇江市",
            "泰州市",
            "宿迁市",
        ],
        "浙江省": [
            "杭州市",
            "宁波市",
            "温州市",
            "嘉兴市",
            "湖州市",
            "绍兴市",
            "金华市",
            "衢州市",
            "舟山市",
            "台州市",
            "丽水市",
        ],
        "安徽省": [
            "合肥市",
            "芜湖市",
            "蚌埠市",
            "淮南市",
            "马鞍山市",
            "淮北市",
            "铜陵市",
            "安庆市",
            "黄山市",
            "滁州市",
            "阜阳市",
            "宿州市",
            "六安市",
            "亳州市",
            "池州市",
            "宣城市",
        ],
        "福建省": [
            "福州市",
            "厦门市",
            "莆田市",
            "三明市",
            "泉州市",
            "漳州市",
            "南平市",
            "龙岩市",
            "宁德市",
        ],
        "江西省": [
            "南昌市",
            "景德镇市",
            "萍乡市",
            "九江市",
            "新余市",
            "鹰潭市",
            "赣州市",
            "吉安市",
            "宜春市",
            "抚州市",
            "上饶市",
        ],
        "山东省": [
            "济南市",
            "青岛市",
            "淄博市",
            "枣庄市",
            "东营市",
            "烟台市",
            "潍坊市",
            "济宁市",
            "泰安市",
            "威海市",
            "日照市",
            "临沂市",
            "德州市",
            "聊城市",
            "滨州市",
            "菏泽市",
        ],
        "河南省": [
            "郑州市",
            "开封市",
            "洛阳市",
            "平顶山市",
            "安阳市",
            "鹤壁市",
            "新乡市",
            "焦作市",
            "濮阳市",
            "许昌市",
            "漯河市",
            "三门峡市",
            "南阳市",
            "商丘市",
            "信阳市",
            "周口市",
            "驻马店市",
        ],
        "湖北省": [
            "武汉市",
            "黄石市",
            "十堰市",
            "宜昌市",
            "襄阳市",
            "鄂州市",
            "荆门市",
            "孝感市",
            "荆州市",
            "黄冈市",
            "咸宁市",
            "随州市",
            "恩施土家族苗族自治州",
        ],
        "湖南省": [
            "长沙市",
            "株洲市",
            "湘潭市",
            "衡阳市",
            "邵阳市",
            "岳阳市",
            "常德市",
            "张家界市",
            "益阳市",
            "郴州市",
            "永州市",
            "怀化市",
            "娄底市",
            "湘西土家族苗族自治州",
        ],
        "广东省": [
            "广州市",
            "韶关市",
            "深圳市",
            "珠海市",
            "汕头市",
            "佛山市",
            "江门市",
            "湛江市",
            "茂名市",
            "肇庆市",
            "惠州市",
            "梅州市",
            "汕尾市",
            "河源市",
            "阳江市",
            "清远市",
            "东莞市",
            "中山市",
            "潮州市",
            "揭阳市",
            "云浮市",
        ],
        "广西壮族自治区": [
            "南宁市",
            "柳州市",
            "桂林市",
            "梧州市",
            "北海市",
            "防城港市",
            "钦州市",
            "贵港市",
            "玉林市",
            "百色市",
            "贺州市",
            "河池市",
            "来宾市",
            "崇左市",
        ],
        "海南省": ["海口市", "三亚市", "三沙市", "儋州市"],
        "重庆市": ["重庆市"],
        "四川省": [
            "成都市",
            "自贡市",
            "攀枝花市",
            "泸州市",
            "德阳市",
            "绵阳市",
            "广元市",
            "遂宁市",
            "内江市",
            "乐山市",
            "南充市",
            "眉山市",
            "宜宾市",
            "广安市",
            "达州市",
            "雅安市",
            "巴中市",
            "资阳市",
            "阿坝藏族羌族自治州",
            "甘孜藏族自治州",
            "凉山彝族自治州",
        ],
        "贵州省": [
            "贵阳市",
            "六盘水市",
            "遵义市",
            "安顺市",
            "毕节市",
            "铜仁市",
            "黔西南布依族苗族自治州",
            "黔东南苗族侗族自治州",
            "黔南布依族苗族自治州",
        ],
        "云南省": [
            "昆明市",
            "曲靖市",
            "玉溪市",
            "保山市",
            "昭通市",
            "丽江市",
            "普洱市",
            "临沧市",
            "楚雄彝族自治州",
            "红河哈尼族彝族自治州",
            "文山壮族苗族自治州",
            "西双版纳傣族自治州",
            "大理白族自治州",
            "德宏傣族景颇族自治州",
            "怒江傈僳族自治州",
            "迪庆藏族自治州",
        ],
        "西藏自治区": [
            "拉萨市",
            "昌都市",
            "林芝市",
            "山南市",
            "那曲市",
            "阿里地区",
            "日喀则市",
        ],
        "陕西省": [
            "西安市",
            "铜川市",
            "宝鸡市",
            "咸阳市",
            "渭南市",
            "延安市",
            "汉中市",
            "榆林市",
            "安康市",
            "商洛市",
        ],
        "甘肃省": [
            "兰州市",
            "嘉峪关市",
            "金昌市",
            "白银市",
            "天水市",
            "武威市",
            "张掖市",
            "平凉市",
            "酒泉市",
            "庆阳市",
            "定西市",
            "陇南市",
            "临夏回族自治州",
            "甘南藏族自治州",
        ],
        "青海省": [
            "西宁市",
            "海东市",
            "海北藏族自治州",
            "黄南藏族自治州",
            "海南藏族自治州",
            "果洛藏族自治州",
            "玉树藏族自治州",
            "海西蒙古族藏族自治州",
        ],
        "宁夏回族自治区": ["银川市", "石嘴山市", "吴忠市", "固原市", "中卫市"],
        "新疆维吾尔自治区": [
            "乌鲁木齐市",
            "克拉玛依市",
            "吐鲁番市",
            "哈密市",
            "昌吉回族自治州",
            "博尔塔拉蒙古自治州",
            "巴音郭楞蒙古自治州",
            "阿克苏地区",
            "克孜勒苏柯尔克孜自治州",
            "喀什地区",
            "和田地区",
            "伊犁哈萨克自治州",
            "塔城地区",
            "阿勒泰地区",
        ],
    }

    # 姓氏和名字列表（用于生成姓名）
    SURNAMES = [
        "王",
        "李",
        "张",
        "刘",
        "陈",
        "杨",
        "赵",
        "黄",
        "周",
        "吴",
        "徐",
        "孙",
        "胡",
        "朱",
        "高",
        "林",
        "何",
        "郭",
        "马",
        "罗",
    ]
    NAMES = [
        "伟",
        "芳",
        "娜",
        "敏",
        "静",
        "强",
        "磊",
        "军",
        "洋",
        "勇",
        "艳",
        "杰",
        "娟",
        "涛",
        "明",
        "超",
        "秀",
        "霞",
        "平",
        "刚",
    ]

    def _generate_id_card(self) -> str:
        """
        生成18位合法格式的身份证号

        Returns:
            18位身份证号
        """
        # 地区码（前6位）- 使用一些真实地区码
        area_codes = [
            "110101",
            "310101",
            "440101",
            "330101",
            "320101",
            "420101",
            "500101",
            "510101",
        ]
        area_code = random.choice(area_codes)

        # 出生日期（8位）- 1970-2000年之间
        year = random.randint(1970, 2000)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        birth_date = f"{year:04d}{month:02d}{day:02d}"

        # 顺序码（3位）
        sequence = random.randint(100, 999)

        # 校验码（1位）
        id_17 = area_code + birth_date + str(sequence)
        weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_codes = ["1", "0", "X", "9", "8", "7", "6", "5", "4", "3", "2"]

        total = sum(int(id_17[i]) * weights[i] for i in range(17))
        check_code = check_codes[total % 11]

        return id_17 + check_code

    def _generate_random_number(self, length: int) -> str:
        """
        生成指定长度的随机数字字符串

        Args:
            length: 数字长度

        Returns:
            随机数字字符串
        """
        return "".join([str(random.randint(0, 9)) for _ in range(length)])

    def _generate_random_date_time_2025(self) -> tuple:
        """
        生成2025年范围内的随机日期和时间

        Returns:
            (日期时间字符串, 证明流水号)
            日期时间格式: "xxxx年xx月xx日 xx:xx:xx"
            证明流水号: 14位数字，前8位是日期时间，后6位是随机数字
        """
        # 生成2025年1月1日到2025年12月31日之间的随机日期时间
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 12, 31)
        random_date = start_date + timedelta(
            days=random.randint(0, (end_date - start_date).days),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )

        # 格式化为字符串
        date_time_str = random_date.strftime("%Y年%m月%d日 %H:%M:%S")

        # 生成证明流水号：前8位是日期（YYYYMMDD），后6位是随机数字
        proof_number = random_date.strftime("%Y%m%d") + self._generate_random_number(6)

        return date_time_str, proof_number

    def _generate_name(self) -> str:
        """
        生成随机姓名

        Returns:
            姓名（2-3个汉字）
        """
        surname = random.choice(self.SURNAMES)
        name_length = random.choice([1, 2])
        name = "".join([random.choice(self.NAMES) for _ in range(name_length)])
        return surname + name

    def _generate_address(self, province: str, city: str) -> str:
        """
        生成详细地址

        Args:
            province: 省份
            city: 城市

        Returns:
            详细地址（XX省XX市XXXXX，精确到门牌号）
        """
        # 街道名称
        streets = [
            "人民路",
            "解放路",
            "建设路",
            "和平路",
            "中山路",
            "胜利路",
            "新华路",
            "光明路",
            "红旗路",
            "东风路",
        ]
        # 建筑类型
        building_types = [
            "小区",
            "花园",
            "公寓",
            "大厦",
            "家园",
            "广场",
            "新城",
            "嘉园",
        ]
        # 楼栋号
        building_num = random.randint(1, 20)
        # 单元号
        unit_num = random.randint(1, 6)
        # 房间号
        room_num = random.randint(101, 1806)

        street = random.choice(streets)
        building_type = random.choice(building_types)

        return f"{province}{city}{street}{building_type}{building_num}栋{unit_num}单元{room_num}室"

    def _generate_computer_operator(self) -> str:
        """
        生成电脑查册人

        Returns:
            格式为：4个大写随机字母+横杠+4个大写随机字母
        """
        part1 = "".join([random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(4)])
        part2 = "".join([random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(4)])
        return f"{part1}-{part2}"

    def _generate_single_record(
        self, province: str, city: str, serial_number: int
    ) -> Dict[str, Any]:
        """
        生成单条不动产记录

        Args:
            province: 省份
            city: 城市
            serial_number: 序号

        Returns:
            单条记录字典
        """
        # 状态：3选1
        status = random.choice(["正常", "有效", "在册"])

        # 合同号：15位随机数字
        contract_number = self._generate_random_number(15)

        # 地址
        address = self._generate_address(province, city)

        # 产权证号：城市名+5位随机数字（去除"市"字）
        city_short = city.replace("市", "")
        property_cert_number = f"{city_short}{self._generate_random_number(5)}"

        # 规划用途：2选1
        planning_purpose = random.choice(["住宅", "商业"])

        # 建筑面积：80-150之间的1位小数
        building_area = round(random.uniform(80, 150), 1)

        # 数据来源：城市名+"不动产登记中心"（城市名已包含"市"字）
        data_source = f"{city}不动产登记中心"

        return {
            "序号": serial_number,
            "状态": status,
            "合同号": contract_number,
            "地址": address,
            "产权证号": property_cert_number,
            "规划用途": planning_purpose,
            "建筑面积": building_area,
            "数据来源": data_source,
        }

    def generate_single_data(self, index: int) -> Dict[str, Any]:
        """
        生成单组不动产数据

        Args:
            index: 数据索引（1-100）

        Returns:
            单组数据字典
        """
        # 省份：国内真实省份
        province = random.choice(self.PROVINCES)

        # 城市：从该省份中选择一个城市
        cities = self.PROVINCE_CITIES.get(province, ["北京市"])
        city = random.choice(cities)

        # 姓名
        name = self._generate_name()

        # 证件号码：18位合法格式
        id_card = self._generate_id_card()

        # 查询目的：4选1
        query_purpose = random.choice(["担保用", "抵押贷款", "财产证明", "购房贷款"])

        # 电脑查册人
        computer_operator = self._generate_computer_operator()

        # 登记字号：15位随机数字
        registration_number = self._generate_random_number(15)

        # 身份证号
        identity_card = self._generate_id_card()

        # 地址：沧瑞省范围内的住宅地址（注：沧瑞省为虚构省份，此处使用真实省份）
        address_cangrui = self._generate_address("沧瑞省", "沧州市")

        # 产权证号：格式为"AA BBBBB"
        property_cert_format = f"{city[:2]} {self._generate_random_number(5)}"

        # 证明流水号和打印日期
        print_date, proof_number = self._generate_random_date_time_2025()

        # 生成表格数据（1-5行）
        table_rows_count = random.randint(1, 5)
        table_data = []
        for i in range(1, table_rows_count + 1):
            table_data.append(self._generate_single_record(province, city, i))

        # 组装完整数据
        data = {
            "index": index,
            "省份": province,
            "姓名（证件号码）": f"{name}（{id_card}）",
            "查询目的": query_purpose,
            "电脑查册人": computer_operator,
            "登记字号": registration_number,
            "身份证号": identity_card,
            "地址": address_cangrui,
            "产权证号": property_cert_format,
            "证明流水号": proof_number,
            "打印日期": print_date,
            "表格数据": table_data,
        }

        return data


class PropertyDataGenerator(Mapper):
    """
    不动产数据生成算子
    类名建议使用驼峰命名法定义，例如 PropertyDataGenerator
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 从UI参数获取配置
        self.data_count = int(kwargs.get("dataCount", 10))
        self.output_format = kwargs.get("outputFormat", "json")
        self.include_table_data = kwargs.get("includeTableData", True)

        # 创建数据生成器实例
        self.generator = DataGenerator()

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑
        :param sample: 输入的数据样本，通常包含 text_key 等字段
        :return: 处理后的数据样本
        """
        try:
            # 生成指定数量的不动产数据
            data_list = []
            for i in range(1, self.data_count + 1):
                data = self.generator.generate_single_data(i)

                # 如果不包含表格数据，则移除该字段
                if not self.include_table_data:
                    data.pop("表格数据", None)

                data_list.append(data)

            # 根据输出格式生成结果
            if self.output_format == "json":
                result = json.dumps(data_list, ensure_ascii=False, indent=2)
            else:
                # 纯文本格式
                result_lines = []
                for data in data_list:
                    result_lines.append(f"=== 第{data['index']}组数据 ===")
                    result_lines.append(f"省份: {data['省份']}")
                    result_lines.append(f"姓名（证件号码）: {data['姓名（证件号码）']}")
                    result_lines.append(f"查询目的: {data['查询目的']}")
                    result_lines.append(f"电脑查册人: {data['电脑查册人']}")
                    result_lines.append(f"登记字号: {data['登记字号']}")
                    result_lines.append(f"身份证号: {data['身份证号']}")
                    result_lines.append(f"地址: {data['地址']}")
                    result_lines.append(f"产权证号: {data['产权证号']}")
                    result_lines.append(f"证明流水号: {data['证明流水号']}")
                    result_lines.append(f"打印日期: {data['打印日期']}")

                    if self.include_table_data and data.get("表格数据"):
                        result_lines.append("表格数据:")
                        for row in data["表格数据"]:
                            result_lines.append(f"  - {row}")

                    result_lines.append("")

                result = "\n".join(result_lines)

            # 将结果添加到 sample 中
            sample[self.text_key] = result

            logger.info(
                f"成功生成{self.data_count}组不动产数据，格式: {self.output_format}"
            )
            return sample

        except Exception as e:
            logger.error(f"生成不动产数据时发生错误: {str(e)}")
            raise
