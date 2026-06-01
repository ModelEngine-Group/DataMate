# DataMate Audio Runtime Dependencies

These dependencies should be installed in the DataMate runtime environment. They should not be vendored inside individual audio operator directories.

## Python Packages

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
- `panns-inference==0.1.1`

## System Packages

- `ffmpeg==6.1.1` is the recommended runtime binary version. `pydub` uses the `ffmpeg` command on `PATH` for formats such as `mp3`, `aac`, `m4a`, and some `flac` paths. If the DataMate base image must use OS packages, keep the installed `ffmpeg` at `>=4.4` and record the exact OS package version in the image build manifest.

Recommended runtime check:

```bash
ffmpeg -version
python -c "import torch, torchaudio, speechbrain, pydub, soundfile, numpy, scipy, onnxruntime, transformers, timm"
```

## WeNet

`audio_asr_transcribe` and `audio_asr_pipeline` import `wenet.bin.recognize` from the runtime environment.

The project previously carried WeNet source under each ASR operator. That source has been removed from the operator package. The removed vendored source does not expose a package version in `wenet/__init__.py`, so this cleanup cannot derive a reliable semantic version from the previous copy. Since `wenet` is not available as a normal PyPI package in this environment, DataMate deployment must provide WeNet with a fixed source pin and record that pin as the runtime version, using one of:

- an internal wheel with a fixed version, installed into the runtime image;
- a fixed git tag or commit of `wenet-e2e/wenet`, installed during image build;
- a system Python package placed on the runtime `PYTHONPATH`.

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
- PANNs model: `/models/AudioOperations/panns/Cnn14_16k_mAP=0.438.pth`

## Operators Affected

The following operators now depend on the DataMate runtime environment instead of vendored libraries:

- `audio_fast_lang_id`
- `audio_fast_lang_id_text`
- `audio_asr_transcribe`
- `audio_asr_pipeline`
- `audio_format_convert`
- `audio_sound_classify`
