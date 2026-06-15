import atexit
import importlib
import importlib.machinery
import importlib.util
import collections
import collections.abc
import multiprocessing
import os
import sys
import threading
import time
import types
import warnings

import numpy as np
import pandas as pd

DEFAULT_MODEL_ROOT = os.environ.get("OCR_ADAPTER_MODEL_ROOT", "/root/.paddlex/official_models")
DEFAULT_CPU_DEVICE = "cpu"
DEFAULT_NPU_DEVICE = "npu"
DEFAULT_CPU_ISOLATION_ROOT = os.environ.get(
    "OCR_ADAPTER_CPU_CUSTOM_DEVICE_ROOT",
    "/tmp/dummy_empty_dir_for_isolation",
)
DEFAULT_LIBGOMP_PATH = os.environ.get(
    "OCR_ADAPTER_LIBGOMP_PATH",
    "/lib/aarch64-linux-gnu/libgomp.so.1",
)
DEFAULT_TORCH_LIBGOMP_PATH = os.environ.get(
    "OCR_ADAPTER_TORCH_LIBGOMP_PATH",
    "/usr/local/lib/python3.10/dist-packages/torch.libs/libgomp-6e1a1d1b.so.1.0.0",
)
DEFAULT_WORKER_INIT_TIMEOUT = int(os.environ.get("OCR_ADAPTER_INIT_TIMEOUT", "300"))
DEFAULT_WORKER_REQUEST_TIMEOUT = int(os.environ.get("OCR_ADAPTER_REQUEST_TIMEOUT", "180"))
ASCEND_NPU_LIBRARY_PATHS = (
    "/usr/local/Ascend/nnal/asdsip/8.5.1/lib",
    "/usr/local/Ascend/nnal/atb/8.5.1/atb/cxx_abi_0/lib",
    "/usr/local/Ascend/nnal/atb/latest/atb/cxx_abi_1/lib",
    "/usr/local/Ascend/nnal/asdsip/latest/lib",
    "/usr/local/Ascend/cann-8.5.1/lib64",
    "/usr/local/Ascend/cann-8.5.1/aarch64-linux/lib64",
    "/usr/local/Ascend/cann-8.5.1/aarch64-linux/devlib",
    "/usr/local/Ascend/ascend-toolkit/latest/lib64",
    "/usr/local/Ascend/ascend-toolkit/latest/aarch64-linux/lib64",
    "/usr/local/Ascend/driver/lib64",
    "/usr/local/Ascend/driver/lib64/driver",
    "/usr/local/Ascend/driver/lib64/common",
)

_REAL_PYTESSERACT = None
_REAL_UNSTRUCTURED_PYTESSERACT = None


def _patch_legacy_collections_aliases():
    for name in ("Mapping", "MutableMapping", "Sequence"):
        if not hasattr(collections, name):
            setattr(collections, name, getattr(collections.abc, name))


def _normalize_device(device):
    return DEFAULT_NPU_DEVICE if str(device).strip().lower() == DEFAULT_NPU_DEVICE else DEFAULT_CPU_DEVICE


