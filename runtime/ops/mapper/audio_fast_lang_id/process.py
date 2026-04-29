# -- encoding: utf-8 --

import time
from pathlib import Path
from typing import Dict, Any

from loguru import logger

from datamate.core.base_op import Mapper


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[6]


def _audio_preprocessor_root() -> Path:
    return _repo_root() / "audio_preprocessor"


class AudioFastLangId(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_source = str(kwargs.get("modelSource", "")).strip()
        self.model_savedir = str(kwargs.get("modelSavedir", "")).strip()
        self.device = str(kwargs.get("device", "cpu")).strip()
        self.batch_size = int(float(kwargs.get("batchSize", 1)))
        self.max_seconds = float(kwargs.get("maxSeconds", 3.0))

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        start = time.time()

        ap_root = _audio_preprocessor_root()
        if not ap_root.exists():
            raise FileNotFoundError(f"audio_preprocessor 不存在: {ap_root}")

        wav_path = Path(sample.get(self.filepath_key, "")).resolve()
        if not wav_path.exists():
            raise FileNotFoundError(f"输入音频不存在: {wav_path}")

        import sys

        utils_dir = ap_root / "src" / "utils"
        if str(utils_dir) not in sys.path:
            sys.path.insert(0, str(utils_dir))

        import fast_lang_id  # type: ignore

        # 组装 args，直接复用其 main() 的 CLI 解析逻辑
        argv_backup = sys.argv[:]
        try:
            out_path = (ap_root / "output_data" / "lid" / "item_with_lang.list").resolve()
            in_list = (ap_root / "output_data" / "lid" / "_single_item.list").resolve()
            in_list.parent.mkdir(parents=True, exist_ok=True)
            in_list.write_text(
                f'{{"key":"{wav_path.stem}","wav":"{str(wav_path)}","txt":""}}\\n',
                encoding="utf-8",
            )

            sys.argv = [
                sys.argv[0],
                "--input_list",
                str(in_list),
                "--output",
                str(out_path),
                "--device",
                self.device,
                "--batch_size",
                str(max(1, self.batch_size)),
                "--max_seconds",
                str(self.max_seconds),
            ]
            if self.model_source:
                sys.argv += ["--model_source", self.model_source]
            if self.model_savedir:
                sys.argv += ["--model_savedir", self.model_savedir]

            rc = fast_lang_id.main()
            if rc != 0:
                raise RuntimeError(f"fast_lang_id 失败，返回码: {rc}")

            # 读取输出第一行
            if not out_path.exists():
                raise RuntimeError(f"LID 输出不存在: {out_path}")
            line = out_path.read_text(encoding="utf-8").splitlines()[0].strip()
            import json

            d = json.loads(line)
            lang = str(d.get("lang", "en"))
        finally:
            sys.argv = argv_backup

        ext = sample.get(self.ext_params_key, {})
        if not isinstance(ext, dict):
            ext = {"_raw": ext}
        ext["audio_lid"] = {"lang": lang}
        sample[self.ext_params_key] = ext

        sample[self.data_key] = b""
        if not sample.get(self.text_key):
            sample[self.text_key] = "lid"

        logger.info(
            f"fileName: {sample.get(self.filename_key)}, method: AudioFastLangId costs {time.time() - start:6f} s"
        )
        return sample

