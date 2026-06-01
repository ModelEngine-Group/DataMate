# 音频算子简易测试步骤

- `audio_anomaly_filter`
- `audio_asr_transcribe`
- `audio_dc_offset_removal`
- `audio_fast_lang_id`
- `audio_fast_lang_id_text`
- `audio_format_convert`
- `audio_gtcrn_denoise`
- `audio_hum_notch`
- `audio_noise_gate`
- `audio_text_summarize`

测试素材可从以下目录选择：

```text
\DataMate\runtime\ops\mapper\__audioOps_Test_Cases__
```

## 通用准备

环境前置依赖：

1. DataMate runtime 需要安装 [audio_runtime_requirements.txt](audio_runtime_requirements.txt) 中固定版本的 Python 包。
2. DataMate runtime 的系统环境需要能直接执行 `ffmpeg -version`。
3. ASR 相关算子需要 runtime 能导入 `wenet.bin.recognize`，WeNet 不再由算子目录内置。
4. 算子目录不再内置 `speechbrain`、`wenet`、`ffmpeg`、`panns_inference` 等第三方依赖。

1. 在 DataMate 中创建一个输入数据集和一个输出数据集。
2. 导入测试素材。建议至少导入以下文件：
   - 中文语音：
     - `humanSpeech\zh\aishell_0000.wav`
     - `humanSpeech\zh\aishell_0001.wav`
     - `humanSpeech\zh\aishell_0002.wav`
   - 英文语音：
     - `humanSpeech\en\librispeech_0000.wav`
     - `humanSpeech\en\librispeech_0001.wav`
     - `humanSpeech\en\librispeech_0002.wav`
   - 摘要/ASR 测试语音：
     - `audio\summary\84-121123-0000.flac`
     - `audio\summary\84-121123-0001.flac`
     - `audio\summary\BAC009S0002W0122.wav`
     - `audio\summary\BAC009S0002W0123.wav`
3. 单算子测试时，每次只选择一个目标算子运行，输出保存到新的输出数据集。
4. 串联测试时，要求上一个算子的输出数据集作为下一个算子的输入数据集。
5. 每次测试后检查三点：
   - 任务是否成功完成，无报错。
   - 输出数据集中文件数量是否与输入样本数量一致，除非算子本身明确过滤或跳过。
   - 输出文件类型、文件内容、文件名标记或 `ext_params` 是否符合算子功能。

## 1. audio_anomaly_filter

用途：检测音频是否异常，并把检测结果写入 `ext_params.audio_quality`。该算子输出仍应保留音频，不能只输出标签。

推荐素材：

```text
humanSpeech\zh\aishell_0000.wav
humanSpeech\en\librispeech_0000.wav
audio\summary\84-121123-0000.flac
```

测试步骤：

1. 输入数据集导入上述音频。
2. 运行 `audio_anomaly_filter`。
3. 参数先使用默认值：
   - `minDur = 1.0`
   - `maxDur = 20000.0`
   - `silenceRatioTh = 0.8`
   - `skipInvalidDownstream = true`
4. 检查输出数据集：
   - 每个输入音频都应有对应输出。
   - 正常音频应仍可作为音频被后续音频算子继续处理。
   - `ext_params.audio_quality.quality_flag` 应为 `ok` 或 `invalid`。
   - `ext_params.audio_quality.duration`、`silence_ratio`、`global_rms` 应存在。
5. 异常分支测试：
   - 将 `minDur` 设置为一个明显大于测试音频时长的值，例如 `9999`。
   - 再次运行。
   - 输出样本应被标记为 `invalid`。
   - 文件名中可能出现 `__quality_invalid_...` 标记。
   - 音频数据仍应保留，供后续算子根据 `skipInvalidDownstream` 决定是否跳过。

通过标准：

- 算子运行成功。
- 输出不丢失音频。
- `audio_quality` 质量信息完整。
- 异常参数下能正确标记异常样本。

## 2. audio_asr_transcribe

用途：输入音频，调用 ASR 模型，输出转写文本。

推荐素材：

```text
humanSpeech\zh\aishell_0000.wav
humanSpeech\zh\aishell_0001.wav
humanSpeech\en\librispeech_0000.wav
humanSpeech\en\librispeech_0001.wav
audio\summary\BAC009S0002W0122.wav
audio\summary\84-121123-0000.flac
```

前置条件：

- 中文模型目录默认应存在：

```text
/models/AudioOperations/asr/aishell
```

- 英文模型目录默认应存在：

```text
/models/AudioOperations/asr/librispeech
```

- 目录中应包含 `train.yaml`、`final.pt`、`units.txt`。

测试步骤：

1. 输入数据集导入中文和英文语音。
2. 推荐先单独测试中文：
   - 参数 `language = zh`
   - 参数 `device` 根据环境选择，优先使用实际可用设备；无 NPU 时使用 `cpu`。
   - 其他参数保持默认。
3. 运行 `audio_asr_transcribe`。
4. 检查输出数据集：
   - 输出文件应为文本。
   - 文本内容不应为空。
   - `ext_params.audio_asr_transcribe.language` 应为 `zh`。
   - `transcript_source` 应存在，通常为 `asr`。
