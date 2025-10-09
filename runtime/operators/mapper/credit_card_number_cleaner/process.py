#!/user/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 信用卡号匿名化
Create: 2024/12/5 15:43
"""
import logging as logger
import re
import time
from typing import Dict, Any

from data_platform.core.base_op import Mapper


class AnonymizedCreditCardNumber(Mapper):
    def __init__(self, *args, **kwargs):
        super(AnonymizedCreditCardNumber, self).__init__(*args, **kwargs)
        self.re_compile = self._get_credit_card_re_compile()

    @staticmethod
    def _verify_credit_card_num(credit_card_num: str):
        """信用卡号码校验"""
        # 从右到左翻转
        digits = [int(x) for x in reversed(credit_card_num) if x.isdigit()]
        # 对偶数位数字翻倍 d*2
        even_digits = [d * 2 for d in digits[1::2]]
        # 如果对某个数字翻倍之后结果是一个两位数，将这两位数字加在一起
        even_digits = [d // 10 + d % 10 for d in even_digits]
        # 将上一步所有一位数相加
        even_sum = sum(even_digits)
        # 将卡号里从右到左奇数位上所有数字相加
        odd_sum = sum(digits[::2])
        # 将even_sum和odd_sum相加，能被10整数为合法，否则不合法
        if (odd_sum + even_sum) % 10 == 0:
            return True
        return False

    @staticmethod
    def _get_credit_card_re_compile():
        separator_symbol = r"([- ]?)"
        # American Express 以 34 或 37 开头的 15 位数号码 格式:NNNN-NNNNNN-NNNNN 或 NNNN NNNNNN NNNNN
        american_express = "3[47][0-9]{2}" + separator_symbol + "[0-9]{6}" + separator_symbol + "[0-9]{5}"
        # 中国银联 以 62 或 60 开头，是一个 16 位数号码。 格式:NNNN-NNNN-NNNN-NNNN 或 NNNN NNNN NNNN NNNN
        china_union_pay = r"(6[02]\d{2})" + r"(%s\d{%d}){%d}" % (separator_symbol, 4, 3)
        # Diner's Club 以 300–305、36、38 或 39、3095 开头, 14 位数号码  格式:NNNN-NNNNNN-NNNN 或 NNNN NNNNNN NNNN。
        diners_club = r"(30[0-5]\d|3[689]\d{2}|3095)" + separator_symbol + r"[0-9]{6}" + separator_symbol + r"[0-9]{4}"
        # Discover 以 6011、644–649 或 65 开头的 16 位数号码 格式:NNNN-NNNN-NNNN-NNNN 或 NNNN NNNN NNNN NNNN
        discover = r"(64[4-9]\d|65\d{2}|6011)" + r"(%s\d{%d}){%d}" % (separator_symbol, 4, 3)
        # JCB 以 3528 到 3589 开头的 16 位数字, 格式:NNNN-NNNN-NNNN-NNNN 或 NNNN NNNN NNNNNNNN
        jcb = r"(352[89]|35[3-8]\d)" + separator_symbol + r"[0-9]{4}" + (
                r"((%s\d{%d}){%d}" % (separator_symbol, 4, 2) + ")|" + separator_symbol + r"[0-9]{8}")
        # Mastercard 以 51–55 或 2221–2720 开头的 16 位数字 格式:NNNN-NNNN-NNNN-NNNN 或 NNNN NNNN NNNN NNNN
        master_card = r"(5[1-5]\d{2}|222[1-9]|22[3-9]\d|2[3-6]\d{2}|27[01]\d|2720)" + r"(%s\d{%d}){%d}" \
                      % (separator_symbol, 4, 3)
        # visa 以4开头 16 位数号码 格式:NNNN-NNNN-NNNN-NNNN 或 NNNN NNNN NNNN NNNN
        visa = r"4\d{3}" + r"(%s\d{%d}){%d}" % (separator_symbol, 4, 3)

        credit_card_pattern = r"(?<=[^\d])(%s|%s|%s|%s|%s|%s|%s)(?=[^\d])" % (
            american_express, china_union_pay, diners_club,
            discover, jcb, master_card, visa)
        credit_card_re_compile = re.compile(credit_card_pattern)
        return credit_card_re_compile

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        sample[self.text_key] = self._credit_card_number_filter(sample[self.text_key])
        logger.info("fileName: %s, method: CreditCardNumberCleaner costs %.6f s",
                    sample[self.filename_key], time.time() - start)
        return sample

    def _credit_card_number_filter(self, input_data: str):
        """提取信用卡号号码"""
        input_data = ''.join(['【', input_data, '】'])
        # 抽取符合信用卡正则匹配的字符串
        credit_card_nums = [item.group(1) for item in self.re_compile.finditer(input_data)]
        # 判断抽取的字符串是不是真实的信用卡号
        for credit_card_num in credit_card_nums:
            if self._verify_credit_card_num(credit_card_num):
                # 替换有效信用卡号号码为<credit_card_number>
                credit_card_num_pattern = r"(?<=[^\d]){}(?=[^\d])".format(credit_card_num)
                input_data = re.compile(credit_card_num_pattern).sub("<credit_card_number>", input_data)
        return input_data[1:-1]
