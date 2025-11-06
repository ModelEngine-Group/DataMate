# -*- coding: utf-8 -*-

import sys
from pathlib import Path
from datamate.core.base_op import OPERATORS
from datamate.common.utils.custom_importer import CustomImporter


def _configure_importer():
    base_path = Path(__file__).resolve().parent
    sys.meta_path.append(CustomImporter(base_path))


_configure_importer()


def _import_operators():
    from . import text_formatter
    from . import word_formatter
    from . import img_formatter
    from . import file_exporter
    from . import slide_formatter
    from . import unstructured_formatter
    from . import mineru_formatter


_import_operators()
