"""
Chunks Saver
分片保存器，用于处理文件分片上传
"""
import os
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

from fastapi import UploadFile

from app.core.logging import get_logger
from app.module.shared.file_models import ChunkUploadRequestDto

logger = get_logger(__name__)


class ChunksSaver:
    """分片保存器"""

    TEMP_DIR_NAME_FORMAT = "req_%s_chunks"

    @staticmethod
    def save(
        file_upload_request: ChunkUploadRequestDto,
        pre_upload_req_id: str,
        upload_path: str,
        file_content: bytes
    ) -> Optional[Path]:
        """
        保存分片

        Args:
            file_upload_request: 上传分片的请求
            pre_upload_req_id: 预上传请求ID
            upload_path: 上传基础路径
            file_content: 文件内容（字节）

        Returns:
            保存后的文件路径，如果不是最后一个分片则返回None
        """
        start_time = datetime.now(timezone.utc)

        temp_dir = Path(upload_path) / (
            ChunksSaver.TEMP_DIR_NAME_FORMAT % pre_upload_req_id
        )
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_file = temp_dir / str(file_upload_request.file_no)

        ChunksSaver._append_to_target_file(temp_file, file_content)

        if file_upload_request.total_chunk_num != file_upload_request.chunk_no:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            logger.debug(f"save chunk {file_upload_request.chunk_no} cost {elapsed}s")
            return None

        final_file = Path(upload_path) / file_upload_request.file_name

        try:
            temp_file.rename(final_file)
        except OSError as e:
            logger.error(
                f"failed to mv file: {temp_file.name}, req id: {pre_upload_req_id}, error: {e}"
            )
            raise ValueError("failed to move file to target dir") from e

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
        logger.debug(f"save chunk {file_upload_request.chunk_no} cost {elapsed}s")

        return final_file

    @staticmethod
    def save_file(
        file_upload_request: ChunkUploadRequestDto,
        upload_path: str,
        file_content: bytes
    ) -> Path:
        """
        保存文件（不分片）

        Args:
            file_upload_request: 上传请求
            upload_path: 上传路径
            file_content: 文件内容（字节）

        Returns:
            保存后的文件路径
        """
        target_file = Path(upload_path) / file_upload_request.file_name

        logger.info(f"file path {target_file}, file size {len(file_content)}")

        try:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_bytes(file_content)
        except OSError as e:
            logger.error(f"failed to save file: {target_file}, error: {e}")
            raise ValueError("failed to save file") from e

        return target_file

    @staticmethod
    def delete_folder(folder_path: str) -> None:
        """
        删除指定路径下的所有文件

        Args:
            folder_path: 文件夹路径
        """
        folder = Path(folder_path)

        if not folder.exists():
            logger.info(f"folder {folder_path} does not exist")
            return

        try:
            for item in folder.glob("*"):
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    for sub_item in item.glob("*"):
                        if sub_item.is_file():
                            sub_item.unlink()
                        elif sub_item.is_dir():
                            ChunksSaver.delete_folder(str(sub_item))
                    item.rmdir()
        except OSError as e:
            logger.error(f"failed to delete folder: {folder_path}, error: {e}")
            raise ValueError("failed to delete folder") from e

    @staticmethod
    def _append_to_target_file(target_file: Path, content: bytes) -> None:
        """
        追加内容到目标文件末尾

        Args:
            target_file: 目标文件
            content: 要追加的内容
        """
        try:
            with open(target_file, "ab") as f:
                f.write(content)
        except OSError as e:
            logger.error(f"failed to append to file: {target_file}, error: {e}")
            raise ValueError("failed to append content to file") from e
