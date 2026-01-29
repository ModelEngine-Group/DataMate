# -*- coding: utf-8 -*-
"""
收入证明生成算子 - DataMate算子入口
功能：批量生成收入证明的多模态训练数据集
"""

import os
import sys
import json
import shutil
import importlib.util
from pathlib import Path
from typing import Dict, Any

from loguru import logger

from datamate.core.base_op import Mapper


class IncomeCertificateGenerator(Mapper):
    """
    收入证明生成算子
    功能：从模板批量生成收入证明的多模态训练数据

    工作流程：
        1. 使用模板生成回填数据并填充文档
        2. 将Word文档转换为图片
        3. 添加公司印章（可选）
        4. 合成真实背景（可选）
        5. 保存初始JSON
        6. 转换为LLaVA或MLLM训练格式
    """

    def __init__(self, *args, **kwargs):
        """
        初始化算子
        :param args: 位置参数
        :param kwargs: 关键字参数，包含UI配置的参数
        """
        super().__init__(*args, **kwargs)

        # 获取UI配置参数
        self.count = int(kwargs.get("count", 5))
        self.output_format = kwargs.get("outputFormat", "llava")
        self.add_seal = kwargs.get("addSeal", True) if isinstance(kwargs.get("addSeal"), bool) else kwargs.get("addSeal", 'true').lower() == 'true'
        self.simulate_real_world = kwargs.get("simulateRealWorld", True) if isinstance(kwargs.get("simulateRealWorld"), bool) else kwargs.get("simulateRealWorld", 'true').lower() == 'true'

        # 获取算子目录
        self.operator_dir = os.path.dirname(os.path.abspath(__file__))

        # 添加common目录到Python路径
        common_dir = os.path.join(self.operator_dir, "common")
        if common_dir not in sys.path:
            sys.path.insert(0, common_dir)

        # 设置默认路径
        self.template_path = os.path.join(self.operator_dir, "template", "income-template.docx")
        self.coordinates_json = os.path.join(self.operator_dir, "data", "coordinates.json")
        self.background_folder = os.path.join(self.operator_dir, "backgrounds")
        self.output_folder = os.path.join(self.operator_dir, "output")

        # DataMate统一管理的输出目录（通过环境变量或配置获取）
        self.datamate_output_dir = kwargs.get("datamate_output_dir", "")

    def _load_main_module(self):
        """
        动态加载main.py模块
        :return: main模块对象
        """
        main_path = os.path.join(self.operator_dir, "main.py")
        spec = importlib.util.spec_from_file_location("income_certificate_main", main_path)
        main_module = importlib.util.module_from_spec(spec)
        sys.modules["income_certificate_main"] = main_module
        spec.loader.exec_module(main_module)
        return main_module

    def _copy_output_to_datamate(self, init_json_path: str, final_json_path: str) -> Dict[str, str]:
        """
        将生成的数据复制到DataMate统一管理目录
        :param init_json_path: 初始JSON文件路径
        :param final_json_path: 最终训练JSON文件路径
        :return: 复制后的文件路径字典
        """
        if not self.datamate_output_dir:
            return {"status": "skipped", "reason": "未配置DataMate输出目录"}

        try:
            # 创建DataMate输出子目录
            datamate_output_subdir = os.path.join(self.datamate_output_dir, "income_certificate")
            os.makedirs(datamate_output_subdir, exist_ok=True)

            # 复制JSON文件
            copied_files = {}

            # 复制初始JSON
            if os.path.exists(init_json_path):
                datamate_init_json = os.path.join(datamate_output_subdir, "income-template_format.json")
                shutil.copy2(init_json_path, datamate_init_json)
                copied_files["init_json"] = datamate_init_json

            # 复制最终JSON
            if os.path.exists(final_json_path):
                datamate_final_json = os.path.join(datamate_output_subdir, os.path.basename(final_json_path))
                shutil.copy2(final_json_path, datamate_final_json)
                copied_files["final_json"] = datamate_final_json

            # 复制整个output目录（可选）
            output_target = os.path.join(datamate_output_subdir, "output")
            if os.path.exists(self.output_folder):
                if os.path.exists(output_target):
                    shutil.rmtree(output_target)
                shutil.copytree(self.output_folder, output_target)
                copied_files["output_dir"] = output_target

            copied_files["status"] = "success"
            return copied_files

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "复制到DataMate目录失败"
            }

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行收入证明生成
        :param sample: 输入样本（可能包含模板路径等配置）
        :return: 处理后的样本，包含生成结果信息
        """
        self.template_path = sample["filePath"]
        file_path = sample.get('filePath')
        if not file_path.endswith('.docx') or os.path.normpath(file_path).count(os.sep) > 3:
            return sample

        parent_path = Path(file_path).parent

        self.coordinates_json = parent_path / "coordinates.json"
        self.background_folder = parent_path / "backgrounds"
        self.output_folder = sample.get("export_path")

        # DataMate统一管理的输出目录（通过环境变量或配置获取）
        self.datamate_output_dir = sample.get("export_path")

        try:
            # 验证模板文件是否存在
            if not os.path.exists(self.template_path):
                return sample

            # 加载main模块
            main_module = self._load_main_module()

            # 调用主生成函数
            main_module.batch_generate_training_data(
                template_path=self.template_path,
                count=self.count,
                coordinates_json_path=self.coordinates_json,
                background_folder_path=self.background_folder,
                output_folder_path=self.output_folder,
                output_format=self.output_format
            )

            return sample

        except Exception as e:
            # 打印错误信息（便于调试）
            logger.error(f"[IncomeCertificateGenerator] Error: {e}")
            import traceback
            traceback.print_exc()

            return sample
