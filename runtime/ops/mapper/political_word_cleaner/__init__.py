# -*- coding: utf-8 -*-

from datamate.core.base_op import OPERATORS

OPERATORS.register_module(module_name='PoliticalWordCleaner',
                          module_path="ops.mapper.political_word_cleaner.process")
