-- 数据归集服务数据库初始化脚本
-- 适用于dataengine数据库

USE dataengine;

create table if not exists t_chunk_upload_request
(
  id  VARCHAR(36) PRIMARY KEY COMMENT 'UUID',
  total_file_num integer,
  uploaded_file_num   integer,
  upload_path   varchar(256),
  timeout     timestamp default now(),
  service_id varchar(64),
  check_info   TEXT
  );
comment on table t_chunk_upload_request is '文件切片上传请求表';
comment on column t_chunk_upload_request.total_file_num is '总文件数';
comment on column t_chunk_upload_request.uploaded_file_num is '已上传文件数';
comment on column t_chunk_upload_request.upload_path is '文件路径';
comment on column t_chunk_upload_request.timeout is '上传请求超时时间';
comment on column t_chunk_upload_request.service_id is '上传请求所属服务：DATA-MANAGEMENT(数据管理);';
comment on column t_chunk_upload_request.check_info is '业务信息';
