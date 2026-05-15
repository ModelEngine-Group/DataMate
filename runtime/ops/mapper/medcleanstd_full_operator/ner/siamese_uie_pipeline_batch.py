"""
自定义 SiameseUIE Pipeline，支持批量输入和批量推理
基于 ModelScope 的 siamese_uie_pipeline.py 修改
"""
import json
from contextlib import nullcontext
from copy import deepcopy
from math import ceil
from typing import Any, Dict, List, Union

import torch

from modelscope.pipelines.nlp.siamese_uie_pipeline import SiameseUiePipeline


def _autocast_context(device):
    device = str(device)
    if device.startswith("npu") and hasattr(torch, "npu") and torch.npu.is_available():
        amp_mod = getattr(torch.npu, "amp", None)
        if amp_mod is not None and hasattr(amp_mod, "autocast"):
            return amp_mod.autocast()
        return nullcontext()
    if (device.startswith("cuda") or device.startswith("gpu")) and torch.cuda.is_available():
        return torch.cuda.amp.autocast()
    return nullcontext()


class SiameseUiePipelineBatch(SiameseUiePipeline):
    """
    支持批量输入的 SiameseUIE Pipeline
    继承自原始 Pipeline，重写 __call__ 方法以支持批量处理
    """
    
    def __call__(self, input: Union[str, List[str]], *args,
                 **kwargs) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        支持批量输入的调用方法（优化版：批量 tokenize）
        
        Args:
            input: 单个文本字符串或文本列表
            schema: 提取目标，例如 {'疾病': None, '症状': None}
        
        Returns:
            单个文本时返回: {'output': [...]}
            批量文本时返回: [{'output': [...]}, {'output': [...]}, ...]
        """
        # 判断是否为批量输入
        if isinstance(input, list):
            # 批量处理（优化：批量 tokenize）
            return self._process_batch(input, **kwargs)
        else:
            # 单个文本处理
            return self._process_single(input, **kwargs)
    
    def _process_batch(self, texts: List[str], **kwargs) -> List[Dict[str, Any]]:
        """
        批量处理多个文本（优化版：批量 tokenize）
        """
        # 准备模型
        if self.model:
            if not self._model_prepare:
                self.prepare_model()
        
        # 解析参数
        schema = kwargs.pop('schema')
        if type(schema) == str:
            schema = json.loads(schema)
        output_all_prefix = kwargs.pop('output_all_prefix', False)
        
        # 过滤空文本，记录原始索引
        non_empty_texts = []
        non_empty_indices = []
        for i, text in enumerate(texts):
            if text:
                non_empty_texts.append(text)
                non_empty_indices.append(i)
        
        if not non_empty_texts:
            return [{'output': []} for _ in texts]
        
        # 批量 tokenize（关键优化：一次性处理所有文本）
        # preprocessor 接受列表，返回 BatchEncoding 或列表
        # 原始代码使用 preprocessor([text])[0]，说明返回的是列表或可索引对象
        # 我们批量调用，然后提取每个文本的结果
        try:
            # 尝试批量 tokenize
            batch_tokenized = self.preprocessor(non_empty_texts)
            
            # 检查返回格式并提取每个文本的结果
            tokenized_texts = []
            if isinstance(batch_tokenized, (list, tuple)):
                # 如果返回列表，直接使用
                tokenized_texts = list(batch_tokenized)
            elif hasattr(batch_tokenized, '__getitem__') and hasattr(batch_tokenized, '__len__'):
                # 如果是可索引对象（如 BatchEncoding），尝试按索引提取
                try:
                    for i in range(len(non_empty_texts)):
                        tokenized_texts.append(batch_tokenized[i])
                except (TypeError, IndexError):
                    # 如果无法索引，回退到逐个处理
                    tokenized_texts = [self.preprocessor([text])[0] for text in non_empty_texts]
            else:
                # 未知格式，回退到逐个处理
                tokenized_texts = [self.preprocessor([text])[0] for text in non_empty_texts]
        except Exception as e:
            # 批量处理失败，回退到逐个处理
            print(f">>> [Warning] 批量 tokenize 失败，回退到逐个处理: {e}")
            tokenized_texts = [self.preprocessor([text])[0] for text in non_empty_texts]
        
        # 批量推理优化：批量处理 get_plm_sequence_output 和 hints
        # 虽然 forward 是递归的，但我们可以批量处理底层的模型推理
        results = []
        for text, tokenized_text in zip(non_empty_texts, tokenized_texts):
            pred_info_list = []
            prefix_info = []
            # 使用优化的批量 forward 方法
            self.forward_batch_optimized(text, tokenized_text, prefix_info, schema, 
                                        pred_info_list, output_all_prefix)
            results.append({'output': pred_info_list})
        
        # 处理空文本：在对应位置插入空结果
        final_results = [{'output': []} for _ in texts]
        for idx, result in zip(non_empty_indices, results):
            final_results[idx] = result
        
        return final_results
    
    def _process_single(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        处理单个文本（从原始 __call__ 方法提取）
        """
        # 移除批量检查
        kwargs.pop('batch_size', None)
        
        # 准备模型
        if self.model:
            if not self._model_prepare:
                self.prepare_model()
        
        # 解析参数
        schema = kwargs.pop('schema')
        if type(schema) == str:
            schema = json.loads(schema)
        output_all_prefix = kwargs.pop('output_all_prefix', False)
        
        # 预处理
        tokenized_text = self.preprocessor([text])[0]
        pred_info_list = []
        prefix_info = []
        
        # 前向推理
        self.forward(text, tokenized_text, prefix_info, schema, pred_info_list,
                     output_all_prefix)
        
        return {'output': pred_info_list}
    
    def forward_batch_optimized(self, text, tokenized_text, prefix_info, curr_schema_dict,
                                pred_info_list, output_all_prefix):
        """
        优化的批量 forward 方法
        批量处理 get_prefix_infos 中的模型推理部分
        """
        next_prefix_infos = self.get_prefix_infos_batch_optimized(
            text, tokenized_text, prefix_info, curr_schema_dict)
        
        for prefix_info in next_prefix_infos:
            next_schema_dict = curr_schema_dict[prefix_info[-1]['type']]
            if next_schema_dict is None:
                pred_info_list.append(prefix_info)
            else:
                if output_all_prefix:
                    pred_info_list.append(prefix_info)
                self.forward_batch_optimized(text, tokenized_text, prefix_info,
                                            next_schema_dict, pred_info_list,
                                            output_all_prefix)
    
    def get_prefix_infos_batch_optimized(self, text, tokenized_text, prefix_info,
                                        schema_types):
        """
        优化的批量 get_prefix_infos 方法
        批量处理 hints 的 tokenization 和模型推理
        """
        hints = []
        for st in schema_types:
            hint = ''
            for item in prefix_info:
                hint += f'{item["type"]}: {item["span"]}, '
            hint += f'{st}: '
            hints.append(hint)
        
        # 批量 tokenize hints（优化点1）
        tokenized_hints = self.preprocessor(
            hints, padding=True, truncation=True, max_length=self.hint_max_len)
        
        # 批量处理文本分段和序列输出（优化点2）
        all_valid_tokenized_data, all_tensor_data = self.get_tokenized_data_and_data_loader_batch_optimized(
            text, tokenized_text, hints, tokenized_hints)
        
        probs = []
        last_uuid = None
        all_pred_entities = []
        all_head_probs = []
        all_tail_probs = []
        
        # 批量推理（优化点3：已经通过 inference_batch_size 批量）
        with torch.no_grad():
            with _autocast_context(self.device):
                for batch_data in zip(*all_tensor_data):
                    batch_head_probs, batch_tail_probs = self.model.fast_inference(
                        *batch_data)
                    batch_head_probs, batch_tail_probs = batch_head_probs.tolist(
                    ), batch_tail_probs.tolist()  # (b, n, l)
                    all_head_probs += batch_head_probs
                    all_tail_probs += batch_tail_probs
        
        all_valid_tokenized_data.append({'id': 'WhatADifferentUUiD'})
        all_head_probs.append(None)
        all_tail_probs.append(None)
        
        for tokenized_sample, head_probs, tail_probs in zip(
                all_valid_tokenized_data, all_head_probs, all_tail_probs):
            uuid = tokenized_sample['id']
            prob = {
                'shift': tokenized_sample.get('shift', 0),
                'head': head_probs,  # (n, l)
                'tail': tail_probs
            }
            if last_uuid is not None and uuid != last_uuid:
                len_tokens = len(tokenized_text.offsets)
                head_probs = [-1] * len_tokens  # (n, l)
                tail_probs = [-1] * len_tokens
                for prob_tmp in probs:
                    shift = prob_tmp['shift']
                    head = prob_tmp['head']
                    tail = prob_tmp['tail']
                    len_sub = len(head)
                    for j in range(len_sub):
                        if j + shift < len_tokens:
                            head_probs[j + shift] = head[j] if head_probs[
                                j + shift] == -1 else (head_probs[j + shift]
                                                       + head[j]) / 2
                            tail_probs[j + shift] = tail[j] if tail_probs[
                                j + shift] == -1 else (tail_probs[j + shift]
                                                       + tail[j]) / 2
                offsets = tokenized_text.offsets
                pred_entities = self.get_entities(text, offsets, head_probs,
                                                  tail_probs)
                all_pred_entities.append(pred_entities)
                probs = []
            probs.append(prob)
            last_uuid = uuid
        
        next_prefix_infos = []
        for st, pred_entities in zip(schema_types, all_pred_entities):
            for e in pred_entities:
                pi = deepcopy(prefix_info)
                item = {'type': st, 'span': e['span'], 'offset': e['offset']}
                pi.append(item)
                next_prefix_infos.append(pi)
        return next_prefix_infos
    
    def get_tokenized_data_and_data_loader_batch_optimized(self, text, tokenized_text, hints, tokenized_hints):
        """
        优化的批量 tokenize_sample 方法
        批量处理多个 hints 的 tokenization
        """
        tokenized_data = []
        
        # 文本分段
        split_num = ceil(
            (len(tokenized_text) - self.max_len)
            / self.slide_len) + 1 if len(tokenized_text) > self.max_len else 1
        
        token_ids = [
            tokenized_text.ids[j * self.slide_len:j * self.slide_len
                               + self.max_len] for j in range(split_num)
        ]
        attention_masks = [
            tokenized_text.attention_mask[j * self.slide_len:j * self.slide_len
                                          + self.max_len]
            for j in range(split_num)
        ]
        
        if split_num > 1:
            token_ids = self._pad(token_ids, 0)
            attention_masks = self._pad(attention_masks, 0)
        
        token_ids = torch.tensor(
            token_ids, dtype=torch.long, device=self.device)
        attention_masks = torch.tensor(
            attention_masks, dtype=torch.long, device=self.device)
        
        # 批量获取序列输出（优化：合并所有分段的批量推理）
        batch_num = max(1, ceil(token_ids.size(0) / self.inference_batch_size))
        all_token_ids = torch.tensor_split(token_ids, batch_num)
        all_attention_masks = torch.tensor_split(attention_masks, batch_num)
        all_sequence_output = []

        with torch.no_grad():
            with _autocast_context(self.device):
                for token_ids_batch, attention_masks_batch in zip(all_token_ids,
                                                                 all_attention_masks):
                    sequence_output = self.model.get_plm_sequence_output(
                        token_ids_batch, attention_masks_batch)
                    all_sequence_output.append(sequence_output)
        
        all_sequence_output = torch.cat(all_sequence_output, dim=0)
        all_attention_masks = torch.cat(all_attention_masks, dim=0)
        
        # 为每个 hint 和每个分段创建数据项
        for i in range(len(hints)):
            hint = hints[i]
            # tokenized_hints 应该是列表或可索引对象
            # 原始代码使用 tokenized_hints[i]，说明是列表
            if isinstance(tokenized_hints, (list, tuple)):
                tokenized_hint = tokenized_hints[i]
            elif hasattr(tokenized_hints, '__getitem__'):
                try:
                    tokenized_hint = tokenized_hints[i]
                except (TypeError, IndexError):
                    # 如果无法索引，回退到逐个处理
                    hint_tokenized = self.preprocessor(
                        [hint], padding=True, truncation=True, max_length=self.hint_max_len)
                    tokenized_hint = hint_tokenized[0] if isinstance(hint_tokenized, list) else hint_tokenized
            else:
                # 回退：逐个处理
                hint_tokenized = self.preprocessor(
                    [hint], padding=True, truncation=True, max_length=self.hint_max_len)
                tokenized_hint = hint_tokenized[0] if isinstance(hint_tokenized, list) else hint_tokenized
            
            # 提取 hint 的 ids 和 attention_mask
            if hasattr(tokenized_hint, 'ids'):
                hint_ids = tokenized_hint.ids
                hint_attention_mask = tokenized_hint.attention_mask
            elif isinstance(tokenized_hint, dict):
                hint_ids = tokenized_hint.get('input_ids', tokenized_hint.get('ids', []))
                hint_attention_mask = tokenized_hint.get('attention_mask', [1] * len(hint_ids))
            else:
                # 最后回退：逐个处理
                hint_tokenized = self.preprocessor(
                    [hint], padding=True, truncation=True, max_length=self.hint_max_len)
                if isinstance(hint_tokenized, list):
                    hint_tokenized = hint_tokenized[0]
                hint_ids = hint_tokenized.ids if hasattr(hint_tokenized, 'ids') else hint_tokenized.get('input_ids', [])
                hint_attention_mask = hint_tokenized.attention_mask if hasattr(hint_tokenized, 'attention_mask') else hint_tokenized.get('attention_mask', [1] * len(hint_ids))
            
            for j in range(split_num):
                a = j * self.slide_len
                item = {
                    'id': hint + '--' + text,
                    'hint': hint,
                    'text': text,
                    'shift': a,
                    'sequence_output': all_sequence_output[j],
                    'hint_token_ids': hint_ids,
                    'attention_masks': all_attention_masks[j],
                    'cross_attention_masks': hint_attention_mask
                }
                tokenized_data.append(item)
        
        # 构建批量张量
        sequence_output = torch.stack(
            [item['sequence_output'] for item in tokenized_data])
        attention_masks = torch.stack(
            [item['attention_masks'] for item in tokenized_data])
        hint_token_ids = torch.tensor(
            [item['hint_token_ids'] for item in tokenized_data],
            dtype=torch.long,
            device=self.device)
        cross_attention_masks = torch.tensor(
            [item['cross_attention_masks'] for item in tokenized_data],
            dtype=torch.long,
            device=self.device)
        
        # 分批处理（利用 inference_batch_size）
        batch_num = max(1, ceil(sequence_output.size(0) / self.inference_batch_size))
        sequence_output = torch.tensor_split(sequence_output, batch_num)
        attention_masks = torch.tensor_split(attention_masks, batch_num)
        hint_token_ids = torch.tensor_split(hint_token_ids, batch_num)
        cross_attention_masks = torch.tensor_split(cross_attention_masks,
                                                   batch_num)
        
        return tokenized_data, (sequence_output, attention_masks,
                                hint_token_ids, cross_attention_masks)
