# -*- coding: utf-8 -*-

import base64
import json
import time
from typing import Dict

import ray
import yaml
from jsonargparse import dict_to_namespace, ArgumentParser
from loguru import logger

from data_platform.common.utils import check_valid_path
from data_platform.core.dataset import RayDataset

import data_platform.ops


class RayExecutor:
    """
    基于Ray的执行器.

    1. 当前仅支持Mapper，Filter类型的算子。
    2. 当前仅加载json文件类型的数据集。
    """

    def __init__(self, cfg=None, meta=None):
        if isinstance(cfg, Dict):
            self.cfg = dict_to_namespace(cfg)
        else:
            logger.error(f"Please set param: cfg as type Dict, but given cfg as type {type(cfg).__name__}")
            raise TypeError(f"To params cfg, Dict type is required, but type {type(cfg).__name__} is given!")

        self.cfg.process = cfg['process']
        self.meta = meta

        # init ray
        logger.info('Initing Ray ...')
        ray.init()

    @staticmethod
    def load_meta(line):
        meta = json.loads(line)
        if meta.get("fileId"):
            meta["sourceFileId"] = meta.get("fileId")
        if meta.get("fileName"):
            meta["sourceFileName"] = meta.get("fileName")
        if meta.get("fileType"):
            meta["sourceFileType"] = meta.get("fileType")
        if meta.get("fileSize"):
            meta["sourceFileSize"] = meta.get("fileSize")
        if not meta.get("totalPageNum"):
            meta["totalPageNum"] = 0
        if not meta.get("extraFilePath"):
            meta["extraFilePath"] = None
        if not meta.get("extraFileType"):
            meta["extraFileType"] = None
        return meta

    def run(self):
        # 1. 加载数据集
        logger.info('Loading dataset with Ray...')

        if self.meta:
            file_content = base64.b64decode(self.meta)
            lines = file_content.splitlines()
            dataset = ray.data.from_items([json.loads(line) for line in lines])
        else:
            dataset = self.load_dataset()
        dataset = RayDataset(dataset, self.cfg)

        # 3. 处理数据
        logger.info('Processing data...')
        tstart = time.time()
        dataset.process(self.cfg.process, **getattr(self.cfg, 'kwargs', {}))
        tend = time.time()
        logger.info(f'All Ops are done in {tend - tstart:.3f}s.')

        dataset.data.materialize()

    def load_dataset(self):
        retry = 0
        dataset = None
        jsonl_file_path = self.cfg.dataset_path
        while True:
            if check_valid_path(jsonl_file_path):
                with open(jsonl_file_path, "r", encoding='utf-8') as meta:
                    lines = meta.readlines()
                    dataset = ray.data.from_items([self.load_meta(line) for line in lines])
                    break
            if retry < 5:
                retry += 1
                time.sleep(retry)
                continue
            else:
                logger.error(f"can not load dataset from dataset_path")
                raise RuntimeError(f"Load dataset Failed!, dataset_path: {self.cfg.dataset_path}.")

        return dataset


if __name__ == '__main__':

    parser = ArgumentParser(description="Create API for Submitting Job to Data-juicer")

    parser.add_argument("--config_path", type=str, required=False, default="../configs/demo.yaml")
    parser.add_argument("--flow_config", type=str, required=False, default=None)

    args = parser.parse_args()

    config_path = args.config_path
    flow_config = args.flow_config

    if flow_config:
        m_cfg = yaml.safe_load(base64.b64decode(flow_config))
    else:
        with open(config_path, "r", encoding='utf-8') as cfg:
            m_cfg = yaml.safe_load(cfg)

    executor = RayExecutor(m_cfg)
    executor.run()
