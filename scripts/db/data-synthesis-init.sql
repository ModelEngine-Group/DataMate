-- 使用现有的datamate数据库
\c datamate;

-- 数据合成任务表
CREATE TABLE IF NOT EXISTS t_data_synth_instances
(
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20),
    synth_type VARCHAR(20) NOT NULL,
    progress INTEGER DEFAULT 0,
    synth_config JSONB NOT NULL,
    total_files INTEGER DEFAULT 0,
    processed_files INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 0,
    processed_chunks INTEGER DEFAULT 0,
    total_synth_data INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

-- 添加注释
COMMENT ON TABLE t_data_synth_instances IS '数据合成任务表（UUID 主键）';
COMMENT ON COLUMN t_data_synth_instances.id IS 'UUID';
COMMENT ON COLUMN t_data_synth_instances.name IS '任务名称';
COMMENT ON COLUMN t_data_synth_instances.description IS '任务描述';
COMMENT ON COLUMN t_data_synth_instances.status IS '任务状态';
COMMENT ON COLUMN t_data_synth_instances.synth_type IS '合成类型';
COMMENT ON COLUMN t_data_synth_instances.progress IS '任务进度(百分比)';
COMMENT ON COLUMN t_data_synth_instances.synth_config IS '合成配置';
COMMENT ON COLUMN t_data_synth_instances.total_files IS '总文件数';
COMMENT ON COLUMN t_data_synth_instances.processed_files IS '已处理文件数';
COMMENT ON COLUMN t_data_synth_instances.total_chunks IS '总文本块数';
COMMENT ON COLUMN t_data_synth_instances.processed_chunks IS '已处理文本块数';
COMMENT ON COLUMN t_data_synth_instances.total_synth_data IS '总合成数据量';
COMMENT ON COLUMN t_data_synth_instances.created_at IS '创建时间';
COMMENT ON COLUMN t_data_synth_instances.updated_at IS '更新时间';
COMMENT ON COLUMN t_data_synth_instances.created_by IS '创建者';
COMMENT ON COLUMN t_data_synth_instances.updated_by IS '更新者';

