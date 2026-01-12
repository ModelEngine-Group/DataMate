-- 使用现有的datamate数据库
\c datamate;

-- 配比实例表
CREATE TABLE IF NOT EXISTS t_st_ratio_instances
(
    id                  VARCHAR(64) PRIMARY KEY,
    name                VARCHAR(64),
    description         TEXT,
    target_dataset_id   VARCHAR(64),
    ratio_parameters    JSONB,
    merge_method        VARCHAR(50),
    status              VARCHAR(20),
    totals              BIGINT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by          VARCHAR(255),
    updated_by          VARCHAR(255)
);

-- 添加注释
COMMENT ON TABLE t_st_ratio_instances IS '配比实例表（UUID 主键）';
COMMENT ON COLUMN t_st_ratio_instances.id IS 'UUID';
COMMENT ON COLUMN t_st_ratio_instances.name IS '名称';
COMMENT ON COLUMN t_st_ratio_instances.description IS '描述';
COMMENT ON COLUMN t_st_ratio_instances.target_dataset_id IS '模板数据集ID';
COMMENT ON COLUMN t_st_ratio_instances.ratio_parameters IS '配比参数';
COMMENT ON COLUMN t_st_ratio_instances.merge_method IS '合并方式';
COMMENT ON COLUMN t_st_ratio_instances.status IS '状态';
COMMENT ON COLUMN t_st_ratio_instances.totals IS '总数';
COMMENT ON COLUMN t_st_ratio_instances.created_at IS '创建时间';
COMMENT ON COLUMN t_st_ratio_instances.updated_at IS '更新时间';
COMMENT ON COLUMN t_st_ratio_instances.created_by IS '创建者';
COMMENT ON COLUMN t_st_ratio_instances.updated_by IS '更新者';

-- 配比关系表
CREATE TABLE IF NOT EXISTS t_st_ratio_relations
(
    id                  VARCHAR(64) PRIMARY KEY,
    ratio_instance_id   VARCHAR(64),
    source_dataset_id   VARCHAR(64),
    ratio_value         VARCHAR(256),
    counts              BIGINT,
    filter_conditions   TEXT,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by          VARCHAR(255),
    updated_by          VARCHAR(255)
);

-- 添加注释
COMMENT ON TABLE t_st_ratio_relations IS '配比关系表（UUID 主键）';
COMMENT ON COLUMN t_st_ratio_relations.id IS 'UUID';
COMMENT ON COLUMN t_st_ratio_relations.ratio_instance_id IS '配比实例ID';
COMMENT ON COLUMN t_st_ratio_relations.source_dataset_id IS '源数据集ID';
COMMENT ON COLUMN t_st_ratio_relations.ratio_value IS '配比值';
COMMENT ON COLUMN t_st_ratio_relations.counts IS '条数';
COMMENT ON COLUMN t_st_ratio_relations.filter_conditions IS '过滤条件';
COMMENT ON COLUMN t_st_ratio_relations.created_at IS '创建时间';
COMMENT ON COLUMN t_st_ratio_relations.updated_at IS '更新时间';
COMMENT ON COLUMN t_st_ratio_relations.created_by IS '创建者';
COMMENT ON COLUMN t_st_ratio_relations.updated_by IS '更新者';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_st_ratio_instances_target_dataset ON t_st_ratio_instances(target_dataset_id);
CREATE INDEX IF NOT EXISTS idx_st_ratio_instances_status ON t_st_ratio_instances(status);
CREATE INDEX IF NOT EXISTS idx_st_ratio_instances_created_at ON t_st_ratio_instances(created_at);

CREATE INDEX IF NOT EXISTS idx_st_ratio_relations_instance ON t_st_ratio_relations(ratio_instance_id);
CREATE INDEX IF NOT EXISTS idx_st_ratio_relations_source_dataset ON t_st_ratio_relations(source_dataset_id);
CREATE INDEX IF NOT EXISTS idx_st_ratio_relations_created_at ON t_st_ratio_relations(created_at);

-- 创建外键约束
ALTER TABLE t_st_ratio_relations ADD CONSTRAINT fk_st_ratio_relations_instance FOREIGN KEY (ratio_instance_id)
REFERENCES t_st_ratio_instances(id) ON DELETE CASCADE;

-- 创建触发器用于自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
RETURN NEW;
END;
$$ language 'plpgsql';

-- 为各个表创建触发器
DROP TRIGGER IF EXISTS update_st_ratio_instances_updated_at ON t_st_ratio_instances;
CREATE TRIGGER update_st_ratio_instances_updated_at
    BEFORE UPDATE ON t_st_ratio_instances
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_st_ratio_relations_updated_at ON t_st_ratio_relations;
CREATE TRIGGER update_st_ratio_relations_updated_at
    BEFORE UPDATE ON t_st_ratio_relations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
