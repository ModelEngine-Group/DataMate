"""
印章添加算子 - process.py
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

from datamate.core.base_op import Mapper
from .src import SealGenerator


class FlowSealAddOperator(Mapper):
    """
    印章添加算子：SealAddOperator
    对应 metadata.yml 中的 raw_id
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 获取 metadata.yml 中定义的参数
        self.seal_size = int(kwargs.get('sealSizeParam', 200))
        self.bank_name = kwargs.get('bankNameParam', '北京兴业银行')
        self.auto_detect = kwargs.get('autoDetectParam', True)

    def _get_bank_config(self, bank_name: str) -> Dict[str, str]:
        """
        获取银行印章配置

        Args:
            bank_name: 银行名称

        Returns:
            印章配置字典
        """
        bank_configs = {
            "北京兴业银行": {
                "top_text": "北京兴业银行信贷部",
                "bottom_text": "业务专用"
            },
            "上海浦发银行": {
                "top_text": "上海浦发银行信贷部",
                "bottom_text": "业务专用"
            },
            "工商银行": {
                "top_text": "工商银行信贷部",
                "bottom_text": "业务专用"
            },
            "农业银行": {
                "top_text": "农业银行信贷部",
                "bottom_text": "业务专用"
            },
            "中国银行": {
                "top_text": "中国银行信贷部",
                "bottom_text": "业务专用"
            },
            "建设银行": {
                "top_text": "建设银行信贷部",
                "bottom_text": "业务专用"
            },
            "交通银行": {
                "top_text": "交通银行信贷部",
                "bottom_text": "业务专用"
            },
            "招商银行": {
                "top_text": "招商银行信贷部",
                "bottom_text": "业务专用"
            },
            "浦发银行": {
                "top_text": "浦发银行信贷部",
                "bottom_text": "业务专用"
            },
            "中信银行": {
                "top_text": "中信银行信贷部",
                "bottom_text": "业务专用"
            },
            "光大银行": {
                "top_text": "光大银行信贷部",
                "bottom_text": "业务专用"
            },
            "民生银行": {
                "top_text": "民生银行信贷部",
                "bottom_text": "业务专用"
            },
            "平安银行": {
                "top_text": "平安银行信贷部",
                "bottom_text": "业务专用"
            },
            "华夏银行": {
                "top_text": "华夏银行信贷部",
                "bottom_text": "业务专用"
            },
            "兴业银行": {
                "top_text": "兴业银行信贷部",
                "bottom_text": "业务专用"
            },
            "广发银行": {
                "top_text": "广发银行信贷部",
                "bottom_text": "业务专用"
            },
            "洛汀城市银行": {
                "top_text": "洛汀城市银行信贷部",
                "bottom_text": "业务专用"
            }
        }

        return bank_configs.get(bank_name, {
            "top_text": f"{bank_name}信贷部",
            "bottom_text": "业务专用"
        })

    def _extract_bank_name_from_json(self, json_path: str) -> Optional[str]:
        """
        从JSON文件中提取银行名称

        Args:
            json_path: JSON文件路径

        Returns:
            银行名称，如果未找到则返回None
        """
        if not os.path.exists(json_path):
            return None

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 从"账号"字段中提取银行名称
                account_info = data.get("账号", "")
                # 提取银行名称（去除数字部分）
                import re
                bank_match = re.search(r'([^\d]+)', account_info)
                if bank_match:
                    bank_name = bank_match.group(1).strip()
                    logger.info(f"从JSON文件中提取到银行名称: {bank_name}")
                    return bank_name
        except Exception as e:
            logger.error(f"读取JSON文件失败: {e}")

        return None

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心执行逻辑

        Args:
            sample: 输入样本

        Returns:
            处理后的样本
        """
        try:
            # 获取输入文件路径
            input_path = sample.get('export_path')
            if not input_path or not os.path.exists(input_path):
                logger.error(f"Warning: Input directory not found: {input_path}")
                return sample

            # 获取输出路径
            export_path = sample.get('export_path')

            # 构建输出目录
            output_path = Path(export_path) / "images"
            output_path.mkdir(parents=True, exist_ok=True)

            # 创建印章生成器
            generator = SealGenerator(seal_size=self.seal_size, font_size=20)

            # 查找JSON文件以提取银行名称
            input_dir = Path(input_path)
            json_files = list(input_dir.glob("*.json"))

            bank_name = self.bank_name
            if json_files and self.auto_detect:
                bank_name_from_json = self._extract_bank_name_from_json(str(json_files[0]))
                if bank_name_from_json:
                    bank_name = bank_name_from_json

            # 获取印章配置
            config = self._get_bank_config(bank_name)

            # 生成印章
            seal_img = generator.create_circular_seal(
                config["top_text"],
                config["bottom_text"],
                bank_name
            )

            # 处理所有图片文件
            img_dir = input_dir / "images"
            image_files = list(img_dir.glob("*.png")) + list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.jpeg"))
            sealed_count = 0

            for img_file in image_files:
                output_file = output_path / f"sealed_{img_file.name}"

                # 合成印章到图片
                generator.composite_seal_to_image(
                    background_path=str(img_file),
                    seal_img=seal_img,
                    output_path=str(output_file),
                    scale=0.3,
                    auto_detect=self.auto_detect
                )

                sealed_count += 1
                logger.info(f"已添加印章: {output_file}")

        except Exception as e:
            logger.error(f"Error in SealAddOperator: {e}")
            import traceback
            traceback.print_exc()

        return sample
