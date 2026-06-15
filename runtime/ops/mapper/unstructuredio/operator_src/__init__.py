# -*- coding: utf-8 -*-

try:
    from datamate.core.base_op import OPERATORS
except ImportError:
    OPERATORS = None

if OPERATORS is not None:
    OPERATORS.register_module(
        module_name="UnstructuredIOMapper",
        module_path="ops.user.unstructuredio.process",
    )
