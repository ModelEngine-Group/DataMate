import shutil
import time
import uuid
import os

import click
import uvicorn
from pydantic import BaseModel
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from loguru import logger
from mineru.cli.common import aio_do_parse, read_fn
from mineru.cli.fast_api import get_infer_result

# 日志配置
LOG_DIR = "/var/log/datamate/mineru"
os.makedirs(LOG_DIR, exist_ok=True)
logger.add(
    f"{LOG_DIR}/mineru.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    enqueue=True
)

app = FastAPI()
class PDFParseRequest(BaseModel):
    source_path: str
    export_path: str

@app.post(path="/api/pdf-extract")
async def parse_pdf(request: PDFParseRequest):
    try:
        start = time.time()
        # 创建唯一的输出目录
        unique_id = str(uuid.uuid4())
        unique_dir = os.path.join(request.export_path, unique_id)
        os.makedirs(unique_dir, exist_ok=True)

        # 如果是PDF，使用read_fn处理
        file_path = Path(request.source_path)
        file_suffix = file_path.suffix.lower()
        if file_suffix == ".pdf":
            try:
                pdf_bytes = read_fn(file_path)
                pdf_name = file_path.stem
                pdf_bytes_list = [pdf_bytes]
                pdf_file_names = [pdf_name]
            except Exception as e:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Failed to load file: {str(e)}"}
                )
        else:
            return JSONResponse(
                status_code=400,
                content={"error": f"Unsupported file type: {file_suffix}"}
            )

        # 调用异步处理函数
        await aio_do_parse(
            output_dir=unique_dir,
            pdf_file_names=pdf_file_names,
            pdf_bytes_list=pdf_bytes_list,
            p_lang_list=["ch"],
            f_draw_layout_bbox=False,
            f_draw_span_bbox=False,
            f_dump_orig_pdf=False,
        )

        if os.getenv("MINERU_BACKEND_MODE").startswith("pipeline"):
            parse_dir = os.path.join(unique_dir, pdf_name, "auto")
        else:
            parse_dir = os.path.join(unique_dir, pdf_name, "vlm")

        content = ""
        if os.path.exists(parse_dir):
            content = get_infer_result(".md", pdf_name, parse_dir)

        if os.path.exists(unique_dir):
            try:
                shutil.rmtree(unique_dir)
            except Exception as e:
                logger.error(f"Failed to remove unique dir for {unique_id}: {str(e)}")

        logger.info(f"fileName: {file_path.name} costs {time.time() - start:.6f} s")

        return JSONResponse(status_code=200, content={"result": content})
    except Exception as e:
        logger.exception(e)
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to process file: {str(e)}"}
        )


@click.command()
@click.option('--ip', default='0.0.0.0', help='Service ip for this API, default to use 0.0.0.0.')
@click.option('--port', default=9001, type=int, help='Service port for this API, default to use 8082.')
def main(ip, port):
    """Create API for Submitting Job to MinerU"""
    logger.info(f"Start MinerU FastAPI Service: http://{ip}:{port}")
    uvicorn.run(
        app,
        host=ip,
        port=port
    )


if __name__ == "__main__":
    main()

