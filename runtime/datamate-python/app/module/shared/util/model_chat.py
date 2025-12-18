from openai import OpenAI


def call_openai_style_model(base_url, api_key, model_name, prompt, **kwargs):
    client = OpenAI(
        base_url=base_url,
        api_key=api_key
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        **kwargs
    )
    return response.choices[0].message.content


def extract_json_substring(raw: str) -> str:
    """从 LLM 的原始回答中提取最可能的 JSON 字符串片段。

    处理思路：
    - 原始回答可能是：说明文字 + JSON + 说明文字，甚至带有 Markdown 代码块。
    - 优先在文本中查找第一个 '{' 或 '[' 作为 JSON 起始；
    - 再从后向前找最后一个 '}' 或 ']' 作为结束；
    - 如果找不到合适的边界，就退回原始字符串。
    - 部分模型可能会在回复中加入 `<think>...</think>` 内部思考内容，应在解析前先去除。
    该方法不会保证截取的一定是合法 JSON，但能显著提高 json.loads 的成功率。
    """
    if not raw:
        return raw

    # 先移除所有 <think>...</think> 段落（包括跨多行的情况）
    try:
        import re

        raw = re.sub(r"<think>[\s\S]*?</think>", "", raw, flags=re.IGNORECASE)
    except Exception:
        # 正则异常时不影响后续逻辑，继续使用原始文本
        pass

    start = None
    end = None

    # 查找第一个 JSON 起始符号
    for i, ch in enumerate(raw):
        if ch in "[{":
            start = i
            break

    # 查找最后一个 JSON 结束符号
    for i in range(len(raw) - 1, -1, -1):
        if raw[i] in "]}":
            end = i + 1  # 切片是左闭右开
            break

    if start is not None and end is not None and start < end:
        return raw[start:end].strip()

    # 兜底：去掉常见 Markdown 包裹（```json ... ```）
    stripped = raw.strip()
    if stripped.startswith("```"):
        # 去掉首尾 ``` 标记
        stripped = stripped.strip("`")
    return stripped
