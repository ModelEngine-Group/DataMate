#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试图像目标检测算子

使用方法：
    python test_detection.py /path/to/image.jpg

或在Python中：
    from test_detection import test_detection
    test_detection('/path/to/image.jpg')
"""

import sys
import os

# 添加项目路径到sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ops.annotation.image_object_detection_bounding_box.process import ImageObjectDetectionBoundingBox


def test_detection(image_path, output_dir=None):
    """
    测试目标检测算子
    
    Args:
        image_path: 图像文件路径
        output_dir: 输出目录（可选）
    """
    print(f"测试图像: {image_path}")
    
    # 检查文件是否存在
    if not os.path.exists(image_path):
        print(f"❌ 错误: 文件不存在 {image_path}")
        return False
    
    # 初始化算子
    try:
        detector = ImageObjectDetectionBoundingBox(
            modelSize='l',           # 使用YOLOv8l模型
            confThreshold=0.7,       # 置信度阈值0.7
            targetClasses=[],        # 检测所有类别（或指定如 [0, 2, 5]）
            outputDir=output_dir     # 输出目录
        )
        print("✓ 算子初始化成功")
    except Exception as e:
        print(f"❌ 算子初始化失败: {e}")
        return False
    
    # 准备样本数据
    sample = {
        'image': image_path,
        'filename': os.path.basename(image_path)
    }
    
    # 执行检测
    try:
        result = detector.execute(sample)
        print("✓ 检测执行成功")
    except Exception as e:
        print(f"❌ 检测执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 输出结果
    print("\n" + "="*50)
    print("检测结果:")
    print("="*50)
    print(f"图像: {result.get('filename', 'N/A')}")
    print(f"检测对象数: {result.get('detection_count', 0)}")
    print(f"输出图像: {result.get('output_image', 'N/A')}")
    print(f"标注文件: {result.get('annotations_file', 'N/A')}")
    
    # 输出检测详情
    annotations = result.get('annotations', {})
    detections = annotations.get('detections', [])
    
    if detections:
        print(f"\n检测到 {len(detections)} 个对象:")
        for i, det in enumerate(detections, 1):
            print(f"  {i}. {det['label']} (置信度: {det['confidence']:.2%})")
            print(f"     位置: {det['bbox_xyxy']}")
    else:
        print("\n未检测到对象")
    
    print("\n✓ 测试完成!")
    return True


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python test_detection.py <图像路径> [输出目录]")
        print("示例: python test_detection.py /path/to/image.jpg /path/to/output")
        sys.exit(1)
    
    image_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = test_detection(image_path, output_dir)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
