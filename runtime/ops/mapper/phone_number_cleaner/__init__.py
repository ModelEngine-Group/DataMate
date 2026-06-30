# -*- coding: utf-8 -*-

from datamate.core.base_op import OPERATORS

OPERATORS.register_module(module_name='AnonymizedPhoneNumber',
                          module_path="ops.mapper.phone_number_cleaner.process")
