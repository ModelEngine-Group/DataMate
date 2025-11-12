-- DataMate Platform 数据库初始化脚本
-- 适用于现有datamate数据库环境

-- 使用现有的datamate数据库
USE datamate;

-- 删除已存在的表（如果需要重新创建）
-- 原有表名保留，但本脚本新建以 t_dm_ 为前缀的新表，并使用 UUID 主键
-- 可按需手工迁移旧数据到新表

-- ===========================================
-- 数据管理（Data Management）模块表（UUID 主键，t_dm_ 前缀）
-- ===========================================

-- 数据集表（支持医学影像、文本、问答等多种类型）
CREATE TABLE IF NOT EXISTS t_dm_datasets (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID',
    name VARCHAR(255) NOT NULL COMMENT '数据集名称',
    description TEXT COMMENT '数据集描述',
    dataset_type VARCHAR(50) NOT NULL COMMENT '数据集类型：IMAGE/TEXT/QA/MULTIMODAL/OTHER',
    category VARCHAR(100) COMMENT '数据集分类：医学影像/问答/文献等',
    path VARCHAR(500) COMMENT '数据存储路径',
    format VARCHAR(50) COMMENT '数据格式：DCM/JPG/JSON/CSV等',
    schema_info JSON COMMENT '数据结构信息',
    size_bytes BIGINT DEFAULT 0 COMMENT '数据大小(字节)',
    file_count BIGINT DEFAULT 0 COMMENT '文件数量',
    record_count BIGINT DEFAULT 0 COMMENT '记录数量',
    retention_days INTEGER DEFAULT 0 COMMENT '数据保留天数（0表示长期保留）',
    tags JSON COMMENT '标签列表',
    metadata JSON COMMENT '元数据信息',
    status VARCHAR(50) DEFAULT 'DRAFT' COMMENT '状态：DRAFT/ACTIVE/ARCHIVED',
    is_public BOOLEAN DEFAULT FALSE COMMENT '是否公开',
    is_featured BOOLEAN DEFAULT FALSE COMMENT '是否推荐',
    version BIGINT NOT NULL DEFAULT 0 COMMENT '版本号',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(255) COMMENT '创建者',
    updated_by VARCHAR(255) COMMENT '更新者',
    INDEX idx_dm_dataset_type (dataset_type),
    INDEX idx_dm_category (category),
    INDEX idx_dm_format (format),
    INDEX idx_dm_status (status),
    INDEX idx_dm_public (is_public),
    INDEX idx_dm_featured (is_featured),
    INDEX idx_dm_created_at (created_at)
) COMMENT='数据集表（UUID 主键）';

-- 数据集文件表
CREATE TABLE IF NOT EXISTS t_dm_dataset_files (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID',
    dataset_id VARCHAR(36) NOT NULL COMMENT '所属数据集ID（UUID）',
    file_name VARCHAR(255) NOT NULL COMMENT '文件名',
    file_path VARCHAR(1000) NOT NULL COMMENT '文件路径',
    file_type VARCHAR(50) COMMENT '文件格式：JPG/PNG/DCM/TXT等',
    file_size BIGINT DEFAULT 0 COMMENT '文件大小(字节)',
    check_sum VARCHAR(64) COMMENT '文件校验和',
    tags      JSON COMMENT '文件标签信息',
    tags_updated_at TIMESTAMP NULL COMMENT '标签最后更新时间',
    metadata JSON COMMENT '文件元数据',
    status VARCHAR(50) DEFAULT 'ACTIVE' COMMENT '文件状态：ACTIVE/DELETED/PROCESSING',
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
    last_access_time TIMESTAMP NULL COMMENT '最后访问时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (dataset_id) REFERENCES t_dm_datasets(id) ON DELETE CASCADE,
    INDEX idx_dm_dataset (dataset_id),
    INDEX idx_dm_file_type (file_type),
    INDEX idx_dm_file_status (status),
    INDEX idx_dm_upload_time (upload_time)
) COMMENT='数据集文件表（UUID 主键）';

