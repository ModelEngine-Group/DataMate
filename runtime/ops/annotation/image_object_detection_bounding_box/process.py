#!/user/bin/python
# -- encoding: utf-8 --

"""
Description: 图像目标检测算子
Create: 2025/12/17
"""
import os
import json
import time
from typing import Dict, Any
import cv2
import numpy as np
from loguru import logger

try:
    from ultralytics import YOLO
except ImportError:
    logger.warning("ultralytics not installed. Please install it using: pip install ultralytics")
    YOLO = None

from datamate.core.base_op import Mapper


# COCO 80 类别映射
COCO_CLASS_MAP = {
    0: "Person", 1: "Bicycle", 2: "Car", 3: "Motorcycle", 4: "Airplane",
    5: "Bus", 6: "Train", 7: "Truck", 8: "Boat", 9: "Traffic Light",
    10: "Fire Hydrant", 11: "Stop Sign", 12: "Parking Meter", 13: "Bench",
    14: "Bird", 15: "Cat", 16: "Dog", 17: "Horse", 18: "Sheep", 19: "Cow",
    20: "Elephant", 21: "Bear", 22: "Zebra", 23: "Giraffe", 24: "Backpack",
    25: "Umbrella", 26: "Handbag", 27: "Tie", 28: "Suitcase", 29: "Frisbee",
    30: "Skis", 31: "Snowboard", 32: "Sports Ball", 33: "Kite",
    34: "Baseball Bat", 35: "Baseball Glove", 36: "Skateboard",
    37: "Surfboard", 38: "Tennis Racket", 39: "Bottle",
    40: "Wine Glass", 41: "Cup", 42: "Fork", 43: "Knife", 44: "Spoon",
    45: "Bowl", 46: "Banana", 47: "Apple", 48: "Sandwich", 49: "Orange",
    50: "Broccoli", 51: "Carrot", 52: "Hot Dog", 53: "Pizza",
    54: "Donut", 55: "Cake", 56: "Chair", 57: "Couch",
    58: "Potted Plant", 59: "Bed", 60: "Dining Table", 61: "Toilet",
    62: "TV", 63: "Laptop", 64: "Mouse", 65: "Remote",
    66: "Keyboard", 67: "Cell Phone", 68: "Microwave", 69: "Oven",
    70: "Toaster", 71: "Sink", 72: "Refrigerator", 73: "Book",
    74: "Clock", 75: "Vase", 76: "Scissors", 77: "Teddy Bear",
    78: "Hair Drier", 79: "Toothbrush"
}


class ImageObjectDetectionBoundingBox(Mapper):
    """图像目标检测算子"""

    # 模型映射
    MODEL_MAP = {
        "n": "yolov8n.pt",
        "s": "yolov8s.pt",
        "m": "yolov8m.pt",
        "l": "yolov8l.pt",
        "x": "yolov8x.pt",
    }

    def __init__(self, *args, **kwargs):
        super(ImageObjectDetectionBoundingBox, self).__init__(*args, **kwargs)
        
        # 获取参数
        self._model_size = kwargs.get("modelSize", "l")
        self._conf_threshold = kwargs.get("confThreshold", 0.7)
        self._target_classes = kwargs.get("targetClasses", [])
        self._output_dir = kwargs.get("outputDir", None)  # 输出目录
        
        # 如果目标类别为空列表，则检测所有类别
        if not self._target_classes:
            self._target_classes = None
        else:
            # 确保是整数列表
            self._target_classes = [int(cls_id) for cls_id in self._target_classes]
        
        # 获取模型路径
        model_filename = self.MODEL_MAP.get(self._model_size, "yolov8l.pt")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, model_filename)
        
        # 初始化模型
        if YOLO is None:
            raise ImportError("ultralytics is not installed. Please install it.")
        
        if not os.path.exists(model_path):
            logger.warning(f"Model file {model_path} not found. Downloading from ultralytics...")
            self.model = YOLO(model_filename)  # 自动下载
        else:
            self.model = YOLO(model_path)
        
        logger.info(f"Loaded YOLOv8 model: {model_filename}, "
                   f"conf_threshold: {self._conf_threshold}, "
                   f"target_classes: {self._target_classes}")

    @staticmethod
    def _get_color_by_class_id(class_id: int):
        """根据 class_id 生成稳定颜色（BGR，OpenCV 用）"""
        np.random.seed(class_id)
        color = np.random.randint(0, 255, size=3).tolist()
        return tuple(color)

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """执行目标检测"""
        start = time.time()
        
        # 读取图像文件
        image_path = sample.get(self.image_key)
        if not image_path or not os.path.exists(image_path):
            logger.warning(f"Image file not found: {image_path}")
            return sample
        
        # 读取图像
        img = cv2.imread(image_path)
        if img is None:
            logger.warning(f"Failed to read image: {image_path}")
            return sample
        
        # 执行目标检测
        results = self.model(img, conf=self._conf_threshold)
        r = results[0]
        
        # 准备标注数据
        h, w = img.shape[:2]
        annotations = {
            "image": os.path.basename(image_path),
            "width": w,
            "height": h,
            "model_size": self._model_size,
            "conf_threshold": self._conf_threshold,
            "selected_class_ids": self._target_classes,
            "detections": []
        }
        
        # 处理检测结果
        if r.boxes is not None:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                
                # 过滤目标类别
                if self._target_classes is not None and cls_id not in self._target_classes:
                    continue
                
                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(float, box.xyxy[0])
                label = COCO_CLASS_MAP.get(cls_id, f"class_{cls_id}")
                
                # 记录检测结果
                annotations["detections"].append({
                    "label": label,
                    "class_id": cls_id,
                    "confidence": round(conf, 4),
                    "bbox_xyxy": [x1, y1, x2, y2],
                    "bbox_xywh": [x1, y1, x2 - x1, y2 - y1]
                })
                
                # 在图像上绘制
                color = self._get_color_by_class_id(cls_id)
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
        
        # 确定输出目录
        if self._output_dir and os.path.exists(self._output_dir):
            output_dir = self._output_dir
        else:
            output_dir = os.path.dirname(image_path)
        
        # 创建输出子目录：仅保留 annotations 目录，不再额外保存标注图像，
        # 以减少冗余占用；检测结果将直接写入 JSON 文件。
        annotations_dir = os.path.join(output_dir, "annotations")
        os.makedirs(annotations_dir, exist_ok=True)
        
        # 保持原始文件名（不添加后缀），确保一一对应
        base_name = os.path.basename(image_path)
        name_without_ext = os.path.splitext(base_name)[0]
        
        # 保存标注 JSON（文件名与图像对应）
        json_filename = f"{name_without_ext}.json"
        json_path = os.path.join(annotations_dir, json_filename)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(annotations, f, indent=2, ensure_ascii=False)
        
        # 更新样本数据
        sample["detection_count"] = len(annotations["detections"])
        # 不再额外保存 output_image 副本，仅返回原始路径和注释信息
        sample["output_image"] = image_path
        sample["annotations_file"] = json_path
        sample["annotations"] = annotations
        
        logger.info(f"Image: {os.path.basename(image_path)}, "
                   f"Detections: {len(annotations['detections'])}, "
                   f"Time: {(time.time() - start):.4f}s")
        
        return sample
