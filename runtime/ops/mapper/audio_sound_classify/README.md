# AudioSoundClassify 音频场景分类算子

AudioSoundClassify 将当前输入音频送入 AST 或 PANNs AudioSet 预训练模型，输出业务大类和 AudioSet 细类 top-k。它只做分类标注，不做准确率计算、数据集评测或流水线批处理。

## 输入输出

- 输入：音频文件路径或上游 `sample["data"]` 音频字节
- 输出：保留当前音频，分类结果写入 `ext_params.audio_sound_classify`
- 作为最后算子时：导出当前音频，并在文件名追加 `__sound_<macro_class>`

## 默认模型

默认后端为 AST，对应 annotation 模块当前标准实现。模型从固定部署路径读取：

- AST：`/models/AudioOperations/recog/audioset_10_10_0.4593.pth`
- PANNs：`/models/AudioOperations/panns/Cnn14_16k_mAP=0.438.pth`

算子内置 AST 的 `audioset_macro_map_v1.json` 与 PANNs 的 `classes_macro_draft.tsv`，可将 AudioSet 527 细类聚合为业务大类。

## 主要参数

| 参数 | 默认值 | 说明 |
|---|---:|---|
| backend | ast | ast 标准实现；panns 旧版兼容 |
| astCheckpoint | `/models/AudioOperations/recog/audioset_10_10_0.4593.pth` | AST 权重 |
| pannsCheckpoint | `/models/AudioOperations/panns/Cnn14_16k_mAP=0.438.pth` | PANNs 权重 |
| astMacroMap | 空 | AST 自定义粗类 JSON |
| macroMap | 空 | PANNs 自定义 label 到大类 TSV |
| device | auto | auto/cpu/npu/cuda |
| topK | 10 | 输出 AudioSet 细类数量 |
| humanSpeechThreshold | 0.2 | 人声优先规则阈值 |
| segmentSeconds | 10.24 | AST 滑窗长度 |
| hopSeconds | 5.12 | AST 滑窗步长 |
| keepAudio | true | 中间节点是否保留音频给下游 |
