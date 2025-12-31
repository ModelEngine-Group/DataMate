-- 数据归集服务数据库初始化脚本
-- 适用于datamate数据库

USE datamate;

-- =====================================
-- DDL语句 - 数据库表结构定义
-- =====================================

-- 删除现有表（支持重复执行 调测阶段使用）
DROP TABLE IF EXISTS t_dc_task_executions;
DROP TABLE IF EXISTS t_dc_collection_tasks;
DROP TABLE IF EXISTS t_dc_collection_templates;

-- 数据归集任务表
CREATE TABLE t_dc_collection_tasks (
    id VARCHAR(36) PRIMARY KEY COMMENT '任务ID（UUID）',
    name VARCHAR(255) NOT NULL COMMENT '任务名称',
    description TEXT COMMENT '任务描述',
    sync_mode VARCHAR(20) DEFAULT 'ONCE' COMMENT '同步模式：ONCE/SCHEDULED',
    template_id VARCHAR(36) NOT NULL COMMENT '归集模板ID',
    template_name VARCHAR(255) NOT NULL COMMENT '归集模板名称',
    target_path VARCHAR(1000) DEFAULT '' COMMENT '目标存储路径',
    config JSON  NOT NULL COMMENT '归集配置（DataX配置），包含源端和目标端配置信息',
    schedule_expression VARCHAR(255) COMMENT 'Cron调度表达式',
    status VARCHAR(20) DEFAULT 'DRAFT' COMMENT '任务状态：DRAFT/READY/RUNNING/SUCCESS/FAILED/STOPPED',
    retry_count INT DEFAULT 3 COMMENT '重试次数',
    timeout_seconds INT DEFAULT 3600 COMMENT '超时时间（秒）',
    last_execution_id VARCHAR(36) COMMENT '最后执行ID（UUID）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(255) COMMENT '创建者',
    updated_by VARCHAR(255) COMMENT '更新者',
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) COMMENT='数据归集任务表';

CREATE TABLE t_dc_task_executions (
    id VARCHAR(36) PRIMARY KEY COMMENT '执行记录ID（UUID）',
    task_id VARCHAR(36) NOT NULL COMMENT '任务ID',
    task_name VARCHAR(255) NOT NULL COMMENT '任务名称',
    status VARCHAR(20) DEFAULT 'RUNNING' COMMENT '执行状态：RUNNING/SUCCESS/FAILED/STOPPED',
    log_path VARCHAR(1000) NOT NULL COMMENT '日志文件路径',
    started_at TIMESTAMP NULL COMMENT '开始时间',
    completed_at TIMESTAMP NULL COMMENT '完成时间',
    duration_seconds INT DEFAULT 0 COMMENT '执行时长（秒）',
    error_message TEXT COMMENT '错误信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(255) COMMENT '创建者',
    updated_by VARCHAR(255) COMMENT '更新者',
    INDEX idx_task_id (task_id),
    INDEX idx_status (status),
    INDEX idx_started_at (started_at)
) COMMENT='任务执行明细表';

-- 数据归集模板配置表
CREATE TABLE t_dc_collection_templates (
    id VARCHAR(36) PRIMARY KEY COMMENT '模板ID（UUID）',
    name VARCHAR(255) NOT NULL UNIQUE COMMENT '模板名称',
    description TEXT COMMENT '模板描述',
    source_type VARCHAR(64) NOT NULL COMMENT '源数据源类型',
    source_name VARCHAR(64) NOT NULL COMMENT '源数据源名称',
    target_type VARCHAR(64) NOT NULL COMMENT '目标数据源类型',
    target_name VARCHAR(64) NOT NULL COMMENT '目标数据源名称',
    template_content JSON NOT NULL COMMENT '模板内容',
    built_in BOOLEAN DEFAULT FALSE COMMENT '是否系统内置',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(255) COMMENT '创建者',
    updated_by VARCHAR(255) COMMENT '更新者',
    INDEX idx_source_target (source_type, target_type)
) COMMENT='数据归集模板配置表';

INSERT IGNORE INTO t_dc_collection_templates(id, name, description, source_type, source_name, target_type, target_name, template_content, built_in, created_by, updated_by)
VALUES ('1', 'NAS归集模板', '将NAS存储上的文件归集到DataMate平台上。', 'nfsreader', 'nfsreader', 'nfswriter', 'nfswriter', '{"parameter": {"ip": {"name": "NAS地址","description": "NAS服务的地址，可以为IP或者域名。","type": "input", "required": true}, "path": {"name": "共享路径","description": "NAS服务的共享路径。","type": "input", "required": true}, "files": {"name": "文件列表","description": "指定文件列表进行归集。","type": "select", "required": false}}, "reader": {}, "writer": {}}', True, 'system', 'system'),
       ('2', 'OBS归集模板', '将OBS存储上的文件归集到DataMate平台上。', 'obsreader', 'obsreader', 'obswriter', 'obswriter', '{"parameter": {"endpoint": {"name": "服务地址","description": "OBS的服务地址。","type": "input", "required": true},"bucket": {"name": "存储桶名称","description": "OBS存储桶名称。","type": "input", "required": true},"accessKey": {"name": "AK","description": "OBS访问密钥。","type": "input", "required": true},"secretKey": {"name": "SK","description": "OBS密钥。","type": "password", "required": true},"prefix": {"name": "匹配前缀","description": "按照匹配前缀去选中OBS中的文件进行归集。","type": "input", "required": true}}, "reader": {}, "writer": {}}', True, 'system', 'system');
