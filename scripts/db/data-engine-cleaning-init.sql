USE dataengine;

CREATE TABLE IF NOT EXISTS t_clean_template
(
    id          varchar(64) primary key not null unique,
    name        varchar(64),
    description varchar(256),
    created_at  timestamp,
    updated_at  timestamp,
    created_by  varchar(256)
);

CREATE TABLE IF NOT EXISTS t_clean_task
(
    id                varchar(64) primary key,
    name              varchar(64),
    description       varchar(256),
    status            varchar(256),
    src_dataset_id    varchar(64),
    src_dataset_name  varchar(64),
    dest_dataset_id   varchar(64),
    dest_dataset_name varchar(64),
    before_size       bigint,
    after_size        bigint,
    created_at        timestamp,
    started_at        timestamp,
    finished_at       timestamp,
    created_by        varchar(256)
);

CREATE TABLE IF NOT EXISTS t_operator_instance
(
    id                int primary key auto_increment,
    instance_id       varchar(256),
    operator_id       varchar(256),
    op_index          int,
    settings_override text
);

CREATE TABLE IF NOT EXISTS t_clean_result
(
    id          int primary key auto_increment,
    instance_id varchar(64),
    src_file_id varchar(64),
    dst_file_id varchar(64),
    src_name    varchar(256),
    src_type    varchar(256),
    src_size    bigint,
    dst_size    bigint,
    status      varchar(256)
);

