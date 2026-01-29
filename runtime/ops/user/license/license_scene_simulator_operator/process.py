# -*- coding: utf-8 -*-

"""
场景模拟算子：SceneSimulatorOperator
将合成图片与真实世界背景图片进行融合
"""
import json
import os
from pathlib import Path
from typing import Dict, Any

from loguru import logger
from datamate.core.base_op import Mapper


class LicenseSceneSimulatorOperator(Mapper):
    """
    场景模拟算子
    将合成图片与真实世界背景图片进行融合
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 从 metadata.yml 的参数获取配置
        self.scenes = int(kwargs.get('scenesParam', 2))
        
        # 处理场景列表（checkbox 返回的是 list 或逗号分隔字符串）
        scenes_val = kwargs.get('sceneListParam', [])
        if isinstance(scenes_val, str):
            self.allowed_scenes = scenes_val.split(',')
        else:
            self.allowed_scenes = scenes_val if scenes_val else ['normal']
            
        self.skip_detect = kwargs.get('skipDetectParam', True)
        
        # 背景图目录（算子目录下）
        self.bg_dir = None
        
        # 坐标缓存文件路径（算子目录下）
        self.coord_cache_file = None
    
    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行场景模拟
        
        Args:
            sample: 输入的数据样本，包含 images_dir 等字段
        
        Returns:
            处理后的数据样本，包含生成的图片
        """
        try:
            file_path = sample.get('filePath')
            if not file_path.endswith('.jpg') or os.path.normpath(file_path).count(os.sep) > 3:
                return sample

            # 获取输入路径
            parent_path = Path(file_path).parent
            coords_files = list(Path(parent_path).glob("*.json"))

            if len(coords_files) == 0:
                sample['text'] = ""
                logger.error(f"坐标文件不存在: {coords_files}")
                return sample

            self.coord_cache_file = coords_files[0]
            self.bg_dir = parent_path / "backgrounds"
            input_dir = sample.get('export_path') + "/images"
            output_dir = input_dir
            
            if not input_dir or not os.path.exists(input_dir):
                logger.error(f"输入目录不存在: {input_dir}")
                return sample
            
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            # 获取所有营业执照合成图片
            src_files = [f for f in os.listdir(input_dir) 
                        if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            src_files.sort()
            
            # 获取所有背景图
            bg_files = [f for f in os.listdir(self.bg_dir) 
                        if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            bg_files.sort()
            
            logger.info(f"找到 {len(src_files)} 张源图")
            logger.info(f"找到 {len(bg_files)} 张背景图")
            
            # 过滤背景图
            filtered_bg_files = []
            for bg_file in bg_files:
                bg_name = bg_file.lower()
                scene_mode = self._determine_scene_mode(bg_name)
                if scene_mode in self.allowed_scenes:
                    filtered_bg_files.append(bg_file)
            
            logger.info(f"过滤后剩余 {len(filtered_bg_files)} 张背景图")
            
            # 处理每张源图
            saved_count = 0
            for src_file in src_files:
                src_name = os.path.splitext(src_file)[0]
                src_path = os.path.join(input_dir, src_file)
                logger.info(f"\n处理源图: {src_file}")
                
                # 决定使用哪些背景图
                use_random_selection = self.scenes < len(filtered_bg_files)
                if use_random_selection:
                    selected_bg_files = [filtered_bg_files[i] for i in range(self.scenes)]
                    logger.info(f"  随机选择了 {len(selected_bg_files)} 个场景")
                else:
                    selected_bg_files = filtered_bg_files
                
                # 处理每个背景图
                for bg_file in selected_bg_files:
                    bg_path = os.path.join(self.bg_dir, bg_file)
                    bg_name = os.path.splitext(bg_file)[0]
                    
                    # 确定场景模式
                    scene_mode = self._determine_scene_mode(bg_file)
                    
                    # 生成输出文件名
                    output_filename = f"{src_name}_{bg_name}.jpg"
                    output_path = os.path.join(output_dir, output_filename)
                    
                    logger.info(f"  背景图: {bg_file} ({scene_mode})")
                    
                    # 检测或加载坐标
                    if self.skip_detect:
                        corners = self._load_cached_coordinates(bg_file)
                        if corners is None:
                            logger.info(f"    跳过：无缓存坐标")
                            continue
                    else:
                        corners = self._detect_document_corners(bg_path)
                        if corners is None:
                            logger.info(f"    跳过：无法检测到文档区域")
                            continue
                        
                        # 保存检测到的坐标到缓存
                        self._save_cached_coordinates(bg_file, corners)
                    
                    # 执行合成（调用原始函数）
                    self._base_synthesis_pipeline(src_path, bg_path, corners, output_path, scene_mode)
                    saved_count += 1
            
        except Exception as e:
            logger.error(f"SceneSimulatorOperator 执行失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return sample
    
    def _determine_scene_mode(self, bg_filename: str) -> str:
        """根据背景图文件名确定场景模式"""
        filename = bg_filename.lower()
        if "3-" in filename or "斜拍" in filename:
            return "tilted"
        elif "4-" in filename or "阴影" in filename:
            return "shadow"
        elif "5-" in filename or "水印" in filename:
            return "watermark"
        elif "6-" in filename or "不完整" in filename:
            return "incomplete"
        else:
            return "normal"
    
    def _load_cached_coordinates(self, bg_filename: str):
        """从缓存文件加载坐标"""
        if not os.path.exists(self.coord_cache_file):
            logger.warning(f"未找到缓存文件: {self.coord_cache_file}")
            return None
        try:
            with open(self.coord_cache_file, "r", encoding="utf-8") as f:
                data = f.read()
                # 简单解析：查找文件名
                for line in data.split('\n'):
                    if bg_filename in line:
                        # 提取坐标数据（简化处理）
                        import json
                        coords_data = json.loads(line.split(':', 1)[1].strip())
                        return coords_data
        except Exception as e:
            logger.warning(f"读取缓存失败: {e}")
            return None
    
    def _save_cached_coordinates(self, bg_filename: str, coords):
        """保存坐标到缓存文件"""
        data = {}
        if os.path.exists(self.coord_cache_file):
            try:
                with open(self.coord_cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                pass
        
        # 添加新坐标
        data[bg_filename] = coords.tolist() if hasattr(coords, 'tolist') else coords
        try:
            with open(self.coord_cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")
    
    def _detect_document_corners(self, bg_path: str):
        """检测文档区域（简化版，返回None表示使用缓存）"""
        # 这里返回 None，表示应该使用缓存坐标
        # 如果需要实时检测，可以在这里实现检测逻辑
        logger.info(f"文档区域检测功能已禁用，使用缓存坐标")
        return None
    
    def _base_synthesis_pipeline(self, src_path, dst_path, corners, output_path, mode):
        """基础合成流水线（调用原始函数）"""
        # 导入原始模块
        from .src.scene_simulator import base_synthesis_pipeline
        from .src.scene_simulator import process_normal_scene
        from .src.scene_simulator import process_tilted_scene
        from .src.scene_simulator import process_shadow_scene
        from .src.scene_simulator import process_watermark_scene
        from .src.scene_simulator import process_incomplete_scene
        
        # 根据场景模式选择处理函数
        scene_handlers = {
            'normal': process_normal_scene,
            'tilted': process_tilted_scene,
            'shadow': process_shadow_scene,
            'watermark': process_watermark_scene,
            'incomplete': process_incomplete_scene
        }
        
        handler = scene_handlers.get(mode, process_normal_scene)
        handler(src_path, dst_path, corners, output_path)
