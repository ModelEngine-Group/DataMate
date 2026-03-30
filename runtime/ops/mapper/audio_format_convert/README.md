## AudioFormatConvert

### 功能
- 常见音频格式互转（优先使用 `pydub`，兜底使用 `soundfile`）
- 可选重采样（Hz）与声道转换（mono/stereo）

### 输入/输出
- **输入**：`sample["filePath"]` 指向音频文件
- **输出**：将转换后的文件写入 `sample["export_path"]`，并更新：
  - `sample["filePath"]` / `sample["fileType"]` / `sample["fileName"]`

### 参数（metadata.yml -> settings）
- `targetFormat`：目标扩展名（wav/flac/mp3/aac/m4a/ogg）
- `sampleRate`：目标采样率，0=不变
- `channels`：目标声道数（0=不变，1/2）
- `overwrite`：是否覆盖同名输出

