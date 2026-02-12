-- 使用现有的datamate数据库
\c datamate;
-- 数据集表
CREATE TABLE IF NOT EXISTS t_dm_datasets (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    dataset_type VARCHAR(50) NOT NULL,
    category VARCHAR(100),
    path VARCHAR(500),
    format VARCHAR(50),
    schema_info JSONB,
    size_bytes BIGINT DEFAULT 0,
    file_count BIGINT DEFAULT 0,
    record_count BIGINT DEFAULT 0,
    retention_days INTEGER DEFAULT 0,
    tags JSONB,
    metadata JSONB,
    status VARCHAR(50) DEFAULT 'DRAFT',
    is_public BOOLEAN DEFAULT FALSE,
    is_featured BOOLEAN DEFAULT FALSE,
    version BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

COMMENT ON TABLE t_dm_datasets IS '数据集表（UUID 主键）';
COMMENT ON COLUMN t_dm_datasets.id IS 'UUID';
COMMENT ON COLUMN t_dm_datasets.name IS '数据集名称';
COMMENT ON COLUMN t_dm_datasets.description IS '数据集描述';
COMMENT ON COLUMN t_dm_datasets.dataset_type IS '数据集类型：IMAGE/TEXT/QA/MULTIMODAL/OTHER';
COMMENT ON COLUMN t_dm_datasets.category IS '数据集分类：医学影像/问答/文献等';
COMMENT ON COLUMN t_dm_datasets.path IS '数据存储路径';
COMMENT ON COLUMN t_dm_datasets.format IS '数据格式：DCM/JPG/JSON/CSV等';
COMMENT ON COLUMN t_dm_datasets.schema_info IS '数据结构信息';
COMMENT ON COLUMN t_dm_datasets.size_bytes IS '数据大小(字节)';
COMMENT ON COLUMN t_dm_datasets.file_count IS '文件数量';
COMMENT ON COLUMN t_dm_datasets.record_count IS '记录数量';
COMMENT ON COLUMN t_dm_datasets.retention_days IS '数据保留天数（0表示长期保留）';
COMMENT ON COLUMN t_dm_datasets.tags IS '标签列表';
COMMENT ON COLUMN t_dm_datasets.metadata IS '元数据信息';
COMMENT ON COLUMN t_dm_datasets.status IS '状态：DRAFT/ACTIVE/ARCHIVED';
COMMENT ON COLUMN t_dm_datasets.is_public IS '是否公开';
COMMENT ON COLUMN t_dm_datasets.is_featured IS '是否推荐';
COMMENT ON COLUMN t_dm_datasets.version IS '版本号';
COMMENT ON COLUMN t_dm_datasets.created_at IS '创建时间';
COMMENT ON COLUMN t_dm_datasets.updated_at IS '更新时间';
COMMENT ON COLUMN t_dm_datasets.created_by IS '创建者';
COMMENT ON COLUMN t_dm_datasets.updated_by IS '更新者';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_dm_dataset_type ON t_dm_datasets(dataset_type);
CREATE INDEX IF NOT EXISTS idx_dm_category ON t_dm_datasets(category);
CREATE INDEX IF NOT EXISTS idx_dm_format ON t_dm_datasets(format);
CREATE INDEX IF NOT EXISTS idx_dm_status ON t_dm_datasets(status);
CREATE INDEX IF NOT EXISTS idx_dm_public ON t_dm_datasets(is_public);
CREATE INDEX IF NOT EXISTS idx_dm_featured ON t_dm_datasets(is_featured);
CREATE INDEX IF NOT EXISTS idx_dm_created_at ON t_dm_datasets(created_at);

-- 创建触发器用于自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_t_dm_datasets_updated_at ON t_dm_datasets;
CREATE TRIGGER update_t_dm_datasets_updated_at
    BEFORE UPDATE ON t_dm_datasets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 数据集文件表
CREATE TABLE IF NOT EXISTS t_dm_dataset_files (
    id VARCHAR(36) PRIMARY KEY,
    dataset_id VARCHAR(36) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_type VARCHAR(50),
    file_size BIGINT DEFAULT 0,
    check_sum VARCHAR(64),
    tags JSONB,
    tags_updated_at TIMESTAMP,
    annotation JSONB,
    metadata JSONB,
    status VARCHAR(50) DEFAULT 'ACTIVE',
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_access_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE t_dm_dataset_files IS '数据集文件表（UUID 主键）';
COMMENT ON COLUMN t_dm_dataset_files.id IS 'UUID';
COMMENT ON COLUMN t_dm_dataset_files.dataset_id IS '所属数据集ID（UUID）';
COMMENT ON COLUMN t_dm_dataset_files.file_name IS '文件名';
COMMENT ON COLUMN t_dm_dataset_files.file_path IS '文件路径';
COMMENT ON COLUMN t_dm_dataset_files.file_type IS '文件格式：JPG/PNG/DCM/TXT等';
COMMENT ON COLUMN t_dm_dataset_files.file_size IS '文件大小(字节)';
COMMENT ON COLUMN t_dm_dataset_files.check_sum IS '文件校验和';
COMMENT ON COLUMN t_dm_dataset_files.tags IS '文件标签信息（结构化标签/标注概要）';
COMMENT ON COLUMN t_dm_dataset_files.tags_updated_at IS '标签最后更新时间';
COMMENT ON COLUMN t_dm_dataset_files.annotation IS '完整标注结果（原始JSON）';
COMMENT ON COLUMN t_dm_dataset_files.metadata IS '文件元数据';
COMMENT ON COLUMN t_dm_dataset_files.status IS '文件状态：ACTIVE/DELETED/PROCESSING';
COMMENT ON COLUMN t_dm_dataset_files.upload_time IS '上传时间';
COMMENT ON COLUMN t_dm_dataset_files.last_access_time IS '最后访问时间';
COMMENT ON COLUMN t_dm_dataset_files.created_at IS '创建时间';
COMMENT ON COLUMN t_dm_dataset_files.updated_at IS '更新时间';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_dm_dataset ON t_dm_dataset_files(dataset_id);
CREATE INDEX IF NOT EXISTS idx_dm_file_type ON t_dm_dataset_files(file_type);
CREATE INDEX IF NOT EXISTS idx_dm_file_status ON t_dm_dataset_files(status);
CREATE INDEX IF NOT EXISTS idx_dm_upload_time ON t_dm_dataset_files(upload_time);

-- 外键约束
ALTER TABLE t_dm_dataset_files
    ADD CONSTRAINT fk_dm_dataset_files_dataset
    FOREIGN KEY (dataset_id)
    REFERENCES t_dm_datasets(id)
    ON DELETE CASCADE;

-- 创建触发器
DROP TRIGGER IF EXISTS update_t_dm_dataset_files_updated_at ON t_dm_dataset_files;
CREATE TRIGGER update_t_dm_dataset_files_updated_at
    BEFORE UPDATE ON t_dm_dataset_files
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 数据集统计信息表
CREATE TABLE IF NOT EXISTS t_dm_dataset_statistics (
    id VARCHAR(36) PRIMARY KEY,
    dataset_id VARCHAR(36) NOT NULL,
    stat_date DATE NOT NULL,
    total_files BIGINT DEFAULT 0,
    total_size BIGINT DEFAULT 0,
    processed_files BIGINT DEFAULT 0,
    error_files BIGINT DEFAULT 0,
    download_count BIGINT DEFAULT 0,
    view_count BIGINT DEFAULT 0,
    quality_metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE t_dm_dataset_statistics IS '数据集统计信息表（UUID 主键）';
COMMENT ON COLUMN t_dm_dataset_statistics.id IS 'UUID';
COMMENT ON COLUMN t_dm_dataset_statistics.dataset_id IS '数据集ID（UUID）';
COMMENT ON COLUMN t_dm_dataset_statistics.stat_date IS '统计日期';
COMMENT ON COLUMN t_dm_dataset_statistics.total_files IS '总文件数';
COMMENT ON COLUMN t_dm_dataset_statistics.total_size IS '总大小(字节)';
COMMENT ON COLUMN t_dm_dataset_statistics.processed_files IS '已处理文件数';
COMMENT ON COLUMN t_dm_dataset_statistics.error_files IS '错误文件数';
COMMENT ON COLUMN t_dm_dataset_statistics.download_count IS '下载次数';
COMMENT ON COLUMN t_dm_dataset_statistics.view_count IS '查看次数';
COMMENT ON COLUMN t_dm_dataset_statistics.quality_metrics IS '质量指标';
COMMENT ON COLUMN t_dm_dataset_statistics.created_at IS '创建时间';
COMMENT ON COLUMN t_dm_dataset_statistics.updated_at IS '更新时间';

-- 创建唯一约束和索引
ALTER TABLE t_dm_dataset_statistics
    ADD CONSTRAINT uk_dm_dataset_date
    UNIQUE (dataset_id, stat_date);

CREATE INDEX IF NOT EXISTS idx_dm_stat_date ON t_dm_dataset_statistics(stat_date);

-- 外键约束
ALTER TABLE t_dm_dataset_statistics
    ADD CONSTRAINT fk_dm_dataset_statistics_dataset
    FOREIGN KEY (dataset_id)
    REFERENCES t_dm_datasets(id)
    ON DELETE CASCADE;

-- 创建触发器
DROP TRIGGER IF EXISTS update_t_dm_dataset_statistics_updated_at ON t_dm_dataset_statistics;
CREATE TRIGGER update_t_dm_dataset_statistics_updated_at
    BEFORE UPDATE ON t_dm_dataset_statistics
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 标签表
CREATE TABLE IF NOT EXISTS t_dm_tags (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(50),
    color VARCHAR(7),
    usage_count BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

COMMENT ON TABLE t_dm_tags IS '标签表（UUID 主键）';
COMMENT ON COLUMN t_dm_tags.id IS 'UUID';
COMMENT ON COLUMN t_dm_tags.name IS '标签名称';
COMMENT ON COLUMN t_dm_tags.description IS '标签描述';
COMMENT ON COLUMN t_dm_tags.category IS '标签分类';
COMMENT ON COLUMN t_dm_tags.color IS '标签颜色(十六进制)';
COMMENT ON COLUMN t_dm_tags.usage_count IS '使用次数';
COMMENT ON COLUMN t_dm_tags.created_at IS '创建时间';
COMMENT ON COLUMN t_dm_tags.updated_at IS '更新时间';
COMMENT ON COLUMN t_dm_tags.created_by IS '创建者';
COMMENT ON COLUMN t_dm_tags.updated_by IS '更新者';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_dm_tag_category ON t_dm_tags(category);
CREATE INDEX IF NOT EXISTS idx_dm_tag_usage_count ON t_dm_tags(usage_count);

-- 创建触发器
DROP TRIGGER IF EXISTS update_t_dm_tags_updated_at ON t_dm_tags;
CREATE TRIGGER update_t_dm_tags_updated_at
    BEFORE UPDATE ON t_dm_tags
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 数据集标签关联表
CREATE TABLE IF NOT EXISTS t_dm_dataset_tags (
    dataset_id VARCHAR(36) NOT NULL,
    tag_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (dataset_id, tag_id)
);

COMMENT ON TABLE t_dm_dataset_tags IS '数据集标签关联表（UUID 外键）';
COMMENT ON COLUMN t_dm_dataset_tags.dataset_id IS '数据集ID（UUID）';
COMMENT ON COLUMN t_dm_dataset_tags.tag_id IS '标签ID（UUID）';
COMMENT ON COLUMN t_dm_dataset_tags.created_at IS '创建时间';

-- 外键约束
ALTER TABLE t_dm_dataset_tags
    ADD CONSTRAINT fk_dm_dataset_tags_dataset
    FOREIGN KEY (dataset_id)
    REFERENCES t_dm_datasets(id)
    ON DELETE CASCADE;

ALTER TABLE t_dm_dataset_tags
    ADD CONSTRAINT fk_dm_dataset_tags_tag
    FOREIGN KEY (tag_id)
    REFERENCES t_dm_tags(id)
    ON DELETE CASCADE;

-- ===========================================
-- 非数据管理表
-- ===========================================

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    avatar_url VARCHAR(500),
    role VARCHAR(50) NOT NULL DEFAULT 'USER',
    organization VARCHAR(255),
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE users IS '用户表';
COMMENT ON COLUMN users.id IS '主键ID';
COMMENT ON COLUMN users.username IS '用户名';
COMMENT ON COLUMN users.email IS '邮箱';
COMMENT ON COLUMN users.password_hash IS '密码哈希';
COMMENT ON COLUMN users.full_name IS '真实姓名';
COMMENT ON COLUMN users.avatar_url IS '头像URL';
COMMENT ON COLUMN users.role IS '角色：ADMIN/USER';
COMMENT ON COLUMN users.organization IS '所属机构';
COMMENT ON COLUMN users.enabled IS '是否启用';
COMMENT ON COLUMN users.last_login_at IS '最后登录时间';
COMMENT ON COLUMN users.created_at IS '创建时间';
COMMENT ON COLUMN users.updated_at IS '更新时间';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_enabled ON users(enabled);

-- 创建触发器
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 插入初始数据
INSERT INTO users (username, email, password_hash, full_name, role, organization)
VALUES
    ('admin', 'admin@datamate.com', '$2a$10$/esawo436yxg2eodpl/JJ.3Xu6y9m91/ihXRHie9al.LUoNQR5fF.', '系统管理员', 'ADMIN', 'DataMate')
ON CONFLICT (username) DO NOTHING;

-- 创建视图：数据集统计摘要
CREATE OR REPLACE VIEW v_dm_dataset_summary AS
SELECT
    COUNT(*) as total_datasets,
    SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) as active_datasets,
    SUM(CASE WHEN is_public = TRUE THEN 1 ELSE 0 END) as public_datasets,
    SUM(CASE WHEN is_featured = TRUE THEN 1 ELSE 0 END) as featured_datasets,
    COALESCE(SUM(file_count), 0) as total_files,
    COALESCE(SUM(record_count), 0) as total_records,
    COUNT(DISTINCT dataset_type) as dataset_types,
    COUNT(DISTINCT category) as categories
FROM t_dm_datasets;
