## AudioAsrPipeline

### 功能
- 端到端流水线（复用 `audio_preprocessor`）：
  - normalization →（可选）GTCRN →（可选）异常过滤 → LID → split → ASR → merge
- 输出转写文本到 `sample["text"]`

### 输入/输出
- **输入**：`sample["filePath"]` 音频文件
- **输出**：
  - `sample["text"]`：合并后的转写文本（`merged_text.txt` 内容）
  - `ext_params.audio_asr.artifacts`：中间产物路径信息

### 参数
- 降噪：`doDenoise/denoiseModelPath`
- 异常过滤：`doAnomalyFilter/minDur/maxDur/silenceRatioTh/silenceRmsRatioTh`
- LID：`lidModelSource/lidDevice/lidMaxSeconds`
- 切分：`maxSegmentSeconds`
- ASR：`asrDevice`

