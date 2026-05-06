import os
import sys
import types
import torch
import torch_npu
import numpy as np
import requests
from torchvision.ops import nms
from requests.exceptions import ConnectionError
from urllib.parse import urlparse, urlunparse

# 如用户未显式设置，默认使用 hf-mirror
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

# ==========================================
# 0. 强力断网拦截 & 基础补丁
# ==========================================
_orig_request = requests.Session.request

def mocked_request(self, method, url, *args, **kwargs):
    # 仅阻断 YOLOX 相关远程拉取，避免影响表格结构模型(table-transformer)下载
    lowered_url = str(url).lower()
    if "yolox" in lowered_url or "yolo_x_layout" in lowered_url:
        resp = requests.Response()
        resp.status_code = 404 
        return resp

    # 强制将 huggingface.co 请求路由到 HF_ENDPOINT（例如 https://hf-mirror.com）
    hf_endpoint = os.environ.get("HF_ENDPOINT", "").strip()
    if hf_endpoint and "huggingface.co" in lowered_url:
        try:
            src = urlparse(str(url))
            dst = urlparse(hf_endpoint)
            if dst.scheme and dst.netloc:
                url = urlunparse((dst.scheme, dst.netloc, src.path, src.params, src.query, src.fragment))
        except Exception:
            pass

    return _orig_request(self, method, url, *args, **kwargs)

requests.Session.request = mocked_request

# ==========================================
# 1. 定义增强版 LayoutElements
# ==========================================
class NpuLayoutElements(list):
    def __init__(self, items=None, **kwargs):
        super().__init__(items if items is not None else [])
        for k, v in kwargs.items():
            try:
                setattr(self, k, v)
            except AttributeError:
                pass

    @property
    def element_class_ids(self):
        return np.array([getattr(x, "type", "Uncategorized") for x in self])

    @property
    def element_coords(self):
        coords = []
        for el in self:
            if hasattr(el, 'bbox'):
                bbox = el.bbox
                if hasattr(bbox, 'x1'):
                    coords.append([bbox.x1, bbox.y1, bbox.x2, bbox.y2])
                elif isinstance(bbox, (list, tuple, np.ndarray)) and len(bbox) >= 4:
                    coords.append([bbox[0], bbox[1], bbox[2], bbox[3]])
                else:
                    coords.append([0, 0, 0, 0])
            elif hasattr(el, 'x1') and hasattr(el, 'y1'):
                coords.append([el.x1, el.y1, el.x2, el.y2])
            else:
                coords.append([0, 0, 0, 0])
        return np.array(coords) if coords else np.empty((0, 4))

    @property
    def x1(self): return self.element_coords[:, 0]
    @property
    def y1(self): return self.element_coords[:, 1]
    @property
    def x2(self): return self.element_coords[:, 2]
    @property
    def y2(self): return self.element_coords[:, 3]

    @property
    def texts(self):
        return np.array([getattr(x, "text", None) for x in self])

    @texts.setter
    def texts(self, values):
        for i, val in enumerate(values):
            if i < len(self):
                if hasattr(self[i], 'text'):
                    self[i].text = val
                else:
                    try:
                        setattr(self[i], 'text', val)
                    except AttributeError:
                        pass
    
    @property
    def probs(self):
        return np.array([getattr(x, "prob", 0.0) for x in self])

    def slice(self, selection):
        if isinstance(selection, np.ndarray):
            if selection.dtype == bool:
                subset = [item for item, keep in zip(self, selection) if keep]
            else:
                subset = [self[i] for i in selection]
            return NpuLayoutElements(subset)

        if isinstance(selection, list):
            subset = [self[i] for i in selection]
            return NpuLayoutElements(subset)
            
        res = super().__getitem__(selection)
        if isinstance(res, list):
            return NpuLayoutElements(res)
        return NpuLayoutElements([res])

    @classmethod
    def concatenate(cls, layouts):
        combined_items = []
        for layout in layouts:
            combined_items.extend(layout)
        return cls(items=combined_items)

# ==========================================
# 2. 核心适配器入口
# ==========================================
class NpuInferenceContext:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

# ==========================================
# 3. NPU 强力安全算子 (带同步检测)
# ==========================================

def safe_add(a, b):
    try:
        res = a + b
        torch.npu.synchronize() 
        return res
    except Exception:
        return (a.cpu() + b.cpu()).to(a.device)

