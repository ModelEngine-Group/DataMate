## AudioSimpleAgc

### 功能
- 分段 RMS 自动增益（AGC），将电平拉向目标并限制最大增益

### 输入/输出
- **输入**：`sample["filePath"]`
- **输出**：写入 `export_path`，并更新 `filePath/fileType/fileName`

### 参数
- `targetRms/frameMs/hopMs/maxGain`
- `outFormat`：输出扩展名（wav/flac）
- `overwrite`

