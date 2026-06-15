# -*- coding: utf-8 -*-
import json
import os
import re

from flask import Flask, jsonify, request

import torch
import torch_npu  # noqa: F401
from PIL import Image
from transformers import AutoTokenizer
from transformers import Qwen2VLImageProcessor, Qwen2_5_VLForConditionalGeneration

DEFAULT_MODEL_DIR = "/models/VideoOps/qwen/Qwen2.5-VL-7B-Instruct"
MODEL_DIR = os.environ.get("QWEN_MODEL_DIR", DEFAULT_MODEL_DIR)
PREPROCESSOR_CFG = os.path.join(MODEL_DIR, "preprocessor_config.json")

SERVER_HOST = os.environ.get("QWEN_SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.environ.get("QWEN_SERVER_PORT", "18080"))

app = Flask(__name__)

cfg = json.load(open(PREPROCESSOR_CFG, "r", encoding="utf-8"))
MERGE_SIZE = int(cfg.get("merge_size", 1))

tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, trust_remote_code=True)
image_processor = Qwen2VLImageProcessor.from_pretrained(MODEL_DIR)
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    MODEL_DIR,
    torch_dtype=torch.float16,
).to("npu").eval()

SENSITIVE_VALID = ["porn", "violence", "blood", "explosion", "politics", "none"]
SENSITIVE_SET = set(SENSITIVE_VALID)

CLASS_NAMES = [
    "影视剧情类",
    "新闻资讯类",
    "教育知识类",
    "美食饮品类",
    "自然风光类",
    "时尚美妆类",
    "亲子育儿类",
    "宠物日常类",
    "游戏电竞类",
    "音乐舞蹈类",
    "动漫二次元类",
    "数码产品类",
    "汽车交通类",
    "财经商业类",
    "文化艺术类",
    "乐器演奏类",
    "国防军事类",
    "体育竞技类",
    "野生动物类",
    "农业类",
    "航空航天类",
    "其他类",
]
DEFAULT_CLASS_ID = len(CLASS_NAMES)
DEFAULT_CLASS_NAME = CLASS_NAMES[-1]


def label_only_prompt() -> str:
    return "只输出一个词：porn|violence|blood|explosion|politics|none。不要解释。"


def classify22_prompt() -> str:
    items = "\n".join([f"{i+1}. {c}" for i, c in enumerate(CLASS_NAMES)])
    return (
        "你是视频分类器。根据图片判断视频类别。\n"
        f"只输出一个数字编号（1-{len(CLASS_NAMES)}），不要解释，不要输出其他内容。\n"
        f"类别列表：\n{items}\n"
        "如果无法明确归入前面的类别，请输出最后一个编号。\n"
        f"输出示例：{len(CLASS_NAMES)}"
    )


def summary_prompt(language: str = "zh", style: str = "normal") -> str:
    if (language or "zh").lower().startswith("en"):
        if style == "short":
            return "Summarize the video in one sentence based on the image. No extra text."
        if style == "detail":
            return "Summarize the video in 3-5 sentences based on the image, including objects, actions, and scene. No extra text."
        return "Summarize the video based on the image. Be concise. No extra text."
    if style == "short":
        return "用一句话概括这段视频内容，不要解释。"
    if style == "detail":
        return "用3到5句话概括视频内容，包含关键对象、动作和场景，不要解释。"
    return "概括视频内容，包含关键对象、动作和场景，不要解释。"


def event_tag_prompt() -> str:
    return "根据图片判断正在发生的事件，用短语输出事件名称（不超过10个字）。不要解释。"