5. 再单独测试英文：
   - 参数 `language = en`
   - 输入英文 `librispeech_*.wav`。
   - 输出文本应为英文内容，且不为空。
6. 串联测试：
   - 先运行 `audio_fast_lang_id`。
   - 将其输出数据集作为 `audio_asr_transcribe` 输入。
   - `audio_asr_transcribe` 参数设置为 `language = auto`。
   - 检查中文音频使用中文模型，英文音频使用英文模型。

通过标准：

- 算子运行成功。
- 输出类型为文本。
- 转写文本非空。
- `language = auto` 时能读取上游 LID 结果或文件名标记。

## 3. audio_dc_offset_removal

用途：去除音频直流偏置，输出处理后的 WAV 音频。

推荐素材：

```text
humanSpeech\zh\aishell_0000.wav
humanSpeech\en\librispeech_0000.wav
audio\summary\BAC009S0002W0122.wav
```

测试步骤：

1. 输入数据集导入上述音频。
2. 运行 `audio_dc_offset_removal`，无需配置参数。
3. 检查输出数据集：
   - 输出文件数量应与输入一致。
   - 输出仍应为音频文件。
   - 输出目标格式应为 `wav`。
   - 音频可以正常播放或被后续音频算子读取。
4. 可选串联验证：
   - 将输出继续输入 `audio_asr_transcribe`。
   - ASR 应能正常产生文本。

通过标准：

- 算子运行成功。
- 输出 WAV 音频可读取。
- 未把音频错误替换为空文本或标签。

## 4. audio_fast_lang_id

用途：识别语音音频语言为 `zh` 或 `en`，结果写入 `ext_params.audio_lid.lang`，同时保留原音频给下游继续使用。

推荐素材：

```text
humanSpeech\zh\aishell_0000.wav
humanSpeech\zh\aishell_0001.wav
humanSpeech\en\librispeech_0000.wav
humanSpeech\en\librispeech_0001.wav
```

前置条件：

- LID 模型目录默认应存在：

```text
/models/AudioOperations/lid/speechbrain_lang-id-voxlingua107-ecapa
```

测试步骤：

1. 输入数据集同时导入中文和英文语音。
2. 运行 `audio_fast_lang_id`。
3. 参数建议保持默认：
   - `device = cpu`
   - `maxSeconds = 3.0`
4. 检查输出数据集：
   - 输出文件数量应与输入一致。
   - 输出仍应为音频，而不是只剩 `zh` 或 `en` 文本。
   - 中文样本的 `ext_params.audio_lid.lang` 应为 `zh`。
   - 英文样本的 `ext_params.audio_lid.lang` 应为 `en`。
   - 文件名中应带有类似 `__lid_zh` 或 `__lid_en` 的标记。
5. 串联验证：
   - 将输出数据集作为 `audio_asr_transcribe` 输入。
   - `audio_asr_transcribe.language` 设置为 `auto`。
   - ASR 应能继续读取音频并输出文本。

通过标准：

- 语言标签正确。
- 输出仍保留音频。
- 能作为 ASR 的上游算子使用。

## 5. audio_fast_lang_id_text

用途：识别语音语言，并直接输出一个文本标签文件。该算子是终端标注算子，会用 `zh` 或 `en` 文本替换音频。

推荐素材：

```text
humanSpeech\zh\aishell_0000.wav
humanSpeech\en\librispeech_0000.wav
```

前置条件：

- LID 模型目录默认应存在：

```text
/models/AudioOperations/lid/speechbrain_lang-id-voxlingua107-ecapa
```

测试步骤：

1. 输入数据集导入一条中文语音和一条英文语音。
2. 运行 `audio_fast_lang_id_text`。
3. 参数建议保持默认：
   - `device = cpu`
   - `maxSeconds = 3.0`
4. 检查输出数据集：
   - 输出文件应为文本。
   - 中文音频输出文本内容应为 `zh`。
   - 英文音频输出文本内容应为 `en`。
   - 该输出不再适合作为 ASR 输入，因为音频已经被标签文本替换。

通过标准：

- 算子运行成功。
- 输出文本只包含语言标签。
- 中文/英文判断符合输入素材。

## 6. audio_format_convert

用途：转换音频格式、采样率和声道数，输出处理后的音频。

推荐素材：

```text
audio\summary\84-121123-0000.flac
audio\summary\84-121123-0001.flac
humanSpeech\zh\aishell_0000.wav
```

测试步骤：

1. 输入数据集导入 FLAC 和 WAV 音频。
2. 运行 `audio_format_convert`。
3. 推荐参数：
   - `targetFormat = wav`
   - `sampleRate = 16000`
   - `channels = 1`
4. 检查输出数据集：
   - 输出文件数量应与输入一致。
   - 输出应为 WAV 音频。
   - 音频应能正常播放或被后续算子读取。
   - `ext_params.audio_format_convert.format` 应为 `wav`。
   - `ext_params.audio_format_convert.sample_rate` 应为 `16000`。
   - `ext_params.audio_format_convert.channels` 应为 `1`。
