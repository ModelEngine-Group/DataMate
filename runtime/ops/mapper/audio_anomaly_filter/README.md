## AudioAnomalyFilter

### 功能
- 异常语音检测：时长范围 + 静音帧比例（基于短时 RMS）
- 过滤策略：
  - `keepInvalid=false`：异常则清空 `text/data`，便于后续被框架过滤
  - `keepInvalid=true`：保留文件，仅打标

### 输入/输出
- **输入**：`sample["filePath"]` 音频文件
- **输出**：
  - 报告写入 `sample["ext_params"]["audio_quality"]`
  - 按配置决定是否清空 `sample["text"]`/`sample["data"]`

### 参数
- `minDur/maxDur`
- `silenceRatioTh/silenceRmsRatioTh`
- `keepInvalid`

