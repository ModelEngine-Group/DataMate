-- 使用现有的datamate数据库
\c datamate;

-- 知识库表
CREATE TABLE IF NOT EXISTS t_rag_knowledge_base
(
    id              VARCHAR(36) PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    description     VARCHAR(512),
    embedding_model VARCHAR(255) NOT NULL,
    chat_model      VARCHAR(255),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by      VARCHAR(255),
    updated_by      VARCHAR(255)
);

-- 添加注释
COMMENT ON TABLE t_rag_knowledge_base IS '知识库表';
COMMENT ON COLUMN t_rag_knowledge_base.id IS 'UUID';
COMMENT ON COLUMN t_rag_knowledge_base.name IS '知识库名称';
COMMENT ON COLUMN t_rag_knowledge_base.description IS '知识库描述';
COMMENT ON COLUMN t_rag_knowledge_base.embedding_model IS '嵌入模型';
COMMENT ON COLUMN t_rag_knowledge_base.chat_model IS '聊天模型';
COMMENT ON COLUMN t_rag_knowledge_base.created_at IS '创建时间';
COMMENT ON COLUMN t_rag_knowledge_base.updated_at IS '更新时间';
COMMENT ON COLUMN t_rag_knowledge_base.created_by IS '创建者';
COMMENT ON COLUMN t_rag_knowledge_base.updated_by IS '更新者';

-- 知识库文件表（修正表名注释为"知识库文件表"）
CREATE TABLE IF NOT EXISTS t_rag_file
(
    id                VARCHAR(36) PRIMARY KEY,
    knowledge_base_id VARCHAR(36)  NOT NULL,
    file_name         VARCHAR(255) NOT NULL,
    file_id           VARCHAR(255) NOT NULL,
    chunk_count       INTEGER,
    metadata          JSONB,
    status            VARCHAR(50),
    err_msg           TEXT,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by        VARCHAR(255),
    updated_by        VARCHAR(255)
);

-- 添加注释
COMMENT ON TABLE t_rag_file IS '知识库文件表';
COMMENT ON COLUMN t_rag_file.id IS 'UUID';
COMMENT ON COLUMN t_rag_file.knowledge_base_id IS '知识库ID';
COMMENT ON COLUMN t_rag_file.file_name IS '文件名';
COMMENT ON COLUMN t_rag_file.file_id IS '文件ID';
COMMENT ON COLUMN t_rag_file.chunk_count IS '切片数';
COMMENT ON COLUMN t_rag_file.metadata IS '元数据';
COMMENT ON COLUMN t_rag_file.status IS '文件状态';
COMMENT ON COLUMN t_rag_file.err_msg IS '错误信息';
COMMENT ON COLUMN t_rag_file.created_at IS '创建时间';
COMMENT ON COLUMN t_rag_file.updated_at IS '更新时间';
COMMENT ON COLUMN t_rag_file.created_by IS '创建者';
COMMENT ON COLUMN t_rag_file.updated_by IS '更新者';

-- 创建外键约束
ALTER TABLE t_rag_file
    ADD CONSTRAINT fk_rag_file_knowledge_base
    FOREIGN KEY (knowledge_base_id)
    REFERENCES t_rag_knowledge_base(id)
    ON DELETE CASCADE;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_rag_file_knowledge_base ON t_rag_file(knowledge_base_id);
CREATE INDEX IF NOT EXISTS idx_rag_file_status ON t_rag_file(status);
CREATE INDEX IF NOT EXISTS idx_rag_file_created_at ON t_rag_file(created_at);

-- 创建触发器用于自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为 t_rag_knowledge_base 表创建触发器
DROP TRIGGER IF EXISTS update_rag_knowledge_base_updated_at ON t_rag_knowledge_base;
CREATE TRIGGER update_rag_knowledge_base_updated_at
    BEFORE UPDATE ON t_rag_knowledge_base
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 为 t_rag_file 表创建触发器
DROP TRIGGER IF EXISTS update_rag_file_updated_at ON t_rag_file;
CREATE TRIGGER update_rag_file_updated_at
    BEFORE UPDATE ON t_rag_file
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
