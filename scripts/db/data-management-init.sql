-- Data-Engine Platform 数据库初始化脚本
-- 适用于现有knowledge_base数据库环境

-- 使用现有的knowledge_base数据库
USE knowledge_base;

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
    data_source_id BIGINT COMMENT '关联数据源ID（保留为数值型）',
    path VARCHAR(500) COMMENT '数据存储路径',
    format VARCHAR(50) COMMENT '数据格式：DCM/JPG/JSON/CSV等',
    schema_info JSON COMMENT '数据结构信息',
    size_bytes BIGINT DEFAULT 0 COMMENT '数据大小(字节)',
    file_count BIGINT DEFAULT 0 COMMENT '文件数量',
    record_count BIGINT DEFAULT 0 COMMENT '记录数量',
    completion_rate DECIMAL(5,2) DEFAULT 0.00 COMMENT '完成率(%)',
    quality_score DECIMAL(5,2) DEFAULT 0.00 COMMENT '质量评分',
    tags JSON COMMENT '标签列表',
    metadata JSON COMMENT '元数据信息',
    status VARCHAR(50) DEFAULT 'DRAFT' COMMENT '状态：DRAFT/ACTIVE/ARCHIVED',
    is_public BOOLEAN DEFAULT FALSE COMMENT '是否公开',
    is_featured BOOLEAN DEFAULT FALSE COMMENT '是否推荐',
    download_count BIGINT DEFAULT 0 COMMENT '下载次数',
    view_count BIGINT DEFAULT 0 COMMENT '查看次数',
    version BIGINT NOT NULL DEFAULT 0 COMMENT '版本号',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(255) COMMENT '创建者',
    updated_by VARCHAR(255) COMMENT '更新者',
    FOREIGN KEY (data_source_id) REFERENCES data_sources(id) ON DELETE SET NULL,
    INDEX idx_dm_dataset_type (dataset_type),
    INDEX idx_dm_category (category),
    INDEX idx_dm_data_source (data_source_id),
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
    file_type VARCHAR(50) COMMENT '文件类型：IMAGE/TEXT/VIDEO/AUDIO等',
    file_format VARCHAR(50) COMMENT '文件格式：JPG/PNG/DCM/TXT等',
    file_size BIGINT DEFAULT 0 COMMENT '文件大小(字节)',
    checksum VARCHAR(64) COMMENT '文件校验和',
    mime_type VARCHAR(100) COMMENT 'MIME类型',
    metadata JSON COMMENT '文件元数据',
    status VARCHAR(50) DEFAULT 'ACTIVE' COMMENT '文件状态：ACTIVE/DELETED/PROCESSING',
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
    last_access_time TIMESTAMP NULL COMMENT '最后访问时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (dataset_id) REFERENCES t_dm_datasets(id) ON DELETE CASCADE,
    INDEX idx_dm_dataset (dataset_id),
    INDEX idx_dm_file_type (file_type),
    INDEX idx_dm_file_format (file_format),
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
-- 非数据管理表（如 users、data_sources）保持不变
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
('admin', 'admin@dataengine.com', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7q7U3.XUO', '系统管理员', 'ADMIN', 'Data-Engine'),
('knowledge_user', 'knowledge@dataengine.com', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iAt6Z5EHsM8lE9lBOsl7q7U3.XUO', '知识库用户', 'USER', '三甲医院');

-- 插入默认数据源
INSERT IGNORE INTO data_sources (name, description, type, host, port, database_name, username, enabled) VALUES 
('知识库MySQL', '知识库MySQL数据库连接', 'MYSQL', 'localhost', 3306, 'knowledge_base', 'knowledge_user', TRUE),
('本地文件系统', '本地文件系统数据源', 'FILE_SYSTEM', NULL, NULL, NULL, NULL, TRUE),
('MinIO存储', 'MinIO对象存储服务', 'MINIO', 'localhost', 9000, NULL, 'admin', TRUE),
('医学影像PACS', 'PACS医学影像存储系统', 'PACS', 'pacs.hospital.com', 104, NULL, 'pacs_user', TRUE);

-- 插入默认标签
INSERT IGNORE INTO t_dm_tags (id, name, description, category, color) VALUES 
('0f3a0c2e-7b1d-4b8f-9e7a-1a2b3c4d5e6f', 'WSI', '全切片图像', '医学影像', '#FF6B6B'),
('1a2b3c4d-5e6f-7a8b-9c0d-1234567890ab', '病理', '病理学相关', '医学', '#4ECDC4'),
('2b3c4d5e-6f7a-8b9c-0d1e-234567890abc', '肺癌', '肺癌相关数据', '疾病', '#45B7D1'),
('3c4d5e6f-7a8b-9c0d-1e2f-34567890abcd', '问答', '问答对数据', '文本', '#96CEB4'),
('4d5e6f7a-8b9c-0d1e-2f3a-4567890abcde', '医学', '医学领域', '领域', '#FFEAA7'),
('5e6f7a8b-9c0d-1e2f-3a4b-567890abcdef', 'NLP', '自然语言处理', '技术', '#DDA0DD'),
('6f7a8b9c-0d1e-2f3a-4b5c-67890abcdef1', '数学', '数学推理', '学科', '#98D8C8'),
('7a8b9c0d-1e2f-3a4b-5c6d-7890abcdef12', 'GSM8K', '小学数学问题', '数据集', '#F7DC6F'),
('8b9c0d1e-2f3a-4b5c-6d7e-890abcdef123', '高质量', '高质量数据集', '质量', '#82E0AA'),
('9c0d1e2f-3a4b-5c6d-7e8f-90abcdef1234', '已验证', '已验证数据', '状态', '#85C1E9');

-- 插入示例数据集
INSERT IGNORE INTO t_dm_datasets (id, name, description, dataset_type, category, data_source_id, format, file_count, record_count, completion_rate, quality_score, status, is_public, is_featured) VALUES 
('11111111-1111-1111-1111-111111111111', '肺癌WSI病理图像数据集', '来自三甲医院的肺癌全切片病理图像，包含详细的病理标注信息', 'IMAGE', '医学影像', 1, 'WSI', 1247, 1205, 94.20, 96.80, 'ACTIVE', TRUE, TRUE),
('22222222-2222-2222-2222-222222222222', '肺癌WSI诊断数据集A', '基于肺癌WSI数据集生成的诊断数据集', 'IMAGE', '医学影像', 1, 'WSI', 850, 0, 0.00, 0.00, 'DRAFT', FALSE, FALSE),
('33333333-3333-3333-3333-333333333333', '肺癌WSI诊断数据集B', '基于肺癌WSI数据集生成的诊断数据集', 'IMAGE', '医学影像', 1, 'WSI', 650, 0, 0.00, 0.00, 'DRAFT', FALSE, FALSE),
('44444444-4444-4444-4444-444444444444', '医学问答对数据集', '包含医学领域的高质量问答对，并行开展医学领域系统训练', 'QA', '问答', 1, 'JSON', 50000, 50000, 97.00, 97.00, 'ACTIVE', TRUE, TRUE),
('55555555-5555-5555-5555-555555555555', '医学文献摘要数据集', '包含10万篇高质量医学文献摘要，用于医学文本分类和摘要任务', 'TEXT', '文献', 1, 'JSON', 100000, 95000, 95.00, 95.00, 'ACTIVE', TRUE, FALSE),
('66666666-6666-6666-6666-666666666666', 'GSM8K数学推理数据集', '包含小学数学应用题的推理数据集，并开展数学推理能力训练', 'TEXT', '数学', 1, 'JSON', 8500, 8500, 96.00, 96.00, 'ACTIVE', FALSE, FALSE);

-- 插入数据集标签关联
INSERT IGNORE INTO t_dm_dataset_tags (dataset_id, tag_id) VALUES 
('11111111-1111-1111-1111-111111111111', '0f3a0c2e-7b1d-4b8f-9e7a-1a2b3c4d5e6f'), ('11111111-1111-1111-1111-111111111111', '1a2b3c4d-5e6f-7a8b-9c0d-1234567890ab'), ('11111111-1111-1111-1111-111111111111', '2b3c4d5e-6f7a-8b9c-0d1e-234567890abc'), ('11111111-1111-1111-1111-111111111111', '4d5e6f7a-8b9c-0d1e-2f3a-4567890abcde'), ('11111111-1111-1111-1111-111111111111', '8b9c0d1e-2f3a-4b5c-6d7e-890abcdef123'), ('11111111-1111-1111-1111-111111111111', '9c0d1e2f-3a4b-5c6d-7e8f-90abcdef1234'),
('22222222-2222-2222-2222-222222222222', '0f3a0c2e-7b1d-4b8f-9e7a-1a2b3c4d5e6f'), ('22222222-2222-2222-2222-222222222222', '1a2b3c4d-5e6f-7a8b-9c0d-1234567890ab'), ('22222222-2222-2222-2222-222222222222', '2b3c4d5e-6f7a-8b9c-0d1e-234567890abc'), ('22222222-2222-2222-2222-222222222222', '4d5e6f7a-8b9c-0d1e-2f3a-4567890abcde'),
('33333333-3333-3333-3333-333333333333', '0f3a0c2e-7b1d-4b8f-9e7a-1a2b3c4d5e6f'), ('33333333-3333-3333-3333-333333333333', '1a2b3c4d-5e6f-7a8b-9c0d-1234567890ab'), ('33333333-3333-3333-3333-333333333333', '2b3c4d5e-6f7a-8b9c-0d1e-234567890abc'), ('33333333-3333-3333-3333-333333333333', '4d5e6f7a-8b9c-0d1e-2f3a-4567890abcde'),
('44444444-4444-4444-4444-444444444444', '3c4d5e6f-7a8b-9c0d-1e2f-34567890abcd'), ('44444444-4444-4444-4444-444444444444', '4d5e6f7a-8b9c-0d1e-2f3a-4567890abcde'), ('44444444-4444-4444-4444-444444444444', '5e6f7a8b-9c0d-1e2f-3a4b-567890abcdef'), ('44444444-4444-4444-4444-444444444444', '8b9c0d1e-2f3a-4b5c-6d7e-890abcdef123'), ('44444444-4444-4444-4444-444444444444', '9c0d1e2f-3a4b-5c6d-7e8f-90abcdef1234'),
('55555555-5555-5555-5555-555555555555', '4d5e6f7a-8b9c-0d1e-2f3a-4567890abcde'), ('55555555-5555-5555-5555-555555555555', '5e6f7a8b-9c0d-1e2f-3a4b-567890abcdef'), ('55555555-5555-5555-5555-555555555555', '8b9c0d1e-2f3a-4b5c-6d7e-890abcdef123'),
('66666666-6666-6666-6666-666666666666', '7a8b9c0d-1e2f-3a4b-5c6d-7890abcdef12'), ('66666666-6666-6666-6666-666666666666', '8b9c0d1e-2f3a-4b5c-6d7e-890abcdef123');

-- 插入示例文件数据（肺癌WSI数据集）
SET @F1 = 'aaaabbbb-0001-0001-0001-aaaabbbb0001';
SET @F2 = 'aaaabbbb-0002-0002-0002-aaaabbbb0002';
SET @F3 = 'aaaabbbb-0003-0003-0003-aaaabbbb0003';
SET @F4 = 'aaaabbbb-0004-0004-0004-aaaabbbb0004';
INSERT IGNORE INTO t_dm_dataset_files (id, dataset_id, file_name, file_path, file_type, file_format, file_size, status) VALUES 
(@F1, '11111111-1111-1111-1111-111111111111', 'lung_cancer_001.jpg', '/datasets/wsi/lung_cancer_001.jpg', 'IMAGE', 'JPG', 2516582, 'ACTIVE'),
(@F2, '11111111-1111-1111-1111-111111111111', 'lung_cancer_002.jpg', '/datasets/wsi/lung_cancer_002.jpg', 'IMAGE', 'JPG', 1887437, 'ACTIVE'),
(@F3, '11111111-1111-1111-1111-111111111111', 'pathology_report_001.txt', '/datasets/wsi/pathology_report_001.txt', 'TEXT', 'TXT', 15360, 'ACTIVE'),
(@F4, '11111111-1111-1111-1111-111111111111', 'ct_scan_001.dcm', '/datasets/wsi/ct_scan_001.dcm', 'IMAGE', 'DCM', 47185920, 'ACTIVE');

-- 插入统计数据
SET @S1 = 'bbbbcccc-1001-1001-1001-bbbbcccc1001';
SET @S2 = 'bbbbcccc-1002-1002-1002-bbbbcccc1002';
SET @S3 = 'bbbbcccc-1003-1003-1003-bbbbcccc1003';
SET @S4 = 'bbbbcccc-1004-1004-1004-bbbbcccc1004';
INSERT IGNORE INTO t_dm_dataset_statistics (id, dataset_id, stat_date, total_files, total_size, processed_files, error_files, download_count, view_count) VALUES 
(@S1, '11111111-1111-1111-1111-111111111111', CURDATE(), 1247, 1342177280, 1205, 15, 0, 0),
(@S2, '44444444-4444-4444-4444-444444444444', CURDATE(), 50000, 943718400, 50000, 0, 0, 0),
(@S3, '55555555-5555-5555-5555-555555555555', CURDATE(), 100000, 2516582400, 95000, 0, 0, 0),
(@S4, '66666666-6666-6666-6666-666666666666', CURDATE(), 8500, 125829120, 8500, 0, 0, 0);

COMMIT;

-- 创建视图：数据集详情视图（引用新表）
CREATE OR REPLACE VIEW v_dm_dataset_details AS
SELECT 
    d.id,
    d.name,
    d.description,
    d.dataset_type,
    d.category,
    d.format,
    d.file_count,
    d.record_count,
    d.completion_rate,
    d.quality_score,
    d.status,
    d.is_public,
    d.is_featured,
    d.download_count,
    d.view_count,
    d.created_at,
    d.updated_at,
    d.created_by,
    ds.name as data_source_name,
    ds.type as data_source_type,
    COALESCE(stats.total_size, 0) as total_size_bytes,
    GROUP_CONCAT(t.name ORDER BY t.name SEPARATOR ', ') as tag_names
FROM t_dm_datasets d
LEFT JOIN data_sources ds ON d.data_source_id = ds.id
LEFT JOIN t_dm_dataset_statistics stats ON d.id = stats.dataset_id AND stats.stat_date = CURDATE()
LEFT JOIN t_dm_dataset_tags dt ON d.id = dt.dataset_id
LEFT JOIN t_dm_tags t ON dt.tag_id = t.id
GROUP BY d.id, ds.name, ds.type, stats.total_size;

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
