# -*- coding: utf-8 -*-

"""
Description:
    文档图像转换器 - 将Word文档转换为JPG图片
Create: 2025/01/28
"""

import glob
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, Any

import cv2
import numpy as np
from loguru import logger

from datamate.core.base_op import Mapper


class LoanReportWordToImageConverter(Mapper):
    """Word转图片转换器"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance_id = None
        self._output_dir = None
        self._dpi = int(kwargs.get("dpi", 300))
        self._keep_pdf = kwargs.get("keep_pdf", False)

    def _cv_imread(self, file_path: str):
        """读取含中文路径的图片"""
        return cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)

    def _check_poppler(self) -> bool:
        """检查poppler是否已安装"""
        try:
            from pdf2image import convert_from_path
            return True
        except ImportError:
            return False

    def _convert_word_to_pdf_com(self, word_path: str, output_dir: str):
        """使用COM接口将Word转换为PDF（Windows）"""
        try:
            # 创建临时目录
            # 转换为PDF
            subprocess.run([
                "libreoffice",
                f"-env:UserInstallation=file:///tmp/LibreOffice_Conversion_{self.instance_id}",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", output_dir,
                word_path
            ], check=True, capture_output=True)

            # 找到生成的PDF文件
            pdf_path = Path(output_dir) / f"{Path(word_path).stem}.pdf"
            time.sleep(0.5)

            if os.path.exists(pdf_path):
                logger.info(f"PDF生成成功: {Path(word_path).stem}.pdf")
                return pdf_path
            else:
                logger.error(f"PDF文件未生成: {pdf_path}")
                return None

        except Exception as e:
            logger.error(f"COM错误: {e}")
            return None

    def _convert_word_to_pdf(self, word_path: str, output_dir: str):
        """将Word文档转换为PDF（主函数）"""
        # 首先尝试使用COM接口
        result = self._convert_word_to_pdf_com(word_path, output_dir)
        return result

    def _convert_pdf_to_images_pymupdf(self, pdf_path: str, output_dir: str):
        """使用PyMuPDF将PDF转换为JPG图片"""
        try:
            from pdf2image import convert_from_path
            from PIL import Image

            # 转换PDF为图片列表，指定 poppler 路径
            images = convert_from_path(pdf_path, dpi=self._dpi)

            if len(images) == 1:
                # 单页，直接保存
                images[0].save(output_dir + "/images/" + Path(pdf_path).stem + ".jpg", 'JPEG')
            else:
                # 多页，保存第一页或合并
                images[0].save(output_dir + "/images/" + Path(pdf_path).stem + ".jpg", 'JPEG')

            return output_dir
        except Exception as e:
            logger.error(f"PDF转换错误: {e}")
            return None

    def _convert_pdf_to_images(self, pdf_path: str, output_dir: str):
        """将PDF转换为JPG图片（主函数）"""
        # 使用PyMuPDF作为首选方法（不需要poppler）
        return self._convert_pdf_to_images_pymupdf(pdf_path, output_dir)

    def _convert_single_document(self, word_file: str) -> list:
        """转换单个Word文档"""
        logger.info(f"处理文档: {os.path.basename(word_file)}")

        # Step 1: Word -> PDF
        pdf_path = self._convert_word_to_pdf(word_file, self._output_dir)
        if not pdf_path or not os.path.exists(pdf_path):
            logger.error(f"PDF转换失败: {word_file}")
            return []

        # Step 2: PDF -> JPG
        image_files = self._convert_pdf_to_images(pdf_path, self._output_dir)
        if not image_files:
            logger.error(f"图片转换失败: {pdf_path}")
            return []

        # 删除临时PDF
        if not self._keep_pdf:
            try:
                os.remove(pdf_path)
            except:
                pass

        return image_files

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """执行文档转换"""
        self._output_dir = sample['export_path']
        self.instance_id = sample['instance_id']

        # 获取输入目录
        input_dir = self._output_dir
        if not os.path.exists(input_dir):
            logger.error(f"输入目录不存在: {input_dir}")
            return sample

        os.mkdir(self._output_dir + "/images")

        # 查找所有Word文档
        word_pattern = os.path.join(input_dir, "*.docx")
        word_files = glob.glob(word_pattern)

        if not word_files:
            logger.warning(f"未找到Word文档 (.docx) 在目录 {input_dir}")
            return sample

        logger.info(f"找到 {len(word_files)} 个Word文档待处理")

        # 转换统计
        success_count = 0
        fail_count = 0
        total_pages = 0

        for word_file in word_files:
            image_files = self._convert_single_document(word_file)
            if image_files:
                success_count += 1
                total_pages += len(image_files)
            else:
                fail_count += 1

        logger.info(f"转换完成: 成功 {success_count}, 失败 {fail_count}, 总页数 {total_pages}")

        return sample
