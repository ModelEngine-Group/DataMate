import os
import sys
import subprocess
import re
import json
import cv2
import numpy as np
import mindspore
from typing import Dict, Any
from datamate.core.base_op import Mapper

# 全局变量实现单例模式，防止显存 OOM
GLOBAL_MODEL = None
GLOBAL_PROCESSOR = None

class VideoAnalysisOperator(Mapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 1. 环境路径修复 (来自 Cell 1 & 2)
        self._setup_env()
        
        # 2. 从 UI 配置获取参数
        self.task_type = kwargs.get("taskType", "safety_check")
        self.model_path = kwargs.get("modelPath", "/mnt/nvme0n1/home/gtx/Video_Analysis_System/models/qwen/Qwen/Qwen2.5-VL-7B-Instruct")
        
        # 3. 初始化加载模型
        self._init_resources()

        # 4. 任务 Prompt 库 (来自 Cell 3 & 4)
        self.prompts = {
            "audit": "分析视频中是否包含违规内容(色情/政治/国家领导人/战争/血腥)。仅返回区间数组如[[s,e]]，若无则返[]。禁言。",
            "summary": "请详细描述这个视频里发生的主要内容，以‘这个视频’开头，30字以内",
            "classify": "请分析视频内容，将其归类为以下类别中的【唯一一个】：\n日常生活, 影视剧集, 音乐舞蹈, 游戏电竞, 动漫, 新闻, 教育, 科技, 财经, 体育, 美食, 时尚, 汽车, 萌宠, 健康, 风光, 三农, 监控, 广告, 其他\n只输出类别名称。",
            "extreme": "你现在是时序审计员。任务：将视频划分为5个以上的连续时间段，描述动作变化。格式必须为：[开始, 结束] 关键词。"
        }

    def _setup_env(self):
        """路径穿透与修复"""
        STD_PATH = "/mnt/nvme0n1/home/gtx/miniconda3/envs/video_ai/lib/python3.9/site-packages"
        CANN_PATH = "/mnt/nvme0n1/home/gtx/my_env/cann/ascend-toolkit/8.3.RC2/python/site-packages"
        for p in [STD_PATH, CANN_PATH]:
            if os.path.exists(p) and p not in sys.path:
                sys.path.insert(0, p)

    def _init_resources(self):
        """单例加载 Qwen2.5-VL"""
        global GLOBAL_MODEL, GLOBAL_PROCESSOR
        if GLOBAL_MODEL is None:
            from mindone.transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
            from mindspore import context
            context.set_context(mode=context.PYNATIVE_MODE, device_target="Ascend", device_id=0)
            
            GLOBAL_MODEL = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                self.model_path, mindspore_dtype=mindspore.bfloat16, 
                trust_remote_code=False, local_files_only=True
            )
            GLOBAL_PROCESSOR = AutoProcessor.from_pretrained(self.model_path, trust_remote_code=False, local_files_only=True)
        self.model = GLOBAL_MODEL
        self.processor = GLOBAL_PROCESSOR

    # --- 通用工具集 ---
    def _get_duration(self, path):
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path]
        return float(subprocess.run(cmd, stdout=subprocess.PIPE).stdout)

    def _read_frames(self, path, num_frames=8, start=None, end=None, res_limit=None):
        cap = cv2.VideoCapture(path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_v_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        s_idx = int(start * fps) if start is not None else 0
        e_idx = int(end * fps) if end is not None else total_v_frames
        indices = np.linspace(s_idx, e_idx - 1, num_frames, dtype=int)
        frames = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                if res_limit:
                    w, h = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    scale = np.sqrt(res_limit / (w * h))
                    frame = cv2.resize(frame, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)
                frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        cap.release()
        return frames

    def _infer(self, frames, prompt, max_tokens=100):
        messages = [{"role": "user", "content": [{"type": "video", "video": frames}, {"type": "text", "text": prompt}]}]
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(text=[text], videos=[frames], padding=True, return_tensors="ms", max_pixels=448*448)
        for k, v in inputs.items():
            if isinstance(v, mindspore.Tensor) and v.dtype == mindspore.float32:
                inputs[k] = v.astype(mindspore.bfloat16)
        gen_ids = self.model.generate(**inputs, max_new_tokens=max_tokens)
        return self.processor.batch_decode(gen_ids[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)[0].strip()

    # --- 核心业务逻辑分流 ---
    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        video_path = sample.get('filePath')
        if not video_path or not os.path.exists(video_path): return sample

        if self.task_type == "safety_check":
            sample['audit_result'] = self._run_safety_audit(video_path)
        elif self.task_type == "video_cut":
            violations = self._run_safety_audit(video_path, return_raw=True)
            if violations:
                sample['filePath'] = self._run_physical_cut(video_path, violations)
        elif self.task_type == "video_annot":
            sample['annotation'] = self._run_extreme_annot(video_path)
        elif self.task_type == "summary_gen":
            frames = self._read_frames(video_path, num_frames=16)
            sample['summary'] = self._infer(frames, self.prompts["summary"])
        elif self.task_type == "video_classify":
            frames = self._read_frames(video_path, num_frames=8)
            sample['category'] = self._infer(frames, self.prompts["classify"])

        return sample

    def _run_safety_audit(self, path, return_raw=False):
        """高精审计 (Cell 3)"""
        duration = self._get_duration(path)
        violations, curr = [], 0.0
        while curr < duration:
            end = min(curr + 10, duration)
            frames = self._read_frames(path, num_frames=12, start=curr, end=end)
            res = self._infer(frames, self.prompts["audit"], max_tokens=40)
            found = re.findall(r'\[\s*(\d+\.?\d*)\s*,\s*(\d+\.?\d*)\s*\]', res)
            for s, e in found: violations.append([curr + float(s), curr + float(e)])
            curr += 8
        if return_raw: return violations
        return f"发现{len(violations)}处违规" if violations else "安全"

    def _run_physical_cut(self, path, violations):
        """FFMPEG 物理切除 (Cell 3)"""
        out_path = path.replace(".mp4", "_cleaned.mp4")
        # 构建 FFMPEG 保留区间逻辑... (此处填入你 Cell 3 的拼接代码)
        return out_path

    def _run_extreme_annot(self, path):
        """极速标注 (Cell 4)"""
        frames = self._read_frames(path, num_frames=12, res_limit=128*128)
        return self._infer(frames, self.prompts["extreme"], max_tokens=256)