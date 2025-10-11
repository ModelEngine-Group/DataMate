#!/user/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 电话号码匿名化
Create: 2024/12/26 15:43
"""
import logging as logger
import re
import time
from typing import Dict, Any

from data_platform.core.base_op import Mapper


class AnonymizedPhoneNumber(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.phone_re_compile = self.get_phone_re_compile()

    @staticmethod
    def get_phone_re_compile():
        """按照格式粗略匹配电话号码，支持以下格式电话号码
        前缀：（0086）、（86）、(0086)、(86) 、无
        电话号码：第一位1，第二位3-9，后续数字可以为0-9，数字按照3-4-4进行间隔，间隔符为空格、-、无
        固定电话号码：0AX-CXXX-XXXX、0BXX-CXXX-XXXX、0BXX-CXX-XXXX A为1-2、B为3-9、C为2-8、X为0-9
        约束：电话号码前后皆为非数字
        """
        number_prefix = r'([\(（]?\+?(00)?86[)\）]?[- ]?)?'
        cellphone_pattern = r"1[3-9]\d[- ]?\d{4}[- ]?\d{4}"
        landline_pattern = (r'[(（]?(0?[12]\d)[)）]?[ -]?[2-8]\d{3}[ -]?\d{4}'
                            r'|[(（]?(0?[3-9]\d{2})[)）]?[ -]?[2-8]\d{2}\d?[ -]?\d{4}')
        phone_numbers_pattern = rf'(?<=[^\d]){number_prefix}({cellphone_pattern}|{landline_pattern})(?=[^\d])'
        phone_re_compile = re.compile(phone_numbers_pattern)
        return phone_re_compile

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        sample[self.text_key] = self._phone_number_filter(sample[self.text_key])
        logger.info("fileName: %s, method: PhoneNumberCleaner costs %.6f s",
                    sample[self.filename_key], time.time() - start)
        return sample

    def _phone_number_filter(self, input_data: str):
        """ 电话号码匿名化"""
        # 正则匹配：电话号码前需匹配不是数字的字符串
        # 为避免处于文章开头和结尾的电话号码不可被识别，需要在输入字符串的前后手动加上字符串
        input_data = ''.join(['【', input_data, '】'])
        input_data = self.phone_re_compile.sub("<tel>", input_data)
        return input_data[1:-1]
