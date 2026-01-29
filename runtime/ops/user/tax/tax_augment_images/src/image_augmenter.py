"""
图片增强模块 - 真实世界模拟（透视变换、泊松融合等）
"""

import cv2
import numpy as np
import json
import os


def load_cached_coordinates(image_path, coord_file):
    """尝试从JSON文件中加载缓存的坐标"""
    if not os.path.exists(coord_file):
        return None

    try:
        with open(coord_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 统一使用正斜杠路径作为key
        key = image_path.replace("\\", "/")
        if key in data:
            print(f"检测到缓存坐标，已从 {coord_file} 加载。")
            return np.array(data[key], dtype="float32")
    except Exception as e:
        print(f"读取缓存文件失败: {e}")

    return None


def save_cached_coordinates(image_path, coords, coord_file):
    """将手工标记的坐标保存到JSON文件"""
    data = {}
    # 如果文件存在，先读取原有数据
    if os.path.exists(coord_file):
        try:
            with open(coord_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            pass  # 如果文件损坏，就覆盖它

    # 转换 numpy 数组为 list 以便 JSON 序列化
    key = image_path.replace("\\", "/")
    data[key] = coords.tolist()

    try:
        with open(coord_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"已将坐标保存至 {coord_file}，下次运行将自动加载。")
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


def detect_document_corners(image_path, coord_file, debug=False):
    """
    智能识别方案：
    1. 优先检查本地 JSON 是否有缓存坐标
    2. 局部对比度增强 + 双边滤波 (针对同色系背景)
    3. Canny边缘检测
    4. 轮廓筛选 + 最小外接矩形
    5. 失败自动触发手动模式，并保存结果到 JSON
    """
    # 步骤 0: 检查缓存
    cached_pts = load_cached_coordinates(image_path, coord_file)
    if cached_pts is not None:
        return order_points(cached_pts)

    image = cv_imread(image_path)
    if image is None:
        print(f"无法读取图片: {image_path}")
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
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
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

    print("正在尝试自动识别...")
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
            print(f"-> 锁定候选轮廓，面积: {cv2.contourArea(c)}")
            break

    # 4. 结果处理
    if screenCnt is not None:
        # 还原到原始尺寸
        detected_pts = (screenCnt * ratio).astype(np.float32)
        ordered_pts = order_points(detected_pts)

        if debug:
            debug_img = orig.copy()
            cv2.polylines(debug_img, [ordered_pts.astype(int)], True, (0, 255, 0), 3)
            debug_path = "output/03_simulated/debug_detection.jpg"
            os.makedirs(os.path.dirname(debug_path), exist_ok=True)
            cv2.imwrite(debug_path, debug_img)
            print("自动识别成功！调试图: debug_detection.jpg")

        return ordered_pts
    else:
        # 5. 兜底方案：手动识别
        manual_pts = manual_select_corners(orig)
        if manual_pts is not None:
            # 如果是用户手工辛苦标的，我们把它存下来
            save_cached_coordinates(image_path, manual_pts, coord_file)
        return manual_pts


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

    # 缩放以适应屏幕显示 (避免 4K 图太大)
    h, w = image.shape[:2]
    scale = 1.0
    if h > 900:
        scale = 900.0 / h

    disp_w, disp_h = int(w * scale), int(h * scale)
    display_img = cv2.resize(image, (disp_w, disp_h))
    temp_img = display_img.copy()  # 用于画点的临时图

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
                cv2.putText(temp_img, str(len(points)), (x + 10, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                cv2.imshow("Manual Selection", temp_img)

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
            print(">> 已重置，请重新点击")

        # 按 'q' 强制退出
        if key == ord('q'):
            print(">> 用户取消操作")
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


def _auto_rotate_to_match_orientation(src, dst_corners):
    """
    检查源图与目标区域的方向（横版/竖版）是否一致，如果不一致则自动旋转源图90度。
    """
    # 计算目标区域的大致宽高
    (tl, tr, br, bl) = dst_corners
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    dst_w = max(int(widthA), int(widthB))

    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    dst_h = max(int(heightA), int(heightB))

    h_src, w_src = src.shape[:2]

    # 判断是否为横版 (Width > Height)
    src_is_landscape = w_src > h_src
    dst_is_landscape = dst_w > dst_h

    if src_is_landscape != dst_is_landscape:
        print(f"   [自动旋转] 方向不匹配 (Src横版={src_is_landscape}, Dst横版={dst_is_landscape})，执行旋转...")
        src = cv2.rotate(src, cv2.ROTATE_90_CLOCKWISE)

    return src


def _pad_src_to_match_ratio(src, dst_corners):
    """
    为了防止电子凭证被拉伸/挤压变形，我们需要先给源图补白边，
    使其宽高比(Aspect Ratio)与目标区域的透视宽高比大致一致。
    """
    # 1. 计算目标区域目前的"物理"宽高近似值
    # 由于有透视，我们取两组边长的最大值作为参考
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

    # 2. 根据比例差异进行填充
    pad_h, pad_w = 0, 0

    if abs(src_ratio - dst_ratio) < 0.1:
        # 如果比例差不多，就不动了
        return src

    if src_ratio > dst_ratio:
        # 源图比目标更"扁/胖"，目标比较"瘦/高"
        # 这种情况下，源图需要上下补白，变高一点，才能塞进去不变形
        new_h = int(w_src / dst_ratio)
        total_pad = new_h - h_src
        pad_top = total_pad // 2
        pad_bot = total_pad - pad_top

        # 使用白色填充 (255, 255, 255)
        src_padded = cv2.copyMakeBorder(src, pad_top, pad_bot, 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
        print(f"   [比例校正] 为源图上下补白: {total_pad}px")

    else:
        # 源图比目标更"瘦/高"，目标比较"扁/胖" (这是您遇到的情况)
        # 这种情况下，源图需要左右补白，变宽一点
        new_w = int(h_src * dst_ratio)
        total_pad = new_w - w_src
        pad_left = total_pad // 2
        pad_right = total_pad - pad_left

        src_padded = cv2.copyMakeBorder(src, 0, 0, pad_left, pad_right, cv2.BORDER_CONSTANT, value=(255, 255, 255))
        print(f"   [比例校正] 为源图左右补白: {total_pad}px")

    return src_padded


def _base_synthesis_pipeline(src_path, dst_path, dst_corners, output_path, mode="normal",
                            enable_ratio_fix=False, enable_auto_rotate=True):
    """
    基础合成流水线
    """
    # 1. 读取图像
    src = cv_imread(src_path)
    dst = cv_imread(dst_path)
    if src is None or dst is None:
        print(f"错误：无法读取图片。\nSrc: {src_path}\nDst: {dst_path}")
        return

    # [新增] 自动旋转校正方向
    if enable_auto_rotate:
        src = _auto_rotate_to_match_orientation(src, dst_corners)

    # [新增] 比例自适应校正
    if enable_ratio_fix:
        src = _pad_src_to_match_ratio(src, dst_corners)

    # 2. 准备透视变换
    h_src, w_src = src.shape[:2]
    src_pts = np.array([[0, 0], [w_src - 1, 0], [w_src - 1, h_src - 1], [0, h_src - 1]], dtype="float32")
    dst_pts = np.array(dst_corners, dtype="float32")

    M = cv2.getPerspectiveTransform(src_pts, dst_pts)
    warped_src = cv2.warpPerspective(src, M, (dst.shape[1], dst.shape[0]))

    # 3. 创建掩模
    mask = np.zeros(dst.shape[:2], dtype=np.uint8)
    cv2.fillConvexPoly(mask, dst_pts.astype(int), 255)

    # 4. 色彩空间匹配
    dst_lab = cv2.cvtColor(dst, cv2.COLOR_BGR2LAB)
    warped_lab = cv2.cvtColor(warped_src, cv2.COLOR_BGR2LAB)

    dst_region_l = dst_lab[:, :, 0][mask > 0]
    if dst_region_l.size == 0:
        print("警告：目标区域掩模为空")
        return

    l_mean_dst, l_std_dst = np.mean(dst_region_l), np.std(dst_region_l)
    src_region_l = warped_lab[:, :, 0][mask > 0]
    l_mean_src, l_std_src = np.mean(src_region_l), np.std(src_region_l)

    # 针对不同模式，微调光照参数 (示例)
    contrast_factor = 1.0
    if mode == "shadow":
        contrast_factor = 0.85  # 阴影下对比度低一点可能更自然
    elif mode == "tilted":
        contrast_factor = 0.95

    l_channel = warped_lab[:, :, 0].astype(float)
    l_channel = (l_channel - l_mean_src) * (l_std_dst / (l_std_src + 1e-5)) * contrast_factor + l_mean_dst
    warped_lab[:, :, 0] = np.clip(l_channel, 0, 255).astype(np.uint8)

    matched_src = cv2.cvtColor(warped_lab, cv2.COLOR_LAB2BGR)

    # 5. 泊松融合
    center = (int((dst_pts[:, 0].min() + dst_pts[:, 0].max()) / 2),
              int((dst_pts[:, 1].min() + dst_pts[:, 1].max()) / 2))

    clone_mode = cv2.NORMAL_CLONE

    try:
        final_output = cv2.seamlessClone(matched_src, dst, mask, center, clone_mode)
    except Exception as e:
        print(f"融合失败，降级为直接覆盖: {e}")
        final_output = dst.copy()
        final_output[mask > 0] = matched_src[mask > 0]

    # 6. 保存
    cv2.imwrite(output_path, final_output)
    print(f"成功！合成图已保存至: {output_path}")


def process_scene_by_filename(src_path, dst_path, dst_corners, output_path, bg_filename, mode="normal"):
    """
    根据背景文件名选择对应的场景处理函数
    """
    print(f"\n>>> 正在合成: {os.path.basename(src_path)} -> {bg_filename}")
    _base_synthesis_pipeline(src_path, dst_path, dst_corners, output_path,
                           mode=mode, enable_ratio_fix=True, enable_auto_rotate=True)


class ImageAugmenter:
    """图片增强器 - 真实世界模拟"""

    def __init__(self, backgrounds_dir: str, output_dir: str, coord_file: str = "coordinates_cache.json"):
        """
        初始化图片增强器

        Args:
            backgrounds_dir: 背景图目录
            output_dir: 输出目录
            coord_file: 坐标缓存文件
        """
        self.backgrounds_dir = backgrounds_dir
        self.output_dir = output_dir
        self.coord_file = coord_file

    def process_images(self, src_dir: str):
        """
        批量处理图片

        Args:
            src_dir: 源图片目录
        """
        # 检查源文件夹是否存在
        if not os.path.exists(src_dir):
            print(f"❌ 源目录不存在: {src_dir}")
            return

        # 检查背景文件夹是否存在
        if not os.path.exists(self.backgrounds_dir):
            print(f"❌ 背景目录不存在: {self.backgrounds_dir}")
            return

        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)

        # 获取源文件夹下所有图片 (支持 jpg, jpeg, png)
        src_files = [f for f in os.listdir(src_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        src_files.sort()

        # 获取背景文件夹下所有图片
        bg_files = [f for f in os.listdir(self.backgrounds_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        bg_files.sort()

        print(f"找到 {len(src_files)} 张源图片")
        print(f"找到 {len(bg_files)} 张背景图待处理")

        # 外层循环：遍历每一张源图片
        for src_file in src_files:
            src_img_path = os.path.join(src_dir, src_file)
            src_base_name = os.path.splitext(src_file)[0]

            print(f"\n{'='*60}")
            print(f"【开始处理源文件】: {src_file}")
            print(f"{'='*60}")

            # 内层循环：遍历每一个背景图
            for bg_file in bg_files:
                dst_img_path = os.path.join(self.backgrounds_dir, bg_file)

                # 提取背景图的基础名（不含扩展名）
                bg_base_name = os.path.splitext(bg_file)[0]

                # 构建输出文件名：源文件名_场景.jpg
                output_img_path = os.path.join(self.output_dir, f"{src_base_name}_{bg_base_name}.jpg")

                # 确定场景类型
                if "3-" in bg_file or "斜拍" in bg_file:
                    mode = "tilted"
                elif "4-" in bg_file or "阴影" in bg_file:
                    mode = "shadow"
                elif "5-" in bg_file or "水印" in bg_file:
                    mode = "watermark"
                elif "6-" in bg_file or "不完整" in bg_file:
                    mode = "incomplete"
                else:
                    mode = "normal"

                # 自动/手动 获取背景图中的坐标
                detected_corners = detect_document_corners(dst_img_path, self.coord_file, debug=False)

                if detected_corners is None:
                    print(f"   跳过: {bg_file} (未获取到有效坐标)")
                    continue

                # 执行合成
                try:
                    process_scene_by_filename(src_img_path, dst_img_path, detected_corners,
                                            output_img_path, bg_base_name, mode=mode)
                except Exception as e:
                    print(f"   处理出错: {e}")
                    continue

        print("\n" + "#" * 60)
        print("🎉 所有任务处理完毕。")


if __name__ == "__main__":
    # 测试代码
    augmenter = ImageAugmenter(
        backgrounds_dir="backgrounds",
        output_dir="output/03_simulated"
    )
    augmenter.process_images("output/02_images")
