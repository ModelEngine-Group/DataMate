# -*- coding: utf-8 -*-
"""
MedCleanStd 医疗文本清洗标准化算子
支持文档解析、文本纠错、NER 实体识别、术语标准化
"""

from typing import Dict, Any, List
import json
import re
import os

from datamate.core.base_op import Mapper


class MedCleanStdMapper(Mapper):
    """
    医疗文本清洗标准化算子

    功能：
    1. 文档解析：解析 docx/txt 格式，提取文本和位置信息
    2. 文本纠错：混淆集匹配 + 可选拼音纠错
    3. NER 实体识别：基于 SiameseUIE 抽取疾病、症状、药品等实体
    4. 术语标准化：将实体映射到 ICD-10 标准术语
    """

    def __init__(self, *args, **kwargs):
        """
        初始化算子参数
        """
        super().__init__(*args, **kwargs)

        # ===== 纠错配置 =====
        self.use_proper_corrector = kwargs.get('use_proper_corrector', False)
        self.proper_segment_length = int(kwargs.get('proper_segment_length', 100))
        self.proper_max_text_length = int(kwargs.get('proper_max_text_length', 200))

        # ===== NER 配置 =====
        ner_schema_str = kwargs.get('ner_schema', '疾病，症状')
        if isinstance(ner_schema_str, str):
            self.ner_schema = [s.strip() for s in ner_schema_str.split(',') if s.strip()]
        else:
            self.ner_schema = ner_schema_str if ner_schema_str else ['疾病', '症状']
        self.ner_inference_batch_size = int(kwargs.get('ner_inference_batch_size', 64))

        # ===== 分句配置 =====
        self.max_sentences = int(kwargs.get('max_sentences', 80))

        # ===== 标准化配置 =====
        self.use_l1_cache = kwargs.get('use_l1_cache', True)
        self.normalizer_batch_size = int(kwargs.get('normalizer_batch_size', 64))
        self.normalizer_search_batch_size = int(kwargs.get('normalizer_search_batch_size', 2000))
        self.normalizer_similarity_threshold = float(kwargs.get('normalizer_similarity_threshold', 0.75))

        # ===== 实体过滤配置 =====
        self.max_entity_length = int(kwargs.get('max_entity_length', 50))

        # ===== 性能优化配置 =====
        self.use_pipeline_mode = kwargs.get('use_pipeline_mode', True)

        # 延迟初始化组件
        self._parser = None
        self._corrector = None
        self._ner = None
        self._normalizer = None
        self._initialized = False

    def _init_components(self):
        """
        延迟初始化所有组件
        """
        if self._initialized:
            return

        try:
            from myparser.parser import DocParser
            from mycorrector.corrector import MedicalCorrector
            from ner.ner_npu import SiameseNER
            from normalizer.normalizer_npu import MedicalNormalizer

            script_dir = os.path.dirname(os.path.abspath(__file__))

            # 设置 normalizer 模块的数据目录为算子目录下的 normalizer
            import normalizer.normalizer_npu as normalizer_module
            normalizer_module.DATA_DIR = os.path.join(script_dir, "normalizer")

            # 1. 初始化解析器
            self._parser = DocParser()

            # 2. 初始化纠错器
            self._corrector = MedicalCorrector(
                use_proper_corrector=self.use_proper_corrector,
                segment_length=self.proper_segment_length,
                max_text_length=self.proper_max_text_length
            )

            # 3. 初始化 NER 模型
            model_dir = os.path.join(script_dir, "model", "SiameseUIE")
            self._ner = SiameseNER(
                model_dir=model_dir,
                inference_batch_size=self.ner_inference_batch_size
            )

            # 4. 初始化标准化器
            normalizer_model_dir = os.path.join(script_dir, "model", "bge-small-zh-v1.5")
            self._normalizer = MedicalNormalizer(
                model_dir=normalizer_model_dir,
                batch_size=self.normalizer_batch_size,
                use_l1_cache=self.use_l1_cache,
                search_batch_size=self.normalizer_search_batch_size,
                similarity_threshold=self.normalizer_similarity_threshold
            )

            self._initialized = True

        except ImportError as e:
            raise RuntimeError(f"导入组件失败：{e}")
        except Exception as e:
            raise RuntimeError(f"初始化组件失败：{e}")

    def _split_by_sentences(self, text: str, max_sentences: int = 80) -> List[str]:
        """
        将文本按句子切分，然后按最大句子数限制分组
        """
        if not text:
            return []

        sentences = re.split(r'([.!?;.!\n])', text)

        complete_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i]
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]
            if sentence.strip():
                complete_sentences.append(sentence)

        if len(sentences) % 2 == 1 and sentences[-1].strip():
            complete_sentences.append(sentences[-1])

        if not complete_sentences:
            return [text] if text.strip() else []

        groups = []
        current_group = []
        current_sentence_count = 0

        for sentence in complete_sentences:
            current_group.append(sentence)
            current_sentence_count += 1
            if current_sentence_count >= max_sentences:
                groups.append(''.join(current_group))
                current_group = []
                current_sentence_count = 0

        if current_group:
            groups.append(''.join(current_group))

        return groups if groups else [text]

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑

        :param sample: 输入的数据样本，包含 text 字段
        :return: 处理后的数据样本，包含原始文本、纠错后文本、实体列表、标准化结果
        """
        if 'sourceFileSize' not in sample or sample.get('sourceFileSize') is None:
            sample['sourceFileSize'] = 0

        try:
            self._init_components()

            input_text = sample.get('text', '')
            if not input_text:
                sample['medclean_error'] = '输入文本为空'
                sample['sourceFileSize'] = 0
                return sample

            # Step 1: 文档解析
            if os.path.exists(input_text):
                clean_text, position_map = self._parser.parse(
                    input_text, return_position_map=True
                )
                sample['parsed_text'] = clean_text
            else:
                clean_text = input_text
                position_map = {}

            # Step 2: 文本纠错
            corrected_text, correction_info = self._corrector.correct(clean_text)
            sample['corrected_text'] = corrected_text
            sample['correction_errors'] = correction_info.get('errors', [])

            # Step 3: 分句处理
            sub_texts = self._split_by_sentences(corrected_text, self.max_sentences)

            chunk_offsets = []
            current_offset = 0
            for sub_text in sub_texts:
                chunk_offsets.append(current_offset)
                current_offset += len(sub_text)

            # Step 4: NER 实体识别
            all_entities = []
            for chunk_id, sub_text in enumerate(sub_texts):
                chunk_entities = self._ner.extract(sub_text, schema=self.ner_schema)

                for entity in chunk_entities:
                    entity['chunk_id'] = chunk_id
                    entity['chunk_offset'] = chunk_offsets[chunk_id]
                    entity['global_start'] = chunk_offsets[chunk_id] + entity.get('start', 0)
                    entity['global_end'] = chunk_offsets[chunk_id] + entity.get('end', 0)

                all_entities.extend(chunk_entities)

            sample['entities'] = all_entities
            sample['entity_count'] = len(all_entities)

            # Step 5: 术语标准化
            entity_texts = [e['text'] for e in all_entities]
            normalized_results = self._normalizer.normalize(entity_texts)

            for entity, norm_result in zip(all_entities, normalized_results):
                entity['normalized'] = norm_result

            # Step 6: 过滤长实体
            filtered_entities = []
            dropped_count = 0
            for entity in all_entities:
                length = entity.get('global_end', 0) - entity.get('global_start', 0)
                if length <= self.max_entity_length:
                    filtered_entities.append(entity)
                else:
                    dropped_count += 1

            sample['filtered_entities'] = filtered_entities
            sample['filtered_entity_count'] = len(filtered_entities)
            sample['dropped_entities_count'] = dropped_count

            # 添加处理元数据
            sample['medclean_metadata'] = {
                'original_length': len(input_text),
                'corrected_length': len(corrected_text),
                'chunk_count': len(sub_texts),
                'ner_schema': self.ner_schema,
                'use_proper_corrector': self.use_proper_corrector,
                'use_l1_cache': self.use_l1_cache,
                'use_pipeline_mode': self.use_pipeline_mode,
                'ner_inference_batch_size': self.ner_inference_batch_size,
                'normalizer_batch_size': self.normalizer_batch_size
            }

            if os.path.exists(input_text):
                sample['sourceFileSize'] = os.path.getsize(input_text)
            else:
                sample['sourceFileSize'] = len(input_text)

            return sample

        except Exception as e:
            sample['medclean_error'] = str(e)
            sample['entities'] = []
            try:
                input_text = sample.get('text', '')
                if os.path.exists(input_text):
                    sample['sourceFileSize'] = os.path.getsize(input_text)
                else:
                    sample['sourceFileSize'] = len(input_text) if input_text else 0
            except Exception:
                sample['sourceFileSize'] = 0
            return sample
