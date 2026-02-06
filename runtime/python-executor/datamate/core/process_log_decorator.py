# -*- coding: utf-8 -*-

import uuid
import traceback
from datetime import datetime
from functools import wraps
from typing import Dict, Any, Callable

from loguru import logger
from sqlalchemy import Table, Column, String, Integer, Text, TIMESTAMP, select, update, insert, func, MetaData

from datamate.sql_manager.sql_manager import SQLManager

# 定义表结构（使用独立的 metadata，因为我们使用原始连接）
_metadata = MetaData()
_process_log_table = Table(
    't_data_process_log',
    _metadata,
    Column('id', String(64), primary_key=True),
    Column('instance_id', String(256)),
    Column('operator_id', String(256)),
    Column('start_time', TIMESTAMP),
    Column('end_time', TIMESTAMP),
    Column('succeed_file_count', Integer, default=0),
    Column('failed_file_count', Integer, default=0),
    Column('error_message', Text, default=''),
    Column('created_at', TIMESTAMP, server_default=func.current_timestamp()),
    Column('updated_at', TIMESTAMP, server_default=func.current_timestamp()),
)


def update_process_log(func: Callable) -> Callable:
    """
    装饰器：在调用 Mapper 或 Filter 的 __call__ 方法前后更新 t_data_process_log 表
    
    在调用前：
    - 通过 instance_id 和 operator_id 查询记录是否存在
    - 如果不存在，创建新记录（使用 UUID 作为 id），设置 start_time
    - 如果存在，不更新 start_time（保持第一次创建的时间）
    
    在调用后：
    - 成功：更新 end_time，succeed_file_count++
    - 失败：更新 end_time，failed_file_count++，追加 error_message
    """
    @wraps(func)
    def wrapper(self, sample: Dict[str, Any], **kwargs):
        # 获取 instance_id 和 operator_id
        instance_id = str(sample.get("instance_id", ""))
        operator_id = getattr(self, 'name', 'UnknownOp')
        
        if not instance_id:
            logger.warning(f"instance_id is missing in sample, skipping process log update")
            return func(self, sample, **kwargs)
        
        start_time = datetime.now()
        log_id = None
        
        try:
            # 调用前：检查记录是否存在，如果不存在则创建（只设置 start_time）
            log_id = _ensure_log_record_exists(instance_id, operator_id, start_time)
            
            # 执行原始方法
            result = func(self, sample, **kwargs)
            
            # 调用后：更新成功记录
            end_time = datetime.now()
            if log_id:
                _update_log_record_success(log_id, end_time)
            
            return result
            
        except Exception as e:
            # 如果执行失败，更新失败记录
            end_time = datetime.now()
            error_message = _get_error_message(e)
            
            try:
                # 获取 log_id（如果之前没有创建，这里需要查询或创建）
                if log_id is None:
                    log_id = _get_or_create_log_id(instance_id, operator_id, start_time)
                if log_id:
                    _update_log_record_failure(log_id, end_time, error_message)
            except Exception as update_error:
                logger.error(f"Failed to update process log after error: {update_error}")
            
            # 重新抛出原始异常
            raise e
    
    return wrapper


def _ensure_log_record_exists(instance_id: str, operator_id: str, start_time: datetime) -> str:
    """确保日志记录存在，如果不存在则创建。使用事务和锁确保并发安全。返回记录的 id（UUID）"""
    try:
        with SQLManager.create_connect() as conn:
            with conn.begin():  # 自动管理事务
                # 使用 SELECT FOR UPDATE 锁定记录
                stmt = select(_process_log_table.c.id).where(
                    _process_log_table.c.instance_id == instance_id,
                    _process_log_table.c.operator_id == operator_id
                ).with_for_update()
                
                result = conn.execute(stmt)
                existing = result.fetchone()
                
                if existing is None:
                    # 记录不存在，创建新记录
                    log_id = str(uuid.uuid4())
                    conn.execute(
                        insert(_process_log_table).values(
                            id=log_id,
                            instance_id=instance_id,
                            operator_id=operator_id,
                            start_time=start_time,
                            succeed_file_count=0,
                            failed_file_count=0,
                            error_message=''
                        )
                    )
                    logger.debug(f"Created new process log record: id={log_id}, instance_id={instance_id}, operator_id={operator_id}")
                    return log_id
                else:
                    log_id = existing[0]
                    logger.debug(f"Process log record already exists: id={log_id}, instance_id={instance_id}, operator_id={operator_id}")
                    return log_id
    except Exception as e:
        logger.error(f"Failed to ensure process log record exists: {e}")
        return str(uuid.uuid4())


def _get_or_create_log_id(instance_id: str, operator_id: str, start_time: datetime) -> str:
    """获取或创建日志记录的 id，用于异常处理时确保有 log_id"""
    return _ensure_log_record_exists(instance_id, operator_id, start_time)


def _update_log_record_success(log_id: str, end_time: datetime):
    """更新日志记录：成功时更新 end_time 和递增 succeed_file_count，使用事务和锁确保并发安全"""
    try:
        with SQLManager.create_connect() as conn:
            with conn.begin():  # 自动管理事务
                # 锁定记录
                conn.execute(
                    select(_process_log_table.c.id)
                    .where(_process_log_table.c.id == log_id)
                    .with_for_update()
                )
                
                # 原子更新
                conn.execute(
                    update(_process_log_table)
                    .where(_process_log_table.c.id == log_id)
                    .values(
                        end_time=end_time,
                        succeed_file_count=_process_log_table.c.succeed_file_count + 1,
                        updated_at=func.current_timestamp()
                    )
                )
                logger.debug(f"Updated process log record (success): id={log_id}")
    except Exception as e:
        logger.error(f"Failed to update process log record (success): {e}")


def _update_log_record_failure(log_id: str, end_time: datetime, error_message: str):
    """更新日志记录：失败时更新 end_time、递增 failed_file_count 和追加 error_message，使用事务和锁确保并发安全"""
    try:
        with SQLManager.create_connect() as conn:
            with conn.begin():  # 自动管理事务
                # 锁定记录并获取当前错误信息
                result = conn.execute(
                    select(_process_log_table.c.error_message)
                    .where(_process_log_table.c.id == log_id)
                    .with_for_update()
                )
                current_error = result.scalar() or ''
                
                # 构建新的错误信息
                new_error = error_message if not current_error else f"{current_error}\n{error_message}"
                
                # 原子更新
                conn.execute(
                    update(_process_log_table)
                    .where(_process_log_table.c.id == log_id)
                    .values(
                        end_time=end_time,
                        failed_file_count=_process_log_table.c.failed_file_count + 1,
                        error_message=new_error,
                        updated_at=func.current_timestamp()
                    )
                )
                logger.debug(f"Updated process log record (failure): id={log_id}")
    except Exception as e:
        logger.error(f"Failed to update process log record (failure): {e}")


def _get_error_message(exception: Exception) -> str:
    """
    获取异常的错误信息，包括异常类型、消息和堆栈跟踪
    """
    try:
        exc_type = type(exception).__name__
        exc_msg = str(exception)
        exc_traceback = traceback.format_exc()
        
        error_message = f"[{exc_type}] {exc_msg}\n{exc_traceback}"
        # 限制错误信息长度，避免数据库字段过大
        max_length = 10000  # TEXT 类型通常可以存储更多，但为了安全设置限制
        if len(error_message) > max_length:
            error_message = error_message[:max_length] + "\n...(truncated)"
        
        return error_message
    except Exception as e:
        logger.error(f"Failed to get error message: {e}")
        return f"Error occurred but failed to extract message: {str(exception)}"
