"""
Vendored minimal AST (Audio Spectrogram Transformer) model definition.

来源：YuanGongND/ast（Interspeech 2021, AST: Audio Spectrogram Transformer）
为了适配本工程：
- 不在运行时下载任何权重（无外网依赖）
- 不强制 timm 版本（尽量兼容常见版本）
- 不使用 CUDA autocast 装饰器（避免在 NPU/CPU 环境报错）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

import torch
import torch.nn as nn

try:
    import timm  # type: ignore
    from timm.models.layers import to_2tuple, trunc_normal_  # type: ignore
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "缺少依赖 timm，AST 模型无法创建。请在环境中安装 timm（建议与 AST 兼容的版本）。\n"
        "例如：pip install timm"
    ) from e


class PatchEmbed(nn.Module):
    """Override timm PatchEmbed: relax input shape constraint."""

    def __init__(self, img_size=224, patch_size=16, in_chans=3, embed_dim=768):
        super().__init__()
        img_size = to_2tuple(img_size)
        patch_size = to_2tuple(patch_size)
        num_patches = (img_size[1] // patch_size[1]) * (img_size[0] // patch_size[0])
        self.img_size = img_size
        self.patch_size = patch_size
        self.num_patches = num_patches
        self.proj = nn.Conv2d(in_chans, embed_dim, kernel_size=patch_size, stride=patch_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.proj(x).flatten(2).transpose(1, 2)
        return x


class ASTModel(nn.Module):
    """
    AST model (inference use).

    Input: [batch, time_frame_num, frequency_bins] => e.g. [B, 1024, 128]
    Output: [batch, label_dim] raw logits (no sigmoid/softmax)
    """

    def __init__(
        self,
        *,
        label_dim: int = 527,
        fstride: int = 10,
        tstride: int = 10,
        input_fdim: int = 128,
        input_tdim: int = 1024,
        imagenet_pretrain: bool = True,
        model_size: str = "base384",
        verbose: bool = False,
    ) -> None:
        super().__init__()

        if verbose:
            print("---------------AST Model Summary---------------", flush=True)
            print(
                f"ImageNet pretraining: {imagenet_pretrain}, model_size={model_size}",
                flush=True,
            )

        # override timm input shape restriction
        # timm 0.x: timm.models.vision_transformer.PatchEmbed
        # timm 1.x: timm.layers.patch_embed.PatchEmbed
        try:
            timm.models.vision_transformer.PatchEmbed = PatchEmbed  # type: ignore[attr-defined]
        except Exception:
            pass
        try:
            import timm.layers  # type: ignore

            timm.layers.PatchEmbed = PatchEmbed  # type: ignore[attr-defined]
        except Exception:
            pass
        try:
            import timm.layers.patch_embed as _pe  # type: ignore

            _pe.PatchEmbed = PatchEmbed  # type: ignore[attr-defined]
        except Exception:
            pass

        if model_size == "tiny224":
            self.v = timm.create_model(
                "vit_deit_tiny_distilled_patch16_224", pretrained=imagenet_pretrain
            )
        elif model_size == "small224":
            self.v = timm.create_model(
                "vit_deit_small_distilled_patch16_224", pretrained=imagenet_pretrain
            )
        elif model_size == "base224":
            self.v = timm.create_model(
                "vit_deit_base_distilled_patch16_224", pretrained=imagenet_pretrain
            )
        elif model_size == "base384":
            # timm 新版本(>=1.x)模型命名与 AST 原仓库不同，这里做兼容回退
            cand = [
                "vit_deit_base_distilled_patch16_384",  # AST 原仓库
                "deit_base_distilled_patch16_384",  # timm 1.x
                "deit_base_patch16_384",  # 无蒸馏token的备选（仍可跑推理，但权重需匹配）
            ]
            last_err: Exception | None = None
            for name in cand:
                try:
                    self.v = timm.create_model(name, pretrained=imagenet_pretrain)
                    break
                except Exception as e:
                    last_err = e
                    continue
            else:
                raise RuntimeError(f"timm 中未找到可用的 deit 384 模型名，尝试过: {cand}") from last_err
        else:
            raise ValueError("model_size 必须是 tiny224/small224/base224/base384 之一。")

        self.original_num_patches = int(self.v.patch_embed.num_patches)
        self.original_hw = int(self.original_num_patches**0.5)
        self.original_embedding_dim = int(self.v.pos_embed.shape[2])

        # timm 1.x 的 PatchEmbed 会强校验输入 img_size，这里直接替换为 AST 版本（无 shape assert）
        # 注意：后续会重新设置 num_patches / proj / pos_embed。
        self.v.patch_embed = PatchEmbed(
            img_size=(int(input_fdim), int(input_tdim)),
            patch_size=16,
            in_chans=1,
            embed_dim=self.original_embedding_dim,
        )

        self.mlp_head = nn.Sequential(
            nn.LayerNorm(self.original_embedding_dim),
            nn.Linear(self.original_embedding_dim, int(label_dim)),
        )

        f_dim, t_dim = self.get_shape(fstride, tstride, input_fdim, input_tdim)
        num_patches = int(f_dim * t_dim)
        self.v.patch_embed.num_patches = num_patches
        if verbose:
            print(f"frequency stride={fstride}, time stride={tstride}", flush=True)
            print(f"patches={num_patches} (f_dim={f_dim}, t_dim={t_dim})", flush=True)

        # projection layer: 1 channel input
        new_proj = nn.Conv2d(
            1,
            self.original_embedding_dim,
            kernel_size=(16, 16),
            stride=(int(fstride), int(tstride)),
        )
        if imagenet_pretrain:
            # sum RGB weights -> single-channel init
            new_proj.weight = nn.Parameter(
                torch.sum(self.v.patch_embed.proj.weight, dim=1).unsqueeze(1)
            )
            new_proj.bias = self.v.patch_embed.proj.bias
        self.v.patch_embed.proj = new_proj

        # positional embedding adaptation
        if imagenet_pretrain:
            # skip cls & dist tokens, reshape pos embed to 2D
            pos = (
                self.v.pos_embed[:, 2:, :]
                .detach()
                .reshape(1, self.original_num_patches, self.original_embedding_dim)
                .transpose(1, 2)
                .reshape(1, self.original_embedding_dim, self.original_hw, self.original_hw)
            )
            # time dim
            if t_dim <= self.original_hw:
                start = int(self.original_hw / 2) - int(t_dim / 2)
                pos = pos[:, :, :, start : start + int(t_dim)]
            else:
                pos = torch.nn.functional.interpolate(pos, size=(self.original_hw, int(t_dim)), mode="bilinear")
            # freq dim
            if f_dim <= self.original_hw:
                start = int(self.original_hw / 2) - int(f_dim / 2)
                pos = pos[:, :, start : start + int(f_dim), :]
            else:
                pos = torch.nn.functional.interpolate(pos, size=(int(f_dim), int(t_dim)), mode="bilinear")

            pos = pos.reshape(1, self.original_embedding_dim, num_patches).transpose(1, 2)
            self.v.pos_embed = nn.Parameter(
                torch.cat([self.v.pos_embed[:, :2, :].detach(), pos], dim=1)
            )
        else:
            self.v.pos_embed = nn.Parameter(
                torch.zeros(1, self.v.patch_embed.num_patches + 2, self.original_embedding_dim)
            )
            trunc_normal_(self.v.pos_embed, std=0.02)

    def get_shape(
        self, fstride: int, tstride: int, input_fdim: int = 128, input_tdim: int = 1024
    ) -> Tuple[int, int]:
        test_input = torch.randn(1, 1, int(input_fdim), int(input_tdim))
        test_proj = nn.Conv2d(
            1,
            self.original_embedding_dim,
            kernel_size=(16, 16),
            stride=(int(fstride), int(tstride)),
        )
        test_out = test_proj(test_input)
        return int(test_out.shape[2]), int(test_out.shape[3])

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, T, F) -> (B, 1, F, T)
        x = x.unsqueeze(1).transpose(2, 3)
        bsz = x.shape[0]

        x = self.v.patch_embed(x)
        cls_tokens = self.v.cls_token.expand(bsz, -1, -1)
        dist_token = self.v.dist_token.expand(bsz, -1, -1)
        x = torch.cat((cls_tokens, dist_token, x), dim=1)
        x = x + self.v.pos_embed
        x = self.v.pos_drop(x)
        for blk in self.v.blocks:
            x = blk(x)
        x = self.v.norm(x)
        x = (x[:, 0] + x[:, 1]) / 2
        x = self.mlp_head(x)
        return x


@dataclass(frozen=True)
class ASTConfig:
    label_dim: int = 527
    fstride: int = 10
    tstride: int = 10
    input_fdim: int = 128
    input_tdim: int = 1024
    model_size: str = "base384"


def _strip_module_prefix(state: Dict[str, Any]) -> Dict[str, Any]:
    if any(k.startswith("module.") for k in state.keys()):
        return {k[len("module.") :]: v for k, v in state.items()}
    return state


def load_ast_from_pth(
    *,
    checkpoint_path: str,
    device: torch.device,
    cfg: ASTConfig = ASTConfig(),
) -> ASTModel:
    """
    从本地 .pth 加载 AST（AudioSet 0.4593 权重）用于推理。
    兼容：
    - 直接 state_dict
    - 包在 dict 里（如 {'state_dict': ...} / {'model': ...}）
    - DataParallel 前缀 module.*
    """
    model = ASTModel(
        label_dim=cfg.label_dim,
        fstride=cfg.fstride,
        tstride=cfg.tstride,
        input_fdim=cfg.input_fdim,
        input_tdim=cfg.input_tdim,
        imagenet_pretrain=False,
        model_size=cfg.model_size,
        verbose=False,
    )
    obj = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    if isinstance(obj, dict) and "state_dict" in obj and isinstance(obj["state_dict"], dict):
        state = obj["state_dict"]
    elif isinstance(obj, dict) and "model" in obj and isinstance(obj["model"], dict):
        state = obj["model"]
    elif isinstance(obj, dict) and all(isinstance(k, str) for k in obj.keys()):
        # assume it's a raw state_dict
        state = obj
    else:
        raise ValueError("不支持的 checkpoint 格式，无法解析 state_dict。")

    state = _strip_module_prefix(state)
    missing, unexpected = model.load_state_dict(state, strict=False)
    if missing:
        # 一般不会影响推理（例如部分 buffer），但需要显式暴露出来方便排障
        print(f"[WARN] AST missing keys: {len(missing)}", flush=True)
    if unexpected:
        print(f"[WARN] AST unexpected keys: {len(unexpected)}", flush=True)
    model.to(device)
    model.eval()
    return model

