import base64
import os
from json import dumps as jdumps
from json import loads as jloads
from typing import Dict, Optional
from urllib.parse import urljoin

import ray
import requests
import yaml
from jsonargparse import ArgumentParser
from loguru import logger

from datamate.core.base_op import FileExporter
from datamate.wrappers.executor import RayExecutor

DJ_OUTPUT = "outputs"


class DataJuicerClient:
    def __init__(self, base_url):
        self.base_url = base_url
        pass

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
            "executor_type": "ray",
            "ray_address": "auto"
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

        url_path = "/data_juicer/core/Executor/run"
        try:
            res = self.call_data_juicer_api(url_path, params={"skip_return": True}, json={"cfg": jdumps(dj_config)})
            print(res)
            assert res["status"] == "success"
            return dj_config["export_path"]
        except Exception as e:
            error_msg = f"An unexpected error occurred in calling {url_path}:\n{e}"
            raise RuntimeError(error_msg)


class DataJuicerExecutor(RayExecutor):
    def __init__(self, cfg = None, meta = None):
        super().__init__(cfg, meta)
        self.client = DataJuicerClient(base_url="http://datamate-data-juicer:8000")
        self.dataset_path = f"/flow/{self.cfg.instance_id}/dataset_on_dj.jsonl"
        self.export_path = f"/flow/{self.cfg.instance_id}/process_on_dj.yaml"

    def run(self):
        # 1. 加载数据集
        logger.info('Loading dataset with Ray...')

        if self.meta:
            file_content = base64.b64decode(self.meta)
            lines = file_content.splitlines()
            dataset = ray.data.from_items([jloads(line) for line in lines])
        else:
            dataset = self.load_dataset()

        dataset.map(FileExporter().read_file,
                    fn_kwargs=getattr(self.cfg, 'kwargs', {}),
                    num_cpus=0.05,
                    compute=ray.data.ActorPoolStrategy(min_size=1, max_size=int(os.getenv("MAX_ACTOR_NUMS", "20"))))


        with open(self.dataset_path, "w", encoding="utf-8") as f:
            # iter_batches(batch_format="pandas") 会以 DataFrame 的形式分批返回数据
            # 这样比一行一行处理（iter_rows）要快得多
            for batch_df in dataset.iter_batches(batch_format="pandas", batch_size=2048):
                batch_df.to_json(f, orient="records", lines=True, force_ascii=False)

        try:
            dj_config = self.client.init_config(self.dataset_path, self.export_path, self.cfg.process)
            result_path = self.client.execute_config(dj_config)
        except Exception as e:
            raise e


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