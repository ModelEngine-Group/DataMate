-- Data-Engine Platform 数据库初始化脚本
-- 适用于现有knowledge_base数据库环境

-- 使用现有的knowledge_base数据库
USE knowledge_base;

-- 删除已存在的表（如果需要重新创建）
-- DROP TABLE IF EXISTS dataset_files;
-- DROP TABLE IF EXISTS dataset_statistics;
-- DROP TABLE IF EXISTS dataset_tags;
-- DROP TABLE IF EXISTS datasets;
-- DROP TABLE IF EXISTS data_sources;

-- 数据源表
CREATE TABLE IF NOT EXISTS data_sources (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE COMMENT '数据源名称',
    description TEXT COMMENT '数据源描述',
    type VARCHAR(50) NOT NULL COMMENT '数据源类型：MYSQL/FILE_SYSTEM/MINIO/HTTP等',
    host VARCHAR(255) COMMENT '主机地址',
    port INT COMMENT '端口号',
    database_name VARCHAR(255) COMMENT '数据库名',
    username VARCHAR(255) COMMENT '用户名',
    password VARCHAR(255) COMMENT '密码',
    connection_url TEXT COMMENT '连接URL',
    additional_properties JSON COMMENT '额外配置属性',
    enabled BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
    version BIGINT NOT NULL DEFAULT 0 COMMENT '版本号',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(255) COMMENT '创建者',
    updated_by VARCHAR(255) COMMENT '更新者',
    INDEX idx_type (type),
    INDEX idx_enabled (enabled),
    INDEX idx_created_at (created_at)
) COMMENT='数据源表';

-- 数据集表（支持医学影像、文本、问答等多种类型）
CREATE TABLE IF NOT EXISTS datasets (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL COMMENT '数据集名称',
    description TEXT COMMENT '数据集描述',
    dataset_type VARCHAR(50) NOT NULL COMMENT '数据集类型：IMAGE/TEXT/QA/MULTIMODAL/OTHER',
    category VARCHAR(100) COMMENT '数据集分类：医学影像/问答/文献等',
    data_source_id BIGINT COMMENT '关联数据源ID',
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
    INDEX idx_dataset_type (dataset_type),
    INDEX idx_category (category),
    INDEX idx_data_source (data_source_id),
    INDEX idx_format (format),
    INDEX idx_status (status),
    INDEX idx_public (is_public),
    INDEX idx_featured (is_featured),
    INDEX idx_created_at (created_at)
) COMMENT='数据集表';

-- 数据集文件表
CREATE TABLE IF NOT EXISTS dataset_files (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    dataset_id BIGINT NOT NULL COMMENT '所属数据集ID',
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
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
    INDEX idx_dataset (dataset_id),
    INDEX idx_file_type (file_type),
    INDEX idx_file_format (file_format),
    INDEX idx_status (status),
    INDEX idx_upload_time (upload_time)
) COMMENT='数据集文件表';

-- 数据集统计信息表
CREATE TABLE IF NOT EXISTS dataset_statistics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    dataset_id BIGINT NOT NULL COMMENT '数据集ID',
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
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
    UNIQUE KEY uk_dataset_date (dataset_id, stat_date),
    INDEX idx_stat_date (stat_date)
) COMMENT='数据集统计信息表';

-- 标签表
CREATE TABLE IF NOT EXISTS tags (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE COMMENT '标签名称',
    description TEXT COMMENT '标签描述',
    category VARCHAR(50) COMMENT '标签分类',
    color VARCHAR(7) COMMENT '标签颜色(十六进制)',
    usage_count BIGINT DEFAULT 0 COMMENT '使用次数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_category (category),
    INDEX idx_usage_count (usage_count)
) COMMENT='标签表';

-- 数据集标签关联表
CREATE TABLE IF NOT EXISTS dataset_tags (
    dataset_id BIGINT NOT NULL COMMENT '数据集ID',
    tag_id BIGINT NOT NULL COMMENT '标签ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (dataset_id, tag_id),
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
) COMMENT='数据集标签关联表';

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
INSERT IGNORE INTO tags (name, description, category, color) VALUES 
('WSI', '全切片图像', '医学影像', '#FF6B6B'),
('病理', '病理学相关', '医学', '#4ECDC4'),
('肺癌', '肺癌相关数据', '疾病', '#45B7D1'),
('问答', '问答对数据', '文本', '#96CEB4'),
('医学', '医学领域', '领域', '#FFEAA7'),
('NLP', '自然语言处理', '技术', '#DDA0DD'),
('数学', '数学推理', '学科', '#98D8C8'),
('GSM8K', '小学数学问题', '数据集', '#F7DC6F'),
('高质量', '高质量数据集', '质量', '#82E0AA'),
('已验证', '已验证数据', '状态', '#85C1E9');

