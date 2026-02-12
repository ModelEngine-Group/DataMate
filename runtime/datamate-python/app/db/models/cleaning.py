from sqlalchemy import Column, String, BigInteger, Integer, TIMESTAMP
from app.db.models.base_entity import BaseEntity, Base


class CleaningTask(BaseEntity):
    """Data cleaning task entity"""
    __tablename__ = "t_clean_task"

    id = Column(String(36), primary_key=True, comment="Task ID")
    name = Column(String(255), nullable=False, comment="Task name")
    description = Column(String(1024), nullable=True, comment="Task description")
    status = Column(String(50), nullable=False, default="PENDING", comment="Task status: PENDING, RUNNING, COMPLETED, STOPPED, FAILED")
    src_dataset_id = Column(String(36), nullable=False, comment="Source dataset ID")
    src_dataset_name = Column(String(255), nullable=False, comment="Source dataset name")
    dest_dataset_id = Column(String(36), nullable=True, comment="Destination dataset ID")
    dest_dataset_name = Column(String(255), nullable=True, comment="Destination dataset name")
    before_size = Column(BigInteger, nullable=True, comment="Data size before cleaning")
    after_size = Column(BigInteger, nullable=True, comment="Data size after cleaning")
    file_count = Column(Integer, nullable=True, comment="Total file count")
    retry_count = Column(Integer, default=0, nullable=False, comment="Retry count")
    started_at = Column(TIMESTAMP, nullable=True, comment="Task start time")
    finished_at = Column(TIMESTAMP, nullable=True, comment="Task finish time")


class CleaningTemplate(BaseEntity):
    """Data cleaning template entity"""
    __tablename__ = "t_clean_template"

    id = Column(String(36), primary_key=True, comment="Template ID")
    name = Column(String(255), nullable=False, comment="Template name")
    description = Column(String(1024), nullable=True, comment="Template description")


class CleaningResult(Base):
    """Data cleaning result entity"""
    __tablename__ = "t_clean_result"

    instance_id = Column(String(36), primary_key=True, comment="Instance ID (task or template ID)")
    src_file_id = Column(String(36), primary_key=True, comment="Source file ID")
    dest_file_id = Column(String(36), nullable=True, comment="Destination file ID")
    src_name = Column(String(512), nullable=True, comment="Source file name")
    dest_name = Column(String(512), nullable=True, comment="Destination file name")
    src_type = Column(String(50), nullable=True, comment="Source file type")
    dest_type = Column(String(50), nullable=True, comment="Destination file type")
    src_size = Column(BigInteger, nullable=True, comment="Source file size")
    dest_size = Column(BigInteger, nullable=True, comment="Destination file size")
    status = Column(String(50), nullable=True, comment="Cleaning status: COMPLETED, FAILED, etc.")
    result = Column(String(1024), nullable=True, comment="Cleaning result message")


class OperatorInstance(Base):
    """Operator instance in task or template"""
    __tablename__ = "t_operator_instance"

    instance_id = Column(String(36), primary_key=True, comment="Instance ID (task or template ID)")
    operator_id = Column(String(36), primary_key=True, comment="Operator ID")
    op_index = Column(Integer, nullable=False, comment="Operator execution order")
    settings_override = Column(String(4096), nullable=True, comment="Operator settings override (JSON)")

