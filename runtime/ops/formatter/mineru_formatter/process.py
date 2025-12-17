#!/user/bin/python
# -*- coding: utf-8 -*-

"""
Description: MinerU PDF文本抽取
Create: 2025/10/29 17:24
"""
import os
import shutil
import time
from typing import Dict, Any

from datamate.common.utils.rest_client import http_request
from datamate.core.base_op import Mapper
from loguru import logger
from mineru.cli.common import do_parse, read_fn
from mineru.cli.fast_api import get_infer_result
from pypdf import PdfReader


class MineruFormatter(Mapper):
    """基于外部API，抽取PDF中的文本"""

    def __init__(self, *args, **kwargs):
        super(MineruFormatter, self).__init__(*args, **kwargs)
        self.server_url = "http://datamate-mineru:8000"
        self.backend = "vlm-http-client"
        self.output_dir = "/dataset/outputs"

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        filename = sample[self.filename_key]
        filename_without_ext = os.path.splitext(filename)[0]
        if not filename.lower().endswith((".png", ".jpeg", ".jpg", ".webp", ".gif", ".pdf")):
            return sample
        try:
            filepath = sample[self.filepath_key]
            parse_dir = os.path.join(self.output_dir, filename_without_ext, "vlm")
            pdf_bytes = read_fn(filepath)
            total_page = len(PdfReader(filepath).pages)
            content = ""
            for page in range(0, total_page, 10):
                do_parse(
                    output_dir=self.output_dir,
                    pdf_file_names=[filename_without_ext],
                    pdf_bytes_list=[pdf_bytes],
                    p_lang_list=["ch"],
                    backend=self.backend,
                    server_url=self.server_url,
                    start_page_id=page,
                    end_page_id=min(page + 9, total_page - 1),
                )
                if os.path.exists(parse_dir):
                    content += get_infer_result(".md", filename_without_ext, parse_dir)
                    shutil.rmtree(parse_dir)
            sample[self.text_key] = content
            logger.info(
                f"fileName: {filename}, method: MineruFormatter costs {(time.time() - start):6f} s")
        except Exception as e:
            logger.exception(f"fileName: {filename}, method: MineruFormatter causes error: {e}")
            raise
        return sample
