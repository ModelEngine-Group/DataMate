import os
import uuid
from loguru import logger
import mimetypes
from datetime import datetime

from datamate.sql_manager.persistence_atction import TaskInfoPersistence

class FileScanner:
    def __init__(self, dataset_id):
        self.dataset_id = dataset_id
        self.persistence = TaskInfoPersistence()

    def get_existing_paths(self):
        """
        优化点1：一次性获取所有已存在的文件路径，存为 Set
        """
        logger.info("Fetching existing files from DB...")
        existing_files = self.persistence.query_existing_files(self.dataset_id)
        # fetchall 返回的是 list of tuples [('path1',), ('path2',)]
        # 我们将其转换为 set {'path1', 'path2'} 以实现 O(1) 查找速度
        existing_set = {row[0] for row in existing_files}
        logger.info(f"Found {len(existing_set)} existing files in DB.")
        return existing_set

    def prepare_file_data(self, sample, file_id):
        """
        优化点2：这部分逻辑从原来的 update_file_result 剥离出来
        只负责数据组装，不负责插入数据库
        """
        file_size = str(sample.get("fileSize"))
        file_type = str(sample.get("fileType"))
        file_name = str(sample.get("fileName"))
        dataset_id = str(sample.get("dataset_id"))
        file_path = str(sample.get("filePath"))
        create_time = datetime.now()

        # 获取最后访问时间，增加异常处理
        try:
            last_access_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        except (FileNotFoundError, OSError):
            last_access_time = create_time

        # 返回字典，供 executemany 使用
        return {
            "id": file_id,
            "dataset_id": dataset_id,
            "file_name": file_name,
            "file_path": file_path,
            "file_type": file_type,
            "file_size": file_size,
            "status": "COMPLETED",
            "upload_time": create_time,
            "last_access_time": last_access_time,
            "created_at": create_time,
            "updated_at": create_time
        }

    def scan_and_process(self, root_dir, batch_size=5000):
        logger.info(f"Scanning directory: {root_dir}")

        # 1. 内存中收集扫描到的所有文件 {path: metadata_dict}
        scanned_files_map = {}

        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file.startswith('.'): continue

                full_path = os.path.join(root, file)

                # 预先收集元数据
                try:
                    stats = os.stat(full_path)
                    f_type, _ = mimetypes.guess_type(full_path)
                    if not f_type: f_type = os.path.splitext(file)[1]

                    # 构造 sample 格式
                    scanned_files_map[full_path] = {
                        "fileSize": stats.st_size,
                        "fileType": f_type,
                        "fileName": file,
                        "dataset_id": self.dataset_id,
                        "filePath": full_path
                    }
                except OSError:
                    continue

        logger.info(f"Scanned {len(scanned_files_map)} files on disk.")

        # 2. 获取数据库中已有的路径
        existing_paths = self.get_existing_paths()

        # 3. 内存做差集 (Set Difference) -> 找出需要新增的路径
        scanned_paths_set = set(scanned_files_map.keys())
        new_paths = list(scanned_paths_set - existing_paths)

        logger.info(f"Need to insert {len(new_paths)} new files.")

        if not new_paths:
            logger.info("No new files to insert.")
            return

        # 4. 准备批量插入的数据
        insert_batch = []
        total_inserted = 0

        for path in new_paths:
            sample_data = scanned_files_map[path]
            new_file_id = str(uuid.uuid4())

            # 调用转换逻辑
            record = self.prepare_file_data(sample_data, new_file_id)
            insert_batch.append(record)

            # 优化点3：分批执行，防止一次性数据包过大导致 SQL 报错
            if len(insert_batch) >= batch_size:
                self.persistence.batch_insert_files(insert_batch)
                total_inserted += len(insert_batch)
                logger.info(f"Progress: {total_inserted}/{len(new_paths)} inserted...")
                insert_batch = [] # 清空列表

        # 插入剩余的数据
        if insert_batch:
            self.persistence.batch_insert_files(insert_batch)
            total_inserted += len(insert_batch)

        logger.info(f"Done. Total inserted: {total_inserted}")