def safe_cat(tensors, dim=1):
    try:
        res = torch.cat(tensors, dim=dim)
        torch.npu.synchronize() 
        return res
    except Exception:
        cpu_tensors = [t.cpu() for t in tensors]
        if not cpu_tensors: return torch.tensor([], device=tensors[0].device)
        return torch.cat(cpu_tensors, dim=dim).to(tensors[0].device)

def safe_sigmoid(x):
    try:
        res = torch.sigmoid(x)
        torch.npu.synchronize()
        return res
    except Exception:
        return torch.sigmoid(x.cpu()).to(x.device)

def safe_exp(x):
    try:
        res = torch.exp(x)
        torch.npu.synchronize()
        return res
    except Exception:
        return torch.exp(x.cpu()).to(x.device)

class SafeNpuSiLU(torch.nn.Module):
    def __init__(self, inplace=False):
        super().__init__()
    
    def forward(self, x):
        try:
            x = x.contiguous()
            res = x * torch.sigmoid(x)
            torch.npu.synchronize() 
            return res
        except Exception:
            device = x.device
            x_cpu = x.cpu()
            return (x_cpu * torch.sigmoid(x_cpu)).to(device)

class SafeNpuUpsample(torch.nn.Module):
    def __init__(self, size=None, scale_factor=None, mode='nearest', align_corners=None):
        super().__init__()
        self.size = size
        self.scale_factor = scale_factor
        self.mode = mode
        self.align_corners = align_corners
        self.op = torch.nn.Upsample(size, scale_factor, mode, align_corners)

    def forward(self, x):
        dev = x.device
        return self.op(x.cpu()).to(dev)

class SafeNpuMaxPool2d(torch.nn.Module):
    def __init__(self, kernel_size, stride=None, padding=0, dilation=1, return_indices=False, ceil_mode=False):
        super().__init__()
        self.op = torch.nn.MaxPool2d(kernel_size, stride, padding, dilation, return_indices, ceil_mode)

    def forward(self, x):
        dev = x.device
        return self.op(x.cpu()).to(dev)

# ==========================================
# 4. YOLOX 模块补丁
# ==========================================

def npu_focus_forward(self, x):
    target_device = x.device
    x_cpu = x.cpu().float()
    patch_top_left = x_cpu[..., ::2, ::2]
    patch_bot_left = x_cpu[..., 1::2, ::2]
    patch_top_right = x_cpu[..., ::2, 1::2]
    patch_bot_right = x_cpu[..., 1::2, 1::2]
    x_cat = torch.cat(
        (patch_top_left, patch_bot_left, patch_top_right, patch_bot_right),
        dim=1,
    ).contiguous()
    
    x_npu = x_cat.to(target_device)
    conv_out_npu = self.conv.conv(x_npu)
    res_cpu = conv_out_npu.cpu()
    res_cpu = res_cpu * torch.sigmoid(res_cpu)
    return res_cpu.to(target_device)

def npu_bottleneck_forward(self, x):
    y = self.conv2(self.conv1(x))
    if self.use_add:
        y = safe_add(y, x)
    return y

def npu_csplayer_forward(self, x):
    x_1 = self.conv1(x)
    x_2 = self.conv2(x)
    x_1 = self.m(x_1)
    x = safe_cat((x_1, x_2), dim=1)
    return self.conv3(x)

def npu_spp_forward(self, x):
    x = self.conv1(x)
    x_1 = self.m[0](x)
    x_2 = self.m[1](x)
    x_3 = self.m[2](x)
    x = safe_cat((x, x_1, x_2, x_3), dim=1)
    return self.conv2(x)

def npu_yolopafpn_forward(self, input):
    out_features = self.backbone(input)
    features = [out_features[f] for f in self.in_features]
    [x2, x1, x0] = features

    fpn_out0 = self.lateral_conv0(x0)
    f_out0 = self.upsample(fpn_out0)
    f_out0 = safe_cat([f_out0, x1], 1)
    f_out0 = self.C3_p4(f_out0)

    fpn_out1 = self.reduce_conv1(f_out0)
    f_out1 = self.upsample(fpn_out1)
    f_out1 = safe_cat([f_out1, x2], 1)
    pan_out2 = self.C3_p3(f_out1)

    p_out1 = self.bu_conv2(pan_out2)
    p_out1 = safe_cat([p_out1, fpn_out1], 1)
    pan_out1 = self.C3_n3(p_out1)

    p_out0 = self.bu_conv1(pan_out1)
    p_out0 = safe_cat([p_out0, fpn_out0], 1)
    pan_out0 = self.C3_n4(p_out0)

    return (pan_out2, pan_out1, pan_out0)

