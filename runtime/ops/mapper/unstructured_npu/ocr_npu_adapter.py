import sys
import pandas as pd
import numpy as np
import os
import warnings
import multiprocessing
import atexit
import time
import threading
import types
import importlib.util
import importlib.machinery

# ==========================================
# 0. Worker Process Logic (Isolated Environment)
# ==========================================
def _paddle_worker_main(in_queue, out_queue):
    """
    Runs in a completely separate process.
    PREVENTS Paddle from loading the NPU plugin to avoid memory conflicts.
    """
    # 1. 基础环境配置
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["Paddle_OP_PARALLELISM_THREADS"] = "1"
    
    # 2. 内存分配器优化
    os.environ["FLAGS_allocator_strategy"] = 'naive_best_fit'
    os.environ["FLAGS_fraction_of_gpu_memory_to_use"] = '0'
    os.environ["FLAGS_use_system_allocator"] = "1"

    # 3. 【核心修复】禁止加载 NPU 插件
    os.environ["CUSTOM_DEVICE_ROOT"] = "/tmp/dummy_empty_dir_for_isolation"
    
    # 4. 辅助屏蔽硬件可见性
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["ASCEND_VISIBLE_DEVICES"] = ""
    os.environ["ASCEND_RT_VISIBLE_DEVICES"] = ""
    
    try:
        import paddle
        from paddleocr import PaddleOCR
        
        warnings.filterwarnings("ignore")
        paddle.disable_signal_handler()
        
        # 显式切换到 CPU
        try:
            paddle.set_device('cpu')
        except Exception:
            pass
        
        # 初始化 OCR
        ocr_engine = PaddleOCR(
            use_angle_cls=False,
            lang="ch",      
            use_gpu=False,
            show_log=False,
            use_mp=False,
            total_process_num=0,
            enable_mkldnn=True, 
            use_tensorrt=False
        )
        
        out_queue.put(("INIT_SUCCESS", "CPU Mode (Plugin Disabled)"))
        
        while True:
            task = in_queue.get()
            if task is None: 
                break
            req_id, img_array = task
            try:
                if not isinstance(img_array, np.ndarray):
                    img_array = np.array(img_array)
                # 执行 OCR
                result = ocr_engine.ocr(img_array, cls=False)
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
        self.ctx = multiprocessing.get_context('spawn') 
        self.in_q = self.ctx.Queue()
        self.out_q = self.ctx.Queue()
        self.lock = threading.Lock()
        self.is_alive = False
        
        print(f"\n\033[94m[OCR Adapter] Spawning isolated OCR process (CPU Mode)...\033[0m")
        self.process = self.ctx.Process(
            target=_paddle_worker_main, 
            args=(self.in_q, self.out_q)
        )
        self.process.daemon = True
        self.process.start()
        
        try:
            status, msg = self.out_q.get(timeout=30) 
            if status == "INIT_SUCCESS":
                print(f"\033[92m[OCR Adapter] OCR Process Ready. [{msg}]\033[0m")
                self.is_alive = True
            else:
                print(f"\033[91m[OCR Adapter] Worker Init Failed: {msg}\033[0m")
                self.kill()
        except Exception as e:
            print(f"\033[91m[OCR Adapter] Worker Timeout/Error: {e}\033[0m")
            self.kill()

        atexit.register(self.kill)

    def kill(self):
        if self.process.is_alive():
            self.in_q.put(None)
            self.process.join(timeout=1)
            if self.process.is_alive():
                self.process.terminate()
        self.is_alive = False

    def ocr(self, img_array):
        if not self.is_alive:
            return [[]]

        with self.lock:
            req_id = time.time()
            try:
                self.in_q.put((req_id, img_array))
                resp_id, status, data = self.out_q.get(timeout=30)
                if resp_id != req_id or status == "ERROR":
                    return [[]]
                return data
            except Exception:
                self.is_alive = False
                return [[]]

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = PaddleOCRInference()
        return cls._instance

