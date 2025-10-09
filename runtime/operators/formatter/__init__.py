# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.

import sys
from pathlib import Path
from data_platform.core.base_op import OPERATORS
from data_platform.common.utils.custom_importer import CustomImporter


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


_import_operators()
