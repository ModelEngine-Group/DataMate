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

- 模型目录：`/models/AudioOperations/emotion/new_model`

模型目录需包含 `config.json`、`preprocessor_config.json` 和 `model.safetensors`。算子固定使用该本地 HuggingFace 音频分类模型，不提供后端切换。

## 输出

情感识别结果写入 `ext_params.audio_emotion_recognize`。输出当前音频，并在文件名追加 `__emotion_<pred_en>`。标注内容包含：

- `pred_en`
- `pred_zh`
- `score`
- `distribution`
- `model_path`
