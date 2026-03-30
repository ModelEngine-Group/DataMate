## AudioSoftPeakLimiter

### 功能
- 软限幅：对超阈值部分做平滑压缩（tanh 近似），减轻硬削波

### 输入/输出
- **输入**：`sample["filePath"]`
- **输出**：写入 `export_path`，并更新 `filePath/fileType/fileName`

### 参数
- `threshold/knee`
- `outFormat/overwrite`

