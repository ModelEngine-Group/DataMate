# # -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
#
# Description:
# Create: 2024/1/30 15:24
# """
import logging as logger
import os
import subprocess
import time
from typing import Dict, Any

from data_platform.common.utils import check_valid_path
from data_platform.core.base_op import Mapper


class WordFormatter(Mapper):
    SEPERATOR = ' | '

    def __init__(self, *args, **kwargs):
        super(WordFormatter, self).__init__(*args, **kwargs)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        file_name = sample[self.filename_key]
        file_path = sample[self.filepath_key]
        file_type = sample[self.filetype_key]
        txt_content = self.word2html(file_path, file_type)
        sample[self.text_key] = txt_content
        logger.info("fileName: %s, method: WordFormatter costs %.6f s", file_name, time.time() - start)
        return sample

    @staticmethod
    def word2html(file_path, file_type):
        check_valid_path(file_path)
        file_dir = file_path.rsplit('/', 1)[0]
        file_name = file_path.rsplit('/', 1)[1]
        html_file_path = os.path.join(file_dir, f"{file_name}.txt")

        current_file_path = os.path.dirname(os.path.abspath(__file__))
        try:
            process = subprocess.Popen(
                ['java', '-jar', f'{current_file_path}/../../../java_operator/WordFormatter-1.0.jar', file_path,
                 html_file_path, file_type], shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            stdout, stderr = process.communicate(timeout=24 * 60 * 60)
            if process.returncode == 0:
                logger.info("Convert %s successfully to DOCX", file_path)
            else:
                logger.info(f"Convert {file_path} failed, error: {stderr.strip().decode('utf-8')}.")
                raise RuntimeError()
        except subprocess.CalledProcessError as e:
            logger.error("Convert failed: %s, return code: %s", e, e.returncode)
        except FileNotFoundError:
            logger.error("LibreOffice command not found, please make sure it is available in PATH")
        except Exception as e:
            logger.error("An unexpected error occurred, convert failed: %s", e)

        try:
            with open(html_file_path, 'r', encoding='utf-8') as file:
                txt_content = file.read()
            os.remove(html_file_path)
            logger.info("Tmp docx file removed")
        except FileNotFoundError:
            logger.error("Tmp file %s does not exist", html_file_path)
        except PermissionError:
            logger.error("You are not allowed to delete tmp file %s", html_file_path)
        logger.info("Convert %s to html success", html_file_path)
        return txt_content
