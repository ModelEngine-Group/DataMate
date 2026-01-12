-- 使用现有的datamate数据库
\c datamate;

-- 评估任务表
CREATE TABLE IF NOT EXISTS t_de_eval_task (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    task_type VARCHAR(50) NOT NULL,
    source_type VARCHAR(36),
    source_id VARCHAR(36),
    source_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'PENDING',
    eval_method VARCHAR(50) DEFAULT 'AUTO',
    eval_process DOUBLE PRECISION NOT NULL DEFAULT 0,
    eval_prompt TEXT,
    eval_config TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

-- 添加注释
COMMENT ON TABLE t_de_eval_task IS '评估任务表（UUID 主键）';
COMMENT ON COLUMN t_de_eval_task.id IS 'UUID';
COMMENT ON COLUMN t_de_eval_task.name IS '评估任务名称';
COMMENT ON COLUMN t_de_eval_task.description IS '评估任务描述';
COMMENT ON COLUMN t_de_eval_task.task_type IS '评估任务类型：QA';
COMMENT ON COLUMN t_de_eval_task.source_type IS '待评估对象类型：DATASET/SYNTHESIS';
COMMENT ON COLUMN t_de_eval_task.source_id IS '待评估对象ID';
COMMENT ON COLUMN t_de_eval_task.source_name IS '待评估对象名称';
COMMENT ON COLUMN t_de_eval_task.status IS '状态：PENDING/RUNNING/COMPLETED/STOPPED/FAILED';
COMMENT ON COLUMN t_de_eval_task.eval_method IS '评估方式：AUTO/MANUAL';
COMMENT ON COLUMN t_de_eval_task.eval_process IS '评估进度';
COMMENT ON COLUMN t_de_eval_task.eval_prompt IS '评估提示词';
COMMENT ON COLUMN t_de_eval_task.eval_config IS '评估配置';
COMMENT ON COLUMN t_de_eval_task.created_at IS '创建时间';
COMMENT ON COLUMN t_de_eval_task.updated_at IS '更新时间';
COMMENT ON COLUMN t_de_eval_task.created_by IS '创建者';
COMMENT ON COLUMN t_de_eval_task.updated_by IS '更新者';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_de_eval_task_status ON t_de_eval_task(status);
CREATE INDEX IF NOT EXISTS idx_de_eval_task_created_at ON t_de_eval_task(created_at);
CREATE INDEX IF NOT EXISTS idx_de_eval_task_source_id ON t_de_eval_task(source_id);

-- 评估文件表
CREATE TABLE IF NOT EXISTS t_de_eval_file (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) NOT NULL,
    file_id VARCHAR(36),
    file_name VARCHAR(255),
    total_count INTEGER DEFAULT 0,
    evaluated_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

-- 添加注释
COMMENT ON TABLE t_de_eval_file IS '评估文件表（UUID 主键）';
COMMENT ON COLUMN t_de_eval_file.id IS 'UUID';
COMMENT ON COLUMN t_de_eval_file.task_id IS '评估任务ID';
COMMENT ON COLUMN t_de_eval_file.file_id IS '文件ID';
COMMENT ON COLUMN t_de_eval_file.file_name IS '文件名';
COMMENT ON COLUMN t_de_eval_file.total_count IS '总数';
COMMENT ON COLUMN t_de_eval_file.evaluated_count IS '已评估数';
COMMENT ON COLUMN t_de_eval_file.error_message IS '错误信息';
COMMENT ON COLUMN t_de_eval_file.created_at IS '创建时间';
COMMENT ON COLUMN t_de_eval_file.updated_at IS '更新时间';
COMMENT ON COLUMN t_de_eval_file.created_by IS '创建者';
COMMENT ON COLUMN t_de_eval_file.updated_by IS '更新者';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_de_eval_file_task_id ON t_de_eval_file(task_id);
CREATE INDEX IF NOT EXISTS idx_de_eval_file_file_id ON t_de_eval_file(file_id);

-- 评估条目表
CREATE TABLE IF NOT EXISTS t_de_eval_item (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) NOT NULL,
    file_id VARCHAR(36),
    item_id VARCHAR(36) NOT NULL,
    eval_content TEXT,
    eval_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    eval_result TEXT,
    status VARCHAR(50) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

-- 添加注释
COMMENT ON TABLE t_de_eval_item IS '评估条目表（UUID 主键）';
COMMENT ON COLUMN t_de_eval_item.id IS 'UUID';
COMMENT ON COLUMN t_de_eval_item.task_id IS '评估任务ID';
COMMENT ON COLUMN t_de_eval_item.file_id IS '文件ID';
COMMENT ON COLUMN t_de_eval_item.item_id IS '评估条目ID';
COMMENT ON COLUMN t_de_eval_item.eval_content IS '评估内容';
COMMENT ON COLUMN t_de_eval_item.eval_score IS '评估分数';
COMMENT ON COLUMN t_de_eval_item.eval_result IS '评估结果';
COMMENT ON COLUMN t_de_eval_item.status IS '状态：PENDING/EVALUATED';
COMMENT ON COLUMN t_de_eval_item.created_at IS '创建时间';
COMMENT ON COLUMN t_de_eval_item.updated_at IS '更新时间';
COMMENT ON COLUMN t_de_eval_item.created_by IS '创建者';
COMMENT ON COLUMN t_de_eval_item.updated_by IS '更新者';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_de_eval_item_task_id ON t_de_eval_item(task_id);
CREATE INDEX IF NOT EXISTS idx_de_eval_item_file_id ON t_de_eval_item(file_id);
CREATE INDEX IF NOT EXISTS idx_de_eval_item_status ON t_de_eval_item(status);
CREATE INDEX IF NOT EXISTS idx_de_eval_item_item_id ON t_de_eval_item(item_id);

-- 创建外键约束
ALTER TABLE t_de_eval_file ADD CONSTRAINT fk_de_eval_file_task FOREIGN KEY (task_id)
REFERENCES t_de_eval_task(id) ON DELETE CASCADE;

ALTER TABLE t_de_eval_item ADD CONSTRAINT fk_de_eval_item_task FOREIGN KEY (task_id)
REFERENCES t_de_eval_task(id) ON DELETE CASCADE;

-- 创建触发器用于自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
RETURN NEW;
END;
$$ language 'plpgsql';

-- 为各个表创建触发器
DROP TRIGGER IF EXISTS update_de_eval_task_updated_at ON t_de_eval_task;
CREATE TRIGGER update_de_eval_task_updated_at
    BEFORE UPDATE ON t_de_eval_task
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_de_eval_file_updated_at ON t_de_eval_file;
CREATE TRIGGER update_de_eval_file_updated_at
    BEFORE UPDATE ON t_de_eval_file
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_de_eval_item_updated_at ON t_de_eval_item;
CREATE TRIGGER update_de_eval_item_updated_at
    BEFORE UPDATE ON t_de_eval_item
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
