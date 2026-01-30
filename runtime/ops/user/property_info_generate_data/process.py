# -*- coding: utf-8 -*-
"""
不动产数据生成算子
功能：生成不动产信息查询结果数据
"""
import os
from typing import Dict, Any
import json
import random
from datetime import datetime, timedelta
from loguru import logger

from datamate.core.base_op import Mapper


class PropertyDataGeneratorMapper(Mapper):
    """
    不动产数据生成算子
    类名必须与 metadata.yml 中的 raw_id 一致
    """

    def __init__(self, *args, **kwargs):
        """
        初始化算子

        Args:
            kwargs: UI 传入的参数
        """
        super().__init__(*args, **kwargs)
        # 获取 UI 参数：生成数量
        self.count = int(kwargs.get("count", 1))

        # 编造的省份列表（避免使用真实省份造成假造印章的违法行为）
        self.PROVINCES = [
            "东华省",
            "西宁省",
            "南康省",
            "北川省",
            "中岳省",
            "东平省",
            "西和省",
            "南安省",
            "北宁省",
            "中康省",
            "东昌省",
            "西瑞省",
            "南和省",
            "北康省",
            "中平省",
            "东宁省",
            "西康省",
            "南川省",
            "北和省",
            "中宁省",
            "东瑞省",
            "西川省",
            "南平省",
            "北康省",
            "中和省",
        ]

        # 编造的省份与城市映射
        self.PROVINCE_CITIES = {
            "东华省": ["东华市", "东平市", "东康市"],
            "西宁省": ["西宁市", "西平市", "西康市"],
            "南康省": ["南康市", "南平市", "南和市"],
            "北川省": ["北川市", "北宁市", "北和市"],
            "中岳省": ["中岳市", "中平市", "中康市"],
            "东平省": ["东平市", "东宁市", "东和市"],
            "西和省": ["西和市", "西宁市", "西康市"],
            "南安省": ["南安市", "南平市", "南和市"],
            "北宁省": ["北宁市", "北平市", "北和市"],
            "中康省": ["中康市", "中宁市", "中平市"],
            "东昌省": ["东昌市", "东宁市", "东和市"],
            "西瑞省": ["西瑞市", "西宁市", "西康市"],
            "南和省": ["南和市", "南平市", "南康市"],
            "北康省": ["北康市", "北宁市", "北平市"],
            "中平省": ["中平市", "中宁市", "中康市"],
            "东宁省": ["东宁市", "东平市", "东和市"],
            "西康省": ["西康市", "西宁市", "西平市"],
            "南川省": ["南川市", "南宁市", "南和市"],
            "北和省": ["北和市", "北宁市", "北平市"],
            "中宁省": ["中宁市", "中康市", "中平市"],
            "东瑞省": ["东瑞市", "东宁市", "东和市"],
            "西川省": ["西川市", "西宁市", "西康市"],
            "南平省": ["南平市", "南宁市", "南和市"],
            "北康省": ["北康市", "北宁市", "北平市"],
            "中和省": ["中和市", "中宁市", "中康市"],
        }

        # 姓氏和名字列表
        self.SURNAMES = [
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
        self.NAMES = [
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
        """生成18位合法格式的身份证号"""
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

        year = random.randint(1970, 2000)
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        birth_date = f"{year:04d}{month:02d}{day:02d}"

        sequence = random.randint(100, 999)

        id_17 = area_code + birth_date + str(sequence)
        weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_codes = ["1", "0", "X", "9", "8", "7", "6", "5", "4", "3", "2"]

        total = sum(int(id_17[i]) * weights[i] for i in range(17))
        check_code = check_codes[total % 11]

        return id_17 + check_code

    def _generate_random_number(self, length: int) -> str:
        """生成指定长度的随机数字字符串"""
        return "".join([str(random.randint(0, 9)) for _ in range(length)])

    def _generate_random_date_time_2025(self) -> tuple:
        """生成2025年范围内的随机日期和时间"""
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 12, 31)
        random_date = start_date + timedelta(
            days=random.randint(0, (end_date - start_date).days),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59),
        )

        date_time_str = random_date.strftime("%Y年%m月%d日 %H:%M:%S")
        proof_number = random_date.strftime("%Y%m%d") + self._generate_random_number(6)

        return date_time_str, proof_number

    def _generate_name(self) -> str:
        """生成随机姓名"""
        surname = random.choice(self.SURNAMES)
        name_length = random.choice([1, 2])
        name = "".join([random.choice(self.NAMES) for _ in range(name_length)])
        return surname + name

    def _generate_address(self, province: str, city: str) -> str:
        """生成详细地址"""
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
        building_num = random.randint(1, 20)
        unit_num = random.randint(1, 6)
        room_num = random.randint(101, 1806)

        street = random.choice(streets)
        building_type = random.choice(building_types)

        return f"{province}{city}{street}{building_type}{building_num}栋{unit_num}单元{room_num}室"

    def _generate_computer_operator(self) -> str:
        """生成电脑查册人"""
        part1 = "".join([random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(4)])
        part2 = "".join([random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(4)])
        return f"{part1}-{part2}"

    def _generate_single_record(
        self, province: str, city: str, serial_number: int
    ) -> Dict[str, Any]:
        """生成单条不动产记录"""
        status = random.choice(["正常", "有效", "在册"])
        contract_number = self._generate_random_number(15)
        address = self._generate_address(province, city)
        city_short = city.replace("市", "")
        property_cert_number = f"{city_short}{self._generate_random_number(5)}"
        planning_purpose = random.choice(["住宅", "商业"])
        building_area = f"{round(random.uniform(80, 150), 1)}㎡"
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

    def _generate_single_data(self, index: int) -> Dict[str, Any]:
        """生成单组不动产数据"""
        try:
            province = random.choice(self.PROVINCES)
            cities = self.PROVINCE_CITIES.get(province, ["东华省"])
            city = random.choice(cities)

            name = self._generate_name()
            id_card = self._generate_id_card()
            query_purpose = random.choice(
                ["担保用", "抵押贷款", "财产证明", "购房贷款"]
            )
            computer_operator = self._generate_computer_operator()
            print_date, proof_number = self._generate_random_date_time_2025()

            table_rows_count = random.randint(1, 2)
            table_data = []
            for i in range(1, table_rows_count + 1):
                table_data.append(self._generate_single_record(province, city, i))

            data = {
                "index": index,
                "省份": province,
                "姓名（证件号码）": f"{name}（{id_card}）",
                "查询目的": query_purpose,
                "电脑查册人": computer_operator,
                "证明流水号": proof_number,
                "打印日期": print_date,
                "表格数据": table_data,
            }

            return data

        except Exception as e:
            logger.error(f"生成第{index}组数据时发生错误: {str(e)}")
            raise

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑 - 生成不动产数据

        Args:
            sample: 输入的数据样本（纯生成型算子，忽略输入）

        Returns:
            处理后的数据样本，包含生成的 JSON 数据
        """
        file_path = sample.get('filePath')
        if not file_path.endswith('.docx') or os.path.normpath(file_path).count(os.sep) > 3:
            return sample

        try:
            logger.info(f"[不动产数据生成] 开始生成{self.count}组数据")

            data_list = []
            for i in range(1, self.count + 1):
                try:
                    data = self._generate_single_data(i)
                    data_list.append(data)
                except Exception as e:
                    logger.error(f"生成第{i}组数据失败: {str(e)}")
                    continue

            logger.info(f"[不动产数据生成] 成功生成{len(data_list)}组数据")

            # 将生成的数据作为 JSON 字符串存入 sample
            sample["text"] = json.dumps(data_list, ensure_ascii=False, indent=2)

            return sample

        except Exception as e:
            logger.error(f"不动产数据生成算子执行失败: {str(e)}")
            raise
