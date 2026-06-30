# -*- coding: utf-8 -*-

from datamate.core.base_op import OPERATORS

OPERATORS.register_module(module_name='SexualAndViolentWordCleaner',
                          module_path="ops.mapper.sexual_and_violent_word_cleaner.process")