def _env_flag(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _native_fallback_disabled():
    return _env_flag("OCR_ADAPTER_DISABLE_NATIVE_FALLBACK", False)


def _select_mp_context_name(device):
    requested = os.environ.get("OCR_ADAPTER_MP_CONTEXT")
    return requested or "fork"


def _worker_env_overrides(device):
    env = {
        "OCR_ADAPTER_WORKER": "1",
        "OCR_ADAPTER_DEVICE": device,
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "Paddle_OP_PARALLELISM_THREADS": "1",
        "FLAGS_allocator_strategy": "naive_best_fit",
        "FLAGS_fraction_of_gpu_memory_to_use": "0",
        "FLAGS_use_system_allocator": "1",
        "PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK": "True",
    }
    if device == DEFAULT_CPU_DEVICE:
        os.makedirs(DEFAULT_CPU_ISOLATION_ROOT, exist_ok=True)
        env.update(
            {
                "CUSTOM_DEVICE_ROOT": DEFAULT_CPU_ISOLATION_ROOT,
                "CUDA_VISIBLE_DEVICES": "",
                "ASCEND_VISIBLE_DEVICES": "",
                "ASCEND_RT_VISIBLE_DEVICES": "",
            }
        )
    else:
        env["CUSTOM_DEVICE_ROOT"] = ""
    return env


def _safe_int(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _resolve_model(kind):
    if kind == "det":
        name_env = "OCR_ADAPTER_TEXT_DET_MODEL_NAME"
        dir_env = "OCR_ADAPTER_TEXT_DET_MODEL_DIR"
        default_name = "PP-OCRv4_mobile_det"
    elif kind == "rec":
        name_env = "OCR_ADAPTER_TEXT_REC_MODEL_NAME"
        dir_env = "OCR_ADAPTER_TEXT_REC_MODEL_DIR"
        default_name = "PP-OCRv4_mobile_rec"
    else:
        raise ValueError(f"Unknown model kind: {kind}")

    model_name = os.environ.get(name_env, default_name).strip()
    explicit_dir = os.environ.get(dir_env)
    if explicit_dir and os.path.isdir(explicit_dir):
        return model_name, explicit_dir

    candidate_dir = os.path.join(DEFAULT_MODEL_ROOT, model_name)
    if model_name and os.path.isdir(candidate_dir):
        return model_name, candidate_dir

    return model_name, explicit_dir or None


def _build_paddleocr_init_kwargs(device):
    det_name, det_dir = _resolve_model("det")
    rec_name, rec_dir = _resolve_model("rec")
    try:
        from paddleocr import VERSION as paddleocr_version
    except Exception:
        paddleocr_version = ""
    is_legacy_paddleocr = str(paddleocr_version).startswith("2.")
    kwargs = {
        "lang": os.environ.get("OCR_ADAPTER_LANG", "ch"),
        "show_log": False,
        "use_angle_cls": False,
    }
    if not is_legacy_paddleocr:
        kwargs.update(
            {
                "use_doc_orientation_classify": False,
                "use_doc_unwarping": False,
                "use_textline_orientation": False,
            }
        )

    if det_name and not is_legacy_paddleocr:
        kwargs["text_detection_model_name"] = det_name
    if det_dir:
        if not is_legacy_paddleocr:
            kwargs["text_detection_model_dir"] = det_dir
        kwargs["det_model_dir"] = det_dir
    if rec_name and not is_legacy_paddleocr:
        kwargs["text_recognition_model_name"] = rec_name
    if rec_dir:
        if not is_legacy_paddleocr:
            kwargs["text_recognition_model_dir"] = rec_dir
        kwargs["rec_model_dir"] = rec_dir
    cls_dir = os.environ.get("OCR_ADAPTER_TEXT_CLS_MODEL_DIR")
    if cls_dir and os.path.isdir(cls_dir):
        kwargs["cls_model_dir"] = cls_dir

    if device == DEFAULT_CPU_DEVICE:
        kwargs["enable_mkldnn"] = _env_flag("OCR_ADAPTER_ENABLE_MKLDNN", True)
        kwargs["cpu_threads"] = _safe_int("OCR_ADAPTER_CPU_THREADS", 1)
        kwargs["use_gpu"] = False
    else:
        if not is_legacy_paddleocr:
            kwargs["device"] = device
        kwargs["use_gpu"] = False
        kwargs["use_npu"] = True

    model_desc = f"det={det_dir or det_name}, rec={rec_dir or rec_name}"
    return kwargs, model_desc


def _configure_worker_env(device):
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["Paddle_OP_PARALLELISM_THREADS"] = "1"
    os.environ["FLAGS_allocator_strategy"] = "naive_best_fit"
    os.environ["FLAGS_fraction_of_gpu_memory_to_use"] = "0"
    os.environ["FLAGS_use_system_allocator"] = "1"
    os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

    if device == DEFAULT_CPU_DEVICE:
        os.makedirs(DEFAULT_CPU_ISOLATION_ROOT, exist_ok=True)
        os.environ["CUSTOM_DEVICE_ROOT"] = DEFAULT_CPU_ISOLATION_ROOT
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        os.environ["ASCEND_VISIBLE_DEVICES"] = ""
        os.environ["ASCEND_RT_VISIBLE_DEVICES"] = ""
    else:
        os.environ.pop("CUSTOM_DEVICE_ROOT", None)
        _prepend_ld_library_paths(ASCEND_NPU_LIBRARY_PATHS)


def _prepend_ld_library_paths(paths):
    current = [part for part in os.environ.get("LD_LIBRARY_PATH", "").split(":") if part]
    merged = []
    for path in list(paths) + current:
        if path and os.path.exists(path) and path not in merged:
            merged.append(path)
    if merged:
        os.environ["LD_LIBRARY_PATH"] = ":".join(merged)


def _merge_ld_preload():
    current = os.environ.get("LD_PRELOAD", "")
    parts = [part for part in current.split(":") if part]
    for candidate in (DEFAULT_TORCH_LIBGOMP_PATH, DEFAULT_LIBGOMP_PATH):
        if os.path.exists(candidate) and candidate not in parts:
            parts.insert(0, candidate)
    return ":".join(parts)


def _load_native_tesseract_modules():
    global _REAL_PYTESSERACT, _REAL_UNSTRUCTURED_PYTESSERACT

    if _REAL_PYTESSERACT is None:
        _REAL_PYTESSERACT = importlib.import_module("pytesseract")

    if _REAL_UNSTRUCTURED_PYTESSERACT is None:
        try:
            _REAL_UNSTRUCTURED_PYTESSERACT = importlib.import_module("unstructured_pytesseract")
        except ImportError:
            _REAL_UNSTRUCTURED_PYTESSERACT = _REAL_PYTESSERACT


def _prefer_native_cpu_ocr():
    return (
        _normalize_device(os.environ.get("OCR_ADAPTER_DEVICE", DEFAULT_CPU_DEVICE)) == DEFAULT_CPU_DEVICE
        and not _env_flag("OCR_ADAPTER_FORCE_PADDLE_CPU", False)
    )


def _paddle_ocr_available():
    try:
        if _normalize_device(os.environ.get("OCR_ADAPTER_DEVICE", DEFAULT_CPU_DEVICE)) == DEFAULT_NPU_DEVICE:
            return importlib.util.find_spec("paddle") is not None and importlib.util.find_spec("paddleocr") is not None
        else:
            # Do not import Paddle in the parent process for CPU OCR. In mixed
            # Torch-NPU + PaddleOCR runs, importing Paddle here may load the
            # custom NPU plugin before the worker has isolated CUSTOM_DEVICE_ROOT.
            return importlib.util.find_spec("paddle") is not None and importlib.util.find_spec("paddleocr") is not None
    except ImportError:
        return False


def _native_pytesseract_module():
    return _REAL_UNSTRUCTURED_PYTESSERACT or _REAL_PYTESSERACT


def _map_native_output_type(output_type):
    native_mod = _native_pytesseract_module()
    if native_mod is None:
        return output_type

    output_map = {
        None: None,
        _ImplOutput.DATAFRAME: native_mod.Output.DATAFRAME,
        "data.frame": native_mod.Output.DATAFRAME,
        _ImplOutput.DICT: native_mod.Output.DICT,
        "dict": native_mod.Output.DICT,
        _ImplOutput.STRING: native_mod.Output.STRING,
        "string": native_mod.Output.STRING,
    }

    if hasattr(native_mod.Output, "BYTES"):
        output_map[_ImplOutput.BYTES] = native_mod.Output.BYTES
        output_map["bytes"] = native_mod.Output.BYTES

    return output_map.get(output_type, output_type)


def _native_image_to_data(image, lang=None, output_type=None, **kwargs):
    native_mod = _native_pytesseract_module()
    if native_mod is None:
        raise _ImplTesseractNotFoundError("原生 pytesseract 不可用")

    native_output_type = _map_native_output_type(output_type)
    return native_mod.image_to_data(
        image,
        lang=lang,
        output_type=native_output_type,
        **kwargs,
    )


def _native_image_to_string(image, lang=None, **kwargs):
    native_mod = _native_pytesseract_module()
    if native_mod is None:
        raise _ImplTesseractNotFoundError("原生 pytesseract 不可用")
    return native_mod.image_to_string(image, lang=lang, **kwargs)


def _native_image_to_pdf(image, **kwargs):
    native_mod = _native_pytesseract_module()
    if native_mod is None:
        raise _ImplTesseractNotFoundError("原生 pytesseract 不可用")
    return native_mod.image_to_pdf_or_hocr(image, **kwargs)


def _legacy_paddle_from_tesseract(image, lang=None, **kwargs):
    data = _native_image_to_data(image, lang=lang, output_type=_ImplOutput.DICT, **kwargs) or {}
    texts = data.get("text", []) or []
    lefts = data.get("left", []) or []
    tops = data.get("top", []) or []
    widths = data.get("width", []) or []
    heights = data.get("height", []) or []
    confs = data.get("conf", []) or []

    page_lines = []
    for idx, text in enumerate(texts):
        text = str(text or "").strip()
        if not text:
            continue

        try:
            conf = float(confs[idx]) if idx < len(confs) else -1.0
        except (TypeError, ValueError):
            conf = -1.0
        if conf < 0:
            continue

        x = int(float(lefts[idx])) if idx < len(lefts) else 0
        y = int(float(tops[idx])) if idx < len(tops) else 0
        w = int(float(widths[idx])) if idx < len(widths) else 0
        h = int(float(heights[idx])) if idx < len(heights) else 0
        quad = [
            [x, y],
            [x + w, y],
            [x + w, y + h],
            [x, y + h],
        ]
        page_lines.append([quad, (text, conf / 100.0)])

    return [page_lines]


def _iter_ocr_lines(result):
    if not result:
        return

    first_item = result[0]
    if isinstance(first_item, dict):
        for page in result:
            texts = page.get("rec_texts") or []
            scores = page.get("rec_scores") or []
            polys = page.get("rec_polys") or page.get("dt_polys") or []
            boxes = page.get("rec_boxes")

            for idx, text in enumerate(texts):
                if not text:
                    continue

                conf = float(scores[idx]) if idx < len(scores) and scores[idx] is not None else 0.0
                box = None
                if idx < len(polys):
                    box = polys[idx]
                elif boxes is not None and idx < len(boxes):
                    box = boxes[idx]
                yield box, str(text), conf
        return

    if isinstance(first_item, list):
        for line in first_item:
            if not line:
                continue
            try:
                box, (text, conf) = line
            except (TypeError, ValueError):
                continue
            if text:
                yield box, str(text), float(conf)


def _to_quad(box):
    if box is None:
        return None

    if hasattr(box, "tolist"):
        box = box.tolist()

    if not box:
        return None

    if len(box) == 4 and not isinstance(box[0], (list, tuple)):
        x1, y1, x2, y2 = [float(v) for v in box]
        return [
            [x1, y1],
            [x2, y1],
            [x2, y2],
            [x1, y2],
        ]

    quad = []
    for point in box:
        if hasattr(point, "tolist"):
            point = point.tolist()
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            continue
        quad.append([float(point[0]), float(point[1])])
    return quad or None


def _box_to_xywh(box):
    quad = _to_quad(box)
    if not quad:
        return 0, 0, 0, 0

    xs = [pt[0] for pt in quad]
    ys = [pt[1] for pt in quad]
    x_min = int(min(xs))
    y_min = int(min(ys))
    width = int(max(xs) - x_min)
    height = int(max(ys) - y_min)
    return x_min, y_min, width, height


def _result_to_legacy_paddle(result):
    if not result:
        return [[]]

    first_item = result[0]
    if isinstance(first_item, list):
        return result

    legacy_pages = []
    for page in result:
        page_lines = []
        texts = page.get("rec_texts") or []
        scores = page.get("rec_scores") or []
        polys = page.get("rec_polys") or page.get("dt_polys") or []
        boxes = page.get("rec_boxes")

        for idx, text in enumerate(texts):
            if not text:
                continue

            conf = float(scores[idx]) if idx < len(scores) and scores[idx] is not None else 0.0
            if idx < len(polys):
                quad = _to_quad(polys[idx])
            elif boxes is not None and idx < len(boxes):
                quad = _to_quad(boxes[idx])
            else:
                quad = None

            if quad:
                page_lines.append([quad, (str(text), conf)])

        legacy_pages.append(page_lines)

    return legacy_pages or [[]]

# ==========================================
# 0. Worker Process Logic (Isolated Environment)
# ==========================================
def _paddle_worker_main(in_queue, out_queue):
    """
    Runs in a completely separate process.
    PREVENTS Paddle from loading the NPU plugin to avoid memory conflicts.
    """
    device = _normalize_device(os.environ.get("OCR_ADAPTER_DEVICE", DEFAULT_CPU_DEVICE))
    _configure_worker_env(device)

    try:
        warnings.filterwarnings("ignore")
        _patch_legacy_collections_aliases()
        init_kwargs, model_desc = _build_paddleocr_init_kwargs(device)

        if device == DEFAULT_NPU_DEVICE:
            from paddleocr import PaddleOCR

            ocr_engine = PaddleOCR(**init_kwargs)
        else:
            import paddle
            from paddleocr import PaddleOCR

            paddle.disable_signal_handler()
            paddle.set_device(DEFAULT_CPU_DEVICE)
            ocr_engine = PaddleOCR(**init_kwargs)

        out_queue.put(("INIT_SUCCESS", f"{device.upper()} Mode [{model_desc}]"))

        while True:
            task = in_queue.get()
            if task is None:
                break
            req_id, img_array = task
            try:
                if not isinstance(img_array, np.ndarray):
                    img_array = np.array(img_array)
                result = _result_to_legacy_paddle(ocr_engine.ocr(img_array))
                out_queue.put((req_id, "OK", result))
            except Exception as e:
                out_queue.put((req_id, "ERROR", str(e)))

    except Exception as e:
        out_queue.put(("INIT_ERROR", f"Worker Crash: {str(e)}"))

# ==========================================
# 1. OCR Client (Main Process)
# ==========================================
class PaddleOCRInference:
    _instance = None
    
    def __init__(self):
        self.device = _normalize_device(os.environ.get("OCR_ADAPTER_DEVICE", DEFAULT_CPU_DEVICE))
        self.native_only = _prefer_native_cpu_ocr()
        self.last_error = ""
        if not self.native_only and not _paddle_ocr_available():
            self.native_only = True
            self.is_alive = False
            self.last_error = "PaddleOCR dependencies are unavailable; using native OCR fallback"
            print(f"\033[93m[OCR Adapter] {self.last_error}\033[0m")
            atexit.register(self.kill)
            return

        self.ctx = multiprocessing.get_context(_select_mp_context_name(self.device))
        self.in_q = self.ctx.Queue()
        self.out_q = self.ctx.Queue()
        self.lock = threading.Lock()
        self.is_alive = False

        if self.native_only:
            print(
                "\n\033[94m[OCR Adapter] CPU 模式下直接回退原生 pytesseract，"
                "避免 Paddle OCR 兼容性风险。\033[0m"
            )
            atexit.register(self.kill)
            return

        print(
            f"\n\033[94m[OCR Adapter] Spawning isolated OCR process "
            f"({self.device.upper()} Mode)...\033[0m"
        )

        env_overrides = _worker_env_overrides(self.device)
        preload_value = _merge_ld_preload()
        if preload_value:
            env_overrides["LD_PRELOAD"] = preload_value

        previous_env = {key: os.environ.get(key) for key in env_overrides}
        for key, value in env_overrides.items():
            if value == "":
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

        self.process = self.ctx.Process(
            target=_paddle_worker_main,
            args=(self.in_q, self.out_q),
        )
        self.process.daemon = True
        try:
            self.process.start()
        finally:
            for key, old_value in previous_env.items():
                if old_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = old_value

        try:
            status, msg = self.out_q.get(timeout=DEFAULT_WORKER_INIT_TIMEOUT)
            if status == "INIT_SUCCESS":
                print(f"\033[92m[OCR Adapter] OCR Process Ready. [{msg}]\033[0m")
                self.is_alive = True
                self.last_error = ""
            else:
                print(f"\033[91m[OCR Adapter] Worker Init Failed: {msg}\033[0m")
                self.last_error = str(msg)
                self.kill()
        except Exception as e:
            print(f"\033[91m[OCR Adapter] Worker Timeout/Error: {e}\033[0m")
            self.last_error = str(e)
            self.kill()

        atexit.register(self.kill)

    def kill(self):
        if hasattr(self, "process") and self.process.is_alive():
            self.in_q.put(None)
            self.process.join(timeout=10)
            if self.process.is_alive():
                self.process.terminate()
        self.is_alive = False

    def ocr(self, img_array):
        if self.native_only or not self.is_alive:
            return None

        with self.lock:
            req_id = time.time()
            try:
                self.in_q.put((req_id, img_array))
                resp_id, status, data = self.out_q.get(timeout=DEFAULT_WORKER_REQUEST_TIMEOUT)
                if resp_id != req_id:
                    self.last_error = "OCR worker response id mismatch"
                    return None
                if status == "ERROR":
                    self.last_error = str(data)
                    return None
                self.last_error = ""
                return data
            except Exception:
                self.is_alive = False
                self.last_error = "OCR worker request failed"
                return None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = PaddleOCRInference()
        return cls._instance


def get_ocr_runtime_status():
    instance = PaddleOCRInference.get_instance()
    return {
        "available": bool(getattr(instance, "is_alive", False)) and not bool(getattr(instance, "native_only", True)),
        "device": getattr(instance, "device", DEFAULT_CPU_DEVICE),
        "native_only": bool(getattr(instance, "native_only", True)),
        "is_alive": bool(getattr(instance, "is_alive", False)),
        "last_error": getattr(instance, "last_error", ""),
    }


class UnstructuredPaddleOCRProxy:
    def __init__(self, *args, **kwargs):
        self.client = PaddleOCRInference.get_instance()

    def ocr(self, img_array, cls=False, **kwargs):
        lang = kwargs.get("lang")
        if self.client.native_only:
            if _native_fallback_disabled():
                raise RuntimeError("OCR native fallback is disabled")
            return _legacy_paddle_from_tesseract(np.array(img_array), lang=lang)

        result = self.client.ocr(np.array(img_array))
        if result is None:
            if _native_fallback_disabled():
                raise RuntimeError("OCR NPU inference failed and native fallback is disabled")
            return _legacy_paddle_from_tesseract(np.array(img_array), lang=lang)
        return _result_to_legacy_paddle(result)

    predict = ocr


# ==========================================
# 2. Logic Implementation
# ==========================================
def _impl_paddle_to_data(image_array):
    client = PaddleOCRInference.get_instance()
    if client.native_only:
        if _native_fallback_disabled():
            raise RuntimeError("OCR native fallback is disabled")
        return _native_image_to_data(image_array, output_type=_ImplOutput.DATAFRAME)

    result = client.ocr(image_array)
    if result is None:
        if _native_fallback_disabled():
            raise RuntimeError("OCR NPU inference failed and native fallback is disabled")
        return _native_image_to_data(image_array, output_type=_ImplOutput.DATAFRAME)

    data = {
        'level': [], 'page_num': [], 'block_num': [], 'par_num': [], 
        'line_num': [], 'word_num': [], 'left': [], 'top': [], 
        'width': [], 'height': [], 'conf': [], 'text': []
    }

    if not result or result[0] is None:
        return pd.DataFrame(data)

    for idx, (box, text, conf) in enumerate(_iter_ocr_lines(result)):
        x_min, y_min, width, height = _box_to_xywh(box)
        data["level"].append(5)
        data["page_num"].append(1)
        data["block_num"].append(1)
        data["par_num"].append(1)
        data["line_num"].append(idx + 1)
        data["word_num"].append(1)
        data["left"].append(x_min)
        data["top"].append(y_min)
        data["width"].append(width)
        data["height"].append(height)
        data["conf"].append(conf * 100)
        data["text"].append(text)
    return pd.DataFrame(data)


def _impl_image_to_data(image, lang=None, output_type=None, **kwargs):
    img_array = np.array(image)
    client = PaddleOCRInference.get_instance()
    if client.native_only or not client.is_alive:
        if _native_fallback_disabled():
            raise RuntimeError("OCR native fallback is disabled")
        return _native_image_to_data(image, lang=lang, output_type=output_type, **kwargs)

    df = _impl_paddle_to_data(img_array)
    if output_type in (_ImplOutput.DATAFRAME, "data.frame"):
        return df
    if output_type in (_ImplOutput.DICT, "dict"):
        return df.to_dict(orient="list")
    return df.to_csv(sep="\t", index=False)


def _impl_image_to_string(image, lang=None, **kwargs):
    img_array = np.array(image)
    client = PaddleOCRInference.get_instance()
    if client.native_only:
        if _native_fallback_disabled():
            raise RuntimeError("OCR native fallback is disabled")
        return _native_image_to_string(image, lang=lang, **kwargs)

    result = client.ocr(img_array)
    if result is None:
        if _native_fallback_disabled():
            raise RuntimeError("OCR NPU inference failed and native fallback is disabled")
        return _native_image_to_string(image, lang=lang, **kwargs)
    if not result or result[0] is None:
        return ""

    lines = [text for _, text, _ in _iter_ocr_lines(result)]
    return "\n".join(lines)


def _impl_image_to_pdf(image, **kwargs):
    client = PaddleOCRInference.get_instance()
    if client.native_only or not client.is_alive:
        if _native_fallback_disabled():
            raise RuntimeError("OCR native fallback is disabled")
        try:
            return _native_image_to_pdf(image, **kwargs)
        except Exception:
            return b""
    return b""


class _ImplOutput:
    BYTES = "bytes"
    DATAFRAME = "data.frame"
    DICT = "dict"
    STRING = "string"


class _ImplTesseractNotFoundError(EnvironmentError):
    pass

# ==========================================
# 3. Apply Patch (Module Injection)
# ==========================================
def apply_ocr_patch():
    if not _native_fallback_disabled() and not _env_flag("OCR_ADAPTER_FORCE_PADDLE_CPU", False):
        _load_native_tesseract_modules()

    fake_mod = types.ModuleType("pytesseract")
    fake_mod.__file__ = "fake_pytesseract.py"
    fake_mod.__path__ = []
    fake_mod.__spec__ = importlib.machinery.ModuleSpec(
        name="pytesseract",
        loader=None,
        origin="fake_pytesseract.py",
    )

    fake_mod.image_to_data = _impl_image_to_data
    fake_mod.image_to_string = _impl_image_to_string
    fake_mod.image_to_pdf_or_hocr = _impl_image_to_pdf
    fake_mod.Output = _ImplOutput
    fake_mod.TesseractNotFoundError = _ImplTesseractNotFoundError

    fake_unstructured_paddleocr = types.ModuleType("unstructured_paddleocr")
    fake_unstructured_paddleocr.__file__ = "fake_unstructured_paddleocr.py"
    fake_unstructured_paddleocr.__path__ = []
    fake_unstructured_paddleocr.__spec__ = importlib.machinery.ModuleSpec(
        name="unstructured_paddleocr",
        loader=None,
        origin="fake_unstructured_paddleocr.py",
    )
    fake_unstructured_paddleocr.PaddleOCR = UnstructuredPaddleOCRProxy

    sys.modules["pytesseract"] = fake_mod
    sys.modules["unstructured_pytesseract"] = fake_mod
    sys.modules["unstructured_paddleocr"] = fake_unstructured_paddleocr

    modules_to_patch = [
        "unstructured.partition.ocr",
        "unstructured.partition.utils.ocr_models",
    ]
    for mod_name in modules_to_patch:
        if mod_name in sys.modules:
            try:
                sys.modules[mod_name].pytesseract = fake_mod
            except AttributeError:
                pass
            try:
                sys.modules[mod_name].unstructured_pytesseract = fake_mod
            except AttributeError:
                pass