def subtitle_ocr_prompt(language: str = "auto") -> str:
    lang_hint = (
        "The subtitle may be in English or Chinese. Keep the original language."
        if (language or "auto").lower() == "auto"
        else f"The subtitle language is {language}. Keep that language."
    )
    return (
        "You are extracting subtitle text from a cropped subtitle image.\n"
        "Output rules:\n"
        "1. Output only the subtitle text.\n"
        "2. Do not describe the image.\n"
        "3. Do not explain.\n"
        "4. Do not apologize.\n"
        "5. Do not say things like 'there is no subtitle', 'no subtitle present', 'no text', or 'the image you provided'.\n"
        "6. If no readable subtitle text is present, return an empty string.\n"
        "7. If the text is uncertain, prefer an empty string over a guessed sentence.\n"
        "8. Output plain text only, with no prefix, no label, and no quotation marks.\n"
        f"{lang_hint}\n"
        "Return one single subtitle line only."
    )


def subtitle_correct_prompt(srt_text: str, language: str = "auto") -> str:
    lang_hint = (
        "Keep the original language of each subtitle line."
        if (language or "auto").lower() == "auto"
        else f"Use {language} when correcting subtitle wording."
    )
    return (
        "You are a subtitle OCR correction assistant.\n"
        "Correct only obvious OCR errors in subtitle text.\n"
        "Do not rewrite style, do not summarize, do not add or remove subtitle items, and do not change timestamps.\n"
        "Only fix character-level OCR issues, spacing, punctuation, and clearly broken words.\n"
        f"{lang_hint}\n"
        "Return JSON only. Format: [{\"index\":1,\"text\":\"corrected subtitle line\"}, ...]\n"
        "The number of items must exactly match the subtitle items in the input.\n"
        "Input SRT:\n"
        f"{srt_text}"
    )


def build_prompt_with_image_tokens(user_text: str, num_image_tokens: int) -> str:
    messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": user_text}]}]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    prompt = prompt.replace("<|image_pad|>", "<|image_pad|>" * num_image_tokens)
    return prompt


def build_text_only_prompt(user_text: str) -> str:
    messages = [{"role": "user", "content": [{"type": "text", "text": user_text}]}]
    return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


def extract_assistant_answer(raw_text: str) -> str:
    if not raw_text:
        return ""
    text = raw_text
    idx = text.rfind("assistant")
    if idx != -1:
        text = text[idx + len("assistant"):]
    return text.strip()


def extract_assistant_answer_sensitive(raw_text: str) -> str:
    text = extract_assistant_answer(raw_text)
    text = re.sub(r"[^a-zA-Z|]+", " ", text).strip().lower()
    return text


def normalize_sensitive_label(raw_text: str) -> str:
    answer = extract_assistant_answer_sensitive(raw_text)
    if "|" in answer:
        parts = [p.strip() for p in answer.split("|") if p.strip()]
        if parts and parts[-1] in SENSITIVE_SET:
            return parts[-1]
        return "none"
    if answer in SENSITIVE_SET:
        return answer
    return "none"


def normalize_class22(raw_text: str) -> dict:
    answer = extract_assistant_answer(raw_text).strip()
    nums = re.findall(r"\d+", answer)
    if not nums:
        return {"id": DEFAULT_CLASS_ID, "label": DEFAULT_CLASS_NAME, "raw": answer}
    idx = int(nums[-1])
    if idx < 1 or idx > len(CLASS_NAMES):
        idx = DEFAULT_CLASS_ID
    return {"id": idx, "label": CLASS_NAMES[idx - 1], "raw": answer}


def infer_raw_text(image_path: str, user_text: str, max_new_tokens: int = 64) -> str:
    image = Image.open(image_path).convert("RGB")
    img_inputs = image_processor(images=image, return_tensors="pt")
    grid = img_inputs["image_grid_thw"][0]
    num_patches = int(grid.prod().item())
    num_image_tokens = num_patches // (MERGE_SIZE * MERGE_SIZE)

    prompt = build_prompt_with_image_tokens(user_text, num_image_tokens)
    text_inputs = tokenizer(prompt, return_tensors="pt")

    inputs = {**text_inputs, **img_inputs}
    inputs = {k: v.to("npu") for k, v in inputs.items()}

    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=int(max_new_tokens),
            do_sample=False,
            temperature=0.0,
        )

    return tokenizer.batch_decode(out, skip_special_tokens=True)[0]


