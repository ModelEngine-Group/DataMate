from typing import Optional
from fastapi import HTTPException

from .dm_client import DMServiceClient
from .label_studio_client import LabelStudioClient

# 全局客户端实例（将在main.py中初始化）
dm_client: Optional[DMServiceClient] = None
ls_client: Optional[LabelStudioClient] = None

def get_clients() -> tuple[DMServiceClient, LabelStudioClient]:
    """获取客户端实例"""
    global dm_client, ls_client
    if not dm_client or not ls_client:
        raise HTTPException(status_code=500, detail="客户端未初始化")
    return dm_client, ls_client

def set_clients(dm_client_instance: DMServiceClient, ls_client_instance: LabelStudioClient) -> None:
    """设置全局客户端实例"""
    global dm_client, ls_client
    dm_client = dm_client_instance
    ls_client = ls_client_instance

def get_dm_client() -> DMServiceClient:
    """获取DM服务客户端"""
    if not dm_client:
        raise HTTPException(status_code=500, detail="DM客户端未初始化")
    return dm_client

def get_ls_client() -> LabelStudioClient:
    """获取Label Studio客户端"""
    if not ls_client:
        raise HTTPException(status_code=500, detail="Label Studio客户端未初始化")
    return ls_client