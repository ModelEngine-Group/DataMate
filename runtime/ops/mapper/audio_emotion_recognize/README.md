# AudioEmotionRecognize 语音情感识别算子

AudioEmotionRecognize 对单个音频样本做 8 类语音情感识别，并把结果写入 `ext_params.audio_emotion_recognize`。该算子只做识别标注，不做测试集准确率统计。

## 类别映射

| 英文标签 | 中文业务标签 |
|---|---|
| happy | 喜 |
| angry | 怒 |
| sad | 哀 |
| fearful | 惧 |
| disgust | 厌 |
| surprised | 惊 |
| neutral | 中 |
| calm | 困惑 |

## 默认模型

- HF 后端：`/models/AudioOperations/emotion/new_model`
- Small 后端：`/models/AudioOperations/emotion/small_model.safetensors`

HF 模型目录需包含 `config.json`、`preprocessor_config.json` 和权重文件。

## 输出

算子会保留当前音频，情感识别结果写入 `ext_params.audio_emotion_recognize`。作为最后算子时导出当前音频，并在文件名追加 `__emotion_<pred_en>`。标注内容包含：

- `pred_en`
- `pred_zh`
- `score`
- `distribution`
- `backend`
- `model_path`
