# DataMate Audio Runtime Dependencies

These dependencies are runtime-level assets. They should not be vendored inside
individual audio operator directories or operator zip files.

For an already published DataMate image, place extra runtime files under the
operator dependency volume mounted at:

```text
/usr/local/lib/ops/site-packages
```

The runtime image already writes this directory into `ops.pth`, so Python
packages placed there are importable without rebuilding the image.

## Python Packages Already Expected In The Image

Use `audio_runtime_requirements.txt` for Python package installation.

Important pinned packages:

- `torch==2.8.0`
- `torch_npu==2.8.0`
- `torchaudio==2.8.0`
- `speechbrain==1.0.3`
- `pydub==0.25.1`
- `soundfile==0.12.1`
- `numpy==2.2.6`
- `scipy==1.13.1`
- `onnxruntime==1.19.2`
- `transformers==4.57.6`
- `timm==1.0.26`

## System Packages

- `ffmpeg==6.1.1` is the recommended binary version. If the image does not
  provide `ffmpeg` on `PATH`, put the executable and runtime libraries at:

```text
/usr/local/lib/ops/site-packages/ffmpeg/bin/ffmpeg
/usr/local/lib/ops/site-packages/ffmpeg/lib/*.so*
```

Audio format conversion operators will detect this path automatically. You can
override the location with `DATAMATE_OPS_SITE_PACKAGES` or `DATAMATE_FFMPEG_ROOT`.

Recommended runtime check:

```bash
DATAMATE_FFMPEG_ROOT=/usr/local/lib/ops/site-packages/ffmpeg \
  /usr/local/lib/ops/site-packages/ffmpeg/bin/ffmpeg -version
python -c "import torch, torchaudio, speechbrain, pydub, soundfile, numpy, scipy, onnxruntime, transformers, timm"
```

## WeNet

`audio_asr_transcribe` and `audio_asr_pipeline` import `wenet.bin.recognize`
from the runtime environment.

For the current deployment strategy, put WeNet source at:

```text
/usr/local/lib/ops/site-packages/wenet
```

The project previously carried duplicate WeNet source under each ASR operator.
That source has been removed from operator packages and kept as a dependency
named by package, not by operator.

The runtime must satisfy:

```bash
python -c "from wenet.bin.recognize import main"
```

Do not rely on an operator-local `local_libs/wenet` directory.

## Model Assets

Model weights are still external runtime assets and are not Python dependencies:

- LID model: `/models/AudioOperations/lid/speechbrain_lang-id-voxlingua107-ecapa`
- Chinese ASR model: `/models/AudioOperations/asr/aishell`
- English ASR model: `/models/AudioOperations/asr/librispeech`
- GTCRN model: `/models/AudioOperations/gtcrn/gtcrn.onnx`
- AST model: `/models/AudioOperations/recog/audioset_10_10_0.4593.pth`

## Operators Affected

The following operators now depend on the DataMate runtime environment instead of vendored libraries:

- `audio_fast_lang_id`
- `audio_fast_lang_id_text`
- `audio_asr_transcribe`
- `audio_asr_pipeline`
- `audio_format_convert`
- `audio_sound_classify`
