#!/usr/bin/env python3
"""
GTCRN 本地智能降噪工具

特点：
- 优先使用 ONNXRuntime 做推理，适合本机快速部署
- 支持单个音频文件或目录批量处理
- 输入音频会被统一到 16k / mono / float32
- 输出为降噪后的 wav

说明：
- 当前仓库只包含 GTCRN 结构代码，不包含训练好的权重文件。
- 你需要把训练好的 .onnx / .tar / .pt 放到本地后再指定给 --model。
- 若给的是 .tar / .pt，可选择 --export_onnx 先导出为 ONNX，再用 ONNXRuntime 推理。
"""

import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

sys.path.insert(0, str(PROJECT_ROOT / "src" / "utils"))

try:
    from color_utils import info, warning, error, ok, success, header  # type: ignore

    def print_info(msg: str):
        print(info(msg))

    def print_warning(msg: str):
        print(warning(msg))

    def print_error(msg: str):
        print(error(msg))

    def print_ok(msg: str):
        print(ok(msg))

    def print_success(msg: str):
        print(success(msg))

    def print_header(msg: str):
        print(header(msg))

except Exception:
    def print_info(msg: str):
        print(f"[INFO] {msg}")

    def print_warning(msg: str):
        print(f"[WARNING] {msg}")

    def print_error(msg: str):
        print(f"[ERROR] {msg}")

    def print_ok(msg: str):
        print(f"[OK] {msg}")

    def print_success(msg: str):
        print(f"[SUCCESS] {msg}")

    def print_header(msg: str):
        print(f"=== {msg} ===")


def _import_audio_backend():
    import soundfile as sf  # type: ignore
    import torch  # type: ignore
    return sf, torch


def _find_audio_files(input_path: Path) -> List[Path]:
    exts = {".wav", ".flac", ".mp3", ".aac", ".m4a", ".ogg", ".webm"}
    if input_path.is_file():
        return [input_path]
    files = []
    for p in input_path.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            files.append(p)
    return sorted(files)


def load_audio_mono_16k(path: Path) -> np.ndarray:
    """
    读取任意常见音频并转换为 16k 单声道 float32。
    """
    sf, torch = _import_audio_backend()
    data, sr = sf.read(str(path), always_2d=False)
    if data.ndim > 1:
        data = np.mean(data, axis=1)
    data = data.astype(np.float32)
    if sr != 16000:
        # 使用 torch 做重采样，减少额外依赖差异
        wav = torch.from_numpy(data).float()[None, None, :]
        resampler = torch.nn.functional.interpolate
        # 简化实现：通过线性插值做基础重采样，够用于前端降噪预处理
        new_len = int(round(wav.shape[-1] * 16000.0 / float(sr)))
        wav = torch.nn.functional.interpolate(wav, size=new_len, mode="linear", align_corners=False)
        data = wav[0, 0].cpu().numpy()
    return data.astype(np.float32)


def stft_complex(x: np.ndarray, n_fft: int = 512, hop_length: int = 256, win_length: int = 512):
    """
    将波形转为 GTCRN 需要的复数谱输入:
    返回 shape = (1, F, T, 2)
    """
    sf, torch = _import_audio_backend()
    _ = sf
    wav = torch.from_numpy(x).float()
    window = torch.hann_window(win_length).pow(0.5)
    spec = torch.stft(
        wav,
        n_fft=n_fft,
        hop_length=hop_length,
        win_length=win_length,
        window=window,
        return_complex=False,
        center=True,
    )  # (F, T, 2)
    spec = spec.unsqueeze(0)  # (1, F, T, 2)
    return spec.cpu().numpy().astype(np.float32)


def istft_complex(spec: np.ndarray, n_fft: int = 512, hop_length: int = 256, win_length: int = 512):
    """
    将 GTCRN 输出的复数谱还原为波形。
    输入 shape = (1, F, T, 2) 或 (F, T, 2)
    """
    sf, torch = _import_audio_backend()
    _ = sf
    if spec.ndim == 4:
        spec = spec[0]
    # spec: (F, T, 2) -> complex tensor
    spec_t = torch.from_numpy(spec).float()
    spec_t = torch.view_as_complex(spec_t.contiguous())
    window = torch.hann_window(win_length).pow(0.5)
    wav = torch.istft(
        spec_t,
        n_fft=n_fft,
        hop_length=hop_length,
        win_length=win_length,
        window=window,
        center=True,
    )
    return wav.cpu().numpy().astype(np.float32)


