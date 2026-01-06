import os
import json
from pathlib import Path
from ultralytics import YOLO
import cv2
import numpy as np


def get_color_by_class_id(class_id: int):
    """根据 class_id 生成稳定颜色（BGR）"""
    np.random.seed(class_id)
    color = np.random.randint(0, 255, size=3).tolist()
    return tuple(color)


def mask_to_polygons(mask: np.ndarray):
    """将二值 mask 转换为 COCO 风格多边形列表"""
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    polygons = []
    for contour in contours:
        if contour.shape[0] < 3:
            continue
        polygon = contour.flatten().tolist()
        polygons.append(polygon)

    return polygons


IMAGE_DIR = "C:/Users/meta/Desktop/Datamate/yolo/Photos"
OUT_IMG_DIR = "outputs_seg/images"
OUT_JSON_DIR = "outputs_seg/annotations"

MODEL_MAP = {
    "n": "yolov8n-seg.pt",
    "s": "yolov8s-seg.pt",
    "m": "yolov8m-seg.pt",
    "l": "yolov8l-seg.pt",
    "x": "yolov8x-seg.pt",
}
MODEL_KEY = "x"
MODEL_PATH = MODEL_MAP[MODEL_KEY]

CONF_THRES = 0.7
DRAW_BBOX = True

COCO_CLASS_MAP = {
    0: "person", 1: "bicycle", 2: "car", 3: "motorcycle", 4: "airplane",
    5: "bus", 6: "train", 7: "truck", 8: "boat", 9: "traffic light",
    10: "fire hydrant", 11: "stop sign", 12: "parking meter", 13: "bench",
    14: "bird", 15: "cat", 16: "dog", 17: "horse", 18: "sheep", 19: "cow",
    20: "elephant", 21: "bear", 22: "zebra", 23: "giraffe", 24: "backpack",
    25: "umbrella", 26: "handbag", 27: "tie", 28: "suitcase", 29: "frisbee",
    30: "skis", 31: "snowboard", 32: "sports ball", 33: "kite",
    34: "baseball bat", 35: "baseball glove", 36: "skateboard",
    37: "surfboard", 38: "tennis racket", 39: "bottle",
    40: "wine glass", 41: "cup", 42: "fork", 43: "knife", 44: "spoon",
    45: "bowl", 46: "banana", 47: "apple", 48: "sandwich", 49: "orange",
    50: "broccoli", 51: "carrot", 52: "hot dog", 53: "pizza",
    54: "donut", 55: "cake", 56: "chair", 57: "couch",
    58: "potted plant", 59: "bed", 60: "dining table", 61: "toilet",
    62: "tv", 63: "laptop", 64: "mouse", 65: "remote",
    66: "keyboard", 67: "cell phone", 68: "microwave", 69: "oven",
    70: "toaster", 71: "sink", 72: "refrigerator", 73: "book",
    74: "clock", 75: "vase", 76: "scissors", 77: "teddy bear",
    78: "hair drier", 79: "toothbrush"
}

TARGET_CLASS_IDS = [0, 2, 5]

os.makedirs(OUT_IMG_DIR, exist_ok=True)
os.makedirs(OUT_JSON_DIR, exist_ok=True)

if TARGET_CLASS_IDS is not None:
    for cid in TARGET_CLASS_IDS:
        if cid not in COCO_CLASS_MAP:
            raise ValueError(f"Invalid class id: {cid}")

model = YOLO(MODEL_PATH)

image_paths = list(Path(IMAGE_DIR).glob("*.*"))

for img_path in image_paths:
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"[WARN] Failed to read {img_path}")
        continue

    results = model(img, conf=CONF_THRES)
    r = results[0]

    h, w = img.shape[:2]
    annotations = {
        "image": img_path.name,
        "width": w,
        "height": h,
        "model_key": MODEL_KEY,
        "conf_threshold": CONF_THRES,
        "supported_classes": COCO_CLASS_MAP,
        "selected_class_ids": TARGET_CLASS_IDS,
        "instances": []
    }

    if r.boxes is not None and r.masks is not None:
        for i, box in enumerate(r.boxes):
            cls_id = int(box.cls[0])
            if TARGET_CLASS_IDS is not None and cls_id not in TARGET_CLASS_IDS:
                continue

            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(float, box.xyxy[0])
            label = COCO_CLASS_MAP[cls_id]

            mask = r.masks.data[i].cpu().numpy()
            mask = (mask > 0.5).astype(np.uint8)
            mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)

            color = get_color_by_class_id(cls_id)
            img[mask == 1] = (
                img[mask == 1] * 0.5 + np.array(color) * 0.5
            ).astype(np.uint8)

            if True:
                cv2.rectangle(
                    img,
                    (int(x1), int(y1)),
                    (int(x2), int(y2)),
                    color,
                    2
                )

                cv2.putText(
                    img,
                    f"{label} {conf:.2f}",
                    (int(x1), max(int(y1) - 5, 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    1
                )

            polygons = mask_to_polygons(mask)

            annotations["instances"].append({
                "label": label,
                "class_id": cls_id,
                "confidence": round(conf, 4),
                "bbox_xyxy": [x1, y1, x2, y2],
                "segmentation": polygons
            })

    out_img_path = os.path.join(OUT_IMG_DIR, img_path.name)
    out_json_path = os.path.join(OUT_JSON_DIR, img_path.stem + ".json")

    cv2.imwrite(out_img_path, img)

    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(annotations, f, indent=2, ensure_ascii=False)

    print(f"[OK] {img_path.name}")

print("Segmentation batch finished.")
