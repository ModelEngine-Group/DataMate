#!/user/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 邮件地址匿名化
Create: 2025/01/15
"""
import logging as logger
import re
import time
from typing import Dict, Any

from email_validator import validate_email, EmailNotValidError


from data_platform.core.base_op import Mapper


class EmailNumberCleaner(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.front_email_pattern = r'(?<=[^0-9a-zA-Z\!\#\$\%\&\'\*\+\-\/\=\?\^\_\`\{\|\}\~\-])'
        self.back_email_pattern = r'(?=[^0-9a-zA-Z\!\#\$\%\&\'\*\+\-\/\=\?\^\_\`\{\|\}\~\-])'
        self.email_pattern = r'([a-zA-Z\d.\-+_]+\s?@\s?[a-zA-Z\d.\-+_]+\.[a-zA-Z0-9]{2,6})'

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        sample[self.text_key] = self._email_number_filter(sample[self.text_key])
        logger.info("fileName: %s, method: EmailCleaner costs %.6f s" % (
            sample[self.filename_key], time.time() - start
        ))
        return sample

    def _email_number_filter(self, input_data: str):
        """ 邮箱匿名化"""
        mixed_data = ''.join(['龥', input_data, '龥'])
        paired_emails = re.compile(self.front_email_pattern + self.email_pattern + self.back_email_pattern).findall(
            mixed_data)
        if paired_emails:
            for email in paired_emails:
                try:
                    # 验证电子邮件地址
                    validate_email(email, check_deliverability=False)
                    mixed_data = re.compile(self.front_email_pattern + re.escape(email) + self.back_email_pattern).sub(
                        "<email>", mixed_data, count=1)
                except EmailNotValidError as err:
                    # 日志打印该电子邮件地址无效（不显示具体电子邮件地址）
                    logger.info("email is abnormal email form: %s", err)
        return mixed_data[1:-1]
