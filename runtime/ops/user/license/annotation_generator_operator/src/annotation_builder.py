"""
标注生成模块
负责生成训练数据所需的JSON标注文件
"""

import os
import json
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class AnnotationBuilder:
    """
    标注生成器
    为增强后的图片生成对应的JSON标注
    """

    # 需要输出的字段（按模板中的顺序）
    OUTPUT_FIELDS = [
        "名称",
        "住所",
        "法定代表人姓名",
        "公司类型",
        "经营范围",
        "成立日期",
        "营业期限",
        "注册资本",
        "实收资本",
        "注册号",
        "发证日期"
    ]

    # 字段别名映射（用于兼容不同的字段名）
    FIELD_ALIASES = {
        "落款日期": "证明开具日期",  # 落款日期与证明开具日期相同
    }

    def __init__(self, output_dir: str = "annotations",
                 format_type: str = "multimodal",
                 human_prompt: str = None,
                 qa_count: int = 3):
        """
        初始化标注生成器

        Args:
            output_dir: 输出目录
            format_type: 标注格式类型 ('multimodal' | 'simple_json')
            human_prompt: human提示词
            qa_count: 每个图片的问答对数量（不含完整JSON提取）
        """
        self.output_dir = output_dir
        self.format_type = format_type
        self.human_prompt = human_prompt or "<image>\\n请提取这张贷款结清证明的关键信息，以JSON格式输出"
        self.qa_count = qa_count

        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def build_single(self, image_path: str, data: Dict[str, Any],
                    output_name: str = None) -> Dict[str, Any]:
        """
        构建单个样本的标注

        Args:
            image_path: 图片路径
            data: 字段数据字典
            output_name: 输出文件名

        Returns:
            标注字典
        """
        # 提取需要的字段
        filtered_data = self._filter_fields(data)

        if self.format_type == "multimodal":
            annotation = self._build_multimodal(image_path, filtered_data)
        else:
            annotation = self._build_simple_json(image_path, filtered_data)

        # 保存到文件
        if output_name:
            output_path = os.path.join(self.output_dir, f"{output_name}.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(annotation, f, ensure_ascii=False, indent=2)

        return annotation

    def _filter_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """过滤并规范化字段数据"""
        filtered = {}

        for field in self.OUTPUT_FIELDS:
            # 直接查找
            if field in data:
                filtered[field] = data[field]
            else:
                # 查找别名
                found = False
                for alias, target in self.FIELD_ALIASES.items():
                    if field == target and alias in data:
                        filtered[field] = data[alias]
                        found = True
                        break

                if not found:
                    # 使用空字符串作为默认值
                    filtered[field] = ""

        return filtered

    def _build_multimodal(self, image_path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建多模态训练格式
        适用于 LLaVA、Qwen-VL 等模型
        随机生成指定数量的问答对 + 1 个完整JSON提取
        """
        import random

        # 生成唯一ID
        image_id = Path(image_path).stem

        # 定义所有可选问答对（前8个）
        all_qa_pairs = [
            # 第1问：文档类型
            {
                "human": "<image>\\n这是什么类型的文档？",
                "gpt": "这是一份企业法人营业执照"
            },
            # 第2问：企业信息
            {
                "human": "营业执照上的名称是什么？",
                "gpt": f"名称是{data.get('名称', '')}"
            },
            # 第3问：住所信息
            {
                "human": "企业的住所地址是什么？",
                "gpt": f"住所为{data.get('住所', '')}"
            },
            # 第4问：法定代表人
            {
                "human": "法定代表人姓名是什么？",
                "gpt": f"法定代表人姓名是{data.get('法定代表人姓名', '')}"
            },
            # 第5问：公司类型
            {
                "human": "公司类型是什么？",
                "gpt": f"公司类型为{data.get('公司类型', '')}"
            },
            # 第6问：经营范围
            {
                "human": "企业的经营范围是什么？",
                "gpt": f"经营范围为{data.get('经营范围', '')}"
            },
            # 第7问：成立日期
            {
                "human": "企业是什么时候成立的？",
                "gpt": f"企业于{data.get('成立日期', '')}成立"
            },
            # 第8问：注册资本
            {
                "human": "注册资本和实收资本分别是多少？",
                "gpt": f"注册资本为{data.get('注册资本', '')}，实收资本为{data.get('实收资本', '')}"
            }
        ]

        # 随机选择指定数量的问答对
        qa_count = min(self.qa_count, len(all_qa_pairs))
        selected_qa = random.sample(all_qa_pairs, qa_count)

        # 构建多轮对话
        conversations = []

        # 添加选中的问答对
        for qa in selected_qa:
            conversations.append({
                "from": "human",
                "value": qa["human"]
            })
            conversations.append({
                "from": "gpt",
                "value": qa["gpt"]
            })

        # 添加最后一个：完整JSON提取
        conversations.append({
            "from": "human",
            "value": "请提取所有关键信息，以JSON格式输出"
        })
        data_json = json.dumps(data, ensure_ascii=False)
        conversations.append({
            "from": "gpt",
            "value": data_json
        })

        return {
            "id": image_id,
            "image": image_path,
            "conversations": conversations
        }

    def _build_simple_json(self, image_path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建简单JSON格式
        适用于自定义训练流程
        """
        image_id = Path(image_path).stem

        return {
            "id": image_id,
            "image": image_path,
            "data": data,
            "metadata": {
                "document_type": "企业法人营业执照",
                "created_at": datetime.now().isoformat()
            }
        }

    def build_batch(self, records: List[Dict[str, Any]],
                   image_mapping: Dict[str, List[str]] = None) -> List[Dict]:
        """
        批量构建标注

        Args:
            records: 数据记录列表（与生成的文档对应）
            image_mapping: 图片映射字典 {原始图片: [增强变体列表]}

        Returns:
            标注列表
        """
        annotations = []

        print(f"\n生成标注文件...")
        print(f"格式类型: {self.format_type}")

        for i, record in enumerate(records):
            base_name = f"loan_clearance_{i+1:03d}"

            # 获取对应的图片路径
            if image_mapping and base_name in image_mapping:
                # 为每个变体生成标注
                for variant_path in image_mapping[base_name]:
                    variant_name = Path(variant_path).stem
                    annotation = self.build_single(variant_path, record, variant_name)
                    annotations.append(annotation)
            else:
                # 为原始记录生成标注（假设图片路径）
                image_path = f"augmented_images/{base_name}_v1_扫描件.png"
                annotation = self.build_single(image_path, record, base_name)
                annotations.append(annotation)

        print(f"共生成 {len(annotations)} 个标注文件")
        return annotations

    def build_dataset(self, annotations: List[Dict],
                     output_path: str = None,
                     split_ratio: tuple = (0.8, 0.1, 0.1)) -> Dict:
        """
        构建完整数据集

        Args:
            annotations: 标注列表
            output_path: 输出文件路径
            split_ratio: 训练/验证/测试分割比例

        Returns:
            数据集字典
        """
        import random

        # 打乱数据
        indices = list(range(len(annotations)))
        random.shuffle(indices)

        # 计算分割点
        n = len(indices)
        train_end = int(n * split_ratio[0])
        val_end = train_end + int(n * split_ratio[1])

        # 分割数据
        train_indices = indices[:train_end]
        val_indices = indices[train_end:val_end]
        test_indices = indices[val_end:]

        dataset = {
            "info": {
                "description": "企业法人营业执照数据集",
                "document_type": "企业法人营业执照",
                "total_samples": len(annotations),
                "format": self.format_type,
                "created_at": datetime.now().isoformat(),
                "fields": self.OUTPUT_FIELDS
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
        if output_path is None:
            output_path = os.path.join(self.output_dir, "dataset.json")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)

        print(f"\n数据集已保存到: {output_path}")
        print(f"  训练集: {dataset['split']['train']} 样本")
        print(f"  验证集: {dataset['split']['validation']} 样本")
        print(f"  测试集: {dataset['split']['test']} 样本")

        return dataset

    def create_summary(self, records: List[Dict[str, Any]],
                      image_mapping: Dict[str, List[str]] = None,
                      output_path: str = None) -> Dict:
        """
        创建数据摘要

        Args:
            records: 原始数据记录
            image_mapping: 图片映射
            output_path: 输出文件路径

        Returns:
            摘要字典
        """
        if output_path is None:
            output_path = os.path.join(self.output_dir, "summary.json")

        total_images = 0
        if image_mapping:
            total_images = sum(len(paths) for paths in image_mapping.values())

        summary = {
            "generation_info": {
                "total_records": len(records),
                "total_images": total_images,
                "images_per_record": total_images // len(records) if records else 0,
                "fields": self.OUTPUT_FIELDS,
                "created_at": datetime.now().isoformat()
            },
            "sample_data": records[:3] if records else [],  # 包含前3条样本数据
            "field_statistics": self._compute_field_stats(records)
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"\n数据摘要已保存到: {output_path}")
        return summary

    def _compute_field_stats(self, records: List[Dict[str, Any]]) -> Dict:
        """计算字段统计信息"""
        stats = {}

        for field in self.OUTPUT_FIELDS:
            values = []
            for record in records:
                if field in record:
                    values.append(record[field])

            if values:
                unique_values = len(set(str(v) for v in values))
                stats[field] = {
                    "unique_count": unique_values,
                    "sample_value": str(values[0]) if values else ""
                }

        return stats


# 保留旧的函数接口以兼容现有代码
def generate_qa_pairs(record: Dict[str, Any], num_qa: int = 3) -> List[Dict[str, str]]:
    """
    为单条记录生成问答对（保留以兼容旧代码）

    Args:
        record: 数据记录
        num_qa: 问答对数量

    Returns:
        问答对列表
    """
    qa_pairs = []

    contents = record.get('contents', [])

    # 生成问答对
    for _ in range(num_qa):
        # 随机选择一个字段
        if contents:
            content = random.choice(contents)
            label = content.get('label', '')
            text = content.get('text', '')

            # 生成不同类型的问题
            question_types = [
                f"这张营业执照的{label}是什么？",
                f"请问{label}的内容是什么？",
                f"营业执照上的{label}填写的什么？",
            ]
            question = random.choice(question_types)

            qa_pairs.append({
                'question': question,
                'answer': text
            })

    return qa_pairs


def generate_dataset(records, images_dir: str, output_dir: str,
                  qa_count: int = 3, train_ratio: float = 0.8, seed: int = None):
    """
    生成完整的数据集（保留以兼容旧代码）

    Args:
        records: 数据文件路径
        images_dir: 图片目录路径
        output_dir: 输出目录
        qa_count: 每张图的问答对数量
        train_ratio: 训练集比例
        seed: 随机种子
    """
    if seed is not None:
        import random
        random.seed(seed)

    # 获取图片列表
    images_path = Path(images_dir)
    image_files = list(images_path.glob("*.jpg"))

    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 使用新的 AnnotationBuilder
    builder = AnnotationBuilder(
        output_dir=str(output_path),
        format_type="multimodal",
        qa_count=qa_count
    )

    # 生成数据集
    dataset = []
    conversations = []

    for i, record in enumerate(records):
        group_id = record.get('group_id', str(i + 1))

        # 查找对应的图片
        matching_images = [img for img in image_files if img.stem.startswith(f"group_{group_id}")]

        for img_file in matching_images:
            img_name = img_file.name
            img_path = str(img_file)

            # 使用 AnnotationBuilder 生成标注
            annotation = builder.build_single(img_path, record, img_file.stem)

            # 添加到数据集
            dataset.append(annotation)

            # 添加到对话列表
            for conv in annotation.get('conversations', []):
                conversations.append({
                    'id': f"{group_id}_{img_file.stem}_{len(conversations)}",
                    'image': img_path,
                    'question': conv.get('value', ''),
                    'answer': conv.get('value', '')
                })

    # 划分训练集、验证集和测试集
    import random
    random.shuffle(dataset)

    # 计算分割点
    n = len(dataset)
    train_end = int(n * train_ratio)
    val_end = train_end + int((n - train_end) * 0.5)  # 剩余部分平分给验证集和测试集

    # 分割数据
    train_data = dataset[:train_end]
    val_data = dataset[train_end:val_end]
    test_data = dataset[val_end:]

    # 保存数据集
    dataset_file = output_path / "dataset.json"
    with open(dataset_file, 'w', encoding='utf-8') as f:
        json.dump({
            'info': {
                'description': '企业法人营业执照数据集',
                'document_type': '企业法人营业执照',
                'total_samples': len(dataset),
                'format': 'multimodal',
                'created_at': datetime.now().isoformat(),
                'fields': [
                    '名称',
                    '住所',
                    '法定代表人姓名',
                    '公司类型',
                    '经营范围',
                    '成立日期',
                    '营业期限',
                    '注册资本',
                    '实收资本',
                    '注册号',
                    '发证日期'
                ]
            },
            'train': train_data,
            'validation': val_data,
            'test': test_data,
            'split': {
                'train': len(train_data),
                'validation': len(val_data),
                'test': len(test_data)
            }
        }, f, ensure_ascii=False, indent=2)

    # 保存对话数据
    conversations_file = output_path / "conversations.json"
    with open(conversations_file, 'w', encoding='utf-8') as f:
        json.dump(conversations, f, ensure_ascii=False, indent=2)

    return {
        'train_count': len(train_data),
        'val_count': len(val_data),
        'test_count': len(test_data),
        'total_count': len(dataset),
        'total_conversations': len(conversations)
    }
