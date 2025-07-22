-- 数据集表结构
CREATE TABLE IF NOT EXISTS t_dataset
(
    id           BIGSERIAL PRIMARY KEY,
    name         VARCHAR(255) NOT NULL,
    description  TEXT,
    type         VARCHAR(100),
    schedule_config VARCHAR(4096),
    src_config   VARCHAR(4096),
    src_type     VARCHAR(50),
    des_config   VARCHAR(4096),
    des_type     VARCHAR(50),
    status       VARCHAR(50),
    parent_id    BIGINT,
    created_time TIMESTAMP    NOT NULL DEFAULT NOW(),
    created_by   VARCHAR(255),
    updated_time TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_by   VARCHAR(255)
);

CREATE OR REPLACE TRIGGER trg_dataset_updated_time BEFORE UPDATE ON t_dataset FOR EACH ROW EXECUTE FUNCTION update_time();

CREATE INDEX idx_dataset_name ON t_dataset (name);
CREATE INDEX idx_dataset_parent_id ON t_dataset (parent_id);
CREATE INDEX idx_dataset_status ON t_dataset (status);


-- 表注释
COMMENT ON TABLE t_dataset IS '系统数据集主表';

-- 列注释
COMMENT ON COLUMN t_dataset.id IS '数据集唯一标识';
COMMENT ON COLUMN t_dataset.name IS '数据集名称（唯一）';
COMMENT ON COLUMN t_dataset.description IS '数据集详细描述';
COMMENT ON COLUMN t_dataset.type IS '数据集分类类型';
COMMENT ON COLUMN t_dataset.status IS '数据集状态：启用/禁用/归档';
COMMENT ON COLUMN t_dataset.parent_id IS '父级数据集ID（用于构建层级关系）';
COMMENT ON COLUMN t_dataset.created_time IS '数据集创建时间';
COMMENT ON COLUMN t_dataset.created_by IS '数据集创建人';
COMMENT ON COLUMN t_dataset.updated_time IS '数据集最后更新时间';
COMMENT ON COLUMN t_dataset.updated_by IS '数据集最后更新人';

-- 索引注释
COMMENT ON INDEX idx_dataset_name IS '数据集名称索引';
COMMENT ON INDEX idx_dataset_parent_id IS '父级数据集关联索引';
COMMENT ON INDEX idx_dataset_status IS '数据集状态筛选索引';

CREATE TABLE IF NOT EXISTS t_dataset_file
(
    id           BIGSERIAL PRIMARY KEY,
    dataset_id   BIGINT       NOT NULL,
    name         VARCHAR(255) NOT NULL,
    path         VARCHAR(512) NOT NULL,
    size         BIGINT       NOT NULL,
    type         VARCHAR(50),
    status       VARCHAR(50),
    parent_id    BIGINT,
    hash         VARCHAR(64),
    source_file  VARCHAR(4096),
    created_time TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_time TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE TRIGGER trg_dataset_file_updated_time BEFORE UPDATE ON t_dataset_file FOR EACH ROW EXECUTE FUNCTION update_time();

CREATE INDEX idx_dataset_file_dataset_id ON t_dataset_file (dataset_id);