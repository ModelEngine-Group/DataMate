import asyncio
import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from unstructured.partition.auto import partition

app = FastAPI(title="unstructured")


class FileProcessingRequest(BaseModel):
    """文件处理请求模型"""
    file_path: Optional[str] = None
    # 可添加其他可选字段


@app.post("/process", tags=["文件处理"])
async def process_file(request_data: FileProcessingRequest):
    """处理文件并返回提取的文本内容"""
    try:
        file_path = request_data.file_path

        if not file_path:
            raise HTTPException(status_code=400, detail="缺少必要参数: filePath")

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")

        # 异步执行可能耗时的文件处理操作
        text_content = await process_file_async(file_path)

        # 返回处理结果
        return {
            "filePath": file_path,
            "text": text_content,
            "status": "success"
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"process failed: {str(e)}")


async def process_file_async(file_path: str) -> str:
    """异步处理文件内容"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partition_file_sync, file_path)


def partition_file_sync(file_path: str) -> str:
    """同步处理文件内容（由异步函数调用）"""
    elements = partition(filename=file_path)
    return "\n\n".join([str(el) for el in elements])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
