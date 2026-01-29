# -*- coding: utf-8 -*-

"""
QA标注生成算子 - process.py
"""

import os
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger

from datamate.core.base_op import Mapper
from .src import QAGenerator


class TaxQAGenOperator(Mapper):
    """
    QA生成算子：TaxQAGenOperator
    对应 metadata.yml 中的 raw_id
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 每个样本随机生成的问题数量
        self.qa_count = int(kwargs.get('qaCountParam', kwargs.get('randomQuestionsParam', 8)))
        self.output_file = kwargs.get('outputFileParam', '个人所得税完税证明_dataset.jsonl')

    def _find_json_files(self, input_dir: Path) -> List[Path]:
        files = list(input_dir.glob("*.json"))
        return sorted(files)

    def _find_image_files(self, image_dir: Path) -> List[Path]:
        images = []
        for ext in ("*.png", "*.jpg", "*.jpeg"):
            images.extend(list(image_dir.glob(ext)))
        return sorted(images)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        批量生成QA对并输出为JSONL文件

        sample 期望包含：
          - export_path: 根路径，包含 data/ 与 output/03_simulated 等（或可传入 dataDirParam/imageDirParam/outputDirParam）

        返回原样 sample。
        """
        try:
            file_path = sample.get('filePath')
            if not file_path.endswith('.docx') or os.path.normpath(file_path).count(os.sep) > 3:
                return sample

            base_path = sample.get('export_path')
            # 如果没有 base_path，退回到 individual params
            data_dir = base_path
            image_dir = base_path + "/images"
            output_dir = base_path


            if not os.path.exists(data_dir):
                logger.error(f"数据目录不存在: {data_dir}")
                return sample
            if not os.path.exists(image_dir):
                logger.error(f"图片目录不存在: {image_dir}")
                return sample

            os.makedirs(output_dir, exist_ok=True)

            # 查找数据文件
            data_files = self._find_json_files(Path(data_dir))
            if not data_files:
                logger.warning(f"No JSON files found in {data_dir}")
                return sample

            # 创建QA生成器
            generator = QAGenerator(random_questions=self.qa_count)

            # 生成并写入JSONL
            abs_output_file = os.path.join(output_dir, self.output_file)
            total = generator.generate_batch(
                data_files=[f for f in data_files],
                image_dir=image_dir,
                output_file=abs_output_file
            )

            logger.info(f"生成完成，共 {total} 条记录，输出: {abs_output_file}")

        except Exception as e:
            logger.error(f"Error in TaxQAGenOperator: {e}")

        return sample
