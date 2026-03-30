## AudioNoiseGate

### 功能
- 噪声门：短时 RMS 低于门限时按 `floorRatio` 衰减（门限相对全段峰值 dB）

### 输入/输出
- **输入**：`sample["filePath"]`
- **输出**：写入 `export_path`，并更新 `filePath/fileType/fileName`

### 参数
- `thresholdDb/frameMs/hopMs/floorRatio`
- `outFormat/overwrite`

