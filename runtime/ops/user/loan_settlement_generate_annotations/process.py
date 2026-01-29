from datetime import datetime
import os
import random
import sys
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from loguru import logger
from datamate.core.base_op import Mapper

# ---------------------------------------------------------------------
# 保持原有的 import 路径
# 请确保将 src 文件夹复制到算子包内，或确保环境中有该模块
# ---------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent))
try:
    from .src.annotation_builder import AnnotationBuilder
except ImportError:
    # 仅作开发提示，运行时需要依赖存在
    logger.info("Warning: src.annotation_builder not found. Please ensure dependencies are packaged.")
    AnnotationBuilder = None


def build_dataset(annotations: List[Dict],
                  output_dir: str,
                  train_ratio: float = 0.8,
                  seed: int = 42) -> Dict:
    """
    构建带 train/val/test 划分的数据集

    Args:
        annotations: 标注列表
        output_dir: 输出目录
        train_ratio: 训练集比例
        seed: 随机种子

    Returns:
        数据集字典
    """
    # 设置随机种子
    random.seed(seed)

    # 打乱数据
    indices = list(range(len(annotations)))
    random.shuffle(indices)

    # 计算分割点
    n = len(indices)
    train_end = int(n * train_ratio)
    val_end = train_end + int((n - train_end) / 2)

    # 分割数据
    train_indices = indices[:train_end]
    val_indices = indices[train_end:val_end]
    test_indices = indices[val_end:]

    dataset = {
        "info": {
            "description": "贷款结清证明数据集",
            "document_type": "贷款结清证明",
            "total_samples": len(annotations),
            "format": annotations[0].get("conversations") and "multimodal" or "simple_json",
            "created_at": datetime.now().isoformat(),
        },
        "train": [annotations[i] for i in train_indices],
        "validation": [annotations[i] for i in val_indices],
        "test": [annotations[i] for i in test_indices],
        "split": {
            "train": len(train_indices),
            "validation": len(val_indices),
            "test": len(test_indices)
        }
    }

    # 保存数据集
    output_path = Path(output_dir) / "dataset.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    logger.info(f"  dataset.json:")
    logger.info(f"    训练集: {dataset['split']['train']} 样本")
    logger.info(f"    验证集: {dataset['split']['validation']} 样本")
    logger.info(f"    测试集: {dataset['split']['test']} 样本")

    return dataset


def build_conversations_summary(annotations: List[Dict], output_dir: str):
    """
    构建 conversations 汇总文件
    将所有图片的问答对汇总到一个 JSON 文件中

    Args:
        annotations: 标注列表
        output_dir: 输出目录
    """
    conversations_summary = []

    for annotation in annotations:
        # 提取问答对（排除最后的完整 JSON 提取）
        image_id = annotation.get("id", "")
        image_path = annotation.get("image", "")

        # 获取 conversations 数组
        all_conversations = annotation.get("conversations", [])

        # 排除最后一组（完整 JSON 提取），只保留问答对
        qa_conversations = []
        for i in range(0, len(all_conversations) - 2, 2):  # -2 排除最后一组 human+gpt
            if i + 1 < len(all_conversations):
                qa_conversations.append(all_conversations[i])
                qa_conversations.append(all_conversations[i + 1])

        conversations_summary.append({
            "id": image_id,
            "image": image_path,
            "conversations": qa_conversations
        })

    # 保存汇总文件
    output_path = Path(output_dir) / "conversations.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(conversations_summary, f, ensure_ascii=False, indent=2)

    logger.info(f"  conversations.json: {len(conversations_summary)} 张图片的问答对汇总")



class LoanSettlementAnnotationGenOperator(Mapper):
    """
    图文对标注生成算子：AnnotationGenOperator
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 1. 获取参数
        self.split = float(kwargs.get('split', 0.8))
        self.format_type = kwargs.get('formatType', 'multimodal')
        self.qa_count = int(kwargs.get('qaCount', 3))
        self.seed = int(kwargs.get('seed', 42))

    def _match_images_to_records(self, image_files: List[Path], records: List[Dict]) -> List[Dict]:
        """
        将图片文件匹配到对应的数据记录

        Args:
            image_files: 图片文件列表
            records: 数据记录列表

        Returns:
            匹配结果列表，每个元素包含 {image, record}
        """
        matched = []

        for img_file in image_files:
            record_index = self._extract_record_index(img_file.name)

            if record_index is not None and 0 <= record_index < len(records):
                matched.append({
                    'image': img_file,
                    'record': records[record_index],
                    'record_index': record_index
                })
            else:
                logger.warning(f"  警告: 无法匹配图片 {img_file.name} 到数据记录")

        return matched

    def _extract_record_index(self, image_filename: str) -> Optional[int]:
        """
        从图片文件名中提取记录索引 (复用原脚本逻辑)
        例如：loan_clearance_003_2-桌面实景图.jpg -> 3
        """
        match = re.search(r'loan_clearance_(\d+)', image_filename)
        if match:
            # 转换为 0-based 索引
            return int(match.group(1)) - 1  
        return None

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑：处理单张图片，生成对应的标注数据
        """
        file_path = sample.get('filePath')
        if not file_path.endswith('.docx') or os.path.normpath(file_path).count(os.sep) > 3:
            return sample

        # 3. 预加载原始数据记录 (records.json)
        records = json.loads(sample['text'])
        sample['text'] = ''
        output_dir = str(sample.get('export_path'))

        image_path = Path(output_dir + "/images")
        image_files = list(image_path.glob("*.png"))
        matched = self._match_images_to_records(image_files, records)

        # 4. 初始化构建器
        if AnnotationBuilder:
            self.builder = AnnotationBuilder(
                output_dir=output_dir,
                format_type=self.format_type,
                qa_count=self.qa_count
            )
        else:
            self.builder = None

        try:
            if not self.builder:
                raise ImportError("AnnotationBuilder module is missing.")

            # 生成每个图片的标注文件
            annotations = []
            for item in matched:
                img_file = item['image']
                record = item['record']

                annotation = self.builder.build_single(
                    image_path=str(img_file),
                    data=record,
                    output_name=img_file.stem
                )
                annotations.append(annotation)

            logger.info(f"  已生成 {len(annotations)} 个标注文件")

            # 步骤5: 生成汇总数据集（带 train/val/test 划分）
            logger.info("\n[5/5] 生成汇总数据集...")
            dataset = build_dataset(
                annotations=annotations,
                output_dir=str(output_dir),
                train_ratio=self.split,
                seed=self.seed
            )

            # 步骤6: 生成问答对汇总文件
            logger.info("\n[6/6] 生成 conversations 汇总文件...")
            build_conversations_summary(annotations, output_dir)

        except Exception as e:
            # 异常处理
            logger.error(f"Error processing sample {sample.get('id', 'unknown')}: {e}")
        
        return sample