from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy import create_engine, text

from alembic import context
import os
from urllib.parse import quote_plus

# 导入应用配置和模型
from app.core.config import settings
from app.db.database import Base
# 导入所有模型，以便 autogenerate 能够检测到它们
from app.models import dataset_mapping  # noqa

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config


def ensure_database_and_user():
    """
    确保数据库和用户存在
    使用 root 用户连接 MySQL，创建数据库和应用用户
    """
    # 只在 MySQL 配置时执行
    if not settings.mysql_host:
        return

    mysql_root_password = os.getenv('MYSQL_ROOT_PASSWORD', 'password')

    # URL 编码密码以处理特殊字符
    encoded_password = quote_plus(mysql_root_password)

    # 使用 root 用户连接（不指定数据库）
    root_url = f"mysql+pymysql://root:{encoded_password}@{settings.mysql_host}:{settings.mysql_port}/"

    try:
        root_engine = create_engine(root_url, poolclass=pool.NullPool)
        with root_engine.connect() as conn:
            # 创建数据库（如果不存在）
            conn.execute(text(
                f"CREATE DATABASE IF NOT EXISTS `{settings.mysql_database}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            ))
            conn.commit()

            # 创建用户（如果不存在）- 使用 MySQL 8 默认的 caching_sha2_password
            conn.execute(text(
                f"CREATE USER IF NOT EXISTS '{settings.mysql_user}'@'%' "
                f"IDENTIFIED BY '{settings.mysql_password}'"
            ))
            conn.commit()

            # 授予权限
            conn.execute(text(
                f"GRANT ALL PRIVILEGES ON `{settings.mysql_database}`.* TO '{settings.mysql_user}'@'%'"
            ))
            conn.commit()

            # 刷新权限
            conn.execute(text("FLUSH PRIVILEGES"))
            conn.commit()

        root_engine.dispose()
        print(f"✓ Database '{settings.mysql_database}' and user '{settings.mysql_user}' are ready")
    except Exception as e:
        print(f"⚠️  Warning: Could not ensure database and user: {e}")
        print(f"   This may be expected if database already exists or permissions are set")


# 从应用配置设置数据库 URL
config.set_main_option('sqlalchemy.url', settings.sync_database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # 先确保数据库和用户存在
    ensure_database_and_user()

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
