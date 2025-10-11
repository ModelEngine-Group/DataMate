# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.

import sys
from pathlib import Path
from data_platform.common.utils.custom_importer import CustomImporter


def _configure_importer():
    base_path = Path(__file__).resolve().parent
    sys.meta_path.append(CustomImporter(base_path))


_configure_importer()


def _import_operators():
    from . import file_with_high_repeat_phrase_rate_filter
    from . import file_with_high_repeat_word_rate_filter
    from . import file_with_high_special_char_rate_filter
    from . import remove_file_with_many_sensitive_words
    from . import remove_file_with_short_or_long_length
    from . import remove_duplicate_file
    from . import img_blurred_images_cleaner
    from . import img_duplicated_images_cleaner
    from . import img_similar_images_cleaner
    from . import img_advertisement_images_cleaner


_import_operators()
