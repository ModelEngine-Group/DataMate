FROM postgres:15-trixie

# 创建日志目录并设置权限
USER root
RUN mkdir -p /var/log/datamate/database && \
    chown -R postgres:postgres /var/log/datamate && \
    chmod -R 755 /var/log/datamate

ENV POSTGRES_INITDB_ARGS="--encoding=UTF8 --lc-collate=en_US.UTF-8 --lc-ctype=en_US.UTF-8"
# 创建配置目录
RUN mkdir -p /etc/postgresql/
# 复制 PostgreSQL 主配置文件
COPY scripts/images/database/postgresql.cnf /etc/postgresql/postgresql.conf

COPY scripts/db/ /docker-entrypoint-initdb.d/

CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]
