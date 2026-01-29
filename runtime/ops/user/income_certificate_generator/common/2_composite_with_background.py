"""
图片合成工具
功能：将原始图片嵌入到随机选择的背景图片中，实现真实场景合成效果
作者：Claude Code
日期：2025-01-26
"""

import cv2
import numpy as np
import json
import os
import random
from pathlib import Path

from loguru import logger


def cv_imread(file_path):
    """读取含中文路径的图片"""
    return cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)


def cv_imwrite(file_path, img):
    """保存含中文路径的图片"""
    try:
        ext = os.path.splitext(file_path)[1]
        is_success, im_buf = cv2.imencode(ext, img)
        if is_success:
            im_buf.tofile(file_path)
            return True
        return False
    except Exception as e:
        logger.info(f"保存图片失败: {file_path}, 错误: {e}")
        return False


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
        logger.info(f"   [自动旋转] 方向不匹配 (Src横版={src_is_landscape}, Dst横版={dst_is_landscape})，执行旋转...")
        src = cv2.rotate(src, cv2.ROTATE_90_CLOCKWISE)

    return src


def _pad_src_to_match_ratio(src, dst_corners):
    """
    为了防止电子凭证被拉伸/挤压变形，我们需要先给源图补白边(Padding)，
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

    logger.info(f"   [比例校正] Src比例: {src_ratio:.2f}, Dst区域比例: {dst_ratio:.2f}")

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
        logger.info(f"   [比例校正] 为源图上下补白: {total_pad}px")

    else:
        # 源图比目标更"瘦/高"，目标比较"扁/胖"
        # 这种情况下，源图需要左右补白，变宽一点
        new_w = int(h_src * dst_ratio)
        total_pad = new_w - w_src
        pad_left = total_pad // 2
        pad_right = total_pad - pad_left

        src_padded = cv2.copyMakeBorder(src, 0, 0, pad_left, pad_right, cv2.BORDER_CONSTANT, value=(255, 255, 255))
        logger.info(f"   [比例校正] 为源图左右补白: {total_pad}px")

    return src_padded


def _base_synthesis_pipeline(src_path, dst_path, dst_corners, output_path,
                             mode="normal", enable_ratio_fix=False, enable_auto_rotate=False,
                             contrast_factor=None):
    """
    基础合成流水线。

    Args:
        contrast_factor: 对比度系数（可选，如果不指定则根据mode自动选择）
    """
    # 1. 读取图像
    src = cv_imread(src_path)
    dst = cv_imread(dst_path)
    if src is None or dst is None:
        logger.info(f"错误：无法读取图片。\nSrc: {src_path}\nDst: {dst_path}")
        return False

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

    dst_region_l = dst_lab[:,:,0][mask > 0]
    if dst_region_l.size == 0:
        logger.info("警告：目标区域掩模为空")
        return False

    l_mean_dst, l_std_dst = np.mean(dst_region_l), np.std(dst_region_l)
    src_region_l = warped_lab[:,:,0][mask > 0]
    l_mean_src, l_std_src = np.mean(src_region_l), np.std(src_region_l)

    # 针对不同模式，微调光照参数
    if contrast_factor is None:
        # 如果没有指定contrast_factor，则根据mode自动选择
        if mode == "shadow":
            contrast_factor = 0.85  # 阴影下对比度低一点可能更自然
        elif mode == "tilted":
            contrast_factor = 0.95
        else:
            contrast_factor = 1.0

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
        logger.info(f"融合失败，降级为直接覆盖: {e}")
        final_output = dst.copy()
        final_output[mask > 0] = matched_src[mask > 0]

    # 6. 保存
    if cv_imwrite(output_path, final_output):
        logger.info(f"   ✓ 成功！合成图已保存至: {output_path}")
        return True
    else:
        logger.info(f"   ✗ 保存失败")
        return False


def process_normal_scene(src_path, dst_path, dst_corners, output_path):
    """场景：正常拍摄（正对或微倾斜，光照均匀）"""
    logger.info("[处理逻辑] 使用【正常场景】合成算法")
    return _base_synthesis_pipeline(src_path, dst_path, dst_corners, output_path,
                                   mode="normal", enable_ratio_fix=True)


def process_tilted_scene(src_path, dst_path, dst_corners, output_path):
    """场景：斜拍（透视变形较大）"""
    print("[处理逻辑] 使用【斜拍场景】合成算法")
    return _base_synthesis_pipeline(src_path, dst_path, dst_corners, output_path,
                                   mode="tilted", enable_ratio_fix=True, enable_auto_rotate=True)


def process_shadow_scene(src_path, dst_path, dst_corners, output_path):
    """场景：有阴影（光照不均匀，有投影）"""
    print("[处理逻辑] 使用【阴影场景】合成算法")
    return _base_synthesis_pipeline(src_path, dst_path, dst_corners, output_path,
                                   mode="shadow")


def process_watermark_scene(src_path, dst_path, dst_corners, output_path):
    """场景：有水印（桌面或背景有复杂纹理）"""
    print("[处理逻辑] 使用【水印场景】合成算法")
    return _base_synthesis_pipeline(src_path, dst_path, dst_corners, output_path,
                                   mode="watermark", enable_ratio_fix=True, enable_auto_rotate=True)


def process_incomplete_scene(src_path, dst_path, dst_corners, output_path):
    """场景：拍摄不完整（凭证部分在画面外）"""
    print("[处理逻辑] 使用【不完整场景】合成算法")
    return _base_synthesis_pipeline(src_path, dst_path, dst_corners, output_path,
                                   mode="incomplete", enable_ratio_fix=True, enable_auto_rotate=True)


def determine_scene_type(background_name):
    """
    根据背景图片文件名判断场景类型（支持多场景匹配）

    Returns:
        list: 场景类型列表，如 ['tilted', 'shadow']
    """
    name_lower = background_name.lower()
    scene_types = []

    # 检查所有可能的关键词，返回所有匹配的场景
    if "斜拍" in name_lower or "旋转" in name_lower:
        scene_types.append("tilted")
    if "阴影" in name_lower or "投影" in name_lower:
        scene_types.append("shadow")
    if "水印" in name_lower or "遮挡" in name_lower:
        scene_types.append("watermark")
    if "不完整" in name_lower:
        scene_types.append("incomplete")

    # 如果没有匹配到任何场景，默认为 normal
    if not scene_types:
        scene_types.append("normal")

    return scene_types


def merge_scene_params(scene_types):
    """
    合并多个场景的参数

    规则：
    - enable_ratio_fix: 任一场景需要则为True
    - enable_auto_rotate: 任一场景需要则为True
    - contrast_factor: 取所有场景中的最小值（效果最强）

    Args:
        scene_types: 场景类型列表，如 ['tilted', 'shadow']

    Returns:
        dict: 包含 mode, enable_ratio_fix, enable_auto_rotate
    """
    # 各场景的参数配置
    scene_params = {
        "normal": {"enable_ratio_fix": True, "enable_auto_rotate": False, "contrast_factor": 1.0},
        "tilted": {"enable_ratio_fix": True, "enable_auto_rotate": True, "contrast_factor": 0.95},
        "shadow": {"enable_ratio_fix": False, "enable_auto_rotate": False, "contrast_factor": 0.85},
        "watermark": {"enable_ratio_fix": True, "enable_auto_rotate": True, "contrast_factor": 1.0},
        "incomplete": {"enable_ratio_fix": True, "enable_auto_rotate": True, "contrast_factor": 1.0},
    }

    # 初始化合并参数
    merged = {
        "enable_ratio_fix": False,
        "enable_auto_rotate": False,
        "contrast_factor": 1.0
    }

    # 遍历所有场景，合并参数
    for scene_type in scene_types:
        if scene_type in scene_params:
            params = scene_params[scene_type]
            # 任一场景需要则为True（OR逻辑）
            merged["enable_ratio_fix"] = merged["enable_ratio_fix"] or params["enable_ratio_fix"]
            merged["enable_auto_rotate"] = merged["enable_auto_rotate"] or params["enable_auto_rotate"]
            # 对比度系数取最小值（效果最强）
            merged["contrast_factor"] = min(merged["contrast_factor"], params["contrast_factor"])

    # 根据对比度系数确定mode
    if merged["contrast_factor"] <= 0.85:
        merged["mode"] = "shadow"
    elif merged["contrast_factor"] <= 0.95:
        merged["mode"] = "tilted"
    else:
        merged["mode"] = "normal"

    return merged


def composite_with_random_background(source_path, json_path, background_folder,
                                     output_folder, background_name=None):
    """
    将原始图片合成到随机选择的背景中

    Args:
        source_path: 原始图片路径
        json_path: JSON文件路径（包含背景图片的坐标信息）
        background_folder: 背景图片文件夹路径
        output_folder: 输出文件夹路径（合成图片将保存到此文件夹）
        background_name: 指定背景图片文件名（可选，如果不指定则随机选择）

    Returns:
        bool: 是否成功
    """
    print("="*60)
    print("图片合成工具")
    print("="*60)
    print(f"原始图片: {source_path}")
    print(f"背景文件夹: {background_folder}")
    print(f"坐标文件: {json_path}")
    print(f"输出文件夹: {output_folder}")
    print("-"*60)

    # 确保输出文件夹存在
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    # 检查原始图片是否存在
    if not os.path.exists(source_path):
        print(f"❌ 原始图片不存在: {source_path}")
        return False

    # 读取JSON文件
    if not os.path.exists(json_path):
        print(f"❌ JSON文件不存在: {json_path}")
        return False

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            coordinates_data = json.load(f)
    except Exception as e:
        print(f"❌ 读取JSON文件失败: {e}")
        return False

    print(f"📋 已加载 {len(coordinates_data)} 条背景坐标记录")

    # 筛选出在背景文件夹中的图片
    background_folder = os.path.abspath(background_folder)
    available_backgrounds = []

    for img_name, coords in coordinates_data.items():
        # 统一路径格式（标准化 + 转绝对路径 + 统一为小写比较）
        img_path_normalized = os.path.normpath(background_folder + "/" + img_name)
        img_dir = os.path.dirname(os.path.abspath(img_path_normalized))

        # Windows路径不区分大小写，统一转换为小写进行比较
        if img_dir.lower() == background_folder.lower():
            if os.path.exists(img_path_normalized):
                available_backgrounds.append((img_path_normalized, coords))

    if not available_backgrounds:
        print(f"❌ 在 {json_path} 中未找到指向 {background_folder} 的背景坐标记录")
        print(f"提示：请先运行 1_mark_background_coordinates.py 标记背景图片")
        return False

    print(f"📁 找到 {len(available_backgrounds)} 张可用背景图片")

    # 选择背景图片
    if background_name:
        # 如果指定了背景名称，查找对应的背景
        selected_bg = None
        for bg_path, coords in available_backgrounds:
            if background_name in os.path.basename(bg_path):
                selected_bg = (bg_path, coords)
                break

        if not selected_bg:
            print(f"❌ 未找到指定的背景图片: {background_name}")
            return False
    else:
        # 随机选择一个背景
        selected_bg = random.choice(available_backgrounds)

    bg_path, bg_corners = selected_bg
    bg_name = os.path.basename(bg_path)

    print(f"\n🎲 随机选择背景: {bg_name}")
    print("-"*60)

    # 判断场景类型（返回数组，支持多场景匹配）
    scene_types = determine_scene_type(bg_name)
    print(f"📊 检测到场景类型: {', '.join(scene_types)}")

    # 合并场景参数
    merged_params = merge_scene_params(scene_types)
    print(f"🔧 合并后参数: mode={merged_params['mode']}, "
          f"enable_ratio_fix={merged_params['enable_ratio_fix']}, "
          f"enable_auto_rotate={merged_params['enable_auto_rotate']}, "
          f"contrast_factor={merged_params['contrast_factor']}")

    # 调整坐标顺序
    bg_corners = order_points(np.array(bg_corners, dtype="float32"))

    # 生成输出文件名
    source_name = Path(source_path).stem
    bg_stem = Path(bg_name).stem
    # 如果有多个场景，在文件名中标注所有场景
    if len(scene_types) > 1:
        scene_suffix = "_".join(scene_types)
        output_filename = f"{source_name}_composite_{bg_stem}_{scene_suffix}.jpg"
    else:
        output_filename = f"{source_name}_composite_{bg_stem}.jpg"
    output_file_path = os.path.join(output_folder, output_filename)

    print(f"📝 输出文件: {output_filename}")

    # 使用合并后的参数进行一次合成
    success = _base_synthesis_pipeline(
        source_path, bg_path, bg_corners, output_file_path,
        mode=merged_params["mode"],
        enable_ratio_fix=merged_params["enable_ratio_fix"],
        enable_auto_rotate=merged_params["enable_auto_rotate"],
        contrast_factor=merged_params["contrast_factor"]
    )

    print("-"*60)
    if success:
        print("✨ 合成完成！")
    else:
        print("❌ 合成失败")

    return success


def batch_composite_with_random_backgrounds(source_folder, json_path, background_folder,
                                           output_folder, count=1):
    """
    批量合成：为每张原始图片随机选择背景进行合成

    Args:
        source_folder: 原始图片文件夹
        json_path: JSON文件路径
        background_folder: 背景图片文件夹
        output_folder: 输出文件夹
        count: 每张原始图片生成的合成图数量
    """
    print("="*60)
    print("批量图片合成工具")
    print("="*60)
    print(f"原始图片文件夹: {source_folder}")
    print(f"背景文件夹: {background_folder}")
    print(f"坐标文件: {json_path}")
    print(f"输出文件夹: {output_folder}")
    print(f"每张生成数量: {count}")
    print("-"*60)

    # 确保输出文件夹存在
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    # 获取所有原始图片
    source_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
        source_files.extend(Path(source_folder).glob(ext))

    if not source_files:
        print(f"❌ 在 {source_folder} 中未找到任何图片")
        return

    source_files.sort()
    print(f"📁 找到 {len(source_files)} 张原始图片\n")

    success_count = 0
    fail_count = 0

    # 遍历原始图片
    for idx, source_file in enumerate(source_files):
        print(f"\n[{idx+1}/{len(source_files)}] 处理: {source_file.name}")
        print("-"*60)

        # 为每张原始图片生成count张合成图
        for _ in range(count):
            # 合成（输出文件夹统一使用 output_folder）
            if composite_with_random_background(
                str(source_file),
                json_path,
                background_folder,
                output_folder
            ):
                success_count += 1
            else:
                fail_count += 1

    # 统计结果
    print("\n" + "="*60)
    print("✨ 批量合成完成！")
    print(f"   ✓ 成功: {success_count} 张")
    print(f"   ✗ 失败: {fail_count} 张")
    print("="*60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="图片合成工具 - 将原始图片嵌入到随机选择的背景中",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 单张图片合成（随机选择背景）
  python 2_composite_with_background.py source.jpg coordinates.json background_folder output_folder

  # 指定背景图片
  python 2_composite_with_background.py source.jpg coordinates.json background_folder output_folder --bg "桌面.jpg"

  # 批量合成模式
  python 2_composite_with_background.py source_folder coordinates.json background_folder output_folder --batch --count 3
        """
    )

    parser.add_argument("source", help="原始图片路径或文件夹")
    parser.add_argument("json_path", help="JSON文件路径（包含背景坐标）")
    parser.add_argument("background_folder", help="背景图片文件夹路径")
    parser.add_argument("output_folder", help="输出文件夹路径")
    parser.add_argument("--bg", help="指定背景图片文件名（可选）")
    parser.add_argument("--batch", action="store_true",
                       help="批量处理模式：处理文件夹中的所有图片")
    parser.add_argument("--count", type=int, default=1,
                       help="每张原始图片生成的合成图数量（批量模式下有效，默认1）")

    args = parser.parse_args()

    if args.batch:
        # 批量模式
        batch_composite_with_random_backgrounds(
            source_folder=args.source,
            json_path=args.json_path,
            background_folder=args.background_folder,
            output_folder=args.output_folder,
            count=args.count
        )
    else:
        # 单张模式
        composite_with_random_background(
            source_path=args.source,
            json_path=args.json_path,
            background_folder=args.background_folder,
            output_folder=args.output_folder,
            background_name=args.bg
        )
