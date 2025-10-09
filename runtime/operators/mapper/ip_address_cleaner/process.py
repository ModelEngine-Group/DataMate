#!/user/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 身份证号码匿名化插件
Create: 2024/12/26 15:43
"""
import ipaddress
import logging as logger
import re
import time
from typing import Dict, Any

from data_platform.core.base_op import Mapper


class AnonymizedIpAddress(Mapper):
    def __init__(self, *args, **kwargs):
        # IP地址校验
        # X.X.X.X与四级目录格式相同，避免误清洗，该格式的IP地址必须匹配 IP/IP地址等字样
        super().__init__(*args, **kwargs)
        self.ipv4_1_and_prefix_pattern = r'ip(地址| address|v4)?( |:|：)*(?<![\.\d])'
        # X.X.X.X
        self.ipv4_pattern = r'(?<![\.\d])\d\.\d\.\d\.\d(?![\.\d])'
        self.ipv4_re_compile = re.compile(r"(?<![\d.])(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?![.\d])")
        self.ipv6_re_compile = re.compile(r"(?<![0-9a-fA-F:])(([0-9a-fA-F]{0,4}:)+[0-9a-fA-F]{0,4})(?![0-9a-fA-F:])")

    @staticmethod
    def verify_ip_address(ip):
        """验证字符串是否为合法ip地址"""
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            return False
        return True

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        sample[self.text_key] = self._ip_address_filter(sample[self.text_key])
        logger.info("fileName: %s, method: IPAddressCleaner costs %.6f s", sample[self.filename_key],
                    time.time() - start)
        return sample

    def filter_ipv4(self, ipv4, line):
        """ipv4地址匿名化"""
        if not self.verify_ip_address(ipv4):
            return line
        ipv4_format = ipv4.replace(".", "\\.")
        # 非单字节ip地址直接匿名化
        if not re.search(self.ipv4_pattern, "【" + ipv4 + "】"):
            line = re.compile(r"(?<![\d.])" + ipv4_format + r"(?![.\d])").sub("<ip>", line)
        elif re.search(self.ipv4_1_and_prefix_pattern + ipv4_format + r"(?![.\d])", line, re.IGNORECASE):
            # 单字节ip地址需搜索关键字眼，有关键字眼则段落中单字节ip地址匿名化
            line = re.compile(self.ipv4_pattern).sub("<ip>", line)
        return line

    def _ip_address_filter(self, input_data: str):
        """ IPv4、IPv6地址匿名化"""
        lines = input_data.split("\n")
        line_list = []
        for line in lines:
            # 为防止IP地址处于段落开头或结尾不能被匹配，需要在字符串首尾加占位符
            line = ''.join(['【', line, '】'])
            ipv4_groups = self.ipv4_re_compile.findall(line)
            for ipv4 in ipv4_groups:
                line = self.filter_ipv4(ipv4, line)
            ipv6_groups = self.ipv6_re_compile.findall(line)
            for group in ipv6_groups:
                ipv6 = group[0]
                if ipv6 and self.verify_ip_address(ipv6):
                    line = re.compile(r"(?<![0-9a-fA-F:])" + ipv6 + "(?![0-9a-fA-F:])").sub("<ip>", line)
            line_list.append(line[1:-1])
        text = "\n".join([line.strip() for line in line_list])
        return text
