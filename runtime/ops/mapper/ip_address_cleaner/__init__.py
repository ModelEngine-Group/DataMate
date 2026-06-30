# -*- coding: utf-8 -*-

from datamate.core.base_op import OPERATORS

OPERATORS.register_module(module_name='AnonymizedIpAddress',
                          module_path="ops.mapper.ip_address_cleaner.process")
