USE datamate;

-- 先删表，避免旧结构冲突
DROP TABLE IF EXISTS t_qa_pairs;
DROP TABLE IF EXISTS t_qa_generation_instances;

-- ===============================
-- t_qa_generation_instances (任务表)
-- ===============================
CREATE TABLE t_qa_generation_instances (
    id VARCHAR(36)
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci
        PRIMARY KEY
        COMMENT 'UUID',

    name VARCHAR(255) NOT NULL COMMENT '任务名称',
    description TEXT COMMENT '任务描述',

    -- 修改 source_dataset_id 为 VARCHAR(255)，支持存储多个 ID，但限制长度
    source_dataset_id VARCHAR(255)
        CHARACTER SET utf8mb4 
        COLLATE utf8mb4_unicode_ci 
        NOT NULL 
        COMMENT '源数据集ID（以逗号分隔多个ID）',

    target_dataset_id VARCHAR(36)
        CHARACTER SET utf8mb4 
        COLLATE utf8mb4_unicode_ci 
        COMMENT '目标数据集ID',

    text_split_config JSON NOT NULL COMMENT '文本切片配置',
    qa_generation_config JSON NOT NULL COMMENT 'QA生成配置',

    status VARCHAR(20) NOT NULL DEFAULT 'PENDING' COMMENT '任务状态',
    total_files INT DEFAULT 0 COMMENT '总文件数',
    processed_files INT DEFAULT 0 COMMENT '已处理文件数',
    total_chunks INT DEFAULT 0 COMMENT '总文本块数',
    processed_chunks INT DEFAULT 0 COMMENT '已处理文本块数',
    total_qa_pairs INT DEFAULT 0 COMMENT '生成的QA对总数',

    error_message TEXT COMMENT '错误信息',

    llm_api_key TEXT NOT NULL COMMENT 'LLM API密钥',
    llm_base_url VARCHAR(512) NOT NULL COMMENT 'LLM Base URL',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP 
        ON UPDATE CURRENT_TIMESTAMP 
        COMMENT '更新时间',

    created_by VARCHAR(255) COMMENT '创建者',
    updated_by VARCHAR(255) COMMENT '更新者',

    -- 移除外键约束
    INDEX idx_source_dataset (source_dataset_id),
    INDEX idx_target_dataset (target_dataset_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='QA生成任务实例表';

-- ===============================
-- t_qa_pairs (QA 对表)
-- ===============================
CREATE TABLE t_qa_pairs (
    id VARCHAR(36)
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci
        PRIMARY KEY
        COMMENT 'UUID',

    task_id VARCHAR(36)
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci
        NOT NULL
        COMMENT 'QA任务ID',

    source_file_id VARCHAR(36)
        CHARACTER SET utf8mb4
        COLLATE utf8mb4_unicode_ci
        NOT NULL
        COMMENT '源文件ID',

    source_file_name VARCHAR(255) NOT NULL COMMENT '源文件名',

    chunk_index INT NOT NULL COMMENT '文本块序号',

    text_chunk LONGTEXT NOT NULL COMMENT '文本片段内容',
    question TEXT NOT NULL COMMENT '问题',
    answer TEXT NOT NULL COMMENT '答案',

    question_type VARCHAR(50),
    confidence_score DECIMAL(5,4),
    metadata JSON,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    -- 移除外键约束
    INDEX idx_task_id (task_id),
    INDEX idx_source_file_id (source_file_id),
    INDEX idx_chunk_index (chunk_index)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci
  COMMENT='QA对数据表';






-- 插入示例数据 (可选)
-- INSERT INTO t_qa_generation_instances (id, name, description, source_dataset_id, text_split_config, qa_generation_config, llm_api_key, llm_base_url, status)
-- VALUES (
--     '550e8400-e29b-41d4-a716-446655440000',
--     '测试QA生成任务',
--     '这是一个测试任务',
--     'dataset-001',
--     '{"max_characters": 50000, "chunk_size": 800, "chunk_overlap": 200}',
--     '{"max_questions": 3, "temperature": 0.3, "model": "gpt-5-nano"}',
--     'sk-xxxxxxxxxxxxx',
--     'https://api.openai.com/v1',
--     'PENDING'
-- );
