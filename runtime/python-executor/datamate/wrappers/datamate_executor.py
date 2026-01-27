# -*- coding: utf-8 -*-

import base64
import json
import time

import ray
import yaml
from jsonargparse import ArgumentParser
from loguru import logger

from datamate.core.dataset import RayDataset
from datamate.wrappers.executor import RayExecutor

import datamate.ops

class DataMateExecutor(RayExecutor):
    """
    基于Ray的执行器.

    1. 当前仅支持Mapper，Filter类型的算子。
    2. 当前仅加载json文件类型的数据集。
    """

    def __init__(self, cfg = None, meta = None):
        super().__init__(cfg, meta)

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

        for _ in dataset.data.iter_batches():
            pass

        self.scan_files()

if __name__ == '__main__':

    parser = ArgumentParser(description="Create API for Submitting Job to ray")

    parser.add_argument("--config_path", type=str, required=False, default="../configs/demo.yaml")
    parser.add_argument("--flow_config", type=str, required=False, default=None)

    args = parser.parse_args()

    config_path = args.config_path
    flow_config = args.flow_config

    if flow_config:
        m_cfg = yaml.safe_load(base64.b64decode(flow_config))
    else:
        with open(config_path, "r", encoding='utf-8') as f:
            m_cfg = yaml.safe_load(f)

    executor = DataMateExecutor(m_cfg)
    try:
        executor.run()
    except Exception as e:
        executor.update_db("FAILED")
        raise e
    executor.update_db("COMPLETED")
