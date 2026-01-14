-- 使用现有的datamate数据库
\c datamate;

-- 数据归集任务表
CREATE TABLE IF NOT EXISTS t_dc_collection_tasks (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    sync_mode VARCHAR(20) DEFAULT 'ONCE',
    template_id VARCHAR(36) NOT NULL,
    template_name VARCHAR(255) NOT NULL,
    target_path VARCHAR(1000) DEFAULT '',
    config JSONB NOT NULL,
    schedule_expression VARCHAR(255),
    status VARCHAR(20) DEFAULT 'DRAFT',
    retry_count INTEGER DEFAULT 3,
    timeout_seconds INTEGER DEFAULT 3600,
    last_execution_id VARCHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

-- 添加注释
COMMENT ON TABLE t_dc_collection_tasks IS '数据归集任务表';
COMMENT ON COLUMN t_dc_collection_tasks.id IS '任务ID（UUID）';
COMMENT ON COLUMN t_dc_collection_tasks.name IS '任务名称';
COMMENT ON COLUMN t_dc_collection_tasks.description IS '任务描述';
COMMENT ON COLUMN t_dc_collection_tasks.sync_mode IS '同步模式：ONCE/SCHEDULED';
COMMENT ON COLUMN t_dc_collection_tasks.template_id IS '归集模板ID';
COMMENT ON COLUMN t_dc_collection_tasks.template_name IS '归集模板名称';
COMMENT ON COLUMN t_dc_collection_tasks.target_path IS '目标存储路径';
COMMENT ON COLUMN t_dc_collection_tasks.config IS '归集配置（DataX配置），包含源端和目标端配置信息';
COMMENT ON COLUMN t_dc_collection_tasks.schedule_expression IS 'Cron调度表达式';
COMMENT ON COLUMN t_dc_collection_tasks.status IS '任务状态：DRAFT/READY/RUNNING/SUCCESS/FAILED/STOPPED';
COMMENT ON COLUMN t_dc_collection_tasks.retry_count IS '重试次数';
COMMENT ON COLUMN t_dc_collection_tasks.timeout_seconds IS '超时时间（秒）';
COMMENT ON COLUMN t_dc_collection_tasks.last_execution_id IS '最后执行ID（UUID）';
COMMENT ON COLUMN t_dc_collection_tasks.created_at IS '创建时间';
COMMENT ON COLUMN t_dc_collection_tasks.updated_at IS '更新时间';
COMMENT ON COLUMN t_dc_collection_tasks.created_by IS '创建者';
COMMENT ON COLUMN t_dc_collection_tasks.updated_by IS '更新者';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_dc_tasks_status ON t_dc_collection_tasks(status);
CREATE INDEX IF NOT EXISTS idx_dc_tasks_created_at ON t_dc_collection_tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_dc_tasks_template_id ON t_dc_collection_tasks(template_id);

-- 任务执行明细表
CREATE TABLE IF NOT EXISTS t_dc_task_executions (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) NOT NULL,
    task_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'RUNNING',
    log_path VARCHAR(1000) NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

-- 添加注释
COMMENT ON TABLE t_dc_task_executions IS '任务执行明细表';
COMMENT ON COLUMN t_dc_task_executions.id IS '执行记录ID（UUID）';
COMMENT ON COLUMN t_dc_task_executions.task_id IS '任务ID';
COMMENT ON COLUMN t_dc_task_executions.task_name IS '任务名称';
COMMENT ON COLUMN t_dc_task_executions.status IS '执行状态：RUNNING/SUCCESS/FAILED/STOPPED';
COMMENT ON COLUMN t_dc_task_executions.log_path IS '日志文件路径';
COMMENT ON COLUMN t_dc_task_executions.started_at IS '开始时间';
COMMENT ON COLUMN t_dc_task_executions.completed_at IS '完成时间';
COMMENT ON COLUMN t_dc_task_executions.duration_seconds IS '执行时长（秒）';
COMMENT ON COLUMN t_dc_task_executions.error_message IS '错误信息';
COMMENT ON COLUMN t_dc_task_executions.created_at IS '创建时间';
COMMENT ON COLUMN t_dc_task_executions.updated_at IS '更新时间';
COMMENT ON COLUMN t_dc_task_executions.created_by IS '创建者';
COMMENT ON COLUMN t_dc_task_executions.updated_by IS '更新者';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_dc_executions_task_id ON t_dc_task_executions(task_id);
CREATE INDEX IF NOT EXISTS idx_dc_executions_status ON t_dc_task_executions(status);
CREATE INDEX IF NOT EXISTS idx_dc_executions_started_at ON t_dc_task_executions(started_at);

-- 外键约束
ALTER TABLE t_dc_task_executions ADD CONSTRAINT fk_dc_executions_task FOREIGN KEY (task_id)
REFERENCES t_dc_collection_tasks(id) ON DELETE CASCADE;

-- 数据归集模板配置表
CREATE TABLE IF NOT EXISTS t_dc_collection_templates (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    source_type VARCHAR(64) NOT NULL,
    source_name VARCHAR(64) NOT NULL,
    target_type VARCHAR(64) NOT NULL,
    target_name VARCHAR(64) NOT NULL,
    template_content JSONB NOT NULL,
    built_in BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

-- 添加注释
COMMENT ON TABLE t_dc_collection_templates IS '数据归集模板配置表';
COMMENT ON COLUMN t_dc_collection_templates.id IS '模板ID（UUID）';
COMMENT ON COLUMN t_dc_collection_templates.name IS '模板名称';
COMMENT ON COLUMN t_dc_collection_templates.description IS '模板描述';
COMMENT ON COLUMN t_dc_collection_templates.source_type IS '源数据源类型';
COMMENT ON COLUMN t_dc_collection_templates.source_name IS '源数据源名称';
COMMENT ON COLUMN t_dc_collection_templates.target_type IS '目标数据源类型';
COMMENT ON COLUMN t_dc_collection_templates.target_name IS '目标数据源名称';
COMMENT ON COLUMN t_dc_collection_templates.template_content IS '模板内容';
COMMENT ON COLUMN t_dc_collection_templates.built_in IS '是否系统内置';
COMMENT ON COLUMN t_dc_collection_templates.created_at IS '创建时间';
COMMENT ON COLUMN t_dc_collection_templates.updated_at IS '更新时间';
COMMENT ON COLUMN t_dc_collection_templates.created_by IS '创建者';
COMMENT ON COLUMN t_dc_collection_templates.updated_by IS '更新者';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_dc_templates_source_target ON t_dc_collection_templates(source_type, target_type);

-- 创建触发器用于自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
RETURN NEW;
END;
$$ language 'plpgsql';

-- 为各个表创建触发器
DROP TRIGGER IF EXISTS update_dc_collection_tasks_updated_at ON t_dc_collection_tasks;
CREATE TRIGGER update_dc_collection_tasks_updated_at
    BEFORE UPDATE ON t_dc_collection_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_dc_task_executions_updated_at ON t_dc_task_executions;
CREATE TRIGGER update_dc_task_executions_updated_at
    BEFORE UPDATE ON t_dc_task_executions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_dc_collection_templates_updated_at ON t_dc_collection_templates;
CREATE TRIGGER update_dc_collection_templates_updated_at
    BEFORE UPDATE ON t_dc_collection_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 插入初始数据 - 数据归集模板
INSERT INTO t_dc_collection_templates (
    id, name, description, source_type, source_name, target_type, target_name,
    template_content, built_in, created_by, updated_by
) VALUES
      (
          '1',
          'NAS归集模板',
          '将NAS存储上的文件归集到DataMate平台上。',
          'nfsreader',
          'nfsreader',
          'nfswriter',
          'nfswriter',
          '{"parameter": {"ip": {"name": "NAS地址","description": "NAS服务的地址，可以为IP或者域名。","type": "input", "required": true, "index": 1}, "path": {"name": "共享路径","description": "NAS服务的共享路径。","type": "input", "required": true, "index": 2}, "files": {"name": "文件列表","description": "指定文件列表进行归集。","type": "selectTag", "required": false, "index": 3}}, "reader": {}, "writer": {}}',
          TRUE,
          'system',
          'system'
      ),
      (
          '2',
          'S3存储归集模板',
          '将S3对象存储（如OBS、MinIO、Ceph等）上的文件归集到DataMate平台上。',
          's3reader',
          's3reader',
          's3writer',
          's3writer',
          '{"parameter": {"endpoint": {"name": "服务地址","description": "S3兼容存储的服务地址（如http://minio.example.com:9000）。","type": "input", "required": true, "index": 1}, "bucket": {"name": "存储桶名称","description": "S3存储桶名称。","type": "input", "required": true, "index": 2}, "accessKey": {"name": "Access Key","description": "S3访问密钥（Access Key ID）。","type": "input", "required": true, "index": 3}, "secretKey": {"name": "Secret Key","description": "S3密钥（Secret Access Key）。","type": "password", "required": true, "index": 4}, "prefix": {"name": "匹配前缀","description": "按照匹配前缀选中S3中的文件进行归集。","type": "input", "required": false, "index": 5}, "region": {"name": "区域","description": "S3区域（默认us-east-1）。","type": "input", "required": false, "index": 6}}, "reader": {}, "writer": {}}',
          TRUE,
          'system',
          'system'
      ),
      (
          '3',
          'MYSQL归集模板',
          '将MYSQL数据库中的数据以csv文件的形式归集到DataMate平台上。',
          'mysqlreader',
          'mysqlreader',
          'txtfilewriter',
          'txtfilewriter',
          '{"parameter": {}, "reader": {"username": {"name": "用户名","description": "数据库的用户名。","type": "input", "required": true, "index": 2}, "password": {"name": "密码","description": "数据库的密码。","type": "password", "required": true, "index": 3}, "connection": {"name": "数据库连接信息", "description": "数据库连接信息。", "type": "multipleList", "size": 1, "index": 1, "properties": {"jdbcUrl": {"type": "inputList", "name": "数据库连接", "description": "数据库连接url。", "required": true, "index": 1}, "querySql": {"type": "inputList", "name": "查询sql", "description": "输入符合语法的sql查询语句。", "required": true, "index": 2}}}}, "writer": {"header": {"name": "列名","description": "查询结果的列名，最终会体现为csv文件的表头。","type": "selectTag", "required": false}}}',
          TRUE,
          'system',
          'system'
      ),
      (
          '4',
          'StarRocks归集模板',
          '将StarRocks中的数据以csv文件的形式归集到DataMate平台上。',
          'starrocksreader',
          'starrocksreader',
          'txtfilewriter',
          'txtfilewriter',
          '{"parameter": {}, "reader": {"username": {"name": "用户名","description": "数据库的用户名。","type": "input", "required": true, "index": 2}, "password": {"name": "密码","description": "数据库的密码。","type": "password", "required": true, "index": 3}, "connection": {"name": "数据库连接信息", "description": "数据库连接信息。", "type": "multipleList", "size": 1, "index": 1, "properties": {"jdbcUrl": {"type": "inputList", "name": "数据库连接", "description": "数据库连接url。", "required": true, "index": 1}, "querySql": {"type": "inputList", "name": "查询sql", "description": "输入符合语法的sql查询语句。", "required": true, "index": 2}}}}, "writer": {"header": {"name": "列名","description": "查询结果的列名，最终会体现为csv文件的表头。","type": "selectTag", "required": false}}}',
          TRUE,
          'system',
          'system'
      ),
      (
          '5',
          'GlusterFS归集模板',
          '将GlusterFS分布式文件系统上的文件归集到DataMate平台上。',
          'glusterfsreader',
          'glusterfsreader',
          'glusterfswriter',
          'glusterfswriter',
          '{"parameter": {"ip": {"name": "服务器地址","description": "GlusterFS服务器的IP地址或域名。","type": "input", "required": true, "index": 1}, "volume": {"name": "卷名称","description": "GlusterFS卷名称。","type": "input", "required": true, "index": 2}, "path": {"name": "子路径","description": "卷内的子目录路径（可选）。","type": "input", "required": false, "index": 3}, "files": {"name": "文件列表","description": "指定文件列表进行归集。","type": "selectTag", "required": false, "index": 4}}, "reader": {}, "writer": {}}',
          TRUE,
          'system',
          'system')
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    source_type = EXCLUDED.source_type,
    source_name = EXCLUDED.source_name,
    target_type = EXCLUDED.target_type,
    target_name = EXCLUDED.target_name,
    template_content = EXCLUDED.template_content,
    built_in = EXCLUDED.built_in,
    created_by = EXCLUDED.created_by,
    updated_by = EXCLUDED.updated_by,
    updated_at = CURRENT_TIMESTAMP;
