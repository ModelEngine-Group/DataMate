# -- encoding: utf-8 --

"""
Description: 医疗图片解析载入
Create: 2025/02/08 11:00
"""

import time
from typing import Dict, Any

from loguru import logger

from datamate.core.base_op import Mapper


class SlideFormatter(Mapper):

    def __init__(self, *args, **kwargs):
        super(SlideFormatter, self).__init__(*args, **kwargs)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        '''
        Read medical image and corresponding mask file, each as Image type in COntent value. Return Content.
        '''
        start = time.time()
        file_type = sample[self.filetype_key]
        types_openslide = ['svs', 'tif', 'dcm', 'vms', 'vmu',
                           'ndpi', 'scn', 'mrxs', 'tiff', 'svslide',
                           'bif', 'czi', 'sdpc']
        if file_type not in types_openslide:
            raise TypeError(f"Format not supported: {file_type}. Supported formats are: {', '.join(types_openslide)}.")

        file_name = sample[self.filename_key]
        logger.info(f"fileName: {file_name}, method: SlideFormatter costs {(time.time() - start):6f} s")
        # Not really loading the slide, instead, use path as lazy loading.
        return sample
