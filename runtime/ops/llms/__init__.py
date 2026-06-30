# -*- coding: utf-8 -*-

"""
since:  
"""

import sys
from pathlib import Path
from datamate.common.utils.custom_importer import CustomImporter


def _configure_importer():
    base_path = Path(__file__).resolve().parent
    sys.meta_path.append(CustomImporter(base_path))


_configure_importer()


def _import_operators():
    from . import qa_condition_evaluator
    from . import text_quality_evaluation


_import_operators()
