import json
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from app.core.logging import get_logger
from app.db.models.data_collection import CollectionTask, TaskExecution, CollectionTemplate
from app.module.collection.schema.collection import CollectionConfig, SyncMode
from app.module.shared.schema import TaskStatus

logger = get_logger(__name__)

class DataxClient:
    def __init__(self, task: CollectionTask, execution: TaskExecution, template: CollectionTemplate):
        self.execution = execution
        self.task = task
        self.template = template
        self.config_file_path = f"/flow/data-collection/{task.id}/config.json"
        self.python_path = "python"
        self.datax_main = "/opt/datax/bin/datax.py"
        Path(self.config_file_path).parent.mkdir(parents=True, exist_ok=True)

    def validate_json_string(self) -> Dict[str, Any]:
        """
        验证 JSON 字符串

        Returns:
            解析后的配置字典
        """
        try:
            config = json.loads(self.task.config)

            # 基本验证
            if 'job' not in config:
                raise ValueError("JSON 必须包含 'job' 字段")

            if 'content' not in config.get('job', {}):
                raise ValueError("job 必须包含 'content' 字段")

            logger.info("JSON 配置验证通过")
            return config

        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 格式错误: {e}")
        except Exception as e:
            raise ValueError(f"配置验证失败: {e}")

    @staticmethod
    def generate_datx_config(task_config: CollectionConfig, template: CollectionTemplate, target_path: str):
        # 校验参数
        reader_parameter = {
            **(task_config.parameter if task_config.parameter else {}),
            **(task_config.reader if task_config.reader else {})
        }
        dest_parameter = {}
        if template.target_type == "txtfilewriter":
            dest_parameter = {
                "path": target_path,
                "fileName": "collection_result",
                "writeMode": "truncate"
            }
        elif template.target_type == "nfswriter":
            dest_parameter = {
                "destPath": target_path
            }
        elif template.target_type == "s3writer" or template.target_type == "glusterfswriter" or template.target_type == "localwriter":
            dest_parameter = {
                "destPath": target_path
            }
        writer_parameter = {
            **(task_config.parameter if task_config.parameter else {}),
            **(task_config.writer if task_config.writer else {}),
            **dest_parameter
        }
        # 生成任务运行配置
        job_config = {
            "content": [
                {
                    "reader": {
                        "name": template.source_type,
                        "parameter": reader_parameter
                    },
                    "writer": {
                        "name": template.target_type,
                        "parameter": writer_parameter
                    }
                }
            ],
            "setting": {
                "speed": {
                    "channel": 2
                }
            }
        }
        task_config.job = job_config

    def create__config_file(self) -> str:
        """
        创建配置文件

        Returns:
            临时文件路径
        """
        # 验证 JSON
        config = self.validate_json_string()

        # 写入临时文件
        with open(self.config_file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        logger.debug(f"创建配置文件: {self.config_file_path}")
        return self.config_file_path

    def run_datax_job(self):
        """
        启动 DataX 任务

        Returns:
            执行结果字典
        """
        # 创建配置文件
        self.create__config_file()
        try:
            # 构建命令
            cmd = [self.python_path, str(self.datax_main), str(self.config_file_path)]
            cmd_str = ' '.join(cmd)
            logger.info(f"执行命令: {cmd_str}")
            if not self.execution.started_at:
                self.execution.started_at = datetime.now()
            # 执行命令并写入日志
            with open(self.execution.log_path, 'w', encoding='utf-8') as log_f:
                # 写入头信息
                self.write_header_log(cmd_str, log_f)
                # 启动datax进程
                exit_code = self._run_process(cmd, log_f)
                # 记录结束时间
                self.execution.completed_at = datetime.now()
                self.execution.duration_seconds = (self.execution.completed_at - self.execution.started_at).total_seconds()
                # 写入结束信息
                self.write_tail_log(exit_code, log_f)
            if exit_code == 0:
                logger.info(f"DataX 任务执行成功: {self.execution.id}")
                logger.info(f"执行耗时: {self.execution.duration_seconds:.2f} 秒")
                self.execution.status = TaskStatus.COMPLETED.name
                self.rename_collection_result()
            else:
                self.execution.error_message = self.execution.error_message or f"DataX 任务执行失败，退出码: {exit_code}"
                self.execution.status = TaskStatus.FAILED.name
                logger.error(self.execution.error_message)
        except Exception as e:
            self.execution.completed_at = datetime.now()
            self.execution.duration_seconds = (self.execution.completed_at - self.execution.started_at).total_seconds()
            self.execution.error_message = f"执行异常: {e}"
            self.execution.status = TaskStatus.FAILED.name
            logger.error(f"执行异常: {e}", exc_info=True)
        if self.task.sync_mode == SyncMode.ONCE:
            self.task.status = self.execution.status

    def rename_collection_result(self):
        if self.template.target_type != "txtfilewriter":
            return
        target_path = Path(self.task.target_path)
        if not target_path.exists():
            logger.warning(f"Target path does not exist: {target_path}")
            return
        # If it's a directory, find all files without extensions
        for file_path in target_path.iterdir():
            if file_path.is_file() and not file_path.suffix:
                new_path = file_path.with_suffix('.csv')
                try:
                    file_path.rename(new_path)
                    logger.info(f"Renamed {file_path} to {new_path}")
                except Exception as e:
                    logger.error(f"Failed to rename {file_path} to {new_path}: {str(e)}")

    def _run_process(self, cmd: list[str], log_f) -> int:
        # 启动进程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            bufsize=1,
            universal_newlines=True
        )

        # 创建读取线程
        stdout_thread = threading.Thread(target=lambda stream=process.stdout: self.read_stream(stream, log_f))
        stderr_thread = threading.Thread(target=lambda stream=process.stderr: self.read_stream(stream, log_f))

        stdout_thread.start()
        stderr_thread.start()

        # 等待进程完成
        try:
            exit_code = process.wait(timeout=self.task.timeout_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            exit_code = -1
            self.execution.error_message = f"任务执行超时（{self.task.timeout_seconds}秒）"
            logger.error(f"任务执行超时（{self.task.timeout_seconds}秒）")

        # 等待线程完成
        stdout_thread.join(timeout=5)
        stderr_thread.join(timeout=5)
        return exit_code

    def write_tail_log(self, exit_code: int, log_f):
        log_f.write("\n" + "=" * 100 + "\n")
        log_f.write(f"End Time: {self.execution.completed_at}\n")
        log_f.write(f"Execution Time: {self.execution.duration_seconds:.2f} seconds\n")
        log_f.write(f"Exit Code: {exit_code}\n")
        log_f.write(f"Status: {'SUCCESS' if exit_code == 0 else 'FAILED'}\n")

    def write_header_log(self, cmd: str, log_f):
        log_f.write(f"DataX Task Execution Log\n")
        log_f.write(f"Job ID: {self.execution.id}\n")
        log_f.write(f"Start Time: {self.execution.started_at}\n")
        log_f.write(f"Config Source: JSON String\n")
        log_f.write(f"Command: {cmd}\n")
        log_f.write("=" * 100 + "\n\n")

    @staticmethod
    def read_stream(stream, log_f):
        """读取输出流"""
        for line in stream:
            line = line.rstrip('\n')
            if line:
                # 写入日志文件
                log_f.write(f"{line}\n")
                log_f.flush()