def npu_yolohead_forward(self, xin, labels=None, imgs=None):
    outputs = []
    for k, (cls_conv, reg_conv, stride_this_level, x) in enumerate(
        zip(self.cls_convs, self.reg_convs, self.strides, xin)
    ):
        x = self.stems[k](x)
        cls_x = x
        reg_x = x

        cls_feat = cls_conv(cls_x)
        cls_output = self.cls_preds[k](cls_feat)

        reg_feat = reg_conv(reg_x)
        reg_output = self.reg_preds[k](reg_feat)
        obj_output = self.obj_preds[k](reg_feat)

        if self.training:
            output = torch.cat(
                [reg_output, obj_output.sigmoid(), cls_output.sigmoid()], 1
            )
        else:
            sig_obj = safe_sigmoid(obj_output)
            sig_cls = safe_sigmoid(cls_output)
            output = safe_cat([reg_output, sig_obj, sig_cls], 1)

        outputs.append(output)

    if self.training:
        return outputs
    else:
        self.hw = [x.shape[-2:] for x in outputs]
        outputs_flattened = [x.flatten(start_dim=2) for x in outputs]
        cat_out = safe_cat(outputs_flattened, dim=2)
        try:
            outputs = cat_out.permute(0, 2, 1).contiguous()
            torch.npu.synchronize()
        except Exception:
            outputs = cat_out.cpu().permute(0, 2, 1).contiguous()
        
        if self.decode_in_inference:
            return self.decode_outputs(outputs, dtype=xin[0].type())
        else:
            return outputs

def npu_yolohead_decode_outputs(self, outputs, dtype=None):
    outputs = outputs.cpu()
    grids = []
    strides = []
    
    for (hsize, wsize), stride in zip(self.hw, self.strides):
        yv, xv = torch.meshgrid([torch.arange(hsize), torch.arange(wsize)])
        grid = torch.stack((xv, yv), 2).view(1, -1, 2)
        grids.append(grid)
        shape = grid.shape[:2]
        strides.append(torch.full((*shape, 1), stride))

    grids = torch.cat(grids, dim=1).type(outputs.dtype)
    strides = torch.cat(strides, dim=1).type(outputs.dtype)
    
    outputs_xy = outputs[..., :2]
    outputs_wh = outputs[..., 2:4]
    outputs_rest = outputs[..., 4:]

    outputs_xy = (outputs_xy + grids) * strides
    outputs_wh = torch.exp(outputs_wh) * strides

    return torch.cat([outputs_xy, outputs_wh, outputs_rest], dim=-1)

# ==========================================
# 5. 模型结构优化
# ==========================================

