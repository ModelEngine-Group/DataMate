# -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
import gc
import os
from pathlib import Path

from argparse import Namespace


class BaseModel:

    def __init__(self, model_type='vertical'):
        models_path = os.getenv("MODELS_PATH", "/home/models")
        self.resources_path = str(Path(models_path, 'img_direction_correct', 'resources'))
        args = Namespace()
        args.cls_image_shape = '3, 224, 224'
        args.cls_batch_num = 6
        args.cls_thresh = 0.9
        args.use_onnx = False
        args.use_gpu = False
        args.use_npu = False
        args.use_xpu = False
        args.enable_mkldnn = False
        if model_type == 'vertical':
            args.cls_model_dir = str(Path(self.resources_path, 'vertical_model'))
            self.model_name = 'standard model to detect image 0 or 90 rotated'
            args.label_list = ['0', '90']
        else:
            args.cls_model_dir = str(Path(self.resources_path, 'standard_model'))
            self.model_name = 'standard model to detect image 0 or 180 rotated'
            args.label_list = ['0', '180']

        from paddleocr.tools.infer.predict_cls import TextClassifier
        self.infer = TextClassifier(args)

    def __del__(self):
        del self.infer
        gc.collect()
