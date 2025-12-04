-- 使用现有的datamate数据库
USE datamate;


-- 数据集表（支持医学影像、文本、问答等多种类型）
CREATE TABLE IF NOT EXISTS t_de_eval_task (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID',
    name VARCHAR(255) NOT NULL COMMENT '评估任务名称',
    description TEXT COMMENT '评估任务描述',
    task_type VARCHAR(50) NOT NULL COMMENT '评估任务类型：QA',
    source_type VARCHAR(36) COMMENT '待评估对象类型：DATASET/SYNTHESIS',
    source_id VARCHAR(36) COMMENT '待评估对象ID',
    source_name VARCHAR(255) COMMENT '待评估对象名称',
    status VARCHAR(50) DEFAULT 'PENDING' COMMENT '状态：PENDING/RUNNING/COMPLETED/STOPPED/FAILED',
    eval_method VARCHAR(50) DEFAULT 'AUTO' COMMENT '评估方式：AUTO/MANUAL',
    eval_process DOUBLE PRECISION NOT NULL DEFAULT 0 COMMENT '评估进度',
    eval_prompt TEXT COMMENT '评估提示词',
    eval_config TEXT COMMENT '评估配置',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(255) COMMENT '创建者',
    updated_by VARCHAR(255) COMMENT '更新者',
    INDEX idx_dm_status (status),
    INDEX idx_dm_created_at (created_at)
) COMMENT='评估任务表（UUID 主键）';

CREATE TABLE IF NOT EXISTS t_de_eval_file (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID',
    task_id VARCHAR(36) NOT NULL COMMENT '评估任务ID',
    file_id VARCHAR(36) COMMENT '文件ID',
    file_name VARCHAR(255) COMMENT '文件名',
    total_count INT DEFAULT 0 COMMENT '总数',
    evaluated_count INT DEFAULT 0 COMMENT '已评估数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(255) COMMENT '创建者',
    updated_by VARCHAR(255) COMMENT '更新者'
) COMMENT='评估文件表（UUID 主键）';

CREATE TABLE IF NOT EXISTS t_de_eval_item (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID',
    task_id VARCHAR(36) NOT NULL COMMENT '评估任务ID',
    file_id VARCHAR(36) COMMENT '文件ID',
    item_id VARCHAR(36) NOT NULL COMMENT '评估条目ID',
    eval_content TEXT COMMENT '评估内容',
    eval_score DOUBLE PRECISION NOT NULL DEFAULT 0 COMMENT '评估分数',
    eval_result TEXT COMMENT '评估结果',
    status VARCHAR(50) DEFAULT 'PENDING' COMMENT '状态：PENDING/EVALUATED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(255) COMMENT '创建者',
    updated_by VARCHAR(255) COMMENT '更新者'
) COMMENT='评估条目表（UUID 主键）';
