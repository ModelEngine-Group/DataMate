## AudioTrimSilenceEdges

### 功能
- 首尾静音裁剪：按短时能量判定静音并向内裁剪，可保留 `padMs` padding

### 输入/输出
- **输入**：`sample["filePath"]`
- **输出**：写入 `export_path`，并更新 `filePath/fileType/fileName`

### 参数
- `frameMs/hopMs/threshDb/padMs`
- `outFormat/overwrite`

