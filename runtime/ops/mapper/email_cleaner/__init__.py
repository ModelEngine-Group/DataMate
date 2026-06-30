# -*- coding: utf-8 -*-

from datamate.core.base_op import OPERATORS

OPERATORS.register_module(module_name='EmailNumberCleaner',
                          module_path="ops.mapper.email_cleaner.process")
