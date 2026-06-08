# AudioSoundClassify 音频场景分类算子

AudioSoundClassify 将当前输入音频送入 AST AudioSet 预训练模型，输出业务大类和 AudioSet 细类 top-k。它只做分类标注，不做准确率计算、数据集评测或批处理汇总。

## 输入输出

- 输入：`sample["filePath"]` 指向的音频文件
- 输出：当前音频文件，分类结果写入 `ext_params.audio_sound_classify`
- 文件名追加 `__sound_<macro_class>`

## 默认模型

模型从固定部署路径读取：

- `/models/AudioOperations/recog/audioset_10_10_0.4593.pth`

算子内置 AST 的 `audioset_macro_map_v1.json` 与 `class_labels_indices.csv`，用于将 AudioSet 527 细类聚合为业务大类。

## 主要参数

| 参数 | 默认值 | 说明 |
|---|---:|---|
| astCheckpoint | `/models/AudioOperations/recog/audioset_10_10_0.4593.pth` | AST 权重 |
| astMacroMap | 空 | 自定义粗类 JSON，留空使用算子内置映射 |
| labelsCsv | 空 | 自定义 AudioSet 标签 CSV，留空使用算子内置标签表 |
| topK | 10 | 输出 AudioSet 细类数量 |
| segmentSeconds | 10.24 | 滑窗长度 |
| hopSeconds | 5.12 | 滑窗步长 |
| macroAgg | max | 细类聚合成业务大类的策略，支持 max/sum |
