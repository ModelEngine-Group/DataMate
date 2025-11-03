USE datamate;

CREATE TABLE IF NOT EXISTS t_st_ratio_instances
(
    id          varchar(64) primary key COMMENT 'UUID',
    name        varchar(64) COMMENT '名称',
    description TEXT COMMENT '描述',
    target_dataset_id     varchar(64) COMMENT '模板数据集ID',
    ratio_method      varchar(50) COMMENT '配比方式，按标签（TAG）,按数据集（DATASET）',
    ratio_parameters     JSON COMMENT '配比参数',
    merge_method     varchar(50) COMMENT '合并方式',
    status    varchar(20) COMMENT '状态',
    totals   BIGINT COMMENT '总数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(255) COMMENT '创建者',
    updated_by VARCHAR(255) COMMENT '更新者'
) COMMENT='配比实例表（UUID 主键）';

CREATE TABLE IF NOT EXISTS t_st_ratio_relations
(
    id          varchar(64) primary key COMMENT 'UUID',
    ratio_instance_id        varchar(64) COMMENT '配比实例ID',
    source_dataset_id varchar(64) COMMENT '源数据集ID',
    ratio_value     varchar(256),
    counts      BIGINT COMMENT '条数',
    filter_conditions     text COMMENT '过滤条件',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(255) COMMENT '创建者',
    updated_by VARCHAR(255) COMMENT '更新者'
) COMMENT='配比关系表（UUID 主键）';
