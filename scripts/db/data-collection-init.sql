-- 数据归集服务数据库初始化脚本
-- 适用于knowledge_base数据库

USE knowledge_base;

-- =====================================
-- DDL语句 - 数据库表结构定义
-- =====================================

-- 删除现有表（支持重复执行 调测阶段使用）
DROP TABLE IF EXISTS t_dc_statistics;
DROP TABLE IF EXISTS t_dc_execution_logs;
DROP TABLE IF EXISTS t_dc_task_executions;
DROP TABLE IF EXISTS t_dc_task_schedules;
DROP TABLE IF EXISTS t_dc_collection_tasks;
DROP TABLE IF EXISTS t_dc_datax_templates;
DROP TABLE IF EXISTS t_dc_data_sources;

-- 数据源配置表
CREATE TABLE t_dc_data_sources (
    id VARCHAR(36) PRIMARY KEY COMMENT '数据源ID（UUID）',
    name VARCHAR(255) NOT NULL UNIQUE COMMENT '数据源名称',
    type VARCHAR(50) NOT NULL COMMENT '数据源类型 MYSQL/POSTGRESQL/ORACLE',
    description TEXT COMMENT '数据源描述',
    config JSON NOT NULL COMMENT '数据源连接配置信息',
    status VARCHAR(20) DEFAULT 'ACTIVE' COMMENT '状态：ACTIVE/INACTIVE',
    last_test_at TIMESTAMP NULL COMMENT '最后测试时间',
    last_test_result JSON COMMENT '最后测试结果',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(255) COMMENT '创建者',
    updated_by VARCHAR(255) COMMENT '更新者',
    INDEX idx_type (type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) COMMENT='数据归集数据源配置表';

-- 数据归集任务表
CREATE TABLE t_dc_collection_tasks (
    id VARCHAR(36) PRIMARY KEY COMMENT '任务ID（UUID）',
    name VARCHAR(255) NOT NULL COMMENT '任务名称',
    description TEXT COMMENT '任务描述',
    source_datasource_id VARCHAR(36) NOT NULL COMMENT '源数据源ID',
    target_datasource_id VARCHAR(36) NOT NULL COMMENT '目标数据源ID',
    config JSON NOT NULL COMMENT '归集配置（DataX配置）',
    schedule_expression VARCHAR(255) COMMENT 'Cron调度表达式',
    status VARCHAR(20) DEFAULT 'DRAFT' COMMENT '任务状态：DRAFT/READY/RUNNING/COMPLETED/FAILED/STOPPED',
    retry_count INT DEFAULT 3 COMMENT '重试次数',
    timeout_seconds INT DEFAULT 3600 COMMENT '超时时间（秒）',
    max_records BIGINT COMMENT '最大处理记录数',
    sort_field VARCHAR(100) COMMENT '增量字段',
    last_execution_id VARCHAR(36) COMMENT '最后执行ID（UUID）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(255) COMMENT '创建者',
    updated_by VARCHAR(255) COMMENT '更新者',
    FOREIGN KEY (source_datasource_id) REFERENCES t_dc_data_sources(id),
    FOREIGN KEY (target_datasource_id) REFERENCES t_dc_data_sources(id),
    INDEX idx_source_datasource (source_datasource_id),
    INDEX idx_target_datasource (target_datasource_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_schedule (schedule_expression)
) COMMENT='数据归集任务表';

-- 任务执行记录表
CREATE TABLE t_dc_task_executions (
    id VARCHAR(36) PRIMARY KEY COMMENT '执行记录ID（UUID）',
    task_id VARCHAR(36) NOT NULL COMMENT '任务ID',
    task_name VARCHAR(255) NOT NULL COMMENT '任务名称',
    status VARCHAR(20) DEFAULT 'RUNNING' COMMENT '执行状态：RUNNING/SUCCESS/FAILED/STOPPED',
    progress DECIMAL(5,2) DEFAULT 0.00 COMMENT '执行进度（百分比）',
    records_total BIGINT DEFAULT 0 COMMENT '总记录数',
    records_processed BIGINT DEFAULT 0 COMMENT '已处理记录数',
    records_success BIGINT DEFAULT 0 COMMENT '成功记录数',
    records_failed BIGINT DEFAULT 0 COMMENT '失败记录数',
    throughput DECIMAL(10,2) DEFAULT 0.00 COMMENT '处理速度（记录/秒）',
    data_size_bytes BIGINT DEFAULT 0 COMMENT '数据大小（字节）',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
    completed_at TIMESTAMP NULL COMMENT '完成时间',
    duration_seconds INT COMMENT '执行时长（秒）',
    error_message TEXT COMMENT '错误信息',
    datax_job_id VARCHAR(64) COMMENT 'DataX作业ID',
    config JSON COMMENT '执行配置',
    result JSON COMMENT '执行结果详情',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (task_id) REFERENCES t_dc_collection_tasks(id) ON DELETE CASCADE,
    INDEX idx_task_id (task_id),
    INDEX idx_status (status),
    INDEX idx_started_at (started_at),
    INDEX idx_completed_at (completed_at)
) COMMENT='任务执行记录表';

-- 执行日志表
CREATE TABLE t_dc_execution_logs (
    id VARCHAR(36) PRIMARY KEY COMMENT '日志ID（UUID）',
    execution_id VARCHAR(36) NOT NULL COMMENT '执行ID',
    log_level VARCHAR(10) NOT NULL COMMENT '日志级别：DEBUG/INFO/WARN/ERROR',
    message TEXT NOT NULL COMMENT '日志消息',
    thread VARCHAR(100) COMMENT '线程名',
    logger VARCHAR(255) COMMENT 'Logger名称',
    exception_stack TEXT COMMENT '异常堆栈',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '日志时间',
    FOREIGN KEY (execution_id) REFERENCES t_dc_task_executions(id) ON DELETE CASCADE,
    INDEX idx_execution_id (execution_id),
    INDEX idx_log_level (log_level),
    INDEX idx_timestamp (timestamp)
) COMMENT='任务执行日志表';

-- 定时任务调度表
CREATE TABLE t_dc_task_schedules (
    id VARCHAR(36) PRIMARY KEY COMMENT '调度ID（UUID）',
    task_id VARCHAR(36) NOT NULL COMMENT '任务ID',
    cron_expression VARCHAR(255) NOT NULL COMMENT 'Cron表达式',
    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai' COMMENT '时区',
    enabled BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    next_execution_time TIMESTAMP COMMENT '下次执行时间',
    last_execution_time TIMESTAMP COMMENT '上次执行时间',
    execution_count BIGINT DEFAULT 0 COMMENT '执行次数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (task_id) REFERENCES t_dc_collection_tasks(id) ON DELETE CASCADE,
    UNIQUE KEY uk_task_schedule (task_id),
    INDEX idx_enabled (enabled),
    INDEX idx_next_execution (next_execution_time)
) COMMENT='定时任务调度表';

-- DataX模板配置表
CREATE TABLE t_dc_datax_templates (
    id VARCHAR(36) PRIMARY KEY COMMENT '模板ID（UUID）',
    name VARCHAR(255) NOT NULL UNIQUE COMMENT '模板名称',
    source_type VARCHAR(50) NOT NULL COMMENT '源数据源类型',
    target_type VARCHAR(50) NOT NULL COMMENT '目标数据源类型',
    template_content JSON NOT NULL COMMENT '模板内容',
    description TEXT COMMENT '模板描述',
    version VARCHAR(20) DEFAULT '1.0.0' COMMENT '版本号',
    is_system BOOLEAN DEFAULT FALSE COMMENT '是否系统模板',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(255) COMMENT '创建者',
    INDEX idx_source_target (source_type, target_type),
    INDEX idx_system (is_system)
) COMMENT='DataX模板配置表';

-- =====================================
-- DML语句 - 数据操作
-- =====================================

-- 统计信息表
CREATE TABLE t_dc_statistics (
    id VARCHAR(36) PRIMARY KEY COMMENT '统计ID（UUID）',
    stat_date DATE NOT NULL COMMENT '统计日期',
    period_type VARCHAR(20) NOT NULL COMMENT '统计周期：HOUR/DAY/WEEK/MONTH',
    total_tasks INT DEFAULT 0 COMMENT '总任务数',
    active_tasks INT DEFAULT 0 COMMENT '活跃任务数',
    total_executions INT DEFAULT 0 COMMENT '总执行次数',
    successful_executions INT DEFAULT 0 COMMENT '成功执行次数',
    failed_executions INT DEFAULT 0 COMMENT '失败执行次数',
    total_records_processed BIGINT DEFAULT 0 COMMENT '总处理记录数',
    avg_execution_time DECIMAL(10,2) DEFAULT 0.00 COMMENT '平均执行时间（秒）',
    avg_throughput DECIMAL(10,2) DEFAULT 0.00 COMMENT '平均吞吐量（记录/秒）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_stat_date_period (stat_date, period_type),
    INDEX idx_stat_date (stat_date),
    INDEX idx_period_type (period_type)
) COMMENT='数据归集统计信息表';

-- 插入默认的DataX模板

INSERT INTO t_dc_datax_templates (id, name, source_type, target_type, template_content, description, is_system, created_by) VALUES
-- MySQL to MySQL 模板
('e4272e51-d431-4681-a370-1b3d0b036cd0', 'MySQL到MySQL', 'MYSQL', 'MYSQL', JSON_OBJECT(
    'job', JSON_OBJECT(
        'setting', JSON_OBJECT(
            'speed', JSON_OBJECT('channel', 3)
        ),
        'content', JSON_ARRAY(
            JSON_OBJECT(
                'reader', JSON_OBJECT(
                    'name', 'mysqlreader',
                    'parameter', JSON_OBJECT(
                        'username', '${source.username}',
                        'password', '${source.password}',
                        'column', JSON_ARRAY('*'),
                        'splitPk', '${source.splitPk:id}',
                        'connection', JSON_ARRAY(
                            JSON_OBJECT(
                                'jdbcUrl', JSON_ARRAY('${source.jdbcUrl}'),
                                'table', JSON_ARRAY('${source.table}')
                            )
                        )
                    )
                ),
                'writer', JSON_OBJECT(
                    'name', 'mysqlwriter',
                    'parameter', JSON_OBJECT(
                        'writeMode', 'insert',
                        'username', '${target.username}',
                        'password', '${target.password}',
                        'column', JSON_ARRAY('*'),
                        'session', JSON_ARRAY('set session sql_mode="PIPES_AS_CONCAT"'),
                        'preSql', JSON_ARRAY('${target.preSql:}'),
                        'connection', JSON_ARRAY(
                            JSON_OBJECT(
                                'jdbcUrl', '${target.jdbcUrl}',
                                'table', JSON_ARRAY('${target.table}')
                            )
                        )
                    )
                )
            )
        )
    )
), 'MySQL到MySQL数据同步模板', TRUE, 'system'),

-- Oracle to MySQL 模板
('8018d3e1-2345-48fe-8732-4fd74ae0aa68', 'Oracle到MySQL', 'ORACLE', 'MYSQL', JSON_OBJECT(
    'job', JSON_OBJECT(
        'setting', JSON_OBJECT(
            'speed', JSON_OBJECT('channel', 3)
        ),
        'content', JSON_ARRAY(
            JSON_OBJECT(
                'reader', JSON_OBJECT(
                    'name', 'oraclereader',
                    'parameter', JSON_OBJECT(
                        'username', '${source.username}',
                        'password', '${source.password}',
                        'column', JSON_ARRAY('*'),
                        'splitPk', '${source.splitPk:ID}',
                        'connection', JSON_ARRAY(
                            JSON_OBJECT(
                                'jdbcUrl', JSON_ARRAY('${source.jdbcUrl}'),
                                'table', JSON_ARRAY('${source.table}')
                            )
                        )
                    )
                ),
                'writer', JSON_OBJECT(
                    'name', 'mysqlwriter',
                    'parameter', JSON_OBJECT(
                        'writeMode', 'insert',
                        'username', '${target.username}',
                        'password', '${target.password}',
                        'column', JSON_ARRAY('*'),
                        'connection', JSON_ARRAY(
                            JSON_OBJECT(
                                'jdbcUrl', '${target.jdbcUrl}',
                                'table', JSON_ARRAY('${target.table}')
                            )
                        )
                    )
                )
            )
        )
    )
), 'Oracle到MySQL数据同步模板', TRUE, 'system'),

-- PostgreSQL to MySQL 模板
('cc930618-f8c7-4f19-abc1-bb1ce880d749', 'PostgreSQL到MySQL', 'POSTGRESQL', 'MYSQL', JSON_OBJECT(
    'job', JSON_OBJECT(
        'setting', JSON_OBJECT(
            'speed', JSON_OBJECT('channel', 3)
        ),
        'content', JSON_ARRAY(
            JSON_OBJECT(
                'reader', JSON_OBJECT(
                    'name', 'postgresqlreader',
                    'parameter', JSON_OBJECT(
                        'username', '${source.username}',
                        'password', '${source.password}',
                        'column', JSON_ARRAY('*'),
                        'splitPk', '${source.splitPk:id}',
                        'connection', JSON_ARRAY(
                            JSON_OBJECT(
                                'jdbcUrl', JSON_ARRAY('${source.jdbcUrl}'),
                                'table', JSON_ARRAY('${source.table}')
                            )
                        )
                    )
                ),
                'writer', JSON_OBJECT(
                    'name', 'mysqlwriter',
                    'parameter', JSON_OBJECT(
                        'writeMode', 'insert',
                        'username', '${target.username}',
                        'password', '${target.password}',
                        'column', JSON_ARRAY('*'),
                        'connection', JSON_ARRAY(
                            JSON_OBJECT(
                                'jdbcUrl', '${target.jdbcUrl}',
                                'table', JSON_ARRAY('${target.table}')
                            )
                        )
                    )
                )
            )
        )
    )
), 'PostgreSQL到MySQL数据同步模板', TRUE, 'system');

-- 插入数据源模拟数据
INSERT INTO t_dc_data_sources (id, name, type, description, config, status, created_by) VALUES
-- 生产MySQL数据源
('bb3d52c8-1bca-4a33-b430-d597ceb4f38d', '生产MySQL数据库', 'MYSQL', '生产环境主要业务数据库', JSON_OBJECT(
    'host', '10.0.1.100',
    'port', 3306,
    'database', 'business_db',
    'username', 'datax_user',
    'password', '${encrypted:prod_password}',
    'encoding', 'utf8mb4',
    'timezone', 'Asia/Shanghai'
), 'ACTIVE', 'admin'),

-- 测试MySQL数据源
('451d1a23-2663-45ab-8cbc-e4e14d7de77c', '测试MySQL数据库', 'MYSQL', '测试环境数据库', JSON_OBJECT(
    'host', '10.0.2.100',
    'port', 3306,
    'database', 'test_db',
    'username', 'test_user',
    'password', '${encrypted:test_password}',
    'encoding', 'utf8mb4',
    'timezone', 'Asia/Shanghai'
), 'ACTIVE', 'admin'),

-- Oracle数据源
('819ffc00-6844-499f-af7b-5cff4f2b0120', 'ERP Oracle数据库', 'ORACLE', 'ERP系统Oracle数据库', JSON_OBJECT(
    'host', '10.0.1.200',
    'port', 1521,
    'serviceName', 'ERPDB',
    'username', 'erp_read',
    'password', '${encrypted:oracle_password}',
    'encoding', 'UTF-8'
), 'ACTIVE', 'admin'),

-- PostgreSQL数据源
('85b3c0bb-af69-4372-afc8-d8d2a5499a6f', '数据仓库PostgreSQL', 'POSTGRESQL', '数据仓库PostgreSQL数据库', JSON_OBJECT(
    'host', '10.0.3.100',
    'port', 5432,
    'database', 'warehouse_db',
    'username', 'warehouse_user',
    'password', '${encrypted:pg_password}',
    'schema', 'public',
    'encoding', 'UTF-8'
), 'ACTIVE', 'admin'),

-- 归档MySQL数据源
('fefe6b61-9163-4a4a-8c5c-f4bcac229a1f', '归档MySQL数据库', 'MYSQL', '历史数据归档库', JSON_OBJECT(
    'host', '10.0.4.100',
    'port', 3306,
    'database', 'archive_db',
    'username', 'archive_user',
    'password', '${encrypted:archive_password}',
    'encoding', 'utf8mb4',
    'timezone', 'Asia/Shanghai'
), 'ACTIVE', 'admin');

-- 插入归集任务模拟数据
INSERT INTO t_dc_collection_tasks (id, name, description, source_datasource_id, target_datasource_id, config, schedule_expression, status, retry_count, timeout_seconds, created_by) VALUES
-- 用户数据同步任务
('54cefc4d-3071-43d9-9fbf-baeb87932acd', '用户数据同步', '从生产环境同步用户表数据到数据仓库', 'bb3d52c8-1bca-4a33-b430-d597ceb4f38d', '85b3c0bb-af69-4372-afc8-d8d2a5499a6f', JSON_OBJECT(
    'sourceTable', 'users',
    'targetTable', 'dim_users',
    'columns', JSON_ARRAY('id', 'username', 'email', 'created_at', 'updated_at'),
    'whereCondition', 'status = "ACTIVE"',
    'splitPk', 'id',
    'batchSize', 1000
), '0 0 2 * * ?', 'READY', 3, 1800, 'admin'),

-- 订单数据增量同步
('3039a5c8-c894-42ab-ad49-5c2c5eccda31', '订单增量同步', '增量同步订单数据到数据仓库', 'bb3d52c8-1bca-4a33-b430-d597ceb4f38d', '85b3c0bb-af69-4372-afc8-d8d2a5499a6f', JSON_OBJECT(
    'sourceTable', 'orders',
    'targetTable', 'fact_orders',
    'columns', JSON_ARRAY('*'),
    'incrementalField', 'updated_at',
    'splitPk', 'id',
    'batchSize', 2000
), '0 */30 * * * ?', 'READY', 3, 3600, 'admin'),

-- ERP财务数据同步
('97fbf9e6-9580-41b8-ad00-f282d3c8deb7', 'ERP财务数据同步', '从ERP系统同步财务数据', '819ffc00-6844-499f-af7b-5cff4f2b0120', '85b3c0bb-af69-4372-afc8-d8d2a5499a6f', JSON_OBJECT(
    'sourceTable', 'FINANCE_TRANSACTIONS',
    'targetTable', 'fact_finance',
    'columns', JSON_ARRAY('TRANS_ID', 'AMOUNT', 'TRANS_DATE', 'ACCOUNT_ID'),
    'whereCondition', 'TRANS_DATE >= SYSDATE - 1',
    'splitPk', 'TRANS_ID',
    'batchSize', 500
), '0 0 1 * * ?', 'READY', 5, 7200, 'admin'),

-- 历史数据归档任务
('6631812e-deba-4e08-acff-e9e9a44c9c08', '日志数据归档', '将旧的日志数据归档到归档库', 'bb3d52c8-1bca-4a33-b430-d597ceb4f38d', 'fefe6b61-9163-4a4a-8c5c-f4bcac229a1f', JSON_OBJECT(
    'sourceTable', 'system_logs',
    'targetTable', 'archived_logs',
    'columns', JSON_ARRAY('*'),
    'whereCondition', 'created_at < DATE_SUB(NOW(), INTERVAL 6 MONTH)',
    'splitPk', 'id',
    'batchSize', 5000
), '0 0 3 1 * ?', 'READY', 2, 10800, 'admin'),

-- 商品数据实时同步
('d850e1d7-5bb2-43ad-a341-ee3c9a65b39b', '商品数据实时同步', '实时同步商品信息变更', 'bb3d52c8-1bca-4a33-b430-d597ceb4f38d', '451d1a23-2663-45ab-8cbc-e4e14d7de77c', JSON_OBJECT(
    'sourceTable', 'products',
    'targetTable', 'products_sync',
    'columns', JSON_ARRAY('id', 'name', 'price', 'category_id', 'status', 'updated_at'),
    'incrementalField', 'updated_at',
    'splitPk', 'id',
    'batchSize', 1000
), '0 */5 * * * ?', 'RUNNING', 3, 1200, 'admin');

-- 插入任务执行记录模拟数据
INSERT INTO t_dc_task_executions (id, task_id, task_name, status, progress, records_total, records_processed, records_success, records_failed, throughput, data_size_bytes, started_at, completed_at, duration_seconds, config) VALUES
-- 成功执行记录
('12128059-a266-4d4f-b647-3cb8c24b8aad', '54cefc4d-3071-43d9-9fbf-baeb87932acd', '用户数据同步', 'SUCCESS', 100.00, 15000, 15000, 15000, 0, 125.50, 2048576, 
 DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY) + INTERVAL 2 MINUTE, 120, 
 JSON_OBJECT('batchSize', 1000, 'parallelism', 3)),

('9d418e0c-fa54-4f01-8633-3a5ad57f46a1', '3039a5c8-c894-42ab-ad49-5c2c5eccda31', '订单增量同步', 'SUCCESS', 100.00, 8500, 8500, 8500, 0, 94.44, 1536000,
 DATE_SUB(NOW(), INTERVAL 12 HOUR), DATE_SUB(NOW(), INTERVAL 12 HOUR) + INTERVAL 90 SECOND, 90,
 JSON_OBJECT('batchSize', 2000, 'parallelism', 2)),

-- 失败执行记录
('1cc7a4a9-faee-41f6-b7f8-92830fa599ea', '97fbf9e6-9580-41b8-ad00-f282d3c8deb7', 'ERP财务数据同步', 'FAILED', 45.00, 5000, 2250, 2250, 0, 25.00, 512000,
 DATE_SUB(NOW(), INTERVAL 8 HOUR), DATE_SUB(NOW(), INTERVAL 8 HOUR) + INTERVAL 90 SECOND, 90,
 JSON_OBJECT('batchSize', 500, 'parallelism', 1)),

-- 运行中执行记录
('7b55b2c1-75e4-4a67-97fe-1920c0779b8c', 'd850e1d7-5bb2-43ad-a341-ee3c9a65b39b', '商品数据实时同步', 'RUNNING', 75.00, 12000, 9000, 9000, 0, 150.00, 1024000,
 DATE_SUB(NOW(), INTERVAL 1 HOUR), NULL, NULL,
 JSON_OBJECT('batchSize', 1000, 'parallelism', 4)),

-- 历史执行记录
('9f74988c-f00c-48a7-a51c-60c21424f35e', '6631812e-deba-4e08-acff-e9e9a44c9c08', '日志数据归档', 'SUCCESS', 100.00, 250000, 250000, 250000, 0, 462.96, 52428800,
 DATE_SUB(NOW(), INTERVAL 3 DAY), DATE_SUB(NOW(), INTERVAL 3 DAY) + INTERVAL 9 MINUTE, 540,
 JSON_OBJECT('batchSize', 5000, 'parallelism', 2));

-- 插入执行日志模拟数据
INSERT INTO t_dc_execution_logs (id, execution_id, log_level, message, thread, logger, timestamp) VALUES
-- 成功执行的日志
('e43672a4-ef77-4064-b096-555b13298473', '12128059-a266-4d4f-b647-3cb8c24b8aad', 'INFO', '开始执行数据同步任务', 'DataX-Job-Thread-1', 'com.dataengine.datax.JobExecutor', DATE_SUB(NOW(), INTERVAL 1 DAY)),
('c7110718-10e7-420d-ab1e-71a8c7ba79d5', '12128059-a266-4d4f-b647-3cb8c24b8aad', 'INFO', '连接源数据库成功: bb3d52c8-1bca-4a33-b430-d597ceb4f38d', 'DataX-Job-Thread-1', 'com.dataengine.datax.reader.MysqlReader', DATE_SUB(NOW(), INTERVAL 1 DAY) + INTERVAL 5 SECOND),
('9b4df410-273a-4b97-a141-87ede10d5f2d', '12128059-a266-4d4f-b647-3cb8c24b8aad', 'INFO', '连接目标数据库成功: 85b3c0bb-af69-4372-afc8-d8d2a5499a6f', 'DataX-Job-Thread-1', 'com.dataengine.datax.writer.PostgresqlWriter', DATE_SUB(NOW(), INTERVAL 1 DAY) + INTERVAL 10 SECOND),
('2d21ed78-3aeb-420f-a99e-d81b59663a67', '12128059-a266-4d4f-b647-3cb8c24b8aad', 'INFO', '开始读取数据，预计处理15000条记录', 'DataX-Job-Thread-1', 'com.dataengine.datax.reader.MysqlReader', DATE_SUB(NOW(), INTERVAL 1 DAY) + INTERVAL 15 SECOND),
('7649f50a-abc7-41e8-a358-94154c71d29a', '12128059-a266-4d4f-b647-3cb8c24b8aad', 'INFO', '数据同步完成，成功处理15000条记录', 'DataX-Job-Thread-1', 'com.dataengine.datax.JobExecutor', DATE_SUB(NOW(), INTERVAL 1 DAY) + INTERVAL 2 MINUTE),

-- 失败执行的日志
('070e3057-eb54-4210-a36d-c35d866f57ed', '1cc7a4a9-faee-41f6-b7f8-92830fa599ea', 'INFO', '开始执行ERP财务数据同步', 'DataX-Job-Thread-3', 'com.dataengine.datax.JobExecutor', DATE_SUB(NOW(), INTERVAL 8 HOUR)),
('2b80f0d0-a4c9-4b64-a775-b66e29ec4288', '1cc7a4a9-faee-41f6-b7f8-92830fa599ea', 'INFO', '连接Oracle数据库: 819ffc00-6844-499f-af7b-5cff4f2b0120', 'DataX-Job-Thread-3', 'com.dataengine.datax.reader.OracleReader', DATE_SUB(NOW(), INTERVAL 8 HOUR) + INTERVAL 10 SECOND),
('2de52b60-ccb6-44c2-935e-80c1a431b68f', '1cc7a4a9-faee-41f6-b7f8-92830fa599ea', 'WARN', '数据库连接响应较慢，重试中...', 'DataX-Job-Thread-3', 'com.dataengine.datax.reader.OracleReader', DATE_SUB(NOW(), INTERVAL 8 HOUR) + INTERVAL 30 SECOND),
('976f94ab-b2c0-4132-b2f9-61dc0a36fbc7', '1cc7a4a9-faee-41f6-b7f8-92830fa599ea', 'ERROR', 'ORA-00942: 表或视图不存在 - FINANCE_TRANSACTIONS', 'DataX-Job-Thread-3', 'com.dataengine.datax.reader.OracleReader', DATE_SUB(NOW(), INTERVAL 8 HOUR) + INTERVAL 90 SECOND),
('717258ee-517e-4c6d-805a-fc20c5bb86bb', '1cc7a4a9-faee-41f6-b7f8-92830fa599ea', 'ERROR', '任务执行失败，已处理2250条记录', 'DataX-Job-Thread-3', 'com.dataengine.datax.JobExecutor', DATE_SUB(NOW(), INTERVAL 8 HOUR) + INTERVAL 90 SECOND),

-- 运行中执行的日志
('3325b5fb-bee4-48fb-95fc-9ef5e6d2b33a', '7b55b2c1-75e4-4a67-97fe-1920c0779b8c', 'INFO', '开始执行商品数据实时同步', 'DataX-Job-Thread-4', 'com.dataengine.datax.JobExecutor', DATE_SUB(NOW(), INTERVAL 1 HOUR)),
('4ae5f3d7-910e-4a25-9c5c-bb3d6c7b6c49', '7b55b2c1-75e4-4a67-97fe-1920c0779b8c', 'INFO', '连接MySQL数据库成功', 'DataX-Job-Thread-4', 'com.dataengine.datax.reader.MysqlReader', DATE_SUB(NOW(), INTERVAL 1 HOUR) + INTERVAL 5 SECOND),
('a47284ae-9acc-4cad-b35e-b63f6dfefa98', '7b55b2c1-75e4-4a67-97fe-1920c0779b8c', 'INFO', '开始增量数据读取，当前处理进度: 75%', 'DataX-Job-Thread-4', 'com.dataengine.datax.reader.MysqlReader', DATE_SUB(NOW(), INTERVAL 30 MINUTE)),
('0cd64db9-ace3-454d-b21d-18c9f488a96d', '7b55b2c1-75e4-4a67-97fe-1920c0779b8c', 'INFO', '已成功同步9000条商品记录', 'DataX-Job-Thread-4', 'com.dataengine.datax.JobExecutor', DATE_SUB(NOW(), INTERVAL 15 MINUTE));

-- 插入任务调度模拟数据
INSERT INTO t_dc_task_schedules (id, task_id, cron_expression, timezone, enabled, next_execution_time, last_execution_time, execution_count) VALUES
('a4646eba-830c-42d8-9965-a6303245ce64', '54cefc4d-3071-43d9-9fbf-baeb87932acd', '0 0 2 * * ?', 'Asia/Shanghai', TRUE, 
 DATE_ADD(CURDATE(), INTERVAL 1 DAY) + INTERVAL 2 HOUR, 
 DATE_SUB(NOW(), INTERVAL 1 DAY), 30),

('f0927bb6-9aec-4381-9361-82f06e86987f', '3039a5c8-c894-42ab-ad49-5c2c5eccda31', '0 */30 * * * ?', 'Asia/Shanghai', TRUE,
 DATE_ADD(NOW(), INTERVAL 30 MINUTE),
 DATE_SUB(NOW(), INTERVAL 30 MINUTE), 48),

('944864f9-4a72-4881-baf3-6fc27b153db2', '97fbf9e6-9580-41b8-ad00-f282d3c8deb7', '0 0 1 * * ?', 'Asia/Shanghai', FALSE,
 NULL, DATE_SUB(NOW(), INTERVAL 8 HOUR), 5),

('03f89366-51e3-4d26-9329-335b44193e18', '6631812e-deba-4e08-acff-e9e9a44c9c08', '0 0 3 1 * ?', 'Asia/Shanghai', TRUE,
 DATE_ADD(DATE_ADD(LAST_DAY(CURDATE()), INTERVAL 1 DAY), INTERVAL 3 HOUR),
 DATE_SUB(NOW(), INTERVAL 3 DAY), 3),

('467f424e-1207-42fd-992a-05441751570b', 'd850e1d7-5bb2-43ad-a341-ee3c9a65b39b', '0 */5 * * * ?', 'Asia/Shanghai', TRUE,
 DATE_ADD(NOW(), INTERVAL 5 MINUTE),
 DATE_SUB(NOW(), INTERVAL 5 MINUTE), 288);

-- 插入统计信息模拟数据
INSERT INTO t_dc_statistics (id, stat_date, period_type, total_tasks, active_tasks, total_executions, successful_executions, failed_executions, total_records_processed, avg_execution_time, avg_throughput) VALUES
-- 今日统计
('5b37f051-a701-4367-b790-43fe94673484', CURDATE(), 'DAY', 5, 4, 12, 10, 2, 125000, 180.50, 135.25),
-- 昨日统计
('55690cdd-6b87-4c9d-a378-30cbc44c87f2', DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'DAY', 5, 3, 15, 12, 3, 156000, 195.30, 142.80),
-- 本周统计
('26283ff9-456e-442a-9259-980929999d01', DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY), 'WEEK', 5, 4, 85, 72, 13, 890000, 188.75, 138.90),
-- 本月统计
('26283ff9-456e-442a-9259-980929999d02', DATE_FORMAT(CURDATE(), '%Y-%m-01'), 'MONTH', 5, 4, 320, 285, 35, 3250000, 192.40, 141.60);