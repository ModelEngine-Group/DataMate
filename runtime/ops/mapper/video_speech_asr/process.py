# -*- coding: utf-8 -*-
import os
import json
import shutil
import subprocess
import re

from .._video_common.paths import make_run_dir, ensure_dir
from .._video_common.log import get_logger


def _write_srt(segments, srt_path):
    def _fmt(t):
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int(round((t - int(t)) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    with open(srt_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(segments, 1):
            f.write(str(i) + "\n")
            f.write(f"{_fmt(seg['start'])} --> {_fmt(seg['end'])}\n")
            f.write((seg.get("text") or "").strip() + "\n\n")


def _contains_cjk(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", s or ""))


def _to_simplified(text: str) -> str:
    try:
        from opencc import OpenCC
        return OpenCC("t2s").convert(text)
    except Exception:
        return text


class VideoSpeechASR:
    """语音转文字（优先 faster-whisper；失败自动回退 openai-whisper）

    params:
      - ffmpeg_path: str, optional
      - model: tiny|base|small|medium|large-v3, default small
      - language: auto|zh|en, default zh
      - beam_size: int, default 5
      - vad_filter: bool, default True
      - compute_type: int8|int8_float16|float16|float32, default int8
      - sample_rate: int, default 16000
      - channels: int, default 1
      - max_audio_sec: float, optional
      - zh_script: simplified|traditional|keep, default simplified

      # 离线/本地模型（faster-whisper）
      - fw_model_path: str, optional   # 本地模型路径（目录）
      - fw_download_root: str, optional
      - local_files_only: bool, default False

    outputs:
      - artifacts/audio.wav
      - artifacts/asr.json / asr.txt / asr.srt
      - artifacts/asr_backend.json（记录用了哪个后端/异常信息）
    """

    @staticmethod
    def execute(sample, params):
        video_path = sample["filePath"]
        export_path = sample.get("export_path", "./outputs")

        op_name = "video_speech_asr"
        out_dir = make_run_dir(export_path, op_name)
        log_dir = ensure_dir(os.path.join(out_dir, "logs"))
        art_dir = ensure_dir(os.path.join(out_dir, "artifacts"))

        logger = get_logger(op_name, log_dir)
        logger.info(f"video={video_path}")
        logger.info(f"out_dir={out_dir}")

        ffmpeg_path = params.get("ffmpeg_path") or shutil.which("ffmpeg")
        if not ffmpeg_path:
            raise RuntimeError("ffmpeg not found. Please install ffmpeg or pass params.ffmpeg_path")

        sr = int(params.get("sample_rate", 16000))
        ch = int(params.get("channels", 1))
        max_audio_sec = params.get("max_audio_sec", None)
        max_audio_sec = float(max_audio_sec) if max_audio_sec is not None else None

        audio_path = os.path.join(art_dir, "audio.wav")
        cmd = [
            ffmpeg_path, "-hide_banner", "-y",
            "-i", video_path,
            "-vn",
            "-ac", str(ch),
            "-ar", str(sr),
            "-c:a", "pcm_s16le",
        ]
        if max_audio_sec is not None and max_audio_sec > 0:
            cmd += ["-t", f"{max_audio_sec}"]
        cmd += [audio_path]

        logger.info("FFmpeg cmd: " + " ".join(cmd))
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if p.returncode != 0:
            raise RuntimeError(f"FFmpeg failed (code={p.returncode}).\nSTDERR:\n{p.stderr}")

        model_name = (params.get("model", "small") or "small")
        language = (params.get("language", "zh") or "zh").lower()
        beam_size = int(params.get("beam_size", 5))
        vad_filter = bool(params.get("vad_filter", True))
        compute_type = (params.get("compute_type", "int8") or "int8")
        zh_script = (params.get("zh_script", "simplified") or "simplified").lower()

        fw_model_path = params.get("fw_model_path", None)
        fw_download_root = params.get("fw_download_root", None)
        local_files_only = bool(params.get("local_files_only", False))

        segments = []
        full_text = ""
        backend_info = {"backend": None, "error": None}

        # ===== try faster-whisper =====
        try:
            from faster_whisper import WhisperModel
            backend_info["backend"] = "faster-whisper"

            # 离线策略：local_files_only 时，把 HF 的联网行为尽量关掉
            if local_files_only:
                os.environ.setdefault("HF_HUB_OFFLINE", "1")
                os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

            model_id = fw_model_path or model_name
            logger.info(f"[ASR] faster-whisper load model={model_id}, compute_type={compute_type}, offline={local_files_only}")

            fw = WhisperModel(
                model_id,
                device="cpu",
                compute_type=compute_type,
                download_root=fw_download_root,
            )

            logger.info("[ASR] faster-whisper transcribe start...")
            seg_iter, info = fw.transcribe(
                audio_path,
                language=None if language == "auto" else language,
                beam_size=beam_size,
                vad_filter=vad_filter,
            )
            for s in seg_iter:
                segments.append({"start": float(s.start), "end": float(s.end), "text": (s.text or "").strip()})
            full_text = " ".join([s["text"] for s in segments]).strip()
            logger.info("[ASR] faster-whisper transcribe done.")

        except Exception as e:
            # ===== fallback openai-whisper =====
            backend_info["backend"] = "openai-whisper"
            backend_info["error"] = f"faster-whisper failed: {repr(e)}"
            logger.warning("[ASR] faster-whisper failed, fallback openai-whisper. reason=" + repr(e))

            try:
                import whisper
            except Exception as e2:
                raise RuntimeError("ASR backend failed. Please install: pip install faster-whisper openai-whisper") from e2

            logger.info(f"[ASR] openai-whisper load model={model_name} (slow on CPU)")
            wmodel = whisper.load_model(model_name)

            wargs = {"fp16": False, "verbose": False}
            if language != "auto":
                wargs["language"] = language

            logger.info("[ASR] openai-whisper transcribe start...")
            result = wmodel.transcribe(audio_path, **wargs)
            logger.info("[ASR] openai-whisper transcribe done.")

            for seg in result.get("segments", []):
                segments.append({
                    "start": float(seg.get("start", 0.0)),
                    "end": float(seg.get("end", 0.0)),
                    "text": (seg.get("text") or "").strip()
                })
            full_text = (result.get("text") or "").strip()

        # 简体化
        if zh_script == "simplified":
            if _contains_cjk(full_text):
                full_text = _to_simplified(full_text)
            for s in segments:
                if _contains_cjk(s["text"]):
                    s["text"] = _to_simplified(s["text"])

        json_path = os.path.join(art_dir, "asr.json")
        txt_path = os.path.join(art_dir, "asr.txt")
        srt_path = os.path.join(art_dir, "asr.srt")
        backend_path = os.path.join(art_dir, "asr_backend.json")

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"text": full_text, "segments": segments}, f, ensure_ascii=False, indent=2)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(full_text + "\n")
        _write_srt(segments, srt_path)

        with open(backend_path, "w", encoding="utf-8") as f:
            json.dump(backend_info, f, ensure_ascii=False, indent=2)

        logger.info(f"Done. segments={len(segments)} asr_json={json_path}")
        return {
            "out_dir": out_dir,
            "audio_wav": audio_path,
            "asr_json": json_path,
            "asr_txt": txt_path,
            "asr_srt": srt_path,
            "asr_backend": backend_path,
        }