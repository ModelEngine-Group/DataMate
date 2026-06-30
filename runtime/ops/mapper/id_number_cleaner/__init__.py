# -*- coding: utf-8 -*-

from datamate.core.base_op import OPERATORS

OPERATORS.register_module(module_name='AnonymizedIdNumber',
                          module_path="ops.mapper.id_number_cleaner.process")
