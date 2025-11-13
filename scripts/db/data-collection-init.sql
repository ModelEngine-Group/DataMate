-- 数据归集服务数据库初始化脚本
-- 适用于datamate数据库

USE datamate;

-- =====================================
-- DDL语句 - 数据库表结构定义
-- =====================================

-- 删除现有表（支持重复执行 调测阶段使用）
DROP TABLE IF EXISTS t_dc_task_executions;
DROP TABLE IF EXISTS t_dc_collection_tasks;
DROP TABLE IF EXISTS t_dc_datax_templates;

CREATE TABLE t_dc_task_executions (
                                    id VARCHAR(36) PRIMARY KEY COMMENT '执行记录ID（UUID）',
                                    task_id VARCHAR(36) NOT NULL COMMENT '任务ID',
                                    task_name VARCHAR(255) NOT NULL COMMENT '任务名称',
                                    status VARCHAR(20) DEFAULT 'RUNNING' COMMENT '执行状态：RUNNING/SUCCESS/FAILED/STOPPED',
                                    progress DECIMAL(5,2) DEFAULT 0.00 COMMENT '进度百分比',
                                    records_total BIGINT DEFAULT 0 COMMENT '总记录数',
                                    records_processed BIGINT DEFAULT 0 COMMENT '已处理记录数',
                                    records_success BIGINT DEFAULT 0 COMMENT '成功记录数',
                                    records_failed BIGINT DEFAULT 0 COMMENT '失败记录数',
                                    throughput DECIMAL(10,2) DEFAULT 0.00 COMMENT '吞吐量（条/秒）',
                                    data_size_bytes BIGINT DEFAULT 0 COMMENT '数据量（字节）',
                                    started_at TIMESTAMP NULL COMMENT '开始时间',
                                    completed_at TIMESTAMP NULL COMMENT '完成时间',
                                    duration_seconds INT DEFAULT 0 COMMENT '执行时长（秒）',
                                    config JSON COMMENT '执行配置',
                                    error_message TEXT COMMENT '错误信息',
                                    datax_job_id TEXT COMMENT 'datax任务ID',
                                    result TEXT COMMENT '执行结果',
                                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                                    created_by VARCHAR(255) COMMENT '创建者',
                                    updated_by VARCHAR(255) COMMENT '更新者',
                                    INDEX idx_task_id (task_id),
                                    INDEX idx_status (status),
                                    INDEX idx_started_at (started_at)
) COMMENT='任务执行明细表';

-- 数据归集任务表
CREATE TABLE t_dc_collection_tasks (
    id VARCHAR(36) PRIMARY KEY COMMENT '任务ID（UUID）',
    name VARCHAR(255) NOT NULL COMMENT '任务名称',
    description TEXT COMMENT '任务描述',
    sync_mode VARCHAR(20) DEFAULT 'ONCE' COMMENT '同步模式：ONCE/SCHEDULED',
    task_type VARCHAR(20) DEFAULT 'NAS' COMMENT '任务类型：NAS/OBS/MYSQL/CUSTOM',
    target_path VARCHAR(1000) DEFAULT '' COMMENT '目标存储路径',
    config TEXT  NOT NULL COMMENT '归集配置（DataX配置），包含源端和目标端配置信息',
    schedule_expression VARCHAR(255) COMMENT 'Cron调度表达式',
    status VARCHAR(20) DEFAULT 'DRAFT' COMMENT '任务状态：DRAFT/READY/RUNNING/SUCCESS/FAILED/STOPPED',
    retry_count INT DEFAULT 3 COMMENT '重试次数',
    timeout_seconds INT DEFAULT 3600 COMMENT '超时时间（秒）',
    max_records BIGINT COMMENT '最大处理记录数',
    sort_field VARCHAR(100) COMMENT '增量字段',
    last_execution_id VARCHAR(36) COMMENT '最后执行ID（UUID）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(255) COMMENT '创建者',
    updated_by VARCHAR(255) COMMENT '更新者',
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_schedule (schedule_expression)
) COMMENT='数据归集任务表';

-- 任务执行记录表
CREATE TABLE t_dc_task_log (
    id VARCHAR(36) PRIMARY KEY COMMENT '执行记录ID（UUID）',
    task_id VARCHAR(36) NOT NULL COMMENT '任务ID',
    task_name VARCHAR(255) NOT NULL COMMENT '任务名称',
    sync_mode VARCHAR(20) DEFAULT 'FULL' COMMENT '同步模式：FULL/INCREMENTAL',
    status VARCHAR(20) DEFAULT 'RUNNING' COMMENT '执行状态：RUNNING/SUCCESS/FAILED/STOPPED',
    start_time TIMESTAMP NULL COMMENT '开始时间',
    end_time TIMESTAMP NULL COMMENT '结束时间',
    duration BIGINT COMMENT '执行时长(毫秒)',
    process_id VARCHAR(50) COMMENT '进程ID',
    log_path VARCHAR(500) COMMENT '日志文件路径',
    error_msg LONGTEXT COMMENT '错误信息',
    result LONGTEXT COMMENT '执行结果',
    retry_times INT DEFAULT 0 COMMENT '重试次数',
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) COMMENT='任务执行记录表';


-- DataX模板配置表
CREATE TABLE t_dc_datax_templates (
    id VARCHAR(36) PRIMARY KEY COMMENT '模板ID（UUID）',
    name VARCHAR(255) NOT NULL UNIQUE COMMENT '模板名称',
    source_type VARCHAR(50) NOT NULL COMMENT '源数据源类型',
    target_type VARCHAR(50) NOT NULL COMMENT '目标数据源类型',
    template_content TEXT NOT NULL COMMENT '模板内容',
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
), 'MySQL到MySQL数据同步模板', TRUE, 'system');

-- 插入任务执行记录模拟数据
INSERT INTO t_dc_task_executions (id, task_id, task_name, status, progress, records_total, records_processed, records_success, records_failed, throughput, data_size_bytes, started_at, completed_at, duration_seconds, config) VALUES
-- 成功执行记录
('12128059-a266-4d4f-b647-3cb8c24b8aad', '54cefc4d-3071-43d9-9fbf-baeb87932acd', '用户数据同步', 'SUCCESS', 100.00, 15000, 15000, 15000, 0, 125.50, 2048576,
 DATE_SUB(NOW(), INTERVAL 1 DAY), DATE_SUB(NOW(), INTERVAL 1 DAY) + INTERVAL 2 MINUTE, 120,
 JSON_OBJECT('batchSize', 1000, 'parallelism', 3)),

('9d418e0c-fa54-4f01-8633-3a5ad57f46a1', '3039a5c8-c894-42ab-ad49-5c2c5eccda31', '订单增量同步', 'SUCCESS', 100.00, 8500, 8500, 8500, 0, 94.44, 1536000,
 DATE_SUB(NOW(), INTERVAL 12 HOUR), DATE_SUB(NOW(), INTERVAL 12 HOUR) + INTERVAL 90 SECOND, 90,
 JSON_OBJECT('batchSize', 2000, 'parallelism', 2));

