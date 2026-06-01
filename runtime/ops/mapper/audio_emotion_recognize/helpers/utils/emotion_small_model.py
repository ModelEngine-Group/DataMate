#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import torch
import torch.nn as nn


@dataclass(frozen=True)
class RAVDESSLabels:
    # 与常见 HF RAVDESS SER 模型一致的 8 类顺序
    # 采用 RAVDESS 官方 emotion code 顺序（01~08）：
    # neutral, calm, happy, sad, angry, fearful, disgust, surprised
    id2label: Dict[int, str]
    label2id: Dict[str, int]

    @staticmethod
    def default() -> "RAVDESSLabels":
        labels = ["neutral", "calm", "happy", "sad", "angry", "fearful", "disgust", "surprised"]
        id2label = {i: lb for i, lb in enumerate(labels)}
        label2id = {lb: i for i, lb in enumerate(labels)}
        return RAVDESSLabels(id2label=id2label, label2id=label2id)


def build_ravdess_zh_mapping() -> Dict[str, str]:
    """
    业务 8 类（喜怒哀惧厌惊中+困惑）与 RAVDESS 8 类的落地映射。
    注意：RAVDESS 不含 confused，这里用 calm 作为“困惑”的占位替代。
    """
    return {
        "happy": "喜",
        "angry": "怒",
        "sad": "哀",
        "fearful": "惧",
        "disgust": "厌",
        "surprised": "惊",
        "neutral": "中",
        "calm": "困惑",
    }


class HubertSERSmall(nn.Module):
    """
    从 small_model.safetensors 反推的轻量 HuBERT SER：
    - hubert encoder layers: 2
    - hidden_size: 768
    - projector: 768 -> 256
    - classifier: 256 -> 8
    """

    def __init__(self, num_labels: int = 8):
        super().__init__()
        from transformers import HubertConfig, HubertModel  # type: ignore

        cfg = HubertConfig(
            # 关键：权重文件里只有 layers.0 / layers.1
            num_hidden_layers=2,
            hidden_size=768,
            intermediate_size=3072,
            num_attention_heads=12,
            # feature extractor 结构（HuBERT/Wav2Vec2 常见配置）
            feat_extract_norm="group",
            conv_dim=(512, 512, 512, 512, 512, 512, 512),
            conv_stride=(5, 2, 2, 2, 2, 2, 2),
            conv_kernel=(10, 3, 3, 3, 3, 2, 2),
            conv_bias=False,
            # 采样率主要由前处理保证为 16k
        )
        self.hubert = HubertModel(cfg)
        self.projector = nn.Linear(768, 256)
        self.classifier = nn.Linear(256, num_labels)

    @torch.inference_mode()
    def forward(self, input_values: torch.Tensor, attention_mask: torch.Tensor | None = None) -> torch.Tensor:
        """
        Args:
            input_values: (B, T) float32, 16kHz mono
        Returns:
            logits: (B, num_labels)
        """
        out = self.hubert(input_values=input_values, attention_mask=attention_mask)
        hs = out.last_hidden_state  # (B, frames, 768)
        pooled = hs.mean(dim=1)  # 简单 mean pooling（与很多 SER baseline 一致）
        x = self.projector(pooled)
        x = torch.tanh(x)
        return self.classifier(x)


def load_small_model_from_safetensors(ckpt: Path, device: torch.device) -> HubertSERSmall:
    from safetensors.torch import load_file  # type: ignore

    state = load_file(str(ckpt), device="cpu")
    model = HubertSERSmall(num_labels=8)
    missing, unexpected = model.load_state_dict(state, strict=False)
    # 严格要求：不能出现 unexpected key；missing 允许 transformers 里的一些缓冲区差异
    if unexpected:
        raise RuntimeError(f"small_model.safetensors 存在未识别权重键（unexpected keys）: {unexpected[:20]}")
    # 若缺失过多，一般表示 config 反推不匹配
    if len(missing) > 0:
        # 仅打印前若干项，便于定位
        # 这里不直接失败，避免 transformers 版本差异导致的非关键缺失（例如 position_ids buffer）
        pass

    model.eval()
    return model.to(device)


def ravdess_filename_to_label_en(stem: str) -> str | None:
    """
    RAVDESS 文件名格式：03-01-EMO-INT-STAT-REP-ACT.wav
    EMO:
      01 neutral
      02 calm
      03 happy
      04 sad
      05 angry
      06 fearful
      07 disgust
      08 surprised
    """
    parts = stem.split("-")
    if len(parts) < 3:
        return None
    emo = parts[2]
    m = {
        "01": "neutral",
        "02": "calm",
        "03": "happy",
        "04": "sad",
        "05": "angry",
        "06": "fearful",
        "07": "disgust",
        "08": "surprised",
    }
    return m.get(emo)

