from __future__ import annotations

import importlib
import json
import os
import warnings
from contextlib import contextmanager

from ner.compat import install_compat_shims

install_compat_shims()

import torch
import torch_npu
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
modelscope_plugins = importlib.import_module("modelscope.utils.plugins")

from ner.siamese_uie_pipeline_batch import SiameseUiePipelineBatch

warnings.filterwarnings("ignore")


def _disable_modelscope_requirement_installs() -> None:
    def _skip_install_module_from_requirements(requirement_path):
        return None

    def _skip_install_requirements_by_files(requirements):
        return None

    modelscope_plugins.install_module_from_requirements = _skip_install_module_from_requirements
    modelscope_plugins.install_requirements_by_files = _skip_install_requirements_by_files


_disable_modelscope_requirement_installs()


def _patch_modelscope_npu_support() -> None:
    """Patch ModelScope runtime so this env can accept `device='npu:0'`."""
    device_mod = importlib.import_module("modelscope.utils.device")
    base_mod = importlib.import_module("modelscope.pipelines.base")

    try:
        device_mod.verify_device("npu:0")
        return
    except Exception:
        pass

    from modelscope.utils.constant import Devices, Frameworks

    logger = getattr(device_mod, "logger", None)

    def verify_device(device_name):
        err_msg = (
            "device should be either cpu, cuda, gpu, npu, gpu:X, cuda:X or "
            "npu:X where X is the ordinal for target device."
        )
        assert device_name is not None and device_name != "", err_msg
        eles = device_name.lower().split(":")
        assert len(eles) <= 2, err_msg
        assert eles[0] in ["cpu", "cuda", "gpu", "npu"], err_msg
        device_type = eles[0]
        device_id = int(eles[1]) if len(eles) > 1 else None
        if device_type == "cuda":
            device_type = Devices.gpu
        if device_type == Devices.gpu and device_id is None:
            device_id = 0
        if device_type == "npu" and device_id is None:
            device_id = 0
        return device_type, device_id

    @contextmanager
    def device_placement(framework, device_name="gpu:0"):
        device_type, device_id = verify_device(device_name)

        if framework == Frameworks.tf:
            import tensorflow as tf

            if device_type == Devices.gpu and not tf.test.is_gpu_available():
                if logger is not None:
                    logger.debug("tensorflow: cuda is not available, using cpu instead.")
                device_type = Devices.cpu

            if device_type == Devices.cpu:
                with tf.device("/CPU:0"):
                    yield
            elif device_type == Devices.gpu:
                with tf.device(f"/device:gpu:{device_id}"):
                    yield
            else:
                yield
            return

        if framework == Frameworks.torch:
            if device_type == Devices.gpu:
                if torch.cuda.is_available():
                    torch.cuda.set_device(f"cuda:{device_id}")
                elif logger is not None:
                    logger.debug("pytorch: cuda is not available, using cpu instead.")
            elif device_type == "npu":
                torch.npu.set_device(f"npu:{device_id}")
            yield
            return

        yield

    def create_device(device_name):
        device_type, device_id = verify_device(device_name)
        if device_type == "npu":
            torch_npu.npu.set_device(f"npu:{device_id}")
            return torch.device(f"npu:{device_id}")
        if device_type == Devices.gpu:
            if torch.cuda.is_available():
                return torch.device(f"cuda:{device_id}")
            if logger is not None:
                logger.info("cuda is not available, using cpu instead.")
        return torch.device("cpu")

    device_mod.verify_device = verify_device
    device_mod.device_placement = device_placement
    device_mod.create_device = create_device
    base_mod.verify_device = verify_device
    base_mod.device_placement = device_placement
    base_mod.create_device = create_device


def _move_model_to_device(model, device_name: str) -> str:
    if not hasattr(model, "to"):
        return "unsupported"

    target_device = torch.device(device_name)
    model.to(target_device)
    if hasattr(model, "eval"):
        model.eval()

    try:
        return str(next(model.parameters()).device)
    except Exception:
        return str(target_device)