# ==========================================
# 2. Logic Implementation
# ==========================================
def _impl_paddle_to_data(image_array):
    client = PaddleOCRInference.get_instance()
    result = client.ocr(image_array)

    data = {
        'level': [], 'page_num': [], 'block_num': [], 'par_num': [], 
        'line_num': [], 'word_num': [], 'left': [], 'top': [], 
        'width': [], 'height': [], 'conf': [], 'text': []
    }

    if not result or result[0] is None:
        return pd.DataFrame(data)

    for idx, line in enumerate(result[0]):
        try:
            box, (txt, conf) = line
            xs = [pt[0] for pt in box]
            ys = [pt[1] for pt in box]
            x_min, y_min = int(min(xs)), int(min(ys))
            w, h = int(max(xs) - x_min), int(max(ys) - y_min)

            data['level'].append(5)
            data['page_num'].append(1)
            data['block_num'].append(1)
            data['par_num'].append(1)
            data['line_num'].append(idx + 1)
            data['word_num'].append(1)
            data['left'].append(x_min)
            data['top'].append(y_min)
            data['width'].append(w)
            data['height'].append(h)
            data['conf'].append(conf * 100)
            data['text'].append(txt)
        except Exception:
            continue
    return pd.DataFrame(data)

def _impl_image_to_data(image, lang=None, output_type=None, **kwargs):
    img_array = np.array(image)
    df = _impl_paddle_to_data(img_array)
    if output_type == 'data.frame': return df
    elif output_type == 'dict': return df.to_dict(orient='list')
    else: return df.to_csv(sep='\t', index=False)

def _impl_image_to_string(image, lang=None, **kwargs):
    img_array = np.array(image)
    client = PaddleOCRInference.get_instance()
    result = client.ocr(img_array)
    if result is None or len(result) == 0 or result[0] is None:
        return ""
    try:
        lines = [line[1][0] for line in result[0] if line[1]]
        return "\n".join(lines)
    except:
        return ""

def _impl_image_to_pdf(image, **kwargs): return b''

class _ImplOutput:
    BYTES = "bytes"
    DATAFRAME = "data.frame"
    DICT = "dict"
    STRING = "string"

class _ImplTesseractNotFoundError(EnvironmentError): pass

# ==========================================
# 3. Apply Patch (Module Injection)
# ==========================================
def apply_ocr_patch():
    # 使用 types.ModuleType 创建一个真实的模块对象
    # 这比使用 Class 伪装更稳定，兼容所有 inspect/importlib 检查
    fake_mod = types.ModuleType("pytesseract")
    fake_mod.__file__ = "fake_pytesseract.py"
    fake_mod.__path__ = []
    
    # 关键修复：设置真实的 ModuleSpec
    # loader=None 表示这是一个命名空间包或动态模块，这是允许的且不会报错
    fake_mod.__spec__ = importlib.machinery.ModuleSpec(
        name="pytesseract", 
        loader=None, 
        origin="fake_pytesseract.py"
    )
    
    # 挂载功能函数
    fake_mod.image_to_data = _impl_image_to_data
    fake_mod.image_to_string = _impl_image_to_string
    fake_mod.image_to_pdf_or_hocr = _impl_image_to_pdf
    fake_mod.Output = _ImplOutput
    fake_mod.TesseractNotFoundError = _ImplTesseractNotFoundError
    
    # 强制替换系统模块
    sys.modules["pytesseract"] = fake_mod
    sys.modules["unstructured_pytesseract"] = fake_mod
    
    # 尝试修补已经加载的引用
    modules_to_patch = [
        "unstructured.partition.pdf_image.ocr",
        "unstructured.partition.utils.ocr_models"
    ]
    for mod_name in modules_to_patch:
        if mod_name in sys.modules:
            try:
                sys.modules[mod_name].pytesseract = fake_mod
            except AttributeError:
                pass