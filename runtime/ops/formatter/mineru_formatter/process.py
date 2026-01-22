#!/user/bin/python
# -*- coding: utf-8 -*-

"""
Description: MinerU PDF文本抽取
Create: 2025/10/29 17:24
"""
import asyncio
import glob
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Dict, Any

from datamate.core.base_op import Mapper, FileExporter
from datamate.sql_manager.persistence_atction import TaskInfoPersistence
from loguru import logger
from mineru.cli.common import aio_do_parse, read_fn
from mineru.cli.fast_api import get_infer_result
from pypdf import PdfReader


class MineruFormatter(Mapper):
    """基于外部API，抽取PDF中的文本"""

    def __init__(self, *args, **kwargs):
        super(MineruFormatter, self).__init__(*args, **kwargs)
        self.server_url = kwargs.get("mineruApi", "http://datamate-mineru:8000")
        self.backend = "vlm-http-client"
        self.output_dir = "/dataset/outputs"
        self.max_retries = 3
        self.target_type = kwargs.get("exportType", "md")

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        filename = sample[self.filename_key]
        if not filename.lower().endswith((".png", ".jpeg", ".jpg", ".webp", ".gif", ".pdf")):
            return sample
        try:
            sample[self.text_key] = asyncio.run(self.async_process_file(sample))
            sample[self.target_type_key] = self.target_type
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
            for attempt in range(self.max_retries):
                try:
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
                    break  # 成功则跳出重试循环
                except Exception as e:
                    logger.warning(
                        f"Extract {filename} [{page}-{page + 9}] failed (attempt {attempt + 1}/{self.max_retries}). "
                        f"Error: {e}. Retrying in 5s..."
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(5)
                    else:
                        logger.error(f"aio_do_parse failed after {self.max_retries} attempts.")
                        raise  # 耗尽次数后抛出异常，交给上层 execute 处理
            if os.path.exists(parse_dir):
                content += get_infer_result(".md", filename_without_ext, parse_dir)
                self.save_images(parse_dir, sample["dataset_id"], os.path.abspath(sample[self.export_path_key]) + "/images")
                shutil.rmtree(parse_dir)
        return content

    def save_images(self, parse_dir, dataset_id, export_path):
        Path(export_path).mkdir(parents=True, exist_ok=True)

        images_dir = os.path.join(parse_dir, "images")
        image_paths = glob.glob(os.path.join(glob.escape(images_dir), "*.jpg"))
        for image_path in image_paths:
            shutil.copy(image_path, export_path)
            image_sample = {}
            image = Path(image_path)
            image_name = image.name
            image_sample[self.filename_key] = image_name
            image_sample[self.filetype_key] = "jpg"
            image_sample[self.filesize_key] = image.stat().st_size
            image_sample["dataset_id"] = dataset_id
            image_sample[self.filepath_key] = export_path + "/" + image_name
            TaskInfoPersistence().update_file_result(image_sample, str(uuid.uuid4()))