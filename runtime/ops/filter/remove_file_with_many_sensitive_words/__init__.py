# -*- coding: utf-8 -*-

from datamate.core.base_op import OPERATORS

OPERATORS.register_module(module_name='FileWithManySensitiveWordsFilter',
                          module_path="ops.filter.remove_file_with_many_sensitive_words.process")
