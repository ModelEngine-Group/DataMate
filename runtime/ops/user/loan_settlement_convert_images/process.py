import os
from pathlib import Path
from typing import Dict, Any, List

from loguru import logger
from datamate.core.base_op import Mapper
from .src import ImageConverter


class LoanSettlementDocToImgOperator(Mapper):
    """
    文档转图片算子：DocToImgOperator
    对应 metadata.yml 中的 raw_id
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 获取 metadata.yml 中定义的参数
        self.dpi = int(kwargs.get('dpiParam', 200))
        self.pattern = kwargs.get('patternParam', "*.docx")

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑
        """
        try:
            # 1. 获取输入文件路径
            # 假设上游算子（Step 2）将生成的 docx 路径放在了 'generated_doc_path' 或 'file_path'
            input_path = sample.get('export_path')
            if not input_path or not os.path.exists(input_path):
                logger.error(f"Warning: Input file not found: {input_path}")
                return sample

            # 2. 执行转换
            # 原脚本使用 convert_batch，为了复用逻辑，我们传入单元素的列表
            # 返回的是生成的图片路径列表
            input_path = Path(input_path)
            docx_files = list(input_path.glob(self.pattern))

            converter = ImageConverter(
                output_dir=str(sample.get('export_path')) + "/images/",
                dpi=self.dpi,
                instance_id=str(sample.get("instance_id"))
            )
            converter.convert_batch([str(f) for f in docx_files])

            for file_path in docx_files:
                # 1. 检查文件是否存在
                if os.path.exists(file_path):
                    try:
                        # 2. 删除文件
                        os.remove(file_path)
                    except OSError as e:
                        logger.error(f"删除失败 {file_path}: {e}")


        except Exception as e:
            logger.error(f"Error converting doc to image: {e}")
        
        return sample