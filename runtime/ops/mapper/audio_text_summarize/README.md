# AudioTextSummarize ASR 文本概括算子

AudioTextSummarize 面向文本数据做高保真概括。它的输入是文本，输出也是文本，不处理音频本体。

## 输入输出

- 输入：`sample["text"]` 中的文本；若为空，可读取 txt/md/json/jsonl 文件路径
- 输出：摘要文本写回 `sample["text"]`
- 运行明细：`ext_params.audio_text_summarize`

## 默认逻辑

算子固定使用本地 ONNX 模型做语义选片概括：

- 中文按字符窗口选取代表片段
- 英文按单词窗口选取代表片段
- 默认 provider 优先级固定为 `CANNExecutionProvider,CPUExecutionProvider`
- 默认线程数固定为 24
- 默认候选窗口上限固定为 96
- 行解析模式固定为 `single`

默认 ONNX 模型目录：

- `/models/AudioOperations/summary/summary-model`

## 常用参数

| 参数 | 默认值 | 说明 |
|---|---:|---|
| onnxModelDir | `/models/AudioOperations/summary/summary-model` | 本地 ONNX 摘要模型目录 |
| maxSummaryCharsZh | 40 | 中文摘要最大字数 |
| maxSummaryWordsEn | 18 | 英文摘要最大词数 |

## 固定默认值

以下配置不再在 UI 中暴露，统一使用当前默认值：

- 方法：`bert_onnx`
- 英文最小词数：`8`
- 行解析模式：`single`
- 保留 key：`true`
- provider 优先级：`CANNExecutionProvider,CPUExecutionProvider`
- CPU 线程数：`24`
- 最大候选片段数：`96`
