#!/user/bin/python
# -*- coding: utf-8 -*-

"""
Description: MinerU PDF文本抽取
Create: 2025/10/29 17:24
"""
import asyncio
import os
import shutil
import time
from typing import Dict, Any

from datamate.core.base_op import Mapper
from loguru import logger
from mineru.cli.common import aio_do_parse, read_fn
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
        if not filename.lower().endswith((".png", ".jpeg", ".jpg", ".webp", ".gif", ".pdf")):
            return sample
        try:
            sample[self.text_key] = asyncio.run(self.async_process_file(sample))
            logger.info(
                f"fileName: {filename}, method: MineruFormatter costs {(time.time() - start):6f} s")
        except Exception as e:
            logger.exception(f"fileName: {filename}, method: MineruFormatter causes error: {e}")
            raise
        return sample

    async def async_process_file(self, sample):
        filename = sample[self.filename_key]
        filename_without_ext = os.path.splitext(filename)[0]
        filepath = sample[self.filepath_key]
        parse_dir = os.path.join(self.output_dir, filename_without_ext, "vlm")
        pdf_bytes = read_fn(filepath)
        total_page = len(PdfReader(filepath).pages)
        content = ""
        for page in range(0, total_page, 10):
            logger.info(f"fileName: {filename}, total_page: {total_page}, page: {page}.")
            await aio_do_parse(
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
        return content
