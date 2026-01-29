"""
背景图片坐标标记工具
功能：批量标记背景图片中文档位置，并保存到JSON文件
作者：Claude Code
日期：2025-01-26
"""

import cv2
import numpy as np
import json
import os
import tkinter as tk
from pathlib import Path

from loguru import logger


def get_screen_resolution():
    """
    获取屏幕分辨率,支持多显示器环境
    返回: (width, height) 主屏幕的分辨率
    """
    try:
        # 创建 Tkinter 根窗口(不会显示)
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口

        # 获取屏幕宽高
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()

        root.destroy()
        return screen_width, screen_height
    except Exception as e:
        logger.info(f"获取屏幕分辨率失败: {e}, 使用默认值 1920x1080")
        return 1920, 1080


def load_cached_coordinates(json_path, image_path):
    """尝试从JSON文件中加载缓存的坐标"""
    if not os.path.exists(json_path):
        return None

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 统一使用正斜杠路径作为key
        key = os.path.basename(image_path)
        if key in data:
            logger.info(f"  ✓ 检测到缓存坐标，已从JSON加载")
            return np.array(data[key], dtype="float32")
    except Exception as e:
        logger.info(f"  ✗ 读取缓存文件失败: {e}")

    return None


def save_cached_coordinates(json_path, image_path, coords):
    """将手工标记的坐标保存到JSON文件"""
    data = {}

    # 如果文件存在，先读取原有数据
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            pass  # 如果文件损坏，就覆盖它

    # 转换 numpy 数组为 list 以便 JSON 序列化
    key = image_path.replace("\\", "/")
    data[key] = coords.tolist()

    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"  ✓ 坐标已保存至JSON文件")
    except Exception as e:
        logger.info(f"  ✗ 保存缓存文件失败: {e}")


def cv_imread(file_path):
    """读取含中文路径的图片"""
    return cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)


def order_points(pts):
    """
    重排坐标点顺序：左上, 右上, 右下, 左下
    """
    rect = np.zeros((4, 2), dtype="float32")

    # 坐标点求和:
    # 左上角 sum 最小
    # 右下角 sum 最大
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    # 坐标点差值 (y - x):
    # 右上角 diff 最小
    # 左下角 diff 最大
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect


def manual_select_corners(image, image_path):
    """
    当自动识别失败时，弹出窗口让用户手动点击4个角
    """
    logger.info("\n" + "="*50)
    logger.info("【进入手动辅助模式】")
    logger.info("自动识别未找到理想结果。")
    logger.info("操作说明：")
    logger.info("1. 请在新弹出的 'Manual Selection' 窗口中。")
    logger.info("2. 依次点击纸张的【四个顶点】（顺序不限）。")
    logger.info("3. 点错请按 'r' 键重置，满意请按任意键确认。")
    logger.info("="*50 + "\n")

    # 缩放以适应屏幕显示 (自动检测屏幕分辨率)
    h, w = image.shape[:2]
    screen_w, screen_h = get_screen_resolution()

    # 全屏模式下直接使用屏幕尺寸，预留少量边距
    margin = 60  # 边距像素
    available_h = screen_h - margin * 2
    available_w = screen_w - margin * 2

    # 计算缩放比例，确保图片完整显示在屏幕内
    scale_h = available_h / h
    scale_w = available_w / w
    scale = min(scale_h, scale_w)

    logger.info(f"[全屏模式] 原图尺寸: {w}x{h}, 屏幕: {screen_w}x{screen_h}, 缩放比例: {scale:.3f}")

    disp_w, disp_h = int(w * scale), int(h * scale)
    display_img = cv2.resize(image, (disp_w, disp_h))
    temp_img = display_img.copy() # 用于画点的临时图

    points = []

    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(points) < 4:
                # 记录点击坐标（还原回原图尺度）
                real_x = int(x / scale)
                real_y = int(y / scale)
                points.append([real_x, real_y])

                # 视觉反馈：在显示图上画红点
                cv2.circle(temp_img, (x, y), 8, (0, 0, 255), -1)
                # 画出坐标序数
                cv2.putText(temp_img, str(len(points)), (x+10, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                cv2.imshow("Manual Selection", temp_img)

    # 创建正常窗口（自动适应图片大小）
    cv2.namedWindow("Manual Selection", cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback("Manual Selection", mouse_callback)
    cv2.imshow("Manual Selection", display_img)

    # 等待用户交互
    final_pts = None
    while True:
        key = cv2.waitKey(20) & 0xFF

        # 按 'r' 重置
        if key == ord('r'):
            points = []
            temp_img = display_img.copy()
            cv2.imshow("Manual Selection", temp_img)
            logger.info(">> 已重置，请重新点击")

        # 按 'q' 强制退出
        if key == ord('q'):
            logger.info(">> 用户取消操作")
            break

        # 如果点满4个点，且按下了任意键 (除了r/q)，则确认
        # 或者为了方便，点满4个点自动暂停等待确认
        if len(points) == 4:
            # 在图上提示"按任意键确认"
            cv2.putText(temp_img, "Press ANY key to Confirm", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
            cv2.imshow("Manual Selection", temp_img)

            # 等用户按键
            key2 = cv2.waitKey(0) & 0xFF
            if key2 == ord('r'):
                # 如果用户这时按了r，则重置，不退出
                points = []
                temp_img = display_img.copy()
                cv2.imshow("Manual Selection", temp_img)
                continue
            else:
                final_pts = np.array(points, dtype="float32")
                break

    cv2.destroyAllWindows()

    if final_pts is not None:
        return order_points(final_pts)
    return None


def detect_document_corners(image_path, json_path, debug=False):
    """
    智能识别方案 (v3.1)：
    1. 优先检查本地 JSON 是否有缓存坐标
    2. 局部对比度增强 + 双边滤波 (针对同色系背景)
    3. Canny边缘检测
    4. 轮廓筛选 + 最小外接矩形
    5. 失败自动触发手动模式，并保存结果到 JSON
    """
    # 步骤 0: 检查缓存
    cached_pts = load_cached_coordinates(json_path, image_path)
    if cached_pts is not None:
        return order_points(cached_pts)

    image = cv_imread(image_path)
    if image is None:
        logger.info(f"  ✗ 无法读取图片: {image_path}")
        return None

    # 1. 图像增强预处理
    ratio = image.shape[0] / 800.0
    orig = image.copy()
    processed_img = cv2.resize(image, (int(image.shape[1] / ratio), 800))

    gray = cv2.cvtColor(processed_img, cv2.COLOR_BGR2GRAY)

    # 双边滤波：能极好地去除桌面的纹理噪点，同时保留纸张边缘
    gray = cv2.bilateralFilter(gray, 11, 75, 75)

    # CLAHE：自适应直方图均衡化，增强局部对比度
    # 这对识别"白桌子上的白纸"至关重要
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)

    # 2. 边缘检测
    # 自动计算 Canny 阈值
    v = np.median(gray)
    sigma = 0.33
    lower_thresh = int(max(0, (1.0 - sigma) * v))
    upper_thresh = int(min(255, (1.0 + sigma) * v))
    edged = cv2.Canny(gray, lower_thresh, upper_thresh)

    # 膨胀处理，连接断开的边缘
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edged = cv2.dilate(edged, kernel, iterations=1)

    # 3. 轮廓提取
    cnts, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

    screenCnt = None

    logger.info("  → 尝试自动识别...")
    for c in cnts:
        peri = cv2.arcLength(c, True)
        # 近似多边形
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        # 只要顶点数在4到6之间，且面积够大，就认为是候选纸张
        if 4 <= len(approx) <= 6 and cv2.contourArea(c) > 50000:
            # 使用最小外接矩形来规整化（解决5、6个点的问题）
            rect = cv2.minAreaRect(c)
            box = cv2.boxPoints(rect)
            screenCnt = np.int64(box)
            logger.info(f"  → 锁定候选轮廓，面积: {cv2.contourArea(c)}")
            break

    # 4. 结果处理
    if screenCnt is not None:
        # 还原到原始尺寸
        detected_pts = (screenCnt * ratio).astype(np.float32)
        ordered_pts = order_points(detected_pts)

        if debug:
            debug_img = orig.copy()
            cv2.polylines(debug_img, [ordered_pts.astype(int)], True, (0, 255, 0), 3)
            debug_path = os.path.join(os.path.dirname(image_path), f"debug_{os.path.basename(image_path)}")
            cv2.imencode(".jpg", debug_img)[1].tofile(debug_path)
            logger.info(f"  ✓ 自动识别成功！调试图已保存")

        # 自动识别成功，也保存到JSON
        save_cached_coordinates(json_path, image_path, ordered_pts)
        return ordered_pts
    else:
        # 5. 兜底方案：手动识别
        logger.info("  → 自动识别失败，切换到手动模式")
        manual_pts = manual_select_corners(orig, image_path)
        if manual_pts is not None:
             # 如果是用户手工辛苦标的，我们把它存下来
             save_cached_coordinates(json_path, image_path, manual_pts)
        return manual_pts


def batch_mark_coordinates(background_folder, json_path, debug=False, skip_existing=True):
    """
    批量标记背景图片中的文档位置

    Args:
        background_folder: 背景图片文件夹路径
        json_path: JSON文件路径（用于存储标记结果）
        debug: 是否生成调试图
        skip_existing: 是否跳过已有标记的图片
    """
    logger.info("="*60)
    logger.info("背景图片坐标标记工具")
    logger.info("="*60)
    logger.info(f"背景文件夹: {background_folder}")
    print(f"JSON文件: {json_path}")
    print(f"调试模式: {'开启' if debug else '关闭'}")
    print(f"跳过已标记: {'是' if skip_existing else '否'}")
    print("-"*60)

    # 获取所有图片文件
    bg_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
        bg_files.extend(Path(background_folder).glob(ext))

    if not bg_files:
        print(f"❌ 在 {background_folder} 中未找到任何图片")
        return

    bg_files.sort()
    print(f"📁 找到 {len(bg_files)} 张背景图片\n")

    # 加载已有的坐标数据
    existing_coords = {}
    if skip_existing and os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                existing_coords = json.load(f)
            print(f"📋 已加载 {len(existing_coords)} 条已有标记记录\n")
        except:
            pass

    success_count = 0
    skip_count = 0
    fail_count = 0

    # 遍历所有背景图片
    for idx, bg_file in enumerate(bg_files):
        bg_path = str(bg_file)
        bg_name = bg_file.name

        print(f"[{idx+1}/{len(bg_files)}] 处理: {bg_name}")

        # 检查是否已有标记
        key = bg_path.replace("\\", "/")
        if skip_existing and key in existing_coords:
            print(f"  ⏭ 已存在标记，跳过\n")
            skip_count += 1
            continue

        # 检测/标记坐标
        corners = detect_document_corners(bg_path, json_path, debug=debug)

        if corners is not None:
            success_count += 1
            print(f"  ✓ 标记完成\n")
        else:
            fail_count += 1
            print(f"  ✗ 标记失败\n")

    # 统计结果
    print("-"*60)
    print("✨ 批量标记完成！")
    print(f"   ✓ 成功: {success_count} 张")
    print(f"   ⏭ 跳过: {skip_count} 张")
    print(f"   ✗ 失败: {fail_count} 张")
    print("-"*60)
    print(f"📝 标记结果已保存至: {json_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="背景图片坐标标记工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 基本用法
  python 1_mark_background_coordinates.py background_folder coordinates.json

  # 生成调试图（显示检测结果）
  python 1_mark_background_coordinates.py background_folder coordinates.json --debug

  # 重新标记所有图片（包括已标记的）
  python 1_mark_background_coordinates.py background_folder coordinates.json --force
        """
    )

    parser.add_argument("background_folder", help="背景图片文件夹路径")
    parser.add_argument("json_path", help="JSON文件路径（存储标记结果）")
    parser.add_argument("--debug", action="store_true",
                       help="生成调试图，显示自动识别结果")
    parser.add_argument("--force", action="store_true",
                       help="强制重新标记所有图片（包括已标记的）")

    args = parser.parse_args()

    batch_mark_coordinates(
        background_folder=args.background_folder,
        json_path=args.json_path,
        debug=args.debug,
        skip_existing=not args.force
    )