def infer_raw_text_only(user_text: str, max_new_tokens: int = 512) -> str:
    prompt = build_text_only_prompt(user_text)
    text_inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {k: v.to("npu") for k, v in text_inputs.items()}

    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=int(max_new_tokens),
            do_sample=False,
            temperature=0.0,
        )

    return tokenizer.batch_decode(out, skip_special_tokens=True)[0]


def extract_json_list(raw_text: str):
    text = extract_assistant_answer(raw_text).strip()
    if not text:
        return None
    match = re.search(r"```json\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        text = match.group(1).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    try:
        return json.loads(text)
    except Exception:
        return None


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "ok": True,
            "model_dir": MODEL_DIR,
            "host": SERVER_HOST,
            "port": SERVER_PORT,
            "num_classes": len(CLASS_NAMES),
            "classes": CLASS_NAMES,
        }
    )


@app.route("/infer", methods=["POST"])
def infer_api():
    data = request.get_json(force=True)
    image_path = data["image_path"]
    task = data.get("task", "sensitive")
    max_new_tokens = int(data.get("max_new_tokens", 64))
    language = data.get("language", "zh")
    style = data.get("style", "normal")

    try:
        if task == "sensitive":
            raw = infer_raw_text(image_path, label_only_prompt(), max_new_tokens=8)
            label = normalize_sensitive_label(raw)
            answer = extract_assistant_answer_sensitive(raw)
            is_sensitive = label != "none"
            score = 0.90 if is_sensitive else 0.05
            return jsonify(
                {
                    "task": task,
                    "is_sensitive": is_sensitive,
                    "label": label,
                    "score": float(score),
                    "reason": answer if answer else label,
                }
            )

        if task in {"classify22", "classify25"}:
            raw = infer_raw_text(image_path, classify22_prompt(), max_new_tokens=16)
            cls = normalize_class22(raw)
            return jsonify(
                {
                    "task": "classify22",
                    "class_id": int(cls["id"]),
                    "class_name": cls["label"],
                    "raw": cls.get("raw", ""),
                }
            )

        if task == "summary":
            raw = infer_raw_text(
                image_path,
                summary_prompt(language=language, style=style),
                max_new_tokens=max_new_tokens,
            )
            return jsonify({"task": task, "summary": extract_assistant_answer(raw).strip()})

        if task == "subtitle_ocr":
            raw = infer_raw_text(
                image_path,
                subtitle_ocr_prompt(language=language),
                max_new_tokens=max_new_tokens,
            )
            text = extract_assistant_answer(raw).strip()
            return jsonify({"task": task, "text": text, "raw": text})

        if task == "event_tag":
            raw = infer_raw_text(image_path, event_tag_prompt(), max_new_tokens=max_new_tokens)
            return jsonify({"task": task, "event": extract_assistant_answer(raw).strip()})

        return jsonify({"task": task, "error": "unknown_task"}), 200

    except Exception as e:
        return jsonify({"task": task, "error": "server_error", "reason": str(e)[:200]}), 200


@app.route("/text", methods=["POST"])
def text_api():
    data = request.get_json(force=True)
    task = data.get("task", "subtitle_correct")
    max_new_tokens = int(data.get("max_new_tokens", 1024))
    language = data.get("language", "auto")

    try:
        if task == "subtitle_correct":
            srt_text = str(data.get("srt_text", "") or "")
            raw = infer_raw_text_only(
                subtitle_correct_prompt(srt_text=srt_text, language=language),
                max_new_tokens=max_new_tokens,
            )
            items = extract_json_list(raw)
            if not isinstance(items, list):
                return jsonify(
                    {
                        "task": task,
                        "error": "bad_response",
                        "reason": "model did not return json list",
                        "raw": extract_assistant_answer(raw),
                    }
                ), 200
            return jsonify({"task": task, "items": items, "raw": extract_assistant_answer(raw)})

        return jsonify({"task": task, "error": "unknown_task"}), 200

    except Exception as e:
        return jsonify({"task": task, "error": "server_error", "reason": str(e)[:200]}), 200


if __name__ == "__main__":
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False)