class OnnxGtcrnDenoiser:
    """
    使用 ONNXRuntime 推理 GTCRN。
    说明：
    - GTCRN 是流式结构，ONNX 输入/输出包含 cache。
    - 这里按 1 帧一帧地做流式推理，然后重建为完整波形。
    """

    def __init__(self, model_path: Path):
        try:
            import onnxruntime as ort  # type: ignore
        except Exception as e:
            raise RuntimeError("未安装 onnxruntime，请先安装 onnxruntime 或 onnxruntime-gpu") from e

        if not model_path.exists():
            raise FileNotFoundError(f"ONNX 模型不存在: {model_path}")

        self.model_path = model_path
        self.session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
        self.input_names = [i.name for i in self.session.get_inputs()]
        self.output_names = [o.name for o in self.session.get_outputs()]

        # 固定 cache 形状来自 GTCRN stream 版本导出
        self.conv_cache = np.zeros([2, 1, 16, 16, 33], dtype=np.float32)
        self.tra_cache = np.zeros([2, 3, 1, 1, 16], dtype=np.float32)
        self.inter_cache = np.zeros([2, 1, 33, 16], dtype=np.float32)

    def denoise(self, wav: np.ndarray) -> np.ndarray:
        spec = stft_complex(wav)  # (1, F, T, 2)
        outputs = []
        conv_cache = self.conv_cache.copy()
        tra_cache = self.tra_cache.copy()
        inter_cache = self.inter_cache.copy()

        # 按时间帧逐帧推理
        for i in range(spec.shape[2]):
            mix = spec[:, :, i:i+1, :].astype(np.float32)
            out_i, conv_cache, tra_cache, inter_cache = self.session.run(
                [],
                {
                    "mix": mix,
                    "conv_cache": conv_cache,
                    "tra_cache": tra_cache,
                    "inter_cache": inter_cache,
                },
            )
            outputs.append(out_i)

        out_spec = np.concatenate(outputs, axis=2)  # (1, F, T, 2)
        wav_out = istft_complex(out_spec)
        return wav_out


def _resolve_model(model: Path, export_dir: Optional[Path] = None) -> Path:
    """
    解析模型路径：
    - 如果是 .onnx，直接返回
    - 如果是 .tar/.pt，可选导出为 ONNX（需要你本地提供训练权重）
    """
    if model.suffix.lower() == ".onnx":
        return model
    if model.suffix.lower() in {".tar", ".pt", ".pth"}:
        raise RuntimeError("算子不再打包 GTCRN 源码，请预先导出 ONNX 并把 --model 指向 .onnx 文件。")
    raise ValueError(f"不支持的模型格式: {model.suffix}")


def process_one(input_file: Path, output_file: Path, denoiser: OnnxGtcrnDenoiser) -> None:
    sf, _ = _import_audio_backend()
    wav = load_audio_mono_16k(input_file)
    enhanced = denoiser.denoise(wav)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_file), enhanced, 16000)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="GTCRN 本地智能降噪工具（优先 ONNXRuntime）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 单文件降噪（ONNX 模型）
  python -m src.utils.gtcrn_denoise --input ./a.wav --model ./models/gtcrn/gtcrn.onnx --output ./out.wav

  # 目录批处理
  python -m src.utils.gtcrn_denoise --input ./input_dir --model ./models/gtcrn/gtcrn.onnx --output ./denoised_dir

  # 如果你手里是 .tar/.pt 权重，可尝试导出 ONNX（需要本地可加载权重）
  python -m src.utils.gtcrn_denoise --input ./a.wav --model ./weights/model_trained_on_dns3.tar --export_dir ./models/gtcrn_onnx --output ./out.wav
        """,
    )
    parser.add_argument("--input", required=True, help="输入音频文件或目录")
    parser.add_argument("--model", required=True, help="GTCRN 模型路径（.onnx/.tar/.pt/.pth）")
    parser.add_argument("--output", required=True, help="输出 wav 文件或目录")
    parser.add_argument("--export_dir", default=None, help="若输入为 .tar/.pt，则导出 ONNX 的目录")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    model_path = Path(args.model).resolve()
    output_path = Path(args.output).resolve()
    export_dir = Path(args.export_dir).resolve() if args.export_dir else None

    print_header("GTCRN 智能降噪")
    print_info(f"输入: {input_path}")
    print_info(f"模型: {model_path}")
    print_info(f"输出: {output_path}")

    try:
        resolved_model = _resolve_model(model_path, export_dir=export_dir)
        print_info(f"使用模型: {resolved_model}")
        denoiser = OnnxGtcrnDenoiser(resolved_model)
    except Exception as e:
        print_error(f"初始化失败: {e}")
        return 1

    files = _find_audio_files(input_path)
    if not files:
        print_warning("未找到可处理的音频文件")
        return 0

    try:
        if input_path.is_file():
            if output_path.suffix.lower() != ".wav":
                output_path = output_path.with_suffix(".wav")
            process_one(files[0], output_path, denoiser)
            print_success(f"完成: {output_path}")
        else:
            output_path.mkdir(parents=True, exist_ok=True)
            for f in files:
                out_file = output_path / f"{f.stem}.wav"
                print_info(f"降噪: {f.name} -> {out_file.name}")
                process_one(f, out_file, denoiser)
            print_success(f"批量完成，输出目录: {output_path}")
    except Exception as e:
        print_error(f"处理失败: {e}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
