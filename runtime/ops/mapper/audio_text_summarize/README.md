# AudioTextSummarize ASR 文本概括算子

AudioTextSummarize 面向音频 ASR 之后的文本，做高保真抽取式概括。它只负责概括，不做关键信息保留率、准确率或测试集指标计算。

## 输入输出

- 输入：`sample["text"]` 中的 ASR 文本；若为空，可读取 txt/md/json/jsonl 文件路径
- 输出：摘要文本写回 `sample["text"]`
- 运行明细：`ext_params.audio_text_summarize`

## 方法

- `extractive`：默认轻量抽取式概括，中文按字符窗口，英文按词窗口，尽量保留原文连续片段
- `bert_onnx`：使用本地 `model.onnx` + tokenizer 对原文与候选片段编码，选择语义最接近原文的片段

默认 ONNX 模型目录：

- `/models/AudioOperations/summary/summary-model`

## 多行模式

`lineMode` 可处理 ASR 合并文件：

- `single`：全文当作一条
- `tab`：每行 `key<TAB>text`
- `space`：每行 `key text`
- `auto`：每行都含 TAB 时按 `tab`，否则按 `single`

## 常用参数

| 参数 | 默认值 | 说明 |
|---|---:|---|
| maxSummaryCharsZh | 40 | 中文摘要最大字数 |
| maxSummaryWordsEn | 18 | 英文摘要最大词数 |
| minSummaryWordsEn | 8 | 英文抽取窗口最小词数 |
| preserveKeys | true | 多行输出是否保留 key |
| cpuThreads | 4 | CPU/ONNX 线程限制 |
