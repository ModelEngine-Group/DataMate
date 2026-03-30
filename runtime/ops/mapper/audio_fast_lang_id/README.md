## AudioFastLangId

### 功能
- SpeechBrain LID（仅输出 zh/en），复用 `audio_preprocessor/src/utils/fast_lang_id.py`

### 输入/输出
- **输入**：`sample["filePath"]`
- **输出**：
  - `ext_params.audio_lid.lang = "zh" | "en"`
  - 不改写音频文件本身

### 参数
- `modelSource/modelSavedir/device/batchSize/maxSeconds`

