# -- encoding: utf-8 --

import gc
import os
from pathlib import Path


class BaseModel:

    def __init__(self, *args, **kwargs):
        models_path = os.getenv("MODELS_PATH", "/home/models")
        model_dir = str(Path(models_path, 'PP-LCNet_x1_0_doc_ori_infer'))

        from paddleocr import DocImgOrientationClassification
        self.infer = DocImgOrientationClassification(model_dir=model_dir)

    def __del__(self):
        del self.infer
        gc.collect()
