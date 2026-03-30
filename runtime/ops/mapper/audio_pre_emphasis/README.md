## AudioPreEmphasis

### 功能
- 一阶预加重：\(y[n]=x[n]-coef*x[n-1]\)

### 输入/输出
- **输入**：`sample["filePath"]`
- **输出**：写入 `export_path`，并更新 `filePath/fileType/fileName`

### 参数
- `coef`：预加重系数
- `outFormat`：输出扩展名（wav/flac）
- `overwrite`：是否覆盖同名输出

