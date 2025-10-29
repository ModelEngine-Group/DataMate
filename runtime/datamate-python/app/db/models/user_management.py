"""
Tables of User Management Module
"""

from sqlalchemy import Column, String, BigInteger, Boolean, TIMESTAMP
from sqlalchemy.sql import func

from app.db.session import Base

class User(Base):
    """用户模型"""
    
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="用户ID")
    username = Column(String(255), nullable=False, unique=True, comment="用户名")
    email = Column(String(255), nullable=False, unique=True, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    full_name = Column(String(255), nullable=True, comment="真实姓名")
    avatar_url = Column(String(500), nullable=True, comment="头像URL")
    role = Column(String(50), nullable=False, default='USER', comment="角色：ADMIN/USER")
    organization = Column(String(255), nullable=True, comment="所属机构")
    enabled = Column(Boolean, nullable=False, default=True, comment="是否启用")
    last_login_at = Column(TIMESTAMP, nullable=True, comment="最后登录时间")
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), comment="更新时间")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
