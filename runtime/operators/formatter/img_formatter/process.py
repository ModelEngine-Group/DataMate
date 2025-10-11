# # -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
#
# Description:
# Create: 2024/1/30 15:24
# """
import logging as logger
import time
from typing import Dict, Any

import cv2
import numpy as np

from data_platform.common.utils import numpy_to_bytes
from data_platform.core.base_op import Mapper


class ImgFormatter(Mapper):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        file_name = sample[self.filename_key]
        file_type = "." + sample[self.filetype_key]
        file_path = sample[self.filepath_key]
        img_data = _img_extract(file_path)
        sample[self.data_key] = numpy_to_bytes(img_data, file_type)
        logger.info("fileName: %s, method: ImgExtract costs %.6f s", file_name, time.time() - start)
        return sample


def _img_extract(file_path):
    return cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), -1)
