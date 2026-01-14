-- 使用现有的datamate数据库
\c datamate;

-- 文件切片上传请求表
CREATE TABLE IF NOT EXISTS t_chunk_upload_request
(
    id                VARCHAR(36) PRIMARY KEY,
    total_file_num    INTEGER,
    uploaded_file_num INTEGER,
    upload_path       VARCHAR(256),
    timeout           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    service_id        VARCHAR(64),
    check_info        TEXT
);

-- 添加注释
COMMENT ON TABLE t_chunk_upload_request IS '文件切片上传请求表';
COMMENT ON COLUMN t_chunk_upload_request.id IS 'UUID';
COMMENT ON COLUMN t_chunk_upload_request.total_file_num IS '总文件数';
COMMENT ON COLUMN t_chunk_upload_request.uploaded_file_num IS '已上传文件数';
COMMENT ON COLUMN t_chunk_upload_request.upload_path IS '文件路径';
COMMENT ON COLUMN t_chunk_upload_request.timeout IS '上传请求超时时间';
COMMENT ON COLUMN t_chunk_upload_request.service_id IS '上传请求所属服务：DATA-MANAGEMENT(数据管理);';
COMMENT ON COLUMN t_chunk_upload_request.check_info IS '业务信息';

-- 如果需要索引可以添加
CREATE INDEX IF NOT EXISTS idx_chunk_upload_service ON t_chunk_upload_request(service_id);
