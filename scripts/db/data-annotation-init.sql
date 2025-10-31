use datamate;

CREATE TABLE t_dm_annotation_templates (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(32) NOT NULL COMMENT '模板名称',
    description VARCHAR(255) COMMENT '模板描述',
    configuration JSON,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    deleted_at TIMESTAMP NULL COMMENT '删除时间（软删除）'
);

CREATE TABLE t_dm_labeling_projects (
    id VARCHAR(36) PRIMARY KEY,
    dataset_id VARCHAR(36) NOT NULL COMMENT '数据集ID',
    name VARCHAR(32) NOT NULL COMMENT '项目名称',
    labeling_project_id VARCHAR(8) NOT NULL COMMENT 'Label Studio项目ID',
    configuration JSON,
    progress JSON,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    deleted_at TIMESTAMP NULL COMMENT '删除时间（软删除）'
);
