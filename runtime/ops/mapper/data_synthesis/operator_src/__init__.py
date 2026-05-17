# -*- coding: utf-8 -*-

try:
    from datamate.core.base_op import OPERATORS
except Exception:  # pragma: no cover
    OPERATORS = None

if OPERATORS is not None:
    OPERATORS.register_module(
        module_name="DataSynthesisMapper",
        module_path="ops.user.data_synthesis.process",
    )
