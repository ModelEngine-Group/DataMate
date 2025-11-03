USE datamate;

create table if not exists t_rag_knowledge_base
(
  id              VARCHAR(36) PRIMARY KEY COMMENT 'UUID',
  name            VARCHAR(255) NOT NULL COMMENT '知识库名称',
  description     VARCHAR(512) NULL COMMENT '知识库描述',
  embedding_model VARCHAR(255) NOT NULL COMMENT '嵌入模型',
  chat_model      VARCHAR(255) NULL COMMENT '聊天模型',
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  created_by      VARCHAR(255) COMMENT '创建者',
  updated_by      VARCHAR(255) COMMENT '更新者'
) comment '知识库表';

create table if not exists t_rag_file
(
  id                VARCHAR(36) PRIMARY KEY COMMENT 'UUID',
  knowledge_base_id VARCHAR(36)  NOT NULL COMMENT '知识库ID',
  file_name         VARCHAR(255) NOT NULL COMMENT '文件名',
  file_id           VARCHAR(255) NOT NULL COMMENT '文件ID',
  chunk_count       INT COMMENT '切片数',
  metadata          JSON COMMENT '元数据',
  status            VARCHAR(50) COMMENT '文件状态',
  created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  created_by        VARCHAR(255) COMMENT '创建者',
  updated_by        VARCHAR(255) COMMENT '更新者'
) comment '知识库切片表';