def optimize_model_for_npu(model):
    print("[NPU Adapter] Optimizing model structure for Ascend NPU...")
    from yolox.models.network_blocks import BaseConv
    import torch.nn as nn
    
    counts = {"bn_fused": 0, "silu_replaced": 0, "upsample_replaced": 0, "maxpool_replaced": 0}

    def recursive_replace(m):
        for name, child in m.named_children():
            if isinstance(child, nn.SiLU):
                setattr(m, name, SafeNpuSiLU())
                counts["silu_replaced"] += 1
            elif isinstance(child, nn.Upsample):
                safe_up = SafeNpuUpsample(
                    size=child.size, 
                    scale_factor=child.scale_factor, 
                    mode=child.mode, 
                    align_corners=child.align_corners
                )
                setattr(m, name, safe_up)
                counts["upsample_replaced"] += 1
            elif isinstance(child, nn.MaxPool2d):
                safe_pool = SafeNpuMaxPool2d(
                    kernel_size=child.kernel_size,
                    stride=child.stride,
                    padding=child.padding,
                    dilation=child.dilation,
                    return_indices=child.return_indices,
                    ceil_mode=child.ceil_mode
                )
                setattr(m, name, safe_pool)
                counts["maxpool_replaced"] += 1
            else:
                recursive_replace(child)
    
    recursive_replace(model)

    for name, m in model.named_modules():
        if isinstance(m, BaseConv):
            if hasattr(m, "bn") and isinstance(m.bn, nn.BatchNorm2d):
                conv = m.conv
                bn = m.bn
                with torch.no_grad():
                    w = conv.weight
                    if conv.bias is None:
                        b = torch.zeros(w.shape[0], device=w.device, dtype=w.dtype)
                    else:
                        b = conv.bias
                    bn_mean = bn.running_mean
                    bn_var = bn.running_var
                    bn_gamma = bn.weight
                    bn_beta = bn.bias
                    bn_eps = bn.eps
                    inv_std = 1.0 / torch.sqrt(bn_var + bn_eps)
                    w_fused = w * (bn_gamma * inv_std).reshape(-1, 1, 1, 1)
                    b_fused = (b - bn_mean) * (bn_gamma * inv_std) + bn_beta
                    m.conv.weight.copy_(w_fused)
                    if m.conv.bias is None:
                        m.conv.bias = torch.nn.Parameter(b_fused)
                    else:
                        m.conv.bias.copy_(b_fused)
                    m.bn = nn.Identity()
                    counts["bn_fused"] += 1
    
    print(f"[NPU Adapter] Optimization Stats: {counts}")

def apply_patches():
    print("[NPU Adapter] Applying monkey patches...")
    import unstructured_inference.models.base as model_base
    model_base.get_model = npu_get_model
    
    try:
        import unstructured_inference.inference.layout as layout_module
        layout_module.get_model = npu_get_model
    except ImportError: pass

    from unstructured_inference.inference.layout import PageLayout
    # 覆盖 PageLayout 的构造工厂方法
    PageLayout.from_image = classmethod(npu_pagelayout_from_image)

    from unstructured_inference.models.yolox import UnstructuredYoloXModel
    UnstructuredYoloXModel.predict = npu_yolox_predict

    import unstructured_inference.inference.layoutelement as layoutelement_pkg
    layoutelement_pkg.LayoutElements = NpuLayoutElements
    sys.modules['unstructured_inference.inference.layoutelement'].LayoutElements = NpuLayoutElements
    
    try:
        from yolox.models.network_blocks import Focus, Bottleneck, CSPLayer, SPPBottleneck
        from yolox.models.yolo_pafpn import YOLOPAFPN
        from yolox.models.yolo_head import YOLOXHead
        
        Focus.forward = npu_focus_forward
        print("✅ Patch: Focus (Hybrid CPU/NPU).")
        Bottleneck.forward = npu_bottleneck_forward
        print("✅ Patch: Bottleneck (Safe Add w/ Sync).")
        CSPLayer.forward = npu_csplayer_forward
        print("✅ Patch: CSPLayer (Safe Cat w/ Sync).")
        SPPBottleneck.forward = npu_spp_forward
        print("✅ Patch: SPPBottleneck (Safe Cat w/ Sync).")
        YOLOPAFPN.forward = npu_yolopafpn_forward
        print("✅ Patch: YOLOPAFPN (Re-implemented with Safe Cat).")
        YOLOXHead.forward = npu_yolohead_forward
        print("✅ Patch: YOLOXHead (Safe Sigmoid & Cat).")
        YOLOXHead.decode_outputs = npu_yolohead_decode_outputs
        print("✅ Patch: YOLOXHead.decode_outputs (Force CPU).")
        
    except ImportError as e:
        print(f"⚠️ Warning: Could not patch YOLOX blocks: {e}")

    print("✅ Monkey Patch: All NPU hooks applied.")

# ==========================================
# 6. 模型加载逻辑
# ==========================================
_NPU_MODEL_CACHE = {}

