import cv2
import numpy as np
import json
import os
from pathlib import Path

COORD_FILE = "coordinates_cache.json"


def load_cached_coordinates(image_path, coord_file=COORD_FILE):
    """尝试从JSON文件中加载缓存的坐标"""
    if not os.path.exists(coord_file):
        return None

    try:
        with open(coord_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        key = os.path.basename(image_path)
        if key in data:
            print(f"检测到缓存坐标，已从 {coord_file} 加载。")
            return np.array(data[key], dtype="float32")
    except Exception as e:
        print(f"读取缓存文件失败: {e}")

    return None


def save_cached_coordinates(image_path, coords):
    """将手工标记的坐标保存到JSON文件"""
    data = {}
    if os.path.exists(COORD_FILE):
        try:
            with open(COORD_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            pass

    key = image_path.replace("\\", "/")
    data[key] = coords.tolist()

    try:
        with open(COORD_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"已将坐标保存至 {COORD_FILE}，下次运行将自动加载。")
    except Exception as e:
        print(f"保存缓存文件失败: {e}")


def cv_imread(file_path):
    """读取含中文路径的图片"""
    return cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)


def order_points(pts):
    """
    重排坐标点顺序：左上, 右上, 右下, 左下
    """
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect


def manual_select_corners(image):
    """
    当自动识别失败时，弹出窗口让用户手动点击4个角
    """
    print("\n" + "=" * 50)
    print("【进入手动辅助模式】")
    print("自动识别未找到理想结果。")
    print("操作说明：")
    print("1. 请在新弹出的 'Manual Selection' 窗口中。")
    print("2. 依次点击纸张的【四个顶点】（顺序不限）。")
    print("3. 点错请按 'r' 键重置，满意请按任意键确认。")
    print("=" * 50 + "\n")

    h, w = image.shape[:2]
    scale = 1.0
    if h > 900:
        scale = 900.0 / h

    disp_w, disp_h = int(w * scale), int(h * scale)
    display_img = cv2.resize(image, (disp_w, disp_h))
    temp_img = display_img.copy()

    points = []

    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(points) < 4:
                real_x = int(x / scale)
                real_y = int(y / scale)
                points.append([real_x, real_y])

                cv2.circle(temp_img, (x, y), 8, (0, 0, 255), -1)
                cv2.putText(temp_img, str(len(points)), (x + 10, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                cv2.imshow("Manual Selection", temp_img)

    cv2.namedWindow("Manual Selection", cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback("Manual Selection", mouse_callback)
    cv2.imshow("Manual Selection", display_img)

    final_pts = None
    while True:
        key = cv2.waitKey(20) & 0xFF

        if key == ord('r'):
            points = []
            temp_img = display_img.copy()
            cv2.imshow("Manual Selection", temp_img)
            print(">> 已重置，请重新点击")

        if key == ord('q'):
            print(">> 用户取消操作")
            break

        if len(points) == 4:
            cv2.putText(temp_img, "Press ANY key to Confirm", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
            cv2.imshow("Manual Selection", temp_img)

            key2 = cv2.waitKey(0) & 0xFF
            if key2 == ord('r'):
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


def detect_document_corners(image_path, coord_file, debug=False):
    """
    智能识别方案
    1. 优先检查本地 JSON 是否有缓存坐标
    2. 局部对比度增强 + 双边滤波
    3. Canny边缘检测
    4. 轮廓筛选 + 最小外接矩形
    5. 失败自动触发手动模式，并保存结果到 JSON
    """
    cached_pts = load_cached_coordinates(image_path, coord_file)
    if cached_pts is not None:
        return order_points(cached_pts)

    image = cv_imread(image_path)
    if image is None:
        print(f"无法读取图片: {image_path}")
        return None

    ratio = image.shape[0] / 800.0
    orig = image.copy()
    processed_img = cv2.resize(image, (int(image.shape[1] / ratio), 800))

    gray = cv2.cvtColor(processed_img, cv2.COLOR_BGR2GRAY)

    gray = cv2.bilateralFilter(gray, 11, 75, 75)

    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    v = np.median(gray)
    sigma = 0.33
    lower_thresh = int(max(0, (1.0 - sigma) * v))
    upper_thresh = int(min(255, (1.0 + sigma) * v))
    edged = cv2.Canny(gray, lower_thresh, upper_thresh)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edged = cv2.dilate(edged, kernel, iterations=1)

    cnts, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

    screenCnt = None

    print("正在尝试自动识别...")
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        if 4 <= len(approx) <= 6 and cv2.contourArea(c) > 50000:
            rect = cv2.minAreaRect(c)
            box = cv2.boxPoints(rect)
            screenCnt = np.int64(box)
            print(f"-> 锁定候选轮廓，面积: {cv2.contourArea(c)}")
            break

    if screenCnt is not None:
        detected_pts = (screenCnt * ratio).astype(np.float32)
        ordered_pts = order_points(detected_pts)

        if debug:
            debug_img = orig.copy()
            cv2.polylines(debug_img, [ordered_pts.astype(int)], True, (0, 255, 0), 3)
            cv2.imencode(".jpg", debug_img)[1].tofile("debug_detection.jpg")
            print("自动识别成功！调试图: debug_detection.jpg")

        return ordered_pts
    else:
        manual_pts = manual_select_corners(orig)
        if manual_pts is not None:
            save_cached_coordinates(image_path, manual_pts)
        return manual_pts


def _auto_rotate_to_match_orientation(src, dst_corners):
    """
    检查源图与目标区域的方向（横版/竖版）是否一致，如果不一致则自动旋转源图90度。
    """
    (tl, tr, br, bl) = dst_corners
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    dst_w = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    dst_h = max(int(heightA), int(heightB))

    h_src, w_src = src.shape[:2]

    src_is_landscape = w_src > h_src
    dst_is_landscape = dst_w > dst_h

    if src_is_landscape != dst_is_landscape:
        print(f"   [自动旋转] 方向不匹配 (Src横版={src_is_landscape}, Dst横版={dst_is_landscape})，执行旋转...")
        src = cv2.rotate(src, cv2.ROTATE_90_CLOCKWISE)

    return src


def _pad_src_to_match_ratio(src, dst_corners):
    """
    为防止电子凭证被拉伸/挤压变形，补白边使宽高比与目标区域一致。
    """
    (tl, tr, br, bl) = dst_corners
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    dst_ratio = maxWidth / float(maxHeight)

    h_src, w_src = src.shape[:2]
    src_ratio = w_src / float(h_src)

    print(f"   [比例校正] Src比例: {src_ratio:.2f}, Dst区域比例: {dst_ratio:.2f}")

    if abs(src_ratio - dst_ratio) < 0.1:
        return src

    if src_ratio > dst_ratio:
        new_h = int(w_src / dst_ratio)
        total_pad = new_h - h_src
        pad_top = total_pad // 2
        pad_bot = total_pad - pad_top

        src_padded = cv2.copyMakeBorder(src, pad_top, pad_bot, 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
        print(f"   [比例校正] 为源图上下补白: {total_pad}px")

    else:
        new_w = int(h_src * dst_ratio)
        total_pad = new_w - w_src
        pad_left = total_pad // 2
        pad_right = total_pad - pad_left

        src_padded = cv2.copyMakeBorder(src, 0, 0, pad_left, pad_right, cv2.BORDER_CONSTANT, value=(255, 255, 255))
        print(f"   [比例校正] 为源图左右补白: {total_pad}px")

    return src_padded


def process_normal_scene(src_path, dst_path, dst_corners, output_path):
    """场景：正常拍摄（正对或微倾斜，光照均匀）"""
    print("[处理逻辑] 使用【正常场景】合成算法")
    _base_synthesis_pipeline(src_path, dst_path, dst_corners, output_path, mode="normal", enable_ratio_fix=True)


def process_tilted_scene(src_path, dst_path, dst_corners, output_path):
    """场景：斜拍（透视变形较大）"""
    print("[处理逻辑] 使用【斜拍场景】合成算法")
    _base_synthesis_pipeline(src_path, dst_path, dst_corners, output_path, mode="tilted", enable_ratio_fix=True,
                             enable_auto_rotate=True)


def process_shadow_scene(src_path, dst_path, dst_corners, output_path):
    """场景：有阴影（光照不均匀，有投影）"""
    print("[处理逻辑] 使用【阴影场景】合成算法")
    _base_synthesis_pipeline(src_path, dst_path, dst_corners, output_path, mode="shadow")


def process_watermark_scene(src_path, dst_path, dst_corners, output_path):
    """场景：有水印（桌面或背景有复杂纹理）"""
    print("[处理逻辑] 使用【水印场景】合成算法")
    _base_synthesis_pipeline(src_path, dst_path, dst_corners, output_path, mode="watermark", enable_ratio_fix=True,
                             enable_auto_rotate=True)


def process_incomplete_scene(src_path, dst_path, dst_corners, output_path):
    """场景：拍摄不完整（凭证部分在画面外）"""
    print("[处理逻辑] 使用【不完整场景】合成算法")
    _base_synthesis_pipeline(src_path, dst_path, dst_corners, output_path, mode="incomplete", enable_ratio_fix=True,
                             enable_auto_rotate=True)


def _base_synthesis_pipeline(src_path, dst_path, dst_corners, output_path, mode="normal", enable_ratio_fix=False,
                             enable_auto_rotate=True):
    """
    基础合成流水线
    """
    src = cv_imread(src_path)
    dst = cv_imread(dst_path)
    if src is None or dst is None:
        print(f"错误：无法读取图片。\nSrc: {src_path}\nDst: {dst_path}")
        return

    if enable_auto_rotate:
        src = _auto_rotate_to_match_orientation(src, dst_corners)

    if enable_ratio_fix:
        src = _pad_src_to_match_ratio(src, dst_corners)

    h_src, w_src = src.shape[:2]
    src_pts = np.array([[0, 0], [w_src - 1, 0], [w_src - 1, h_src - 1], [0, h_src - 1]], dtype="float32")
    dst_pts = np.array(dst_corners, dtype="float32")

    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped_src = cv2.warpPerspective(src, M, (dst.shape[1], dst.shape[0]))

    mask = np.zeros(dst.shape[:2], dtype=np.uint8)
    cv2.fillConvexPoly(mask, dst_pts.astype(int), 255)

    dst_lab = cv2.cvtColor(dst, cv2.COLOR_BGR2LAB)
    warped_lab = cv2.cvtColor(warped_src, cv2.COLOR_BGR2LAB)

    dst_region_l = dst_lab[:, :, 0][mask > 0]
    if dst_region_l.size == 0:
        print("警告：目标区域掩模为空")
        return

    l_mean_dst, l_std_dst = np.mean(dst_region_l), np.std(dst_region_l)
    src_region_l = warped_lab[:, :, 0][mask > 0]
    l_mean_src, l_std_src = np.mean(src_region_l), np.std(src_region_l)

    contrast_factor = 1.0
    if mode == "shadow":
        contrast_factor = 0.85
    elif mode == "tilted":
        contrast_factor = 0.95

    l_channel = warped_lab[:, :, 0].astype(float)
    l_channel = (l_channel - l_mean_src) * (l_std_dst / (l_std_src + 1e-5)) * contrast_factor + l_mean_dst
    warped_lab[:, :, 0] = np.clip(l_channel, 0, 255).astype(np.uint8)

    matched_src = cv2.cvtColor(warped_lab, cv2.COLOR_LAB2BGR)

    center = (int((dst_pts[:, 0].min() + dst_pts[:, 0].max()) / 2),
              int((dst_pts[:, 1].min() + dst_pts[:, 1].max()) / 2))

    clone_mode = cv2.NORMAL_CLONE

    try:
        final_output = cv2.seamlessClone(matched_src, dst, mask, center, clone_mode)
    except Exception as e:
        print(f"融合失败，降级为直接覆盖: {e}")
        final_output = dst.copy()
        final_output[mask > 0] = matched_src[mask > 0]

    is_success, im_buf = cv2.imencode(".jpg", final_output)
    if is_success:
        im_buf.tofile(output_path)
        print(f"成功！合成图已保存至: {output_path}")
    else:
        print("保存失败")


def augment_images(source_dir, output_dir, backgrounds_dir, coord_file, mode="all"):
    """批量图片增强合成"""

    if not os.path.exists(source_dir):
        print(f"错误: 目录 {source_dir} 不存在")
        return

    source_files = [f for f in os.listdir(source_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    source_files.sort()

    if not source_files:
        print(f"错误: {source_dir} 目录中没有找到图片文件")
        return

    print(f"找到 {len(source_files)} 张待处理图片")

    template_files = [f for f in os.listdir(backgrounds_dir) if
                      f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    template_files.sort()

    if not template_files:
        print(f"错误: {backgrounds_dir} 目录中没有找到背景图片")
        return

    print(f"找到 {len(template_files)} 张背景图片")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建输出目录: {output_dir}")

    for i, source_file in enumerate(source_files):
        source_img_path = os.path.join(source_dir, source_file)

        print(f"\n{'=' * 60}")
        print(f"正在处理第 {i + 1}/{len(source_files)} 张图片: {source_file}")
        print(f"{'=' * 60}")

        for template_file in template_files:
            template_img_path = os.path.join(backgrounds_dir, template_file)

            if not os.path.isfile(template_img_path):
                continue

            template_base_name = os.path.splitext(template_file)[0]
            source_base_name = os.path.splitext(source_file)[0]
            output_img_path = os.path.join(output_dir, f'{source_base_name}_on_{template_base_name}.jpg')

            print(f"\n>>> 处理背景: {template_file}")

            detected_corners = detect_document_corners(template_img_path, coord_file, debug=True)

            if detected_corners is None:
                print(f"跳过: {template_file} (未获取到有效坐标)")
                continue

            if mode != "all":
                if mode == "tilted" and "3-" not in template_file and "斜拍" not in template_file:
                    continue
                elif mode == "shadow" and "4-" not in template_file and "阴影" not in template_file:
                    continue
                elif mode == "watermark" and "5-" not in template_file and "水印" not in template_file:
                    continue
                elif mode == "incomplete" and "6-" not in template_file and "不完整" not in template_file:
                    continue
                elif mode == "normal" and ("3-" in template_file or "斜拍" in template_file or
                                           "4-" in template_file or "阴影" in template_file or
                                           "5-" in template_file or "水印" in template_file or
                                           "6-" in template_file or "不完整" in template_file):
                    continue

            if "3-" in template_file or "斜拍" in template_file:
                process_tilted_scene(source_img_path, template_img_path, detected_corners, output_img_path)
            elif "4-" in template_file or "阴影" in template_file:
                process_shadow_scene(source_img_path, template_img_path, detected_corners, output_img_path)
            elif "5-" in template_file or "水印" in template_file:
                process_watermark_scene(source_img_path, template_img_path, detected_corners, output_img_path)
            elif "6-" in template_file or "不完整" in template_file:
                process_incomplete_scene(source_img_path, template_img_path, detected_corners, output_img_path)
            else:
                process_normal_scene(source_img_path, template_img_path, detected_corners, output_img_path)

    print("\n" + "#" * 60)
    print("所有任务处理完毕。")
    print(f"总共处理了 {len(source_files)} 张待处理图片")
    print(f"每张都应用到了 {len(template_files)} 张背景图片上。")
    print(f"结果保存在: {output_dir}")
    print("#" * 60)

    return
