USE datamate;

-- ===============================
-- t_data_synthesis_instances (数据合成任务表)
create table if not exists t_data_synth_instances
(
    id VARCHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci PRIMARY KEY COMMENT 'UUID',
    name VARCHAR(255) NOT NULL COMMENT '任务名称',
    description TEXT COMMENT '任务描述',
    status VARCHAR(20) COMMENT '任务状态',
    synth_type VARCHAR(20) NOT NULL COMMENT '合成类型',
    progress INT DEFAULT 0 COMMENT '任务进度(百分比)',
    synth_config JSON NOT NULL COMMENT '合成配置',
    total_files INT DEFAULT 0 COMMENT '总文件数',
    processed_files INT DEFAULT 0 COMMENT '已处理文件数',
    total_chunks INT DEFAULT 0 COMMENT '总文本块数',
    processed_chunks INT DEFAULT 0 COMMENT '已处理文本块数',
    total_synth_data INT DEFAULT 0 COMMENT '总合成数据量',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(255) COMMENT '创建者',
    updated_by VARCHAR(255) COMMENT '更新者'
) COMMENT='数据合成任务表（UUID 主键）';

-- ===============================
-- t_data_synthesis_file_instances (数据合成文件任务表)
create table if not exists t_data_synthesis_file_instances
(
    id VARCHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci PRIMARY KEY COMMENT 'UUID',
    synthesis_instance_id VARCHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据合成任务ID',
    file_name VARCHAR(255) NOT NULL COMMENT '文件名',
    source_file_id VARCHAR(255) NOT NULL COMMENT '原始文件ID',
    target_file_location VARCHAR(1000) NULL COMMENT '目标文件存储位置',
    status VARCHAR(20) COMMENT '任务状态',
    total_chunks INT DEFAULT 0 COMMENT '总文本块数',
    processed_chunks INT DEFAULT 0 COMMENT '已处理文本块数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(255) COMMENT '创建者',
    updated_by VARCHAR(255) COMMENT '更新者'
) COMMENT='数据合成文件任务表（UUID 主键）';


create table if not exists t_data_synthesis_chunk_instances
(
    id VARCHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci PRIMARY KEY COMMENT 'UUID',
    synthesis_file_instance_id VARCHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据合成文件任务ID',
    chunk_index INT COMMENT '分块索引',
    chunk_content TEXT COMMENT '分块内容',
    metadata JSON COMMENT '分块元数据'
) COMMENT='数据合成分块任务表（UUID 主键）';


create table if not exists t_data_synthesis_data
(
    id VARCHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci PRIMARY KEY COMMENT 'UUID',
    data json COMMENT '合成的数据',
    synthesis_file_instance_id VARCHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '数据合成文件任务ID',
    chunk_instance_id VARCHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '分块任务ID'
) COMMENT='数据合成任务队列表（UUID 主键）';
