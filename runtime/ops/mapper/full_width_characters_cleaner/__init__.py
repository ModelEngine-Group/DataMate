# -*- coding: utf-8 -*-

from datamate.core.base_op import OPERATORS

OPERATORS.register_module(module_name='FullWidthCharacterCleaner',
                          module_path="ops.mapper.full_width_characters_cleaner.process")
