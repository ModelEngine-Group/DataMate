import json
import os
import shutil
import time
from pathlib import Path
from typing import Dict

from datamate.common.utils.file_scanner import FileScanner
import ray
from jsonargparse import dict_to_namespace
from loguru import logger

from datamate.common.utils import check_valid_path
from datamate.sql_manager.persistence_atction import TaskInfoPersistence


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

    def load_meta(self, line):
        meta = json.loads(line)
        if meta.get("fileId"):
            meta["sourceFileId"] = meta.get("fileId")
        if meta.get("fileName"):
            meta["sourceFileName"] = meta.get("fileName")
        if meta.get("fileType"):
            meta["sourceFileType"] = meta.get("fileType")
        if meta.get("fileSize"):
            meta["sourceFileSize"] = meta.get("fileSize")
        else:
            meta["sourceFileSize"] = 0
        if not meta.get("totalPageNum"):
            meta["totalPageNum"] = 0
        if not meta.get("extraFilePath"):
            meta["extraFilePath"] = None
        if not meta.get("extraFileType"):
            meta["extraFileType"] = None
        meta["dataset_id"] = self.cfg.dataset_id
        return meta

    def load_dj_meta(self, line):
        meta = json.loads(line)
        filepath = ""
        file = ""
        if meta.get("images"):
            if isinstance(meta["images"], list):
                filepath = meta["images"][0]
                file = Path(filepath)
                del meta["images"]
        elif meta.get("audios"):
            if isinstance(meta["audios"], list):
                filepath = meta["audios"][0]
                file = Path(filepath)
                del meta["audios"]
        elif meta.get("videos"):
            if isinstance(meta["videos"], list):
                filepath = meta["videos"][0]
                file = Path(filepath)
                del meta["videos"]
        if filepath and file:
            filename = f"{Path(meta['fileName']).stem}{file.suffix}"
            meta["fileName"] = filename
            meta["filePath"] = f"/dataset/{self.cfg.dataset_id}/{filename}"
            meta["fileType"] = file.suffix[1:]
            meta["fileSize"] = file.stat().st_size
            os.makedirs(f"/dataset/{self.cfg.dataset_id}", exist_ok=True)
            shutil.move(filepath, f"/dataset/{self.cfg.dataset_id}/{filename}")
        return {k: v for k, v in meta.items() if not (isinstance(k, str) and k.startswith('_'))}

    def run(self):
        pass

    def load_dataset(self, jsonl_file_path = None):
        retry = 0
        dataset = None
        if jsonl_file_path is None:
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

    def load_dj_dataset(self, jsonl_file_path = None):
        retry = 0
        dataset = None
        if jsonl_file_path is None:
            jsonl_file_path = self.cfg.dataset_path
        while True:
            if check_valid_path(jsonl_file_path):
                with open(jsonl_file_path, "r", encoding='utf-8') as meta:
                    lines = meta.readlines()
                    dataset = ray.data.from_items([self.load_dj_meta(line) for line in lines])
                    break
            if retry < 5:
                retry += 1
                time.sleep(retry)
                continue
            else:
                logger.error(f"can not load dataset from dataset_path")
                raise RuntimeError(f"Load dataset Failed!, dataset_path: {self.cfg.dataset_path}.")

        return dataset

    def update_db(self, status):
        task_info = TaskInfoPersistence()
        task_info.update_result(self.cfg.dataset_id, self.cfg.instance_id, status)

    def scan_files(self):
        scanner = FileScanner(self.cfg.dataset_id)
        scanner.scan_and_process(self.cfg.export_path)
