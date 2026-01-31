"""
File Models
文件相关模型定义
"""
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ChunkUploadPreRequestDto(BaseModel):
    """分片上传预请求DTO"""
    id: str = Field(..., description="请求ID")
    total_file_num: int = Field(..., description="总文件数", ge=1)
    uploaded_file_num: Optional[int] = Field(None, description="已上传文件数", ge=0)
    upload_path: str = Field(..., description="文件路径")
    timeout: Optional[datetime] = Field(None, description="上传请求超时时间")
    service_id: Optional[str] = Field(None, description="上传请求所属服务ID")
    check_info: Optional[str] = Field(None, description="业务信息")


class ChunkUploadRequestDto(BaseModel):
    """分片上传请求DTO"""
    req_id: str = Field(..., description="预上传返回的ID")
    file_no: int = Field(1, description="文件编号", ge=1)
    file_name: str = Field(..., description="文件名称")
    total_chunk_num: int = Field(1, description="总分块数量", ge=1)
    chunk_no: int = Field(1, description="当前分块编号", ge=1)
    file_size: Optional[int] = Field(None, description="文件大小", ge=0)
    check_sum_hex: Optional[str] = Field(None, description="文件校验和（十六进制字符串）")


class FileUploadResult(BaseModel):
    """文件上传结果"""
    is_all_files_uploaded: bool = Field(..., description="是否所有文件已上传")
    check_info: Optional[str] = Field(None, description="业务上传信息")
    saved_file_path: Optional[str] = Field(None, description="保存的文件路径")
    file_name: str = Field(..., description="文件名称")
