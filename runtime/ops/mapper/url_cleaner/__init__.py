# -*- coding: utf-8 -*-

from datamate.core.base_op import OPERATORS

OPERATORS.register_module(module_name='AnonymizedUrlCleaner',
                          module_path="ops.mapper.url_cleaner.process")
