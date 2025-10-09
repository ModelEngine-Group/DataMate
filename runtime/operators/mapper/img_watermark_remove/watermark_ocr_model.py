# -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
import gc
import os
from pathlib import Path


class WatermarkOcrModel:

    def __init__(self, *args, **kwargs):
        models_path = os.getenv("MODELS_PATH", "/home/models")
        self.resources_path = str(Path(models_path, 'img_watermark_remove', 'resources'))
        self.det_model_dir = str(Path(self.resources_path, 'ch_PP-OCRv4_det_infer'))
        self.rec_model_dir = str(Path(self.resources_path, 'ch_PP-OCRv4_rec_infer'))
        self.cls_model_dir = str(Path(self.resources_path, 'ch_ppocr_mobild_v2_cls_infer'))

        from paddleocr import PaddleOCR
        self.ocr_model = PaddleOCR(det_model_dir=self.det_model_dir, cls_model_dir=self.cls_model_dir,
                                   rec_model_dir=self.rec_model_dir,
                                   use_angle_cls=True,
                                   lang='ch')

    def __del__(self):
        del self.ocr_model
        gc.collect()