class SiameseNER:
    def __init__(self, model_dir, inference_batch_size=None):
        _patch_modelscope_npu_support()

        config_path = os.path.join(model_dir, "config.json")
        if not os.path.exists(config_path):
            raise ValueError(f"config.json not found under {model_dir}")

        print(f">>> [System] Loading local model: {model_dir}")

        if torch.npu.is_available():
            self.device = "npu:0"
            torch.npu.set_device(self.device)
            print(f">>> [Device] Using Ascend NPU ({torch.npu.get_device_name(0)})")
        else:
            self.device = "cpu"
            print(">>> [Device] No NPU detected, using CPU")
        self.pipe_device = self.device

        pipeline_loaded = False
        base_pipe = None
        load_errors = []
        load_attempts = (
            ("Tasks.siamese_uie", dict(task=Tasks.siamese_uie)),
            (
                "manual siamese-uie pipeline",
                dict(task=Tasks.information_extraction, pipeline="siamese-uie"),
            ),
        )

        for label, kwargs in load_attempts:
            try:
                print(f">>> [System] Trying {label} (device={self.device})")
                base_pipe = pipeline(model=model_dir, device=self.device, **kwargs)
                self.pipe_device = str(getattr(base_pipe, "device", self.device))
                print(
                    f">>> [System] Base pipeline loaded "
                    f"(requested={self.device}, actual={self.pipe_device})"
                )
                pipeline_loaded = True
                break
            except Exception as exc:
                load_errors.append(f"{label}: {exc}")
                print(f">>> [Warning] {label} failed: {exc}")

        if not pipeline_loaded or base_pipe is None:
            raise RuntimeError("Unable to load SiameseUIE model.\n" + "\n".join(load_errors))

        if self.device.startswith("npu") and not self.pipe_device.startswith("npu"):
            raise RuntimeError(
                f"SiameseUIE did not switch to NPU. requested={self.device}, actual={self.pipe_device}"
            )

        param_device = _move_model_to_device(base_pipe.model, self.pipe_device)
        print(f">>> [Device] Model parameter device: {param_device}")

        self.pipe = SiameseUiePipelineBatch(
            model=base_pipe.model,
            preprocessor=base_pipe.preprocessor,
            device=self.pipe_device,
        )
        self.pipe.slide_len = base_pipe.slide_len
        self.pipe.max_len = base_pipe.max_len
        self.pipe.hint_max_len = base_pipe.hint_max_len

        if inference_batch_size is None:
            inference_batch_size = 64 if self.pipe_device.startswith("npu") else base_pipe.inference_batch_size

        self.pipe.inference_batch_size = inference_batch_size
        self.pipe.threshold = base_pipe.threshold
        print(
            f">>> [System] Batch pipeline ready "
            f"(device={self.pipe_device}, inference_batch_size={inference_batch_size})"
        )

        self._schema_cache = {}

    def _get_schema_dict(self, schema):
        schema_key = tuple(schema) if isinstance(schema, list) else id(schema)
        if schema_key not in self._schema_cache:
            self._schema_cache[schema_key] = {name: None for name in schema} if isinstance(schema, list) else schema
        return self._schema_cache[schema_key]

    @staticmethod
    def _flatten_result(result):
        if not result or "output" not in result:
            return []
        return [
            {
                "text": entity["span"],
                "type": entity.get("type", ""),
                "start": entity.get("offset", [0, 0])[0],
                "end": entity.get("offset", [0, 0])[1],
            }
            for entity_list in result["output"]
            for entity in entity_list
            if isinstance(entity, dict) and "span" in entity
        ]

    def extract(self, text, schema):
        if not text:
            return []

        try:
            schema_dict = self._get_schema_dict(schema)
            result = self.pipe(text, schema=schema_dict)
            return self._flatten_result(result)
        except Exception as exc:
            print(f"NER inference failed: {exc}")
            import traceback

            traceback.print_exc()
            return []

    def extract_batch(self, texts, schema):
        if not texts:
            return []

        non_empty_texts = []
        non_empty_indices = []
        for idx, text in enumerate(texts):
            if text:
                non_empty_texts.append(text)
                non_empty_indices.append(idx)

        if not non_empty_texts:
            return [[] for _ in texts]

        try:
            schema_dict = self._get_schema_dict(schema)
            results = self.pipe(non_empty_texts, schema=schema_dict)
            flattened_results = [self._flatten_result(result) for result in results]

            final_results = [[] for _ in texts]
            for idx, entities in zip(non_empty_indices, flattened_results):
                final_results[idx] = entities
            return final_results
        except Exception as exc:
            print(f"Batch NER inference failed: {exc}")
            import traceback

            traceback.print_exc()
            print(">>> [Fallback] Falling back to one-by-one inference...")

            results = [self.extract(text, schema) for text in non_empty_texts]

            final_results = [[] for _ in texts]
            for idx, entities in zip(non_empty_indices, results):
                final_results[idx] = entities
            return final_results


if __name__ == "__main__":
    local_path = "./model/SiameseUIE"
    print(f"Target model path: {os.path.abspath(local_path)}")

    try:
        ner = SiameseNER(local_path)
        text = "Patient has acute appendicitis with right lower abdominal pain."
        schema = ["Disease", "Symptom", "Drug"]
        print(f"\n[input text]: {text}")
        print(f"[schema]: {schema}")
        result = ner.extract(text, schema)
        print("\n[result]:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(f"\nProgram failed: {exc}")
