#!/user/bin/python
# -*- coding: utf-8 -*-

"""
Description: MinerU PDF文本抽取（Pipeline模式）
Create: 2025/10/29 17:24
"""

import glob
import os
import shutil
import time
import uuid
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, List, Tuple

import httpx
from pypdf import PdfReader, PdfWriter

from datamate.core.base_op import Mapper, FileExporter
from datamate.sql_manager.persistence_atction import TaskInfoPersistence
from loguru import logger


class MineruFormatter(Mapper):
    """基于MinerU Pipeline API，抽取PDF中的文本"""

    def __init__(self, *args, **kwargs):
        super(MineruFormatter, self).__init__(*args, **kwargs)
        self.server_url = kwargs.get("mineruApi", "http://datamate-mineru:8000")
        self.max_retries = 3
        self.target_type = kwargs.get("exportType", "md")

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()
        filename = sample[self.filename_key]
        if not filename.lower().endswith(
            (".png", ".jpeg", ".jpg", ".webp", ".gif", ".pdf")
        ):
            return sample
        try:
            sample[self.text_key] = self.process_file(sample)
            sample[self.target_type_key] = self.target_type
            logger.info(
                f"fileName: {filename}, method: MineruFormatter costs {(time.time() - start):6f} s"
            )
        except Exception as e:
            logger.exception(
                f"fileName: {filename}, method: MineruFormatter causes error: {e}"
            )
            raise
        return sample

    def _split_pdf_pages(
        self, filepath: str, filename: str
    ) -> list[tuple[str, tuple[str, BytesIO]]] | list[tuple[str, BytesIO]]:
        """将多页PDF拆分为单页，返回 [(filename, BytesIO), ...] 列表"""
        reader = PdfReader(filepath)
        num_pages = len(reader.pages)

        if num_pages <= 1:
            with open(filepath, "rb") as f:
                return [("files", (filename, BytesIO(f.read())))]

        base_name, ext = os.path.splitext(filename)
        pages: List[Tuple[str, Tuple[str, BytesIO]]] = []
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            buf = BytesIO()
            writer.write(buf)
            buf.seek(0)
            page_filename = f"{base_name}_page{i + 1}{ext}"
            pages.append(("files", (page_filename, buf)))

        logger.info(f"Split PDF {filename} into {len(pages)} pages")
        return pages

    def process_file(self, sample):
        filepath = sample[self.filepath_key]
        filename = sample[self.filename_key]

        if filename.lower().endswith(".pdf"):
            file_entries = self._split_pdf_pages(filepath, filename)
        else:
            with open(filepath, "rb") as f:
                file_entries = [("files", (filename, BytesIO(f.read())))]

        for attempt in range(self.max_retries):
            try:
                resp = httpx.post(
                    f"{self.server_url}/file_parse",
                    files=file_entries,
                    data={"return_md": "true", "backend": "pipeline"},
                    timeout=300,
                )
                resp.raise_for_status()
                break
            except Exception as e:
                logger.warning(
                    f"Extract {filename} failed (attempt {attempt + 1}/{self.max_retries}). "
                    f"Error: {e}. Retrying in 5s..."
                )
                if attempt < self.max_retries - 1:
                    time.sleep(5)
                else:
                    logger.error(
                        f"mineru-api call failed after {self.max_retries} attempts."
                    )
                    raise

        result = resp.json()
        content = result.get("markdown", "")
        output_dir = result.get("output_dir", "")
        if output_dir:
            self.save_images(
                output_dir,
                sample["dataset_id"],
                os.path.abspath(sample[self.export_path_key]) + "/images",
            )

        return content

    def save_images(self, parse_dir, dataset_id, export_path):
        images_dir = os.path.join(parse_dir, "images")
        if not os.path.isdir(images_dir):
            return

        Path(export_path).mkdir(parents=True, exist_ok=True)
        image_paths = glob.glob(os.path.join(glob.escape(images_dir), "*.jpg"))
        for image_path in image_paths:
            shutil.copy(image_path, export_path)
            image = Path(image_path)
            image_name = image.name
            image_sample = {
                self.filename_key: image_name,
                self.filetype_key: "jpg",
                self.filesize_key: image.stat().st_size,
                "dataset_id": dataset_id,
                self.filepath_key: export_path + "/" + image_name,
            }
            TaskInfoPersistence().update_file_result(image_sample, str(uuid.uuid4()))
