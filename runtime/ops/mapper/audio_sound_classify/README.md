# AudioSoundClassify 音频场景分类算子

AudioSoundClassify 对单个音频样本做 AST AudioSet 声音分类，并把结构化结果写入 `ext_params.audio_sound_classify`。

默认 `saveAsText=true`：每个输入音频输出一个 `.txt`，内容为预测声音大类标签，例如 `HumanSpeech`、`Music`、`Animal`。

当 `saveAsText=false`：音频按原文件名原样输出，同时识别结果写入输出数据集的 `references/sound_classification.jsonl`。

## 输入输出

- 输入：`sample["filePath"]` 指向的音频文件
- 输出：分类结果写入 `ext_params.audio_sound_classify`
- `saveAsText=true`：输出 `.txt`
- `saveAsText=false`：输出原音频，文件名不变，并追加 `references/sound_classification.jsonl`

## 默认模型

模型从固定部署路径读取：

- `/models/AudioOperations/recog/audioset_10_10_0.4593.pth`

标签文件读取规则：

- 优先读取与模型同目录下的 `class_labels_indices.csv`
- 优先读取与模型同目录下的 `audioset_macro_map_v1.json`
- 若模型目录下不存在，则回退到算子内置文件

## 主要参数

| 参数 | 默认值 | 说明 |
|---|---:|---|
| astCheckpoint | `/models/AudioOperations/recog/audioset_10_10_0.4593.pth` | AST 权重 |
| saveAsText | true | true=输出声音大类 txt；false=保留音频并写 references 清单 |
| resultSavePath | `/dataset/{dataset_id}/references/sound_classification.jsonl` | saveAsText=false 时写入的结果 JSONL 文件 |
| topK | 10 | 输出 AudioSet 细类数量 |
| segmentSeconds | 10.24 | 滑窗长度 |
| hopSeconds | 5.12 | 滑窗步长 |
| macroAgg | max | 细类聚合成业务大类的策略，支持 max/sum |

## 输出内容

- `sample["ext_params"]["audio_sound_classify"]`：结构化识别结果
- `saveAsText=true`：输出 txt，文本内容为 `macro_class`
- `saveAsText=false`：输出原音频，文件名不变；额外写入 `references/sound_classification.jsonl`

## 结果清单示例

`saveAsText=false` 时，每行一个 JSON 对象，例如：

```json
{"file":"example.wav","fileName":"example.wav","key":"example","macro_class":"Music","macro_scores":{"HumanSpeech":0.01646949,"Music":0.83607644},"small_topk":[{"label":"Music","macro_class":"Music","prob":0.83607644}]}
```