def npu_get_model(model_name: str, **kwargs):
    global _NPU_MODEL_CACHE
    kwargs.pop('password', None)
    
    if model_name in _NPU_MODEL_CACHE:
        return _NPU_MODEL_CACHE[model_name]

    if os.path.exists("./yolox_l.pt"):
        model_path = "./yolox_l.pt"
    else:
        model_path = "/mnt/nvme0n1/pjj-data/data/models/yolox_l.pt"
        
    print(f"[NPU Adapter] Loading local model: {model_path}")
    
    from unstructured_inference.models.yolox import UnstructuredYoloXModel
    model = UnstructuredYoloXModel()
    model.model_path = model_path
    
    try:
        ckpt = torch.load(model_path, map_location="cpu")
    except Exception:
        try:
            ckpt = torch.jit.load(model_path, map_location="cpu")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            raise FileNotFoundError(f"Model file not found or corrupted: {model_path}. Please download it.")

    if isinstance(ckpt, dict):
        state_dict = ckpt.get("model", ckpt.get("state_dict", ckpt))
    else:
        state_dict = ckpt.state_dict() if hasattr(ckpt, "state_dict") else ckpt
            
    from yolox.models import YOLOX, YOLOPAFPN, YOLOXHead
    
    num_classes = 5 
    for k, v in state_dict.items():
        if "head.cls_preds" in k and hasattr(v, "shape"):
            if v.shape[0] != num_classes:
                num_classes = v.shape[0]
            break

    def init_yolo(depth, width):
        in_channels = [256, 512, 1024]
        backbone = YOLOPAFPN(depth, width, in_channels=in_channels)
        head = YOLOXHead(num_classes, width, in_channels=in_channels)
        return YOLOX(backbone, head)

    model.model = init_yolo(1.0, 1.0)
    model.model.load_state_dict(state_dict, strict=False)
    model.model.eval()
    optimize_model_for_npu(model.model)
    
    print("Moving model to NPU (FP32)...")
    model.model.to("npu")
    
    print("[NPU Adapter] Model Ready.")
    
    _NPU_MODEL_CACHE[model_name] = model
    return model

# ==========================================
# 7. 推理逻辑重写
# ==========================================
def _local_yolox_preprocess(img, input_size, swap=(2, 0, 1)):
    import cv2
    if len(img.shape) == 3:
        padded_img = np.ones((input_size[0], input_size[1], 3), dtype=np.uint8) * 114
    else:
        padded_img = np.ones(input_size, dtype=np.uint8) * 114

    r = min(input_size[0] / img.shape[0], input_size[1] / img.shape[1])
    resized_img = cv2.resize(
        img,
        (int(img.shape[1] * r), int(img.shape[0] * r)),
        interpolation=cv2.INTER_LINEAR,
    ).astype(np.uint8)

    padded_img[: int(img.shape[0] * r), : int(img.shape[1] * r)] = resized_img
    padded_img = padded_img.transpose(swap)
    padded_img = np.ascontiguousarray(padded_img, dtype=np.float32)
    return padded_img, r

