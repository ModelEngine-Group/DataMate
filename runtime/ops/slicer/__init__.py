# -*- coding: utf-8 -*-

import sys
from pathlib import Path
from datamate.common.utils.custom_importer import CustomImporter


def _configure_importer():
    base_path = Path(__file__).resolve().parent
    sys.meta_path.append(CustomImporter(base_path))


_configure_importer()


def _import_operators():
    from . import slide_simple_slicer
    from . import slide_annotation_slicer
    from . import segmentation


_import_operators()
