# AudioEmotionRecognize 语音情感识别算子

AudioEmotionRecognize 对单个音频样本做 8 类语音情感识别，并把结果写入 `ext_params.audio_emotion_recognize`。

默认 `saveAsText=true`：每个输入音频输出一个 `.txt`，内容为预测英文情感标签，例如 `happy`、`sad`。

当 `saveAsText=false`：音频按原文件名原样输出，同时识别结果写入输出数据集的 `references/emotion_recognition.jsonl`。

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

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---:|---|
| hfModelDir | input | /models/AudioOperations/emotion/wav2vec2-lg-xlsr-en-speech-emotion-recognition | 情感识别模型目录 |
| saveAsText | switch | true | true=输出情感标签 txt；false=保留音频并写 references 清单 |
| resultSavePath | input | /dataset/{dataset_id}/references/emotion_recognition.jsonl | saveAsText=false 时写入的情感识别结果 JSONL 文件 |

## 输出

- `sample["ext_params"]["audio_emotion_recognize"]`：结构化识别结果
- `saveAsText=true`：输出 `.txt`，文本内容为 `pred_en`
- `saveAsText=false`：输出原音频，文件名不变；额外写入 `references/emotion_recognition.jsonl`

## 模型目录

默认模型目录：

```text
/models/AudioOperations/emotion/wav2vec2-lg-xlsr-en-speech-emotion-recognition
```

模型目录需包含：

- `config.json`
- `preprocessor_config.json`
- `model.safetensors`

## 识别结果清单

`saveAsText=false` 时，每行一个 JSON 对象，例如：

```json
{"file":"03-01-06-01-02-02-08.wav","fileName":"03-01-06-01-02-02-08.wav","key":"03-01-06-01-02-02-08","pred_en":"fearful","pred_zh":"惧","score":0.92345678}
```

## 版本历史

- **v1.0.0**：支持单文件 8 类语音情感识别
- **v1.0.1**：模型目录改名；新增文本标签输出与保留音频写清单模式