-- 插入示例数据集
INSERT IGNORE INTO datasets (name, description, dataset_type, category, data_source_id, format, file_count, record_count, completion_rate, quality_score, status, is_public, is_featured) VALUES 
('肺癌WSI病理图像数据集', '来自三甲医院的肺癌全切片病理图像，包含详细的病理标注信息', 'IMAGE', '医学影像', 1, 'WSI', 1247, 1205, 94.20, 96.80, 'ACTIVE', TRUE, TRUE),
('肺癌WSI诊断数据集A', '基于肺癌WSI数据集生成的诊断数据集', 'IMAGE', '医学影像', 1, 'WSI', 850, 0, 0.00, 0.00, 'DRAFT', FALSE, FALSE),
('肺癌WSI诊断数据集B', '基于肺癌WSI数据集生成的诊断数据集', 'IMAGE', '医学影像', 1, 'WSI', 650, 0, 0.00, 0.00, 'DRAFT', FALSE, FALSE),
('医学问答对数据集', '包含医学领域的高质量问答对，并行开展医学领域系统训练', 'QA', '问答', 1, 'JSON', 50000, 50000, 97.00, 97.00, 'ACTIVE', TRUE, TRUE),
('医学文献摘要数据集', '包含10万篇高质量医学文献摘要，用于医学文本分类和摘要任务', 'TEXT', '文献', 1, 'JSON', 100000, 95000, 95.00, 95.00, 'ACTIVE', TRUE, FALSE),
('GSM8K数学推理数据集', '包含小学数学应用题的推理数据集，并开展数学推理能力训练', 'TEXT', '数学', 1, 'JSON', 8500, 8500, 96.00, 96.00, 'ACTIVE', FALSE, FALSE);

-- 插入数据集标签关联
INSERT IGNORE INTO dataset_tags (dataset_id, tag_id) VALUES 
(1, 1), (1, 2), (1, 3), (1, 5), (1, 9), (1, 10),  -- 肺癌WSI病理图像数据集
(2, 1), (2, 2), (2, 3), (2, 5),  -- 肺癌WSI诊断数据集A
(3, 1), (3, 2), (3, 3), (3, 5),  -- 肺癌WSI诊断数据集B
(4, 4), (4, 5), (4, 6), (4, 9), (4, 10),  -- 医学问答对数据集
(5, 5), (5, 6), (5, 9),  -- 医学文献摘要数据集
(6, 7), (6, 8), (6, 9);  -- GSM8K数学推理数据集

-- 插入示例文件数据（肺癌WSI数据集）
INSERT IGNORE INTO dataset_files (dataset_id, file_name, file_path, file_type, file_format, file_size, status) VALUES 
(1, 'lung_cancer_001.jpg', '/datasets/wsi/lung_cancer_001.jpg', 'IMAGE', 'JPG', 2516582, 'ACTIVE'),
(1, 'lung_cancer_002.jpg', '/datasets/wsi/lung_cancer_002.jpg', 'IMAGE', 'JPG', 1887437, 'ACTIVE'),
(1, 'pathology_report_001.txt', '/datasets/wsi/pathology_report_001.txt', 'TEXT', 'TXT', 15360, 'ACTIVE'),
(1, 'ct_scan_001.dcm', '/datasets/wsi/ct_scan_001.dcm', 'IMAGE', 'DCM', 47185920, 'ACTIVE');

-- 插入统计数据
INSERT IGNORE INTO dataset_statistics (dataset_id, stat_date, total_files, total_size, processed_files, error_files, download_count, view_count) VALUES 
(1, CURDATE(), 1247, 1342177280, 1205, 15, 0, 0),  -- 1.2TB = 1342177280000 bytes, 约1.2TB/1000 ≈ 1.3GB用于示例
(4, CURDATE(), 50000, 943718400, 50000, 0, 0, 0),  -- 约900MB
(5, CURDATE(), 100000, 2516582400, 95000, 0, 0, 0),  -- 约2.3GB
(6, CURDATE(), 8500, 125829120, 8500, 0, 0, 0);  -- 约120MB

COMMIT;

-- 创建视图：数据集详情视图
CREATE OR REPLACE VIEW dataset_details AS
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
FROM datasets d
LEFT JOIN data_sources ds ON d.data_source_id = ds.id
LEFT JOIN dataset_statistics stats ON d.id = stats.dataset_id AND stats.stat_date = CURDATE()
LEFT JOIN dataset_tags dt ON d.id = dt.dataset_id
LEFT JOIN tags t ON dt.tag_id = t.id
GROUP BY d.id, ds.name, ds.type, stats.total_size;

-- 创建视图：数据集统计摘要
CREATE OR REPLACE VIEW dataset_summary AS
SELECT 
    COUNT(*) as total_datasets,
    SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) as active_datasets,
    SUM(CASE WHEN is_public = TRUE THEN 1 ELSE 0 END) as public_datasets,
    SUM(CASE WHEN is_featured = TRUE THEN 1 ELSE 0 END) as featured_datasets,
    SUM(file_count) as total_files,
    SUM(record_count) as total_records,
    COUNT(DISTINCT dataset_type) as dataset_types,
    COUNT(DISTINCT category) as categories
FROM datasets;

```
