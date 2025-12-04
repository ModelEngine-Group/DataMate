USE datamate;

CREATE TABLE IF NOT EXISTS t_model_config
(
    id         VARCHAR(36) PRIMARY KEY COMMENT '主键ID',
    model_name VARCHAR(100) NOT NULL COMMENT '模型名称（如 qwen2）',
    provider   VARCHAR(50)  NOT NULL COMMENT '模型提供商（如 Ollama、OpenAI、DeepSeek）',
    base_url   VARCHAR(255) NOT NULL COMMENT 'API 基础地址',
    api_key    VARCHAR(512) DEFAULT '' COMMENT 'API 密钥（无密钥则为空）',
    type       VARCHAR(50)  NOT NULL COMMENT '模型类型（如 chat、embedding）',
    is_enabled TINYINT      DEFAULT 1 COMMENT '是否启用：1-启用，0-禁用',
    is_default TINYINT      DEFAULT 0 COMMENT '是否默认：1-默认，0-非默认',
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(255) COMMENT '创建者',
    updated_by VARCHAR(255) COMMENT '更新者',
    UNIQUE KEY uk_model_provider (model_name, provider) COMMENT '避免同一提供商下模型名称重复'
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='模型配置表';

CREATE TABLE IF NOT EXISTS t_sys_param
(
    id          VARCHAR(100) PRIMARY KEY COMMENT '主键ID,设置项键',
    param_value TEXT         NOT NULL COMMENT '设置项值',
    param_type  VARCHAR(50)  DEFAULT 'string' COMMENT '设置项类型（仅 string、number、boolean 三种类型）',
    option_list TEXT COMMENT '选项列表（逗号分隔，仅对 enum 类型有效）',
    description VARCHAR(255) DEFAULT '' COMMENT '设置项描述',
    is_built_in TINYINT      DEFAULT 0 COMMENT '是否内置：1-是，0-否',
    can_modify  TINYINT      DEFAULT 1 COMMENT '是否可修改：1-可修改，0-不可修改',
    is_enabled  TINYINT      DEFAULT 1 COMMENT '是否启用：1-启用，0-禁用',
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by  VARCHAR(255) COMMENT '创建者',
    updated_by  VARCHAR(255) COMMENT '更新者'
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='设置管理表';

insert ignore into t_sys_param (id, param_value, param_type, option_list, description, is_built_in,
                                can_modify,
                                is_enabled, created_by, updated_by)
values ('sys.knowledge.base.count', '200', 'number', '10,200,500', '知识库最大数量', 1, 1, 1, 'system', 'system'),
       ('SEARCH_API', 'tavily', 'string', 'tavily,infoquest,duckduckgo,brave_search,arxiv', 'deer-flow使用的搜索引擎', 1, 1, 1, 'system', 'system'),
       ('TAVILY_API_KEY', 'tvly-dev-xxx', 'string', '', 'deer-flow使用的搜索引擎所需的apiKey', 1, 1, 1, 'system', 'system'),
       ('BRAVE_SEARCH_API_KEY', 'api-xxx', 'string', '', 'deer-flow使用的搜索引擎所需的apiKey', 1, 1, 1, 'system', 'system'),
       ('JINA_API_KEY', '', 'string', '', 'deer-flow使用的JINA搜索引擎所需的apiKey', 1, 1, 1, 'system', 'system'),
       ('sys.management.dataset.pvc.name', 'dataset-pvc', 'string', '', '数据集所在pvc名称', 1, 0, 1, 'system', 'system'),
       ('test_bool', 'true', 'boolean', '', '测试布尔值', 1, 1, 1, 'system', 'system');
