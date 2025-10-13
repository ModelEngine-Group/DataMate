import os
from typing import Optional, Dict, Any, List

import uvicorn
import yaml
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from jsonargparse import ArgumentParser
from loguru import logger
from pydantic import BaseModel

from data_platform.common.error_code import ErrorCode
from data_platform.scheduler import cmd_scheduler
from data_platform.scheduler import func_scheduler
from data_platform.wrappers import WRAPPERS

# 日志配置
LOG_DIR = "/var/log/data-platform/runtime"
os.makedirs(LOG_DIR, exist_ok=True)
logger.add(
    f"{LOG_DIR}/runtime.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    enqueue=True
)

app = FastAPI()


class APIException(Exception):
    """自定义API异常"""

    def __init__(self, error_code: ErrorCode, detail: Optional[str] = None,
                 extra_data: Optional[Dict] = None):
        self.error_code = error_code
        self.detail = detail or error_code.value[1]
        self.code = error_code.value[0]
        self.extra_data = extra_data
        super().__init__(self.detail)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "code": self.code,
            "message": self.detail,
            "success": False
        }
        if self.extra_data:
            result["data"] = self.extra_data
        return result


@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=200,  # 业务错误返回 200，错误信息在响应体中
        content=exc.to_dict()
    )


class QueryTaskRequest(BaseModel):
    task_ids: List[str]


@app.post("/api/task/list")
async def query_task_info(request: QueryTaskRequest):
    try:
        return [{task_id: cmd_scheduler.get_task_status(task_id)} for task_id in request.task_ids]
    except Exception as e:
        raise APIException(ErrorCode.UNKNOWN_ERROR)


@app.post("/api/task/{task_id}/submit")
async def submit_task(task_id):
    config_path = f"/flow/{task_id}/process.yaml"
    logger.info("Start submitting job...")

    dataset_path = get_from_cfg(task_id, "dataset_path")
    if not check_valid_path(dataset_path):
        logger.error(f"dataset_path is not existed! please check this path.")
        raise APIException(ErrorCode.FILE_NOT_FOUND_ERROR)

    try:
        executor_type = get_from_cfg(task_id, "executor_type")
        await WRAPPERS.get(executor_type).submit(task_id, config_path)

    except Exception as e:
        logger.error(f"Error happens during submitting task. Error Info following: {e}")
        raise APIException(ErrorCode.SUBMIT_TASK_ERROR)

    logger.info(f"task id: {task_id} has been submitted.")
    success_json_info = JSONResponse(
        content={"status": "Success", "message": f"{task_id} has been submitted"},
        status_code=200
    )
    return success_json_info


@app.post("/api/task/{task_id}/stop")
async def stop_task(task_id):
    logger.info("Start stopping ray job...")
    success_json_info = JSONResponse(
        content={"status": "Success", "message": f"{task_id} has been stopped"},
        status_code=200
    )

    try:
        executor_type = get_from_cfg(task_id, "executor_type")
        if not WRAPPERS.get(executor_type).cancel(task_id):
            raise APIException(ErrorCode.CANCEL_TASK_ERROR)
    except Exception as e:
        if isinstance(e, APIException):
            raise e
        raise APIException(ErrorCode.UNKNOWN_ERROR)

    logger.info(f"{task_id} has been stopped.")
    return success_json_info


def check_valid_path(file_path):
    full_path = os.path.abspath(file_path)
    return os.path.exists(full_path)


def get_from_cfg(task_id, key):
    config_path = f"/flow/{task_id}/process.yaml"
    if not check_valid_path(config_path):
        logger.error(f"config_path is not existed! please check this path.")
        raise APIException(ErrorCode.FILE_NOT_FOUND_ERROR)

    with open(config_path, "r", encoding='utf-8') as f:
        content = f.read()
        cfg = yaml.safe_load(content)
    return cfg[key]


def parse_args():
    parser = ArgumentParser(description="Create API for Submitting Job to Data-juicer")

    parser.add_argument(
        '--ip',
        type=str,
        default="0.0.0.0",
        help='Service ip for this API, default to use 0.0.0.0.'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=8080,
        help='Service port for this API, default to use 8600.'
    )

    return parser.parse_args()


if __name__ == '__main__':
    p_args = parse_args()

    uvicorn.run(
        app,
        host=p_args.ip,
        port=p_args.port
    )
