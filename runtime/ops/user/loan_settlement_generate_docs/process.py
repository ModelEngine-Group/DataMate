import json
import os
from typing import Dict, Any

from loguru import logger
from datamate.core.base_op import Mapper
from .src import DocGenerator

# -----------------------------------------------------------
# 注意：您需要将原项目中 src.doc_generator 的逻辑引入进来。
# 如果它是一个独立的库，请在 requirements.txt 中声明。
# 这里假设您会将 DocGenerator 类代码直接集成，或放在同级目录引用。
# 下面是一个为了让代码跑通的引用示例，实际请调整为相对引用：
# from .doc_generator import DocGenerator 
# -----------------------------------------------------------

class LoanSettlementDocGenOperator(Mapper):
    """
    文档生成算子：DocGenOperator
    对应 metadata.yml 中的 raw_id
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 获取 metadata.yml 中定义的参数
        self.output_dir = kwargs.get('outputDirParam', '/dataset').strip()
        self.prefix = kwargs.get('filePrefixParam', 'loan_clearance').strip()
        
        # 确保输出目录存在
        if self.output_dir and not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

        # 初始化生成器 (这里假设 DocGenerator 可以在此处初始化)
        # 如果 DocGenerator 需要每次重新加载模板，则移到 execute 中
        # self.generator = DocGenerator(self.template_path, self.output_dir)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑：处理单条 sample 数据并生成文档
        """
        file_path = sample.get('filePath')
        if not file_path.endswith('.docx') or os.path.normpath(file_path).count(os.sep) > 3:
            return sample

        try:
            # 1. 准备数据
            self.output_dir = str(sample.get('export_path'))

            # 3. 调用生成逻辑
            records = json.loads(sample['text'])
            doc_generator = DocGenerator(
                template_path=sample['filePath'],
                output_dir=str(self.output_dir)
            )
            doc_generator.generate_batch(records, prefix=self.prefix)
            # self.generator.render_one(template_path=self.template_path, context=context, output_path=output_path)
            
            # 模拟生成过程 (替换为您真实的 DocGenerator 调用)
            # doc = DocxTemplate(self.template_path)
            # doc.render(context)
            # doc.save(output_path)
            

        except Exception as e:
            # 异常处理，防止单条失败导致崩溃
            logger.error(f"Error generating doc for sample: {e}")
        
        return sample