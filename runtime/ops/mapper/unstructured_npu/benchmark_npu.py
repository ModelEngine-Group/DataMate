import os
import sys
import types
import importlib.machinery
import json

# ==============================================================================
# [阶段 0] 绝对优先导入 OpenCV
# ==============================================================================
try:
    import cv2
    cv2.setNumThreads(0)
except ImportError:
    pass

# ==============================================================================
# [阶段 1] 依赖屏蔽 (The Surgical Mock - Deep Path Fix)
# ==============================================================================
class MockClass:
    """通用的伪造类，用于充当 TextBlock, UnstructuredModel 等"""
    def __init__(self, *args, **kwargs): pass
    def to_dict(self): return {}
    def initialize(self, *args, **kwargs): pass
    def predict(self, *args, **kwargs): return []

def create_fake_module(name, **kwargs):
    fake_mod = types.ModuleType(name)
    fake_mod.__file__ = f"fake_{name}.py"
    fake_mod.__path__ = []
    fake_mod.__spec__ = importlib.machinery.ModuleSpec(
        name=name, loader=None, origin=f"fake_{name}.py"
    )
    fake_mod.is_available = lambda: False
    for k, v in kwargs.items():
        setattr(fake_mod, k, v)
    return fake_mod

def mock_deep_path(full_path, **kwargs):
    """
    递归创建路径上的所有模块
    例如输入 "a.b.c"，会确保 a, a.b, a.b.c 都存在于 sys.modules
    """
    parts = full_path.split('.')
    for i in range(1, len(parts) + 1):
        curr_name = ".".join(parts[:i])
        if curr_name not in sys.modules:
            # 如果是路径终点，注入 kwargs；否则只创建空模块
            attrs = kwargs if i == len(parts) else {}
            sys.modules[curr_name] = create_fake_module(curr_name, **attrs)
            
            # 将子模块挂载到父模块 (例如将 b 挂载到 a.b)
            if i > 1:
                parent_name = ".".join(parts[:i-1])
                child_name = parts[i-1]
                setattr(sys.modules[parent_name], child_name, sys.modules[curr_name])
                
    print(f"🛡️ [Deep Mock] 已构建路径: {full_path}")

def mock_leaf(module_name, **kwargs):
    """仅屏蔽叶子，假设父模块已存在或不需要"""
    sys.modules[module_name] = create_fake_module(module_name, **kwargs)
    print(f"🛡️ [Leaf Mock] 已屏蔽: {module_name}")

# --- 开始屏蔽 ---

# 1. 彻底干掉 ONNXRuntime
mock_deep_path("onnxruntime.capi._pybind_state")
sys.modules["onnxruntime"].InferenceSession = None
sys.modules["onnxruntime"].get_available_providers = lambda: ["CPUExecutionProvider"]

# 2. 干掉 LayoutParser (关键修复：构建完整引用链)
# 报错显示代码需要 layoutparser.elements.layout.TextBlock
mock_deep_path("layoutparser.elements.layout", TextBlock=MockClass)

# 3. 干掉 Detectron2
mock_deep_path("detectron2.config")
mock_deep_path("detectron2.engine")

# 4. 干掉 Unstructured 内部模型
mock_leaf("unstructured_inference.models.chipper", 
    MODEL_TYPES={}, 
    UnstructuredChipperModel=MockClass
)
mock_leaf("unstructured_inference.models.detectron2", 
    MODEL_TYPES={},
    UnstructuredDetectronModel=MockClass
)
mock_leaf("unstructured_inference.models.detectron2onnx", 
    MODEL_TYPES={},
    UnstructuredDetectronONNXModel=MockClass
)
mock_leaf("unstructured_inference.models.super_gradients",
    UnstructuredSuperGradients=MockClass,
    UnstructuredSuperGradientsModel=MockClass
)
mock_leaf("unstructured_inference.models.paddle_ocr",
    UnstructuredPaddleOCRModel=MockClass
)

import logging
import time

# ==============================================================================
# [阶段 2] 初始化 PyTorch NPU
# ==============================================================================
import torch
try:
    import torch_npu
    torch.npu.set_device(0)
    print(f"✅ [Main Process] PyTorch NPU Initialized: {torch.npu.get_device_name(0)}")
except ImportError:
    print("❌ 严重错误: 未找到 torch_npu。")
    sys.exit(1)

# ==============================================================================
# [阶段 3] 配置环境
# ==============================================================================
os.environ["CUSTOM_DEVICE_ROOT"] = "/tmp/block_paddle_npu_in_main_process"
# 使用 hf-mirror 访问 HuggingFace
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
# 表格结构模型（table-transformer）需要从 HuggingFace 拉取/读取缓存
os.environ["HF_HUB_OFFLINE"] = "0"

sys.path.append(os.getcwd())
if os.path.exists("YOLOX-main"):
    sys.path.append(os.path.abspath("YOLOX-main"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NPU_Benchmark")

# ==============================================================================
# [阶段 4] 加载适配器
# ==============================================================================
if os.path.exists("npu_adapter.py"):
    try:
        import npu_adapter
        logger.info("应用 YOLOX NPU 补丁...")
        npu_adapter.apply_patches()
    except Exception as e:
        logger.error(f"NPU 适配器加载失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# ==============================================================================
# [阶段 5] 业务逻辑
# ==============================================================================
try:
    from unstructured.partition.pdf import partition_pdf
    from unstructured.partition.docx import partition_docx
except ImportError as e:
    logger.error(f"缺少 unstructured 库: {e}")
    sys.exit(1)

try:
    from unstructured.partition.doc import partition_doc
except ImportError:
    partition_doc = None


def save_results(file_path, elements, duration):
    output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)

    file_name = os.path.splitext(os.path.basename(file_path))[0]
    txt_path = os.path.join(output_dir, f"{file_name}_result.txt")
    json_path = os.path.join(output_dir, f"{file_name}_result.json")

    txt_sections = []
    for idx, e in enumerate(elements):
        category = getattr(e, "category", "Unknown")
        text = str(getattr(e, "text", str(e))).strip()
        meta = getattr(e, "metadata", None)
        text_as_html = getattr(meta, "text_as_html", None) if meta else None

        txt_sections.append(f"[{idx}] [{category}] {text}")
        if text_as_html:
            txt_sections.append(f"HTML: {text_as_html}")

    full_text = "\n\n".join(txt_sections)

    json_items = []
    for idx, e in enumerate(elements):
        meta = getattr(e, "metadata", None)
        coords = getattr(meta, "coordinates", None) if meta else None
        page_number = getattr(meta, "page_number", None) if meta else None
        item = {
            "index": idx,
            "category": getattr(e, "category", "Unknown"),
            "text": str(getattr(e, "text", str(e))),
            "page_number": page_number,
            "coordinates": str(coords) if coords is not None else None,
            "text_as_html": getattr(meta, "text_as_html", None) if meta else None,
        }
        json_items.append(item)

    summary = {
        "input_file": file_path,
        "duration_seconds": round(duration, 2),
        "element_count": len(elements),
        "elements": json_items,
    }

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    logger.info(f"结果已写入: {txt_path}")
    logger.info(f"结果已写入: {json_path}")

def _extract_elements(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return partition_pdf(
            filename=file_path,
            strategy="hi_res",
            hi_res_model_name="yolox",
            infer_table_structure=True,
            ocr_strategy="force",
            languages=["chi_sim", "eng"],
        ), "PyTorch Native (NPU) + Deep Mock LayoutParser"

    if ext == ".docx":
        return partition_docx(
            filename=file_path,
            infer_table_structure=True,
        ), "Word 文档解析 (docx)"

    if ext == ".doc":
        if partition_doc is None:
            raise RuntimeError("当前环境未安装 .doc 解析依赖，请先安装 unstructured[doc] 相关依赖")
        return partition_doc(
            filename=file_path,
            infer_table_structure=True,
        ), "Word 文档解析 (doc)"

    raise ValueError(f"暂不支持该文件类型: {ext}，当前仅支持 .pdf/.docx/.doc")


def run_benchmark(file_path):
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return

    logger.info(f"处理文件: {file_path}")
    
    start_time = time.time()
    
    try:
        elements, mode_desc = _extract_elements(file_path)
        logger.info(f"模式: {mode_desc}")
    except Exception as e:
        logger.error(f"处理崩溃: {e}")
        import traceback
        traceback.print_exc()
        return

    duration = time.time() - start_time
    
    if not elements:
        logger.error("未提取到元素。")
        return

    count = len(elements)
    full_text = "\n".join([str(e) for e in elements])
    
    logger.info("-" * 40)
    logger.info(f"耗时: {duration:.2f}s")
    logger.info(f"检测到元素: {count}")
    logger.info(f"字符数: {len(full_text)}")
    
    if count > 0:
        types = list(set([e.category for e in elements]))
        logger.info(f"元素类型: {types}")
        
    if len(full_text) > 0:
        logger.info(f"预览:\n{full_text[:300]}...")
    else:
        logger.warning("OCR 结果为空")

    save_results(file_path, elements, duration)
        
    logger.info("-" * 40)

if __name__ == "__main__":
    test_file = sys.argv[1] if len(sys.argv) > 1 else "attention.pdf"
    if not os.path.exists(test_file):
        if os.path.exists("test_doc.pdf"):
            test_file = "test_doc.pdf"

    if os.path.exists(test_file):
        run_benchmark(test_file)
    else:
        logger.error("找不到测试文件。")