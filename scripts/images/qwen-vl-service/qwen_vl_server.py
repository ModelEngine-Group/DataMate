# -*- coding: utf-8 -*-
import json
import os
import re

from flask import Flask, request, jsonify

import torch
import torch_npu  # noqa: F401
from PIL import Image
from transformers import AutoTokenizer
from transformers import Qwen2VLImageProcessor, Qwen2_5_VLForConditionalGeneration

DEFAULT_MODEL_DIR = "/mnt/models/qwen/Qwen/Qwen2.5-VL-7B-Instruct"
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
    torch_dtype=torch.float16
).to("npu").eval()

SENSITIVE_VALID = ["porn", "violence", "blood", "explosion", "politics", "none"]
SENSITIVE_SET = set(SENSITIVE_VALID)

CLASS_NAMES = [
    "影视剧情类", "新闻资讯类", "教育知识类", "美食饮品类", "自然风光类",
    "时尚美妆类", "亲子育儿类", "宠物日常类", "游戏电竞类", "音乐舞蹈类",
    "动漫二次元类", "数码产品类", "汽车交通类", "财经商业类", "文化艺术类",
    "乐器演奏类", "国防军事类", "体育竞技类", "野生动物类", "农业类",
    "航空航天类", "其他类"
]
DEFAULT_CLASS_ID = len(CLASS_NAMES)
DEFAULT_CLASS_NAME = CLASS_NAMES[-1]


def label_only_prompt() -> str:
    return "只输出一个词：porn|violence|blood|explosion|politics|none。不要解释。"


def classify25_prompt() -> str:
    items = "\n".join([f"{i+1}. {c}" for i, c in enumerate(CLASS_NAMES)])
    return (
        "你是视频分类器。根据图片判断视频类别。\n"
        f"只输出一个数字编号（1-{len(CLASS_NAMES)}），不要解释、不要输出其它内容。\n"
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
        return "用一句话概括这段视频内容。不要解释。"
    if style == "detail":
        return "用3-5句概括视频内容，包含关键对象、动作、场景。不要解释。"
    return "概括视频内容，包含关键对象、动作、场景。不要解释。"


def event_tag_prompt() -> str:
    return "根据图片判断正在发生的事件，用短语输出事件名称（不超过10个字）。不要解释。"


def build_prompt_with_image_tokens(user_text: str, num_image_tokens: int) -> str:
    messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": user_text}]}]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    prompt = prompt.replace("<|image_pad|>", "<|image_pad|>" * num_image_tokens)
    return prompt


def extract_assistant_answer(raw_text: str) -> str:
    if not raw_text:
        return ""
    t = raw_text
    idx = t.rfind("assistant")
    if idx != -1:
        t = t[idx + len("assistant"):]
    t = t.strip().splitlines()[-1].strip()
    return t


def extract_assistant_answer_sensitive(raw_text: str) -> str:
    t = extract_assistant_answer(raw_text)
    t = re.sub(r"[^a-zA-Z|]+", " ", t).strip().lower()
    return t


def normalize_sensitive_label(raw_text: str) -> str:
    ans = extract_assistant_answer_sensitive(raw_text)
    if "|" in ans:
        parts = [p.strip() for p in ans.split("|") if p.strip()]
        if parts and parts[-1] in SENSITIVE_SET:
            return parts[-1]
        return "none"
    if ans in SENSITIVE_SET:
        return ans
    return "none"


def normalize_class25(raw_text: str) -> dict:
    ans = extract_assistant_answer(raw_text).strip()
    nums = re.findall(r"\d+", ans)
    if not nums:
        return {"id": DEFAULT_CLASS_ID, "label": DEFAULT_CLASS_NAME, "raw": ans}
    idx = int(nums[-1])
    if idx < 1 or idx > len(CLASS_NAMES):
        idx = DEFAULT_CLASS_ID
    return {"id": idx, "label": CLASS_NAMES[idx - 1], "raw": ans}


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
            temperature=0.0
        )

    return tokenizer.batch_decode(out, skip_special_tokens=True)[0]


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "ok": True,
        "model_dir": MODEL_DIR,
        "host": SERVER_HOST,
        "port": SERVER_PORT,
        "num_classes": len(CLASS_NAMES),
        "classes": CLASS_NAMES
    })


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
            is_sensitive = (label != "none")
            score = 0.90 if is_sensitive else 0.05
            return jsonify({
                "task": task,
                "is_sensitive": is_sensitive,
                "label": label,
                "score": float(score),
                "reason": answer if answer else label
            })

        if task == "classify25":
            raw = infer_raw_text(image_path, classify25_prompt(), max_new_tokens=16)
            cls = normalize_class25(raw)
            return jsonify({
                "task": task,
                "class_id": int(cls["id"]),
                "class_name": cls["label"],
                "raw": cls.get("raw", "")
            })

        if task == "summary":
            raw = infer_raw_text(
                image_path,
                summary_prompt(language=language, style=style),
                max_new_tokens=max_new_tokens
            )
            return jsonify({
                "task": task,
                "summary": extract_assistant_answer(raw).strip()
            })

        if task == "event_tag":
            raw = infer_raw_text(image_path, event_tag_prompt(), max_new_tokens=max_new_tokens)
            return jsonify({
                "task": task,
                "event": extract_assistant_answer(raw).strip()
            })

        return jsonify({"task": task, "error": "unknown_task"}), 200

    except Exception as e:
        return jsonify({"task": task, "error": "server_error", "reason": str(e)[:200]}), 200


if __name__ == "__main__":
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False)