-- 数据合成文件任务表
CREATE TABLE IF NOT EXISTS t_data_synthesis_file_instances
(
    id VARCHAR(36) PRIMARY KEY,
    synthesis_instance_id VARCHAR(36),
    file_name VARCHAR(255) NOT NULL,
    source_file_id VARCHAR(255) NOT NULL,
    target_file_location VARCHAR(1000),
    status VARCHAR(20),
    total_chunks INTEGER DEFAULT 0,
    processed_chunks INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

-- 添加注释
COMMENT ON TABLE t_data_synthesis_file_instances IS '数据合成文件任务表（UUID 主键）';
COMMENT ON COLUMN t_data_synthesis_file_instances.id IS 'UUID';
COMMENT ON COLUMN t_data_synthesis_file_instances.synthesis_instance_id IS '数据合成任务ID';
COMMENT ON COLUMN t_data_synthesis_file_instances.file_name IS '文件名';
COMMENT ON COLUMN t_data_synthesis_file_instances.source_file_id IS '原始文件ID';
COMMENT ON COLUMN t_data_synthesis_file_instances.target_file_location IS '目标文件存储位置';
COMMENT ON COLUMN t_data_synthesis_file_instances.status IS '任务状态';
COMMENT ON COLUMN t_data_synthesis_file_instances.total_chunks IS '总文本块数';
COMMENT ON COLUMN t_data_synthesis_file_instances.processed_chunks IS '已处理文本块数';
COMMENT ON COLUMN t_data_synthesis_file_instances.created_at IS '创建时间';
COMMENT ON COLUMN t_data_synthesis_file_instances.updated_at IS '更新时间';
COMMENT ON COLUMN t_data_synthesis_file_instances.created_by IS '创建者';
COMMENT ON COLUMN t_data_synthesis_file_instances.updated_by IS '更新者';

-- 数据合成分块任务表
CREATE TABLE IF NOT EXISTS t_data_synthesis_chunk_instances
(
    id VARCHAR(36) PRIMARY KEY,
    synthesis_file_instance_id VARCHAR(36),
    chunk_index INTEGER,
    chunk_content TEXT,
    metadata JSONB
);

-- 添加注释
COMMENT ON TABLE t_data_synthesis_chunk_instances IS '数据合成分块任务表（UUID 主键）';
COMMENT ON COLUMN t_data_synthesis_chunk_instances.id IS 'UUID';
COMMENT ON COLUMN t_data_synthesis_chunk_instances.synthesis_file_instance_id IS '数据合成文件任务ID';
COMMENT ON COLUMN t_data_synthesis_chunk_instances.chunk_index IS '分块索引';
COMMENT ON COLUMN t_data_synthesis_chunk_instances.chunk_content IS '分块内容';
COMMENT ON COLUMN t_data_synthesis_chunk_instances.metadata IS '分块元数据';

-- 数据合成任务队列表
CREATE TABLE IF NOT EXISTS t_data_synthesis_data
(
    id VARCHAR(36) PRIMARY KEY,
    data JSONB,
    synthesis_file_instance_id VARCHAR(36),
    chunk_instance_id VARCHAR(36)
);

-- 添加注释
COMMENT ON TABLE t_data_synthesis_data IS '数据合成任务队列表（UUID 主键）';
COMMENT ON COLUMN t_data_synthesis_data.id IS 'UUID';
COMMENT ON COLUMN t_data_synthesis_data.data IS '合成的数据';
COMMENT ON COLUMN t_data_synthesis_data.synthesis_file_instance_id IS '数据合成文件任务ID';
COMMENT ON COLUMN t_data_synthesis_data.chunk_instance_id IS '分块任务ID';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_synth_instances_status ON t_data_synth_instances(status);
CREATE INDEX IF NOT EXISTS idx_synth_instances_created_at ON t_data_synth_instances(created_at);
CREATE INDEX IF NOT EXISTS idx_synth_instances_synth_type ON t_data_synth_instances(synth_type);

CREATE INDEX IF NOT EXISTS idx_synth_file_instances_instance ON t_data_synthesis_file_instances(synthesis_instance_id);
CREATE INDEX IF NOT EXISTS idx_synth_file_instances_status ON t_data_synthesis_file_instances(status);
CREATE INDEX IF NOT EXISTS idx_synth_file_instances_source_file ON t_data_synthesis_file_instances(source_file_id);

CREATE INDEX IF NOT EXISTS idx_synth_chunk_instances_file ON t_data_synthesis_chunk_instances(synthesis_file_instance_id);
CREATE INDEX IF NOT EXISTS idx_synth_chunk_instances_index ON t_data_synthesis_chunk_instances(chunk_index);

CREATE INDEX IF NOT EXISTS idx_synth_data_file ON t_data_synthesis_data(synthesis_file_instance_id);
CREATE INDEX IF NOT EXISTS idx_synth_data_chunk ON t_data_synthesis_data(chunk_instance_id);

-- 创建外键约束
ALTER TABLE t_data_synthesis_file_instances ADD CONSTRAINT fk_synth_file_instances_instance
FOREIGN KEY (synthesis_instance_id) REFERENCES t_data_synth_instances(id) ON DELETE CASCADE;

ALTER TABLE t_data_synthesis_chunk_instances ADD CONSTRAINT fk_synth_chunk_instances_file
FOREIGN KEY (synthesis_file_instance_id) REFERENCES t_data_synthesis_file_instances(id) ON DELETE CASCADE;

ALTER TABLE t_data_synthesis_data ADD CONSTRAINT fk_synth_data_file FOREIGN KEY (synthesis_file_instance_id)
REFERENCES t_data_synthesis_file_instances(id) ON DELETE CASCADE;

ALTER TABLE t_data_synthesis_data ADD CONSTRAINT fk_synth_data_chunk FOREIGN KEY (chunk_instance_id)
REFERENCES t_data_synthesis_chunk_instances(id) ON DELETE CASCADE;

-- 创建触发器用于自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
RETURN NEW;
END;
$$ language 'plpgsql';

-- 为有 updated_at 字段的表创建触发器
DROP TRIGGER IF EXISTS update_synth_instances_updated_at ON t_data_synth_instances;
CREATE TRIGGER update_synth_instances_updated_at
    BEFORE UPDATE ON t_data_synth_instances
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_synth_file_instances_updated_at ON t_data_synthesis_file_instances;
CREATE TRIGGER update_synth_file_instances_updated_at
    BEFORE UPDATE ON t_data_synthesis_file_instances
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