def npu_yolox_predict(self, x: np.ndarray):
    if not isinstance(x, np.ndarray):
        x = np.asarray(x)

    input_shape = (1024, 1024)
    image_h, image_w = x.shape[:2]
    preprocessed_img, ratio = _local_yolox_preprocess(x, input_shape)
    
    input_tensor = torch.from_numpy(preprocessed_img).unsqueeze(0).to("npu")
    
    with torch.no_grad():
        torch.npu.synchronize()
        outputs = self.model(input_tensor)
        torch.npu.synchronize()
        
        raw_out = outputs.get("det", outputs.get("dets")) if isinstance(outputs, dict) else outputs
            
        if raw_out is not None:
            decoder_outputs = raw_out.float().cpu()
            decoder_outputs = torch.nan_to_num(decoder_outputs, nan=0.0, posinf=10000.0, neginf=0.0)
            predictions = decoder_outputs[0]
        else:
            predictions = None
    
    if predictions is None:
        return NpuLayoutElements([])

    boxes_xywh = predictions[:, :4]
    boxes_xyxy = torch.empty_like(boxes_xywh)
    boxes_xyxy[:, 0] = boxes_xywh[:, 0] - boxes_xywh[:, 2] / 2.0
    boxes_xyxy[:, 1] = boxes_xywh[:, 1] - boxes_xywh[:, 3] / 2.0
    boxes_xyxy[:, 2] = boxes_xywh[:, 0] + boxes_xywh[:, 2] / 2.0
    boxes_xyxy[:, 3] = boxes_xywh[:, 1] + boxes_xywh[:, 3] / 2.0
    obj_scores = predictions[:, 4:5]
    cls_scores = predictions[:, 5:]
    
    cls_max_scores, cls_ids = cls_scores.max(1, keepdim=True)
    final_scores = obj_scores * cls_max_scores
    
    conf_thr = 0.1 
    mask = final_scores.squeeze() > conf_thr
    
    filtered_boxes = boxes_xyxy[mask]
    filtered_scores = final_scores[mask].squeeze()
    filtered_cls_ids = cls_ids[mask].squeeze()
    
    if len(filtered_boxes) == 0:
        return NpuLayoutElements([])

    nms_thr = 0.45
    keep_indices = nms(filtered_boxes, filtered_scores, nms_thr)
    
    final_boxes = filtered_boxes[keep_indices]
    final_scores = filtered_scores[keep_indices]
    final_cls_ids = filtered_cls_ids[keep_indices]

    final_boxes /= ratio

    # 将坐标约束到原图边界内，并修正可能出现的颠倒坐标
    x1 = torch.minimum(final_boxes[:, 0], final_boxes[:, 2]).clamp(0.0, float(image_w))
    y1 = torch.minimum(final_boxes[:, 1], final_boxes[:, 3]).clamp(0.0, float(image_h))
    x2 = torch.maximum(final_boxes[:, 0], final_boxes[:, 2]).clamp(0.0, float(image_w))
    y2 = torch.maximum(final_boxes[:, 1], final_boxes[:, 3]).clamp(0.0, float(image_h))
    final_boxes = torch.stack([x1, y1, x2, y2], dim=1)

    valid_mask = (final_boxes[:, 2] - final_boxes[:, 0] > 1.0) & (final_boxes[:, 3] - final_boxes[:, 1] > 1.0)
    final_boxes = final_boxes[valid_mask]
    final_scores = final_scores[valid_mask]
    final_cls_ids = final_cls_ids[valid_mask]

    if len(final_boxes) == 0:
        return NpuLayoutElements([])

    from unstructured_inference.inference.layoutelement import LayoutElement
    elements_list = []
    
    label_map = {
        0: "Caption", 1: "Footnote", 2: "Formula", 3: "List-item",
        4: "Page-footer", 5: "Page-header", 6: "Picture", 7: "Section-header",
        8: "Table", 9: "Text", 10: "Title"
    }

    for box, score, cls_id in zip(final_boxes, final_scores, final_cls_ids):
        x1, y1, x2, y2 = box.numpy()
        label = label_map.get(int(cls_id.item()), "Text")
        elements_list.append(LayoutElement.from_coords(x1, y1, x2, y2, text=None, type=label, prob=score.item()))
    
    return NpuLayoutElements(elements_list)

# 【核心修复】兼容当前 unstructured_inference 版本的 PageLayout.from_image
def npu_pagelayout_from_image(
    cls,
    image,
    image_path=None,
    document_filename=None,
    number=1,
    detection_model=None,
    element_extraction_model=None,
    layout=None,
    extract_tables=False,
    fixed_layout=None,
    extract_images_in_pdf=False,
    image_output_dir_path=None,
    analysis=False,
    **kwargs,
):
    if detection_model is None:
        from unstructured_inference.models.base import get_model
        detection_model = get_model("yolox", **kwargs)

    page = cls(
        number=number,
        image=image,
        layout=layout,
        detection_model=detection_model,
        element_extraction_model=element_extraction_model,
        extract_tables=extract_tables,
        analysis=analysis,
    )

    if element_extraction_model is not None:
        page.get_elements_using_image_extraction()
    elif fixed_layout is not None:
        page.elements = page.get_elements_from_layout(fixed_layout)
    else:
        inferred_layout = detection_model.predict(np.array(image))
        try:
            inferred_layout = detection_model.deduplicate_detected_elements(inferred_layout)
        except Exception:
            pass
        page.elements = page.get_elements_from_layout(inferred_layout)
        if analysis:
            page.inferred_layout = inferred_layout

    page.image_metadata = {
        "format": page.image.format if page.image else None,
        "width": page.image.width if page.image else None,
        "height": page.image.height if page.image else None,
    }
    page.image_path = os.path.abspath(image_path) if image_path else None
    page.document_filename = os.path.abspath(document_filename) if document_filename else None

    if extract_images_in_pdf:
        page.extract_images(image_output_dir_path)

    # 与原始实现保持一致，释放图片内存
    page.image = None
    return page