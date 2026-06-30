# -*- coding: utf-8 -*-

from datamate.core.base_op import OPERATORS

OPERATORS.register_module(module_name='DuplicateSentencesFilter',
                          module_path="ops.mapper.remove_duplicate_sentences.process")
