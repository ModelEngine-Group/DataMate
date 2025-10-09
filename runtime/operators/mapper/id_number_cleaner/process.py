#!/user/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 身份证号码匿名化插件
Create: 2024/12/5 15:43
"""
import logging as logger
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import pytz


from data_platform.core.base_op import Mapper


class AnonymizedIdNumber(Mapper):
    def __init__(self, *args, **kwargs):
        super(AnonymizedIdNumber, self).__init__(*args, **kwargs)
        self.id_number_re_compile = self.get_id_number_re_compile()
        self.id_coefficient = (7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2)
        self.id_verification = ("1", "0", "X", "9", "8", "7", "6", "5", "4", "3", "2")
        self.area_code_enum = self.load_code_list()

    @staticmethod
    def get_id_number_re_compile():
        """获取身份证号码正则匹配对象"""
        # 中国身份证号共计18位，1,2位省份，3,4位城市，5,6位县区码，7~14位为出生日期，最后一位为校验码，做了严格限定
        id_card_pattern = r'(?<=[^0-9])' \
                          r'((1[1-5]|2[1-3]|3[1-7]|4[1-6]|5[0-4]|6[1-5]|71|81|82)' \
                          r'(0[0-9]|1[0-9]|2[0-9]|3[0-4]|4[0-3]|5[1-3]|90)' \
                          r'(0[0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-3]|5[1-7]|6[1-4]|7[1-4]|8[1-7])' \
                          r'(18|19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])' \
                          r'\d{3}[0-9xX])' \
                          r'(?=[^0-9xX])'
        return re.compile(id_card_pattern)

    @staticmethod
    def load_code_list():
        """编码表加载"""
        area_code_enum_path = str(Path(__file__).parent / 'resources' / 'area_code_enum.txt')
        with open(area_code_enum_path, 'r', encoding='utf-8') as f:
            area_code_list = set(f.read().splitlines())
        return area_code_list

    @staticmethod
    def _verify_birthday_code(birthday_code: str):
        """判断出生日期编码的8位数是否有效"""
        year = int(birthday_code[:4])
        month = int(birthday_code[4:6])
        day = int(birthday_code[6:8])
        date_string = "{}-{}-{}".format(year, month, day)
        date_format = "%Y-%m-%d"
        try:
            # 将日期字符串转换成时间
            date = datetime.strptime(date_string, date_format)
            # 设置时区为上海
            china_tz = pytz.timezone("Asia/Shanghai")
            china_date = china_tz.localize(date)
            # 获取当前时间
            current_date = datetime.now(china_tz)
            # 判断出生日期是否晚于当前时间；若晚于，则出生日期不合法
            return china_date <= current_date
        except ValueError:
            return False

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        sample[self.text_key] = self._id_number_filter(sample[self.text_key])
        logger.info("fileName: %s, method: IDNumberCleaner costs %.6f s",
                    sample[self.filename_key], time.time() - start)
        return sample

    def _verify_area_code(self, area_code: str):
        """判断地域编码的6位数是否有效"""
        return area_code in self.area_code_enum

    def _verify_verification_code(self, id_number: str):
        """身份证号码校验码正确性校验"""
        verify_num = id_number[-1]
        # 将身份证号码前17位数分别乘以不同的系数，即self.id_coefficient，再将相乘结果相加
        id_sum = sum([int(num) * coe for num, coe in zip(id_number[:-1], self.id_coefficient)])
        # 判断相加总和除以11的余数是否等于身份证号码最后一位
        return verify_num.upper() == self.id_verification[id_sum % 11].upper()

    def _verify_id_number(self, id_number: str):
        """验证身份证号码有效性主函数"""
        return self._verify_verification_code(id_number) and \
            self._verify_birthday_code(id_number[6:14]) and \
            self._verify_area_code(id_number[:6])

    def _verify_similar_id_number(self, id_number: str):
        """用于宽松匹配类似身份证的字符串，不进行严格有效性验证。"""
        if len(id_number) != 18:
            return False
        if not id_number[:17].isdigit():
            return False
        last_char = id_number[-1].upper()
        return last_char in set('0123456789X')

    def _id_number_filter(self, input_data: str):
        """身份证号码匿名化"""
        input_data = ''.join(['【', input_data, '】'])
        # 抽取符合身份证正则匹配的字符串
        id_nums = [item.group(1) for item in self.id_number_re_compile.finditer(input_data)]
        # 判断抽取的字符串是不是真实的身份证号码
        for id_num in id_nums:
            if self._verify_id_number(id_num) or self._verify_similar_id_number(id_num):
                # 替换有效身份证号码为<id>
                id_num_pattern = r"(?<=[^0-9]){}(?=[^0-9xX])".format(id_num)
                input_data = re.compile(id_num_pattern).sub("<id>", input_data)
        return input_data[1:-1]
