import os
import json
import glob
from pathlib import Path
from .src import DocGenerator

import json
import os
from typing import Dict, Any

from loguru import logger
from datamate.core.base_op import Mapper
from .src import DocGenerator


class TaxDocGenOperator(Mapper):
    """
    文档生成算子：DocGenOperator
    对应 metadata.yml 中的 raw_id
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 获取 metadata.yml 中定义的参数
        self.output_dir = None

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑：处理单条 sample 数据并生成文档
        """
        try:
            file_path = sample.get('filePath')
            if not file_path.endswith('.docx') or os.path.normpath(file_path).count(os.sep) > 3:
                return sample

            template_abs_path = file_path
            data_abs_dir = sample["export_path"]
            output_abs_dir = data_abs_dir
            os.makedirs(output_abs_dir, exist_ok=True)

            # 获取所有 JSON 文件（按文件名排序）
            json_files = sorted(glob.glob(os.path.join(data_abs_dir, "*.json")))

            if not json_files:
                logger.error(f"❌ 在 '{data_abs_dir}' 中未找到任何 JSON 文件")
                return sample

            logger.info(f"找到 {len(json_files)} 个 JSON 文件，开始批量生成 Word 文档...")

            # 创建文档生成器
            generator = DocGenerator(str(template_abs_path))

            # 批量处理
            for json_file in json_files:
                try:
                    # 从 JSON 文件加载数据
                    with open(json_file, 'r', encoding='utf-8') as f:
                        tax_data = json.load(f)

                    # 生成安全的文件名（避免特殊字符）
                    taxpayer_name = tax_data.get("纳税人姓名", "未知纳税人")
                    safe_name = "".join(c if c not in r'\/:*?"<>|' else "_" for c in taxpayer_name)

                    # 构造输出路径
                    output_path = os.path.join(output_abs_dir, f"{safe_name}_个人所得税完税证明.docx")

                    # 填充并保存
                    generator.fill_tax_certificate(tax_data, output_path)

                except Exception as e:
                    logger.error(f"❌ 处理 {json_file} 时出错: {e}")
                    raise e

            logger.info(f"\n🎉 全部完成！共处理 {len(json_files)} 份文件，保存在 '{output_abs_dir}' 目录中。")


        except Exception as e:
            # 异常处理，防止单条失败导致崩溃
            logger.error(f"Error generating doc for sample: {e}")
            raise e

        return sample

