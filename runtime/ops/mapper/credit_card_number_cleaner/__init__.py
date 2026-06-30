# -*- coding: utf-8 -*-

from datamate.core.base_op import OPERATORS

OPERATORS.register_module(module_name='AnonymizedCreditCardNumber',
                          module_path="ops.mapper.credit_card_number_cleaner.process")