5. 可选格式测试：
   - 将 `targetFormat` 改为 `flac` 或 `ogg`。
   - 检查输出扩展名和文件格式是否匹配。

通过标准：

- 算子运行成功。
- 输出格式、采样率、声道配置符合参数。
- 输出仍是音频，可作为下游音频算子输入。

## 7. audio_gtcrn_denoise

用途：调用 GTCRN ONNX 模型对音频降噪，输出 WAV 音频。

推荐素材：

```text
humanSpeech\zh\aishell_0000.wav
humanSpeech\en\librispeech_0000.wav
audio\summary\BAC009S0002W0122.wav
```

前置条件：

- GTCRN 模型默认应存在：

```text
/models/AudioOperations/gtcrn/gtcrn.onnx
```

测试步骤：

1. 输入数据集导入上述音频。
2. 运行 `audio_gtcrn_denoise`。
3. 参数 `modelPath` 使用默认值，或填写实际模型绝对路径。
4. 检查输出数据集：
   - 输出文件数量应与输入一致。
   - 输出应为 WAV 音频。
   - 音频应能正常播放或被后续音频算子读取。
5. 可选串联验证：
   - 将输出继续输入 `audio_asr_transcribe`。
   - ASR 应能正常输出文本。

通过标准：

- 算子运行成功。
- 输出 WAV 音频可读取。
- 模型路径不存在时应明确报错，而不是静默输出空文件。

## 8. audio_hum_notch

用途：对 50Hz 或 60Hz 工频噪声做陷波抑制，输出 WAV 音频。

推荐素材：

```text
humanSpeech\zh\aishell_0000.wav
humanSpeech\en\librispeech_0000.wav
audio\summary\BAC009S0002W0122.wav
```

前置条件：

- 运行环境应安装 `soundfile`、`numpy`、`scipy`。

测试步骤：

1. 输入数据集导入上述音频。
2. 运行 `audio_hum_notch`。
3. 推荐参数：
   - `freqHz = 50`
   - `q = 30`
4. 检查输出数据集：
   - 输出文件数量应与输入一致。
   - 输出应为 WAV 音频。
   - 音频应能正常播放或被后续音频算子读取。
5. 参数分支测试：
   - 将 `freqHz` 改为 `60`。
   - 再次运行，任务应成功。

通过标准：

- 算子运行成功。
- 50Hz 和 60Hz 参数均可运行。
- 输出仍是可读取音频。

## 9. audio_noise_gate

用途：对低于阈值的低能量音频帧做衰减，输出 WAV 音频。

推荐素材：

```text
humanSpeech\zh\aishell_0000.wav
humanSpeech\en\librispeech_0000.wav
audio\summary\BAC009S0002W0122.wav
```

前置条件：

- 运行环境应安装 `soundfile`、`numpy`。

测试步骤：

1. 输入数据集导入上述音频。
2. 运行 `audio_noise_gate`。
3. 推荐参数先使用默认值：
   - `thresholdDb = -45`
   - `frameMs = 20`
   - `hopMs = 10`
   - `floorRatio = 0.05`
4. 检查输出数据集：
   - 输出文件数量应与输入一致。
   - 输出应为 WAV 音频。
   - 音频应能正常播放或被后续音频算子读取。
5. 参数分支测试：
   - 将 `thresholdDb` 设置为 `-20`。
   - 将 `floorRatio` 设置为 `0`。
   - 再次运行，任务应成功，输出音频仍可读取。

通过标准：

- 算子运行成功。
- 默认参数和较强门限参数均可运行。
- 输出仍是可读取音频。

## 10. audio_text_summarize

用途：输入 ASR 文本，输出摘要文本。该算子输入是文本，不是音频。

推荐素材和前置流程：

建议先用以下音频跑出 ASR 文本，再把 ASR 输出数据集作为本算子的输入：

```text
audio\summary\84-121123-0000.flac
audio\summary\84-121123-0001.flac
audio\summary\BAC009S0002W0122.wav
audio\summary\BAC009S0002W0123.wav
```

测试步骤：

1. 先运行 `audio_asr_transcribe`，得到文本输出数据集。
2. 将 ASR 输出数据集作为 `audio_text_summarize` 的输入。
3. 运行 `audio_text_summarize`。
4. 推荐参数：
   - `method = extractive`
   - `lineMode = single`
   - `maxSummaryCharsZh = 40`
   - `maxSummaryWordsEn = 18`
   - `preserveKeys = true`
5. 检查输出数据集：
   - 输出文件应为文本。
   - 摘要文本不应为空。
   - 中文摘要长度应大致受 `maxSummaryCharsZh` 控制。
   - 英文摘要词数应大致受 `maxSummaryWordsEn` 控制。
   - `ext_params.audio_text_summarize.method` 应为 `extractive`。
- 模型目录默认：

```text
/models/AudioOperations/summary/summary-model
```

通过标准：

- 算子运行成功。
- 输出摘要文本非空。
- 默认 `extractive` 方法不依赖 ONNX 模型即可完成。
- 文本输入为空时，应被明确跳过或标记为空文本，不应产生异常崩溃。
