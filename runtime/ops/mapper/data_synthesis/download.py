import argparse
import os
from pathlib import Path

from modelscope import snapshot_download


def _ensure_writable_dir(path: str) -> Path:
    p = Path(path).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)
    if not os.access(p, os.W_OK):
        raise PermissionError(f"目录不可写: {p}")
    return p


def main():
    parser = argparse.ArgumentParser(description="下载 ModelScope 模型")
    parser.add_argument(
        "--model_id",
        default="testUser/Qwen3-1.7b-Medical-R1-sft",
        help="ModelScope 模型 ID"
    )
    parser.add_argument(
        "--cache_dir",
        default="/mnt/nvme0n1/home/pjj/.cache/modelscope",
        help="模型缓存目录（必须可写）"
    )
    parser.add_argument(
        "--download_train_artifacts",
        action="store_true",
        help="是否下载训练中间文件（optimizer/rng_state/trainer_state 等）"
    )
    args = parser.parse_args()

    cache_dir = _ensure_writable_dir(args.cache_dir)
    print(f"📦 准备下载模型: {args.model_id}")
    print(f"📂 缓存目录: {cache_dir}")

    # 默认只下推理需要的文件，避免拉取超大训练中间产物
    allow_patterns = None
    ignore_patterns = None
    if not args.download_train_artifacts:
        allow_patterns = [
            "*.json",
            "*.model",
            "*.txt",
            "*.safetensors",
            "*.bin",
            "tokenizer*",
            "vocab*",
            "merges*",
            "configuration*",
            "README*",
        ]
        ignore_patterns = [
            "optimizer.pt",
            "rng_state.pth",
            "trainer_state.json",
            "scheduler.pt",
            "training_args.bin",
            "*.ckpt",
        ]

    model_dir = snapshot_download(
        args.model_id,
        cache_dir=str(cache_dir),
        allow_patterns=allow_patterns,
        ignore_patterns=ignore_patterns,
    )

    print(f"✅ 模型已下载到: {model_dir}")


if __name__ == "__main__":
    main()