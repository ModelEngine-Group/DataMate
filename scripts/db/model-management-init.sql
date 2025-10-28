CREATE TABLE t_model_config
(
    id         VARCHAR(36) AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    model_name VARCHAR(100) NOT NULL COMMENT '模型名称（如 qwen2）',
    provider   VARCHAR(50)  NOT NULL COMMENT '模型提供商（如 Ollama、OpenAI、DeepSeek）',
    base_url   VARCHAR(255) NOT NULL COMMENT 'API 基础地址',
    api_key    VARCHAR(255) DEFAULT '' COMMENT 'API 密钥（无密钥则为空）',
    type       VARCHAR(50)  NOT NULL COMMENT '模型类型（如 chat、embedding）',
    is_enabled TINYINT      DEFAULT 1 COMMENT '是否启用：1-启用，0-禁用',
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(255) COMMENT '创建者',
    updated_by VARCHAR(255) COMMENT '更新者',
    UNIQUE KEY uk_model_provider (model_name, provider) COMMENT '避免同一提供商下模型名称重复'
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4 COMMENT ='模型配置表';

