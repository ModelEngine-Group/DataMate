"""
Tables for Data Evaluation module

Derived from scripts/db/data-evaluation-init.sql
 - t_de_eval_task
 - t_de_eval_item
"""

import uuid
from sqlalchemy import Column, String, Text, Float, TIMESTAMP, ForeignKey, Integer
from sqlalchemy.sql import func

from app.db.session import Base


class EvaluationTask(Base):
    """评估任务表（UUID 主键） -> t_de_eval_task

    Columns per data-evaluation-init.sql:
      id, name, description, task_type, source_type, source_id, source_name,
      status, eval_process, eval_promt, eval_config, created_at, updated_at,
      created_by, updated_by
    """

    __tablename__ = "t_de_eval_task"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="UUID")
    name = Column(String(255), nullable=False, comment="评估任务名称")
    description = Column(Text, nullable=True, comment="评估任务描述")
    task_type = Column(String(50), nullable=False, comment="评估任务类型：QA")
    source_type = Column(String(36), nullable=True, comment="待评估对象类型：DATASET/SYNTHESIS")
    source_id = Column(String(36), nullable=True, comment="待评估对象ID")
    source_name = Column(String(255), nullable=True, comment="待评估对象名称")
    status = Column(String(50), server_default="PENDING", nullable=False, comment="状态：PENDING/RUNNING/COMPLETED/STOPPED/FAILED")
    eval_method = Column(String(50), server_default="AUTO", nullable=False, comment="评估方式：AUTO/MANUAL")
    eval_process = Column(Float, nullable=False, server_default="0", comment="评估进度")
    eval_prompt = Column(Text, nullable=True, comment="评估提示词")
    eval_config = Column(Text, nullable=True, comment="评估配置")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    created_by = Column(String(255), nullable=True, comment="创建者")
    updated_by = Column(String(255), nullable=True, comment="更新者")


class EvaluationFile(Base):
    """评估条目表（UUID 主键） -> t_de_eval_file"""

    __tablename__ = "t_de_eval_file"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="UUID")
    task_id = Column(String(36), ForeignKey('t_de_eval_task.id'), nullable=False, comment="评估任务ID")
    file_id = Column(String(36), ForeignKey('t_dm_dataset_files.id'), nullable=True, comment="文件ID")
    file_name = Column(String(255), nullable=False, comment="文件名")
    total_count = Column(Integer, nullable=False, default=0, comment="总数")
    evaluated_count = Column(Integer, nullable=False, default=0, comment="已评估数")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    created_by = Column(String(255), nullable=True, comment="创建者")
    updated_by = Column(String(255), nullable=True, comment="更新者")


class EvaluationItem(Base):
    """评估条目表（UUID 主键） -> t_de_eval_item

    Columns per data-evaluation-init.sql:
      id, task_id, item_id, eval_score, eval_result, status
    """

    __tablename__ = "t_de_eval_item"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="UUID")
    task_id = Column(String(36), ForeignKey('t_de_eval_task.id'), nullable=False, comment="评估任务ID")
    file_id = Column(String(36), ForeignKey('t_dm_dataset_files.id'), nullable=True, comment="文件ID")
    item_id = Column(String(36), nullable=False, comment="评估条目ID")
    eval_content = Column(Text, nullable=True, comment="评估内容")
    eval_score = Column(Float, nullable=False, server_default="0", comment="评估分数")
    eval_result = Column(Text, nullable=True, comment="评估结果")
    status = Column(String(50), server_default="PENDING", nullable=False, comment="状态：PENDING/EVALUATED")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    created_by = Column(String(255), nullable=True, comment="创建者")
    updated_by = Column(String(255), nullable=True, comment="更新者")