-- 数据集统计信息表
CREATE TABLE IF NOT EXISTS t_dm_dataset_statistics (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID',
    dataset_id VARCHAR(36) NOT NULL COMMENT '数据集ID（UUID）',
    stat_date DATE NOT NULL COMMENT '统计日期',
    total_files BIGINT DEFAULT 0 COMMENT '总文件数',
    total_size BIGINT DEFAULT 0 COMMENT '总大小(字节)',
    processed_files BIGINT DEFAULT 0 COMMENT '已处理文件数',
    error_files BIGINT DEFAULT 0 COMMENT '错误文件数',
    download_count BIGINT DEFAULT 0 COMMENT '下载次数',
    view_count BIGINT DEFAULT 0 COMMENT '查看次数',
    quality_metrics JSON COMMENT '质量指标',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (dataset_id) REFERENCES t_dm_datasets(id) ON DELETE CASCADE,
    UNIQUE KEY uk_dm_dataset_date (dataset_id, stat_date),
    INDEX idx_dm_stat_date (stat_date)
) COMMENT='数据集统计信息表（UUID 主键）';

-- 标签表
CREATE TABLE IF NOT EXISTS t_dm_tags (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID',
    name VARCHAR(100) NOT NULL UNIQUE COMMENT '标签名称',
    description TEXT COMMENT '标签描述',
    category VARCHAR(50) COMMENT '标签分类',
    color VARCHAR(7) COMMENT '标签颜色(十六进制)',
    usage_count BIGINT DEFAULT 0 COMMENT '使用次数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_dm_tag_category (category),
    INDEX idx_dm_tag_usage_count (usage_count)
) COMMENT='标签表（UUID 主键）';

-- 数据集标签关联表
CREATE TABLE IF NOT EXISTS t_dm_dataset_tags (
    dataset_id VARCHAR(36) NOT NULL COMMENT '数据集ID（UUID）',
    tag_id VARCHAR(36) NOT NULL COMMENT '标签ID（UUID）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (dataset_id, tag_id),
    FOREIGN KEY (dataset_id) REFERENCES t_dm_datasets(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES t_dm_tags(id) ON DELETE CASCADE
) COMMENT='数据集标签关联表（UUID 外键）';

-- ===========================================
-- 非数据管理表（如 users、t_data_sources）保持不变
-- ===========================================

-- 用户表（如果不存在）
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(255) NOT NULL UNIQUE COMMENT '用户名',
    email VARCHAR(255) NOT NULL UNIQUE COMMENT '邮箱',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    full_name VARCHAR(255) COMMENT '真实姓名',
    avatar_url VARCHAR(500) COMMENT '头像URL',
    role VARCHAR(50) NOT NULL DEFAULT 'USER' COMMENT '角色：ADMIN/USER',
    organization VARCHAR(255) COMMENT '所属机构',
    enabled BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
    last_login_at TIMESTAMP NULL COMMENT '最后登录时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (role),
    INDEX idx_enabled (enabled)
) COMMENT='用户表';

-- 插入初始数据

-- 插入默认用户
INSERT IGNORE INTO users (username, email, password_hash, full_name, role, organization) VALUES
('admin', 'admin@datamate.com', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7q7U3.XUO', '系统管理员', 'ADMIN', 'DataMate'),
('knowledge_user', 'knowledge@datamate.com', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7q7U3.XUO', '知识库用户', 'USER', '三甲医院');

-- 创建视图：数据集统计摘要（引用新表）
CREATE OR REPLACE VIEW v_dm_dataset_summary AS
SELECT
    COUNT(*) as total_datasets,
    SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) as active_datasets,
    SUM(CASE WHEN is_public = TRUE THEN 1 ELSE 0 END) as public_datasets,
    SUM(CASE WHEN is_featured = TRUE THEN 1 ELSE 0 END) as featured_datasets,
    SUM(file_count) as total_files,
    SUM(record_count) as total_records,
    COUNT(DISTINCT dataset_type) as dataset_types,
    COUNT(DISTINCT category) as categories
FROM t_dm_datasets;
