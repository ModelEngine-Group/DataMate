# -*- coding: utf-8 -*-

from datamate.core.base_op import OPERATORS
from .process import AudioEmotionRecognize

OPERATORS.register_module(module_name='AudioEmotionRecognize',
                          module_cls=AudioEmotionRecognize)
