# -- encoding: utf-8 --

"""
Description:
Create: 2025/01/16
"""
import re
import time

from loguru import logger

from datamate.common.utils import bytes_transform
from datamate.core.base_op import Mapper


class ImgTypeUnify(Mapper):
    def __init__(self, *args, **kwargs):
        super(ImgTypeUnify, self).__init__(*args, **kwargs)
        """勾选图片编码格式统一，未输入参数时，默认设置为jpg格式"""
        self._setting_type = kwargs.get("imgType", "jpg")

    def execute(self, sample):
        start = time.time()
        self.read_file_first(sample)
        file_name = sample[self.filename_key]
        origin_file_type = sample[self.filetype_key]
        if origin_file_type == self._setting_type:
            # 原文件格式与目标文件编码格式一致，无需处理
            return sample
        file_path = sample[self.filepath_key]
        # 读取图片
        img_bytes = sample[self.data_key]
        if img_bytes:
            origin_data = bytes_transform.bytes_to_numpy(img_bytes)
            # 按指定编码格式转字节
            sample[self.data_key] = bytes_transform.numpy_to_bytes(origin_data, "." + self._setting_type)
            # 修改meta数据
            sample[self.filetype_key] = self._setting_type
            sample[self.filename_key] = re.sub(self._setting_type + "$", self._setting_type, file_name)
            sample[self.filepath_key] = re.sub(self._setting_type + "$", self._setting_type, file_path)
            logger.info(f"fileName: {file_name}, method: ImgTypeUnify costs {time.time() - start:6f} s")
        return sample
