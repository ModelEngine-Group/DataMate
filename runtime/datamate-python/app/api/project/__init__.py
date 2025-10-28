"""
标注工程相关API路由模块
"""
from fastapi import APIRouter

project_router = APIRouter()

from . import create
from . import sync
from . import list
from . import delete