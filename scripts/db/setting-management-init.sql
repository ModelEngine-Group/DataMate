-- 使用现有的datamate数据库
\c datamate;

-- 模型配置表
CREATE TABLE IF NOT EXISTS t_model_config
(
    id         VARCHAR(36) PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    provider   VARCHAR(50)  NOT NULL,
    base_url   VARCHAR(255) NOT NULL,
    api_key    VARCHAR(512) DEFAULT '',
    type       VARCHAR(50)  NOT NULL,
    is_enabled BOOLEAN     DEFAULT TRUE,
    is_default BOOLEAN     DEFAULT FALSE,
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

-- 添加注释
COMMENT ON TABLE t_model_config IS '模型配置表';
COMMENT ON COLUMN t_model_config.id IS '主键ID';
COMMENT ON COLUMN t_model_config.model_name IS '模型名称（如 qwen2）';
COMMENT ON COLUMN t_model_config.provider IS '模型提供商（如 Ollama、OpenAI、DeepSeek）';
COMMENT ON COLUMN t_model_config.base_url IS 'API 基础地址';
COMMENT ON COLUMN t_model_config.api_key IS 'API 密钥（无密钥则为空）';
COMMENT ON COLUMN t_model_config.type IS '模型类型（如 chat、embedding）';
COMMENT ON COLUMN t_model_config.is_enabled IS '是否启用：1-启用，0-禁用';
COMMENT ON COLUMN t_model_config.is_default IS '是否默认：1-默认，0-非默认';
COMMENT ON COLUMN t_model_config.created_at IS '创建时间';
COMMENT ON COLUMN t_model_config.updated_at IS '更新时间';
COMMENT ON COLUMN t_model_config.created_by IS '创建者';
COMMENT ON COLUMN t_model_config.updated_by IS '更新者';

-- 添加唯一约束
ALTER TABLE t_model_config
    ADD CONSTRAINT uk_model_provider
    UNIQUE (model_name, provider);

COMMENT ON CONSTRAINT uk_model_provider ON t_model_config
    IS '避免同一提供商下模型名称重复';

-- 创建触发器用于自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_t_model_config_updated_at ON t_model_config;
CREATE TRIGGER update_t_model_config_updated_at
    BEFORE UPDATE ON t_model_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 设置管理表
CREATE TABLE IF NOT EXISTS t_sys_param
(
    id          VARCHAR(100) PRIMARY KEY,
    param_value TEXT         NOT NULL,
    param_type  VARCHAR(50)  DEFAULT 'string',
    option_list TEXT,
    description VARCHAR(255) DEFAULT '',
    is_built_in BOOLEAN     DEFAULT FALSE,
    can_modify  BOOLEAN     DEFAULT TRUE,
    is_enabled  BOOLEAN     DEFAULT TRUE,
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    created_by  VARCHAR(255),
    updated_by  VARCHAR(255)
);

-- 添加注释
COMMENT ON TABLE t_sys_param IS '设置管理表';
COMMENT ON COLUMN t_sys_param.id IS '主键ID,设置项键';
COMMENT ON COLUMN t_sys_param.param_value IS '设置项值';
COMMENT ON COLUMN t_sys_param.param_type IS '设置项类型（仅 string、number、boolean 三种类型）';
COMMENT ON COLUMN t_sys_param.option_list IS '选项列表（逗号分隔，仅对 enum 类型有效）';
COMMENT ON COLUMN t_sys_param.description IS '设置项描述';
COMMENT ON COLUMN t_sys_param.is_built_in IS '是否内置：1-是，0-否';
COMMENT ON COLUMN t_sys_param.can_modify IS '是否可修改：1-可修改，0-不可修改';
COMMENT ON COLUMN t_sys_param.is_enabled IS '是否启用：1-启用，0-禁用';
COMMENT ON COLUMN t_sys_param.created_at IS '创建时间';
COMMENT ON COLUMN t_sys_param.updated_at IS '更新时间';
COMMENT ON COLUMN t_sys_param.created_by IS '创建者';
COMMENT ON COLUMN t_sys_param.updated_by IS '更新者';

-- 创建触发器
DROP TRIGGER IF EXISTS update_t_sys_param_updated_at ON t_sys_param;
CREATE TRIGGER update_t_sys_param_updated_at
    BEFORE UPDATE ON t_sys_param
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 插入初始数据
INSERT INTO t_sys_param (id, param_value, param_type, option_list, description, is_built_in,
                         can_modify, is_enabled, created_by, updated_by)
VALUES
    ('sys.knowledge.base.count', '200', 'number', '10,200,500', '知识库最大数量', true, true, true, 'system', 'system'),
    ('SEARCH_API', 'tavily', 'string', 'tavily,infoquest,duckduckgo,brave_search,arxiv', 'deer-flow使用的搜索引擎', true, true, true, 'system', 'system'),
    ('TAVILY_API_KEY', 'tvly-dev-xxx', 'string', '', 'deer-flow使用的搜索引擎所需的apiKey', true, true, true, 'system', 'system'),
    ('BRAVE_SEARCH_API_KEY', 'api-xxx', 'string', '', 'deer-flow使用的搜索引擎所需的apiKey', true, true, true, 'system', 'system'),
    ('JINA_API_KEY', '', 'string', '', 'deer-flow使用的JINA搜索引擎所需的apiKey', true, true, true, 'system', 'system'),
    ('sys.management.dataset.pvc.name', 'datamate-dataset-pvc', 'string', '', '数据集所在pvc名称', true, false,true, 'system', 'system'),
    ('DATA_JUICER_EXECUTOR', 'default', 'string', 'default,ray', 'data-juicer使用的执行器', true, true, true, 'system', 'system')
ON CONFLICT (id) DO NOTHING;
