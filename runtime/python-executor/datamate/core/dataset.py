# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import importlib
import sys
import uuid
from abc import ABC, abstractmethod

import pyarrow as pa
from enum import Enum
from loguru import logger
from ray import data as rd

from datamate.core.base_op import Filter, Mapper, Slicer
from datamate.core.constant import Fields
from datamate.core.base_op import OPERATORS, BaseOp

from core.base_op import Filter as RELATIVE_Filter, Mapper as RELATIVE_Mapper, Slicer as RELATIVE_Slicer

rd.DataContext.get_current().enable_progress_bars = False


class Formatters(Enum):
    """
    抽取算子和落盘算子枚举类
    """
    FILE_EXPORTER = "FileExporter"
    IMG_FORMATTER = "ImgFormatter"
    OCR_FORMATTER = "OcrFormatter"
    PDF_CPU_FORMATTER = "PdfCpuFormatter"
    SLID_FORMATTER = "SlideFormatter"
    TEXT_FORMATTER = "TextFormatter"
    WORD_FORMATTER = "WordFormatter"
    UNION_FORMATTER = "UnionFormatter"
    ONNX_FORMATTER = "OnnxImg2TextFormatter"

    @classmethod
    def is_member(cls, op_name):
        return op_name in cls._value2member_map_


class BasicDataset(ABC):

    @abstractmethod
    def process(
            self,
            cfg_process,
            *,
            exporter=None,
            checkpointer=None
    ) -> BasicDataset:
        pass


def preprocess_dataset(dataset: rd.Dataset, cfg) -> rd.Dataset:
    columns = dataset.columns()
    new_column_names = [getattr(Fields, attr_name)
                        for attr_name in vars(Fields)
                        if attr_name not in columns and not attr_name.startswith('__')]

    def process_batch_arrow(table: pa.Table, names_list=None) -> pa.Table:
        name2value_table = {
            Fields.instance_id: cfg.instance_id,
            Fields.export_path: cfg.export_path
        }

        for column_name in names_list:
            if column_name in name2value_table.keys():
                new_column_data = [name2value_table[column_name] for _ in range(len(table))]
            else:
                new_column_data = [None for _ in range(len(table))]
            table = table.append_column(column_name, [new_column_data])
        return table

    if new_column_names:
        dataset = dataset.map_batches(process_batch_arrow,
                                      fn_kwargs={"names_list": new_column_names},
                                      num_cpus=0.05,
                                      batch_format='pyarrow')

    return dataset


class RayDataset(BasicDataset):

    def __init__(self,
                 dataset: rd.Dataset,
                 cfg=None) -> None:
        self.onnx_ops_name = ["OnnxImg2TextFormatter", "OnnxImageContentFilter"]
        self.npu_ops_name = ["Img2TextFormatter", "ImageContentFilter"]
        self.data = preprocess_dataset(dataset, cfg)

    def process(self,
                cfg_process,
                *,
                exporter=None,
                checkpointer=None,
                **kwargs) -> BasicDataset:

        # 从注册器加载类
        operators_cls_list = []
        init_kwargs_list = []
        for index, process in enumerate(cfg_process):
            op_name, init_kwargs = list(process.items())[0]
            init_kwargs = {} if not init_kwargs else init_kwargs
            init_kwargs.update({'op_name': op_name})

            # 加载Ops module
            temp_ops = self.load_ops_module(op_name)
            operators_cls_list.append(temp_ops)

            if index == 0:
                init_kwargs["is_first_op"] = True

            if index == len(cfg_process) - 1:
                init_kwargs["is_last_op"] = True
            init_kwargs["instance_id"] = kwargs.get("instance_id", str(uuid.uuid4()))
            init_kwargs_list.append(init_kwargs)

        for cls_id, operators_cls in enumerate(operators_cls_list):
            self._run_single_op(operators_cls, init_kwargs_list[cls_id], **kwargs)
        return self

    def load_ops_module(self, op_name):
        '''
        加载算子模块
        :param op_name: 算子名称
        :return: 算子对象
        '''
        parent_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ops")
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        registry_content = OPERATORS.modules.get(op_name)
        if registry_content is None:
            from core.base_op import OPERATORS as RELATIVE_OPERATORS
            registry_content = RELATIVE_OPERATORS.modules.get(op_name)
        if isinstance(registry_content, str):
            # registry_content是module的路径
            submodule = importlib.import_module(registry_content)
            res = getattr(submodule, op_name, None)
            if res is None:
                raise ImportError(f"Import Ops module {op_name} Failed.")
            else:
                logger.info(f"Import Ops module {op_name} Success.")
        elif isinstance(registry_content, type) and issubclass(registry_content, BaseOp):
            # registry_content是module本身
            res = registry_content
        else:
            res = None
        return res

    def _run_single_op(self, operators_cls, init_kwargs, **kwargs):
        max_actor_nums = os.getenv("MAX_ACTOR_NUMS", "20")

        resources = {}

        if init_kwargs.get("npu", 0) > 0:
            resources["npu"] = init_kwargs.get("npu")

        if init_kwargs.get("arch", "arm").startswith("x86"):
            resources["arch"] = "x86"

        cpu = init_kwargs.get("cpu", 0.05)
        memory = init_kwargs.get("memory", None)

        kwargs.update({"ext_params": {}, "failed_reason": {}, "target_type": None})
        try:
            if issubclass(operators_cls, (Mapper, RELATIVE_Mapper)):
                self.data = self.data.map(operators_cls,
                                          fn_constructor_kwargs=init_kwargs,
                                          fn_kwargs=kwargs,
                                          resources=resources,
                                          num_cpus=cpu,
                                          memory=memory,
                                          compute=rd.ActorPoolStrategy(min_size=1,
                                                                       max_size=int(max_actor_nums)))

            elif issubclass(operators_cls, (Slicer, RELATIVE_Slicer)):
                self.data = self.data.flat_map(operators_cls,
                                               fn_constructor_kwargs=init_kwargs,
                                               fn_kwargs=kwargs,
                                               resources=resources,
                                               num_cpus=cpu,
                                               memory=memory,
                                               compute=rd.ActorPoolStrategy(min_size=1,
                                                                            max_size=int(max_actor_nums)))

            elif issubclass(operators_cls, (Filter, RELATIVE_Filter)):
                self.data = self.data.filter(operators_cls,
                                             fn_constructor_kwargs=init_kwargs,
                                             fn_kwargs=kwargs,
                                             resources=resources,
                                             num_cpus=cpu,
                                             memory=memory,
                                             compute=rd.ActorPoolStrategy(min_size=1,
                                                                          max_size=int(max_actor_nums)))
            else:
                logger.error(
                    'Ray executor only support Filter, Mapper and Slicer OPs for now')
                raise NotImplementedError
        except Exception as e:
            logger.error(e)
            raise Exception("Error! Ops Details:") from e
