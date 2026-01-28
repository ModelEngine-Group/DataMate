"""
标注生成模块
负责生成训练数据所需的JSON标注文件
"""

import os
import json
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
        "客户姓名",
        "身份证号码",
        "征信专线名称",
        "贷款银行",
        "贷款账户标识",
        "贷款开立日期",
        "贷款到期日期",
        "贷款期限",
        "授信额度",
        "应还款金额",
        "实还款金额",
        "利息结清状态",
        "贷款结清日期",
        "证明开具日期",
        "证明出具单位",
        "联系人姓名",
        "联系电话",
        "地址"
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
                "gpt": "这是一份贷款结清证明"
            },
            # 第2问：客户信息
            {
                "human": "证明中的客户姓名和身份证号码是什么？",
                "gpt": f"客户姓名是{data.get('客户姓名', '')}，身份证号码是{data.get('身份证号码', '')}"
            },
            # 第3问：征信专线
            {
                "human": "征信专线名称是什么？",
                "gpt": f"征信专线名称为{data.get('征信专线名称', '')}"
            },
            # 第4问：贷款银行和账户
            {
                "human": "贷款银行和贷款账户标识分别是多少？",
                "gpt": f"贷款银行为{data.get('贷款银行', '')}，贷款账户标识为{data.get('贷款账户标识', '')}"
            },
            # 第5问：金额信息
            {
                "human": "授信额度、应还款金额和实还款金额分别是多少？",
                "gpt": f"授信额度{data.get('授信额度', '')}，应还款金额{data.get('应还款金额', '')}，实还款金额{data.get('实还款金额', '')}"
            },
            # 第6问：时间信息
            {
                "human": "贷款什么时候开立、到期和结清的？贷款期限是多久？",
                "gpt": f"贷款于{data.get('贷款开立日期', '')}开立，{data.get('贷款到期日期', '')}到期，贷款期限{data.get('贷款期限', '')}，于{data.get('贷款结清日期', '')}结清"
            },
            # 第7问：证明信息
            {
                "human": "证明的开具日期和出具单位是什么？",
                "gpt": f"证明开具于{data.get('证明开具日期', '')}，出具单位为{data.get('证明出具单位', '')}"
            },
            # 第8问：联系方式
            {
                "human": "联系人的姓名和电话是多少？",
                "gpt": f"联系人为{data.get('联系人姓名', '')}，联系电话为{data.get('联系电话', '')}"
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
            "image": "images/" + Path(image_path).name,
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
            "image": "images/" + Path(image_path).name,
            "data": data,
            "metadata": {
                "document_type": "贷款结清证明",
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
                "description": "贷款结清证明数据集",
                "document_type": "贷款结清证明",
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


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("标注生成器测试")
    print("=" * 60)

    # 创建测试数据
    test_data = {
        "客户姓名": "张三",
        "身份证号码": "110101199001011234",
        "征信专线名称": "个人征信查询专线",
        "贷款银行": "中国工商银行",
        "贷款账户标识": "2024011500001234567",
        "贷款开立日期": "2020年01月15日",
        "贷款到期日期": "2025年01月15日",
        "贷款期限": "60个月",
        "授信额度": "150000元",
        "应还款金额": "165000元",
        "实还款金额": "165000元",
        "利息结清状态": "已结清",
        "贷款结清日期": "2024年06月15日",
        "证明开具日期": "2024年06月20日",
        "落款日期": "2024年06月20日",
        "证明出具单位": "中国工商银行股份有限公司",
        "联系人姓名": "李四",
        "联系电话": "010-12345678",
        "地址": "北京市朝阳区建国路88号"
    }

    builder = AnnotationBuilder(output_dir="annotations", format_type="multimodal")

    print("\n生成的标注示例:")
    print("-" * 60)

    annotation = builder.build_single(
        image_path="augmented_images/test.png",
        data=test_data,
        output_name="test_annotation"
    )

    print(json.dumps(annotation, ensure_ascii=False, indent=2))

    print("\n标注文件已保存到: annotations/test_annotation.json")
