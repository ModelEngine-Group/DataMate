## AudioQuantizeEncode

### 功能
- 重采样到目标采样率
- 量化编码为 WAV PCM（8/16/24/32 bit）

### 输入/输出
- **输入**：`sample["filePath"]`
- **输出**：写入 `export_path`（输出为 `.wav`），并更新 `filePath/fileType/fileName`

### 参数
- `sampleRate`：0=不变
- `bitDepth`：8/16/24/32
- `channels`：0/1/2
- `overwrite`

