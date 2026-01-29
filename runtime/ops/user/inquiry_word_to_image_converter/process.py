"""
Word转图片算子
功能：将Word文档转换为高质量JPG图片，支持多页文档

使用 runtime Docker 镜像已有依赖：
- docx->pdf: LibreOffice (apt install libreoffice)
- pdf->jpg: PyMuPDF + Pillow (ops extra 依赖)
"""

import os
import subprocess
import tempfile
import time
from typing import Dict, Any, List
from loguru import logger

from datamate.core.base_op import Mapper


class WordToImageConverterHelper:
    """Word转图片辅助类"""

    def __init__(
        self,
        output_dir: str,
        dpi: int = 300,
        skip_blank_pages: bool = True,
        max_retries: int = 3,
    ):
        """
        初始化Word转图片转换器

        Args:
            output_dir: 输出图片目录
            dpi: 图片分辨率（DPI），默认300
            skip_blank_pages: 是否跳过空白页，默认True
            max_retries: Word转PDF失败时的最大重试次数，默认3
        """
        self.output_dir = output_dir
        self.dpi = dpi
        self.skip_blank_pages = skip_blank_pages
        self.max_retries = max_retries

        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)

        logger.info(f"Word转图片转换器初始化完成，DPI: {dpi}")

    def _convert_docx_to_pdf(self, docx_path: str) -> str:
        """
        将Word文档转换为PDF（使用 LibreOffice，runtime Docker 镜像已安装）

        Args:
            docx_path: Word文档路径

        Returns:
            PDF文件路径
        """
        # 生成PDF文件路径（LibreOffice 输出到指定目录，保持原文件名）
        output_dir = os.path.dirname(docx_path)
        pdf_filename = os.path.basename(docx_path).replace(".docx", ".pdf")
        pdf_path = os.path.join(output_dir, pdf_filename)

        for attempt in range(self.max_retries):
            try:
                # 使用 LibreOffice 命令行转换（runtime 镜像 apt 已安装 libreoffice）
                result = subprocess.run(
                    [
                        "libreoffice",
                        "--headless",
                        "--invisible",
                        "--convert-to",
                        "pdf",
                        "--outdir",
                        output_dir,
                        docx_path,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                if result.returncode != 0:
                    raise RuntimeError(
                        f"LibreOffice 转换失败: {result.stderr or result.stdout}"
                    )

                if not os.path.exists(pdf_path):
                    raise FileNotFoundError(f"PDF 文件未生成: {pdf_path}")

                logger.info(f"Word转PDF完成: {docx_path} -> {pdf_path}")
                return pdf_path

            except Exception as e:
                error_msg = str(e)
                logger.warning(
                    f"Word转PDF失败 (尝试 {attempt + 1}/{self.max_retries}): {error_msg}"
                )

                if attempt == self.max_retries - 1:
                    logger.error(f"Word转PDF最终失败: {error_msg}")
                    raise

                wait_time = (attempt + 1) * 2
                logger.info(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)

    def _is_blank_page(self, image) -> bool:
        """
        检查图片是否为空白页（大部分区域是白色）

        Args:
            image: PIL Image对象

        Returns:
            True表示是空白页，False表示有内容
        """
        # 获取图片尺寸
        width, height = image.size

        # 方法1：检查整页的唯一颜色数
        pixels = list(image.getdata())
        total_unique_colors = len(set(pixels))

        # 如果整页只有很少的颜色（如<5种），很可能是空白页
        # 正常的文档页面会有很多种颜色（文字、边框、表格等）
        if total_unique_colors < 5:
            return True

        # 方法2：检查多个采样区域
        # 将页面分成多个区域进行采样
        num_regions = 20  # 水平方向20个区域
        region_height = height // num_regions

        regions_with_content = 0

        for i in range(num_regions):
            start = i * region_height * width
            end = min((i + 1) * region_height * width, len(pixels))
            region_pixels = pixels[start:end]

            # 如果这个区域有多种颜色（>3种），认为有内容
            if len(set(region_pixels)) > 3:
                regions_with_content += 1

        # 如果有至少1个区域有内容，则不是空白页
        return regions_with_content == 0

    def _convert_pdf_to_jpg(self, pdf_path: str, output_filename: str) -> List[str]:
        """
        将PDF转换为JPG图片（使用 PyMuPDF，runtime Docker 镜像 ops extra 已安装）

        Args:
            pdf_path: PDF文件路径
            output_filename: 输出图片文件名

        Returns:
            JPG图片路径列表
        """
        try:
            import fitz
            from PIL import Image

            # 使用 PyMuPDF 转换 PDF 到图片（runtime 镜像 ops extra 已安装 PyMuPDF）
            doc = fitz.open(pdf_path)
            images = []
            for page in doc:
                pix = page.get_pixmap(dpi=self.dpi, alpha=False)
                img = Image.frombytes(
                    "RGB", [pix.width, pix.height], pix.samples
                )
                images.append(img)
            doc.close()

            output_paths = []

            # 过滤掉空白页
            valid_images = []
            for i, img in enumerate(images):
                if self.skip_blank_pages and self._is_blank_page(img):
                    logger.info(f"  跳过空白页: 第{i + 1}页")
                else:
                    valid_images.append((i + 1, img))

            # 保存有效页面为JPG
            if len(valid_images) == 0:
                # 如果所有页都是空白（异常情况），至少保存第一页
                output_path = os.path.join(self.output_dir, output_filename)
                images[0].save(output_path, "JPEG", quality=95)
                output_paths.append(output_path)
                logger.warning(
                    f"PDF所有页都是空白，仅保存第一页: {pdf_path} -> {output_path}"
                )
            elif len(valid_images) == 1:
                # 只有一页有效内容，使用原文件名
                page_num, image = valid_images[0]
                output_path = os.path.join(self.output_dir, output_filename)
                image.save(output_path, "JPEG", quality=95)
                output_paths.append(output_path)
                logger.info(f"PDF转JPG完成 (1页有效): {pdf_path} -> {output_path}")
            else:
                # 多页有效内容，为每页生成单独的图片
                base_name, ext = os.path.splitext(output_filename)
                for idx, (page_num, image) in enumerate(valid_images):
                    if idx == 0:
                        # 第一页使用原文件名
                        output_path = os.path.join(self.output_dir, output_filename)
                    else:
                        # 后续页面添加序号后缀
                        output_path = os.path.join(
                            self.output_dir, f"{base_name}-{idx + 1}{ext}"
                        )

                    image.save(output_path, "JPEG", quality=95)
                    output_paths.append(output_path)

                logger.info(
                    f"PDF转JPG完成 ({len(valid_images)}页有效): {pdf_path} -> {len(output_paths)}张图片"
                )

            return output_paths

        except Exception as e:
            logger.error(f"PDF转JPG失败: {pdf_path}, 错误: {str(e)}")
            raise

    def _cleanup_pdf(self, pdf_path: str):
        """
        清理临时PDF文件

        Args:
            pdf_path: PDF文件路径
        """
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
                logger.info(f"已清理临时PDF文件: {pdf_path}")
        except Exception as e:
            logger.warning(f"清理PDF文件失败: {str(e)}")

    def convert_single_document(
        self, docx_path: str, jpg_filename: str = None
    ) -> List[str]:
        """
        转换单个Word文档为JPG图片（支持多页）

        Args:
            docx_path: Word文档路径
            jpg_filename: 输出JPG文件名（可选，默认使用docx文件名替换扩展名）

        Returns:
            JPG图片路径列表
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(docx_path):
                raise FileNotFoundError(f"Word文档不存在: {docx_path}")

            # 生成输出文件名
            if jpg_filename is None:
                jpg_filename = os.path.basename(docx_path).replace(".docx", ".jpg")

            # Word -> PDF
            pdf_path = self._convert_docx_to_pdf(docx_path)

            # PDF -> JPG
            jpg_paths = self._convert_pdf_to_jpg(pdf_path, jpg_filename)

            # 清理临时PDF文件
            self._cleanup_pdf(pdf_path)

            return jpg_paths

        except Exception as e:
            logger.error(f"转换文档失败: {docx_path}, 错误: {str(e)}")
            raise


class WordToImageConverter(Mapper):
    """
    Word转图片算子
    类名建议使用驼峰命名法定义，例如 WordToImageConverter
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 从UI参数获取配置
        self.image_dpi = int(kwargs.get("imageDPI", 300))
        self.skip_blank_pages = kwargs.get("skipBlankPages", True)
        self.max_retries = int(kwargs.get("maxRetries", 3))
        self.output_format = kwargs.get("outputFormat", "JPEG")

        # 创建临时输出目录
        self.temp_output_dir = tempfile.mkdtemp(prefix="word_to_image_")

        # 创建转换器实例
        self.converter = WordToImageConverterHelper(
            self.temp_output_dir,
            self.image_dpi,
            self.skip_blank_pages,
            self.max_retries,
        )

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑
        :param sample: 输入的数据样本，通常包含 text_key 等字段
        :return: 处理后的数据样本
        """
        try:
            # 获取Word文档路径
            self.converter = WordToImageConverterHelper(
                sample["export_path"] + "/images",
                self.image_dpi,
                self.skip_blank_pages,
                self.max_retries,
            )

            # 优先从 export_path 获取（上游算子输出）
            if "export_path" in sample and sample["export_path"]:
                export_path = sample["export_path"]
                docx_files = []
                if os.path.isdir(export_path):
                    for file in os.listdir(export_path):
                        if file.lower().endswith(".docx"):
                            docx_files.append(os.path.join(export_path, file))
                elif export_path.lower().endswith(".docx"):
                    docx_files.append(export_path)
                else:
                    logger.warning(f"在export_path未找到docx文件: {export_path}")
                    docx_files = []

                all_jpg_paths = []
                for docx_path in docx_files:
                    jpg_paths = self.converter.convert_single_document(docx_path)
                    all_jpg_paths.extend(jpg_paths)

                sample["generated_images"] = all_jpg_paths
                logger.info(f"成功转换Word文档为JPG图片，共{len(all_jpg_paths)}张图片")
            return sample

        except Exception as e:
            logger.error(f"转换Word文档为JPG图片时发生错误: {str(e)}")
            raise
