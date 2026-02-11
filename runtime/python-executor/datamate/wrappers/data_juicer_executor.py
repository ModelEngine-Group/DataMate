import base64
import time
from json import dumps as jdumps
from json import loads as jloads
from typing import Dict, Optional
from urllib.parse import urljoin

import ray
import requests
import yaml
from jsonargparse import ArgumentParser
from loguru import logger

from datamate.core.base_op import FileExporter, SUCCESS_STATUS
from datamate.core.constant import Fields
from datamate.wrappers.executor import RayExecutor
from datamate.sql_manager.persistence_atction import TaskInfoPersistence

DJ_OUTPUT = "outputs"


class DataJuicerClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def call_data_juicer_api(self, path: str, params: Optional[Dict] = None, json: Optional[Dict] = None):
        url = urljoin(self.base_url, path)

        if json is not None:
            response = requests.post(url, params=params, json=json)
        else:
            response = requests.get(url, params=params)

        return jloads(response.text)


    def init_config(self, dataset_path: str, export_path, process):
        """
        Initialize Data-Juicer config.

        Args:
            :param dataset_path: The input dataset path.
            :param process: The ops
            :param export_path: The export path.
        """
        dj_config = {
            "dataset_path": dataset_path,
            "export_path": export_path,
            "process": process,
            "executor_type": "default",
        }
        url_path = "/data_juicer/config/get_init_configs"
        try:
            res = self.call_data_juicer_api(url_path, params={"cfg": jdumps(dj_config)})
        except Exception as e:
            error_msg = f"An unexpected error occurred in calling {url_path}:\n{e}"
            raise RuntimeError(error_msg)
        return res["result"]

    def execute_config(self, dj_config: Dict):
        """
        Execute data-juicer data process.

        Args:
            dj_config: configs of data-juicer
        """

        url_path = "/data_juicer/core/DefaultExecutor/run"
        try:
            res = self.call_data_juicer_api(url_path, params={"skip_return": True}, json={"cfg": jdumps(dj_config)})
            if res.get("status") != "success":
                raise RuntimeError(f"An error occurred in calling {url_path}:\n{res}")
            return dj_config["export_path"]
        except Exception as e:
            error_msg = f"An unexpected error occurred in calling {url_path}:\n{e}"
            raise RuntimeError(error_msg)


class DataJuicerExecutor(RayExecutor):
    def __init__(self, cfg = None, meta = None):
        super().__init__(cfg, meta)
        self.client = DataJuicerClient(base_url="http://datamate-data-juicer:8000")
        self.dataset_path = f"/flow/{self.cfg.instance_id}/dataset_on_dj.jsonl"
        self.export_path = f"/flow/{self.cfg.instance_id}/processed_dataset.jsonl"

    def add_column(self, batch):
        batch_size = len(batch["filePath"])
        batch["execute_status"] = [SUCCESS_STATUS] * batch_size
        batch[Fields.instance_id] = [self.cfg.instance_id] * batch_size
        batch[Fields.export_path] = [self.cfg.export_path] * batch_size
        return batch

    def run(self):
        # 1. 加载数据集
        logger.info('Loading dataset with Ray...')

        if self.meta:
            file_content = base64.b64decode(self.meta)
            lines = file_content.splitlines()
            dataset = ray.data.from_items([jloads(line) for line in lines])
        else:
            dataset = self.load_dataset()

        logger.info('Read data...')
        dataset = dataset.map(FileExporter().read_file, num_cpus=0.05)

        # 保存原始数据文件ID集合，用于后续过滤数据检测
        original_file_ids = set(dataset.unique("fileId"))

        # 写入数据集文件
        with open(self.dataset_path, "w", encoding="utf-8") as f:
            for batch_df in dataset.iter_batches(batch_format="pandas", batch_size=2048):
                batch_df.to_json(f, orient="records", lines=True, force_ascii=False)

        logger.info('Processing data...')
        tstart = time.time()
        try:
            dj_config = self.client.init_config(self.dataset_path, self.export_path, self.cfg.process)
            result_path = self.client.execute_config(dj_config)

            processed_dataset = self.load_dataset(result_path)
            processed_dataset = processed_dataset.map_batches(self.add_column, num_cpus=0.05)
            processed_dataset = processed_dataset.map(FileExporter().save_file_and_db, num_cpus=0.05)
            for _ in processed_dataset.iter_batches():
                pass

            # 特殊处理：识别被过滤的数据
            if processed_dataset.count() == 0:
                processed_file_ids = set()
            else:
                processed_file_ids = set(processed_dataset.unique("fileId"))
            filtered_file_ids = original_file_ids - processed_file_ids

            if filtered_file_ids:
                logger.info(f"Found {len(filtered_file_ids)} filtered files, updating task result only")
                for sample_dict in dataset.iter_batches(batch_format="pandas", batch_size=2048):
                    for _, row in sample_dict.iterrows():
                        if str(row.get("fileId", "")) in filtered_file_ids:
                            row["fileSize"] = "0"
                            row["fileType"] = ""
                            row["execute_status"] = SUCCESS_STATUS
                            row[Fields.instance_id] = self.cfg.instance_id
                            TaskInfoPersistence().update_task_result(row)

            self.scan_files()
        except Exception as e:
            logger.error(f"An unexpected error occurred.", e)
            raise e
        tend = time.time()
        logger.info(f'All Ops are done in {tend - tstart:.3f}s.')


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
        with open(config_path, "r", encoding='utf-8') as f:
            m_cfg = yaml.safe_load(f)

    executor = DataJuicerExecutor(m_cfg)
    try:
        executor.run()
    except Exception as e:
        executor.update_db("FAILED")
        raise e
    executor.update_db("COMPLETED")