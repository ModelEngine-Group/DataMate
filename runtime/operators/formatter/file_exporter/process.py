#!/user/bin/python
# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: Json文本抽取
Create: 2024/06/06 15:43
"""
import time
import os
import uuid
from typing import Tuple, Dict, Any
from loguru import logger

from data_platform.core.constant import Fields
from data_platform.core.base_op import Mapper
from data_platform.common.utils import check_valid_path


class FileExporter(Mapper):
    """把输入的json文件流抽取为txt"""

    def __init__(self, *args, **kwargs):
        super(FileExporter, self).__init__(*args, **kwargs)
        self.last_ops = True
        self.text_support_ext = kwargs.get("text_support_ext", ['txt', 'html', 'md', 'markdown',
                                                                'xml', 'json', 'doc', 'docx', 'pdf'])
        self.data_support_ext = kwargs.get("data_support_ext", ['jpg', 'jpeg', 'png', 'bmp'])
        self.medical_support_ext = kwargs.get("medical_support_ext", ['svs', 'tif', 'tiff'])

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        file_name = sample[self.filename_key]
        file_type = sample[self.filetype_key]

        try:
            start = time.time()
            if file_type in self.text_support_ext:
                sample, save_path = self.get_textfile_handler(sample)
            elif file_type in self.data_support_ext:
                sample, save_path = self.get_datafile_handler(sample)
            elif file_type in self.medical_support_ext:
                sample, save_path = self.get_medicalfile_handler(sample)
            else:
                raise TypeError(f"{file_type} is unsupported! please check support_ext in FileExporter Ops")

            if sample[self.text_key] == '' and sample[self.data_key] == b'':
                sample[self.filesize_key] = "0B"
                return sample

            if save_path:
                self.save_file(sample, save_path)
                sample[self.text_key] = ''
                sample[self.data_key] = b''
                sample[Fields.result] = True

                file_type = save_path.split('.')[-1]
                sample[self.filetype_key] = file_type

                base_name, _ = os.path.splitext(file_name)
                new_file_name = base_name + '.' + file_type
                sample[self.filename_key] = new_file_name

                base_name, _ = os.path.splitext(save_path)
                sample[self.filepath_key] = base_name
                file_size = os.path.getsize(base_name)
                sample[self.filesize_key] = f"{file_size}B"

            logger.info(f"origin file named {file_name} has been save to {save_path}")
            logger.info(f"fileName: {sample[self.filename_key]}, "
                        f"method: FileExporter costs {time.time() - start:.6f} s")
        except UnicodeDecodeError as err:
            logger.error(f"fileName: {sample[self.filename_key]}, "
                         f"method: FileExporter causes decode error: {err}")
            raise
        return sample

    def get_save_path(self, sample: Dict[str, Any], target_type) -> str:
        export_path = os.path.abspath(sample[self.export_path_key])
        uuid_file = self._get_uuid()
        new_file_name = uuid_file + '.' + target_type

        if not check_valid_path(export_path):
            os.makedirs(export_path, exist_ok=True)
        res = os.path.join(export_path, new_file_name)
        return res

    def get_textfile_handler(self, sample: Dict[str, Any]) -> Tuple[Dict, str]:
        target_type = sample.get("target_type", None)

        # target_type存在则保存为扫描件, docx格式
        if target_type:
            sample = self._get_from_data(sample)
            save_path = self.get_save_path(sample, target_type)
        # 不存在则保存为txt文件，正常文本清洗
        else:
            sample = self._get_from_text(sample)
            save_path = self.get_save_path(sample, 'txt')
        return sample, save_path

    def get_datafile_handler(self, sample: Dict[str, Any]) -> Tuple[Dict, str]:
        target_type = sample.get("target_type", None)

        # target_type存在, 图转文保存为target_type，markdown格式
        if target_type:
            sample = self._get_from_text(sample)
            save_path = self.get_save_path(sample, target_type)
        # 不存在则保存为原本图片文件格式，正常图片清洗
        else:
            sample = self._get_from_data(sample)
            save_path = self.get_save_path(sample, sample[self.filetype_key])
        return sample, save_path

    def get_medicalfile_handler(self, sample: Dict[str, Any]) -> Tuple[Dict, str]:
        target_type = 'png'

        sample = self._get_from_data(sample)
        save_path = self.get_save_path(sample, target_type)

        return sample, save_path

    def save_file(self, sample, save_path):
        file_name, _ = os.path.splitext(save_path)
        # 以二进制格式保存文件
        file_sample = sample[self.text_key].encode('utf-8') if sample[self.text_key] else sample[self.data_key]
        with open(file_name, 'wb') as f:
            f.write(file_sample)
            # 获取父目录路径

        parent_dir = os.path.dirname(file_name)
        os.chmod(parent_dir, 0o770)
        os.chmod(file_name, 0o640)

    def _get_from_data(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        sample[self.data_key] = bytes(sample[self.data_key])
        sample[self.text_key] = ''
        return sample

    def _get_from_text(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        sample[self.data_key] = b''
        sample[self.text_key] = str(sample[self.text_key])
        return sample

    def _get_uuid(self):
        res = str(uuid.uuid4())
        return res
