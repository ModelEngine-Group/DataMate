FROM mysql:8

COPY scripts/images/database/utf8.cnf /etc/mysql/conf.d/utf8.cnf
COPY scripts/db/ /docker-entrypoint-initdb.d/

RUN chmod 644 /etc/mysql/conf.d/utf8.cnf