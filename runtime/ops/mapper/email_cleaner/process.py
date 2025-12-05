#!/user/bin/python
# -*- coding: utf-8 -*-

"""
Description: 邮件地址匿名化
Create: 2025/01/15
"""
from loguru import logger
import re
import time
from typing import Dict, Any

from email_validator import validate_email, EmailNotValidError


from datamate.core.base_op import Mapper


class EmailNumberCleaner(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.front_email_pattern = r'(?<=[^0-9a-zA-Z\!\#\$\%\&\'\*\+\-\/\=\?\^\_\`\{\|\}\~\-])'
        self.back_email_pattern = r'(?=[^0-9a-zA-Z\!\#\$\%\&\'\*\+\-\/\=\?\^\_\`\{\|\}\~\-])'
        self.email_pattern = r'([a-zA-Z\d.\-+_]+\s?@\s?[a-zA-Z\d.\-+_]+\.[a-zA-Z0-9]{2,6})'

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        self.read_file_first(sample)
        sample[self.text_key] = self._email_number_filter(sample[self.text_key])
        logger.info(f"fileName: {sample[self.filename_key]}, method: EmailCleaner costs {time.time() - start:6f} s")
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
                    logger.error(f"email is abnormal email form: {err}")
        return mixed_data[1:-1]
