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

-- =========================
-- 数据血缘：节点表
-- 节点表示实体对象（归集来源、数据集、知识库、模型等）
-- =========================
CREATE TABLE IF NOT EXISTS t_lineage_node
(
    id            VARCHAR(36) PRIMARY KEY,
    graph_id      VARCHAR(36) NOT NULL,
    node_type     VARCHAR(64) NOT NULL,
    name          VARCHAR(256) NOT NULL,
    description   TEXT,
    node_metadata TEXT
);

COMMENT ON TABLE t_lineage_node IS '数据血缘节点表（实体对象）';
COMMENT ON COLUMN t_lineage_node.id IS '主键ID';
COMMENT ON COLUMN t_lineage_node.graph_id IS '图ID';
COMMENT ON COLUMN t_lineage_node.node_type IS '节点类型：DATASOURCE/DATASET/KNOWLEDGE_BASE/MODEL等';
COMMENT ON COLUMN t_lineage_node.name IS '节点名称';
COMMENT ON COLUMN t_lineage_node.description IS '节点描述';
COMMENT ON COLUMN t_lineage_node.node_metadata IS '节点扩展信息（JSON）';

CREATE INDEX IF NOT EXISTS idx_lineage_node_id ON t_lineage_node(id);
CREATE INDEX IF NOT EXISTS idx_lineage_graph_id ON t_lineage_node(graph_id);

-- =========================
-- 数据血缘：边表
-- 边表示处理流程（归集任务、数据清洗、数据标注、数据合成、数据配比等）
-- =========================
CREATE TABLE IF NOT EXISTS t_lineage_edge
(
    id            VARCHAR(36) PRIMARY KEY,
    process_id    VARCHAR(36) NOT NULL,
    graph_id      VARCHAR(36) NOT NULL,
    edge_type     VARCHAR(64) NOT NULL,
    name          VARCHAR(256),
    description   TEXT,
    edge_metadata TEXT,
    from_node_id  VARCHAR(36) NOT NULL,
    to_node_id    VARCHAR(36) NOT NULL
);

COMMENT ON TABLE t_lineage_edge IS '数据血缘边表（处理流程）';
COMMENT ON COLUMN t_lineage_edge.id IS '边ID';
COMMENT ON COLUMN t_lineage_edge.graph_id IS '图ID';
COMMENT ON COLUMN t_lineage_edge.process_id IS '处理流程ID';
COMMENT ON COLUMN t_lineage_edge.edge_type IS '边类型：DATA_COLLECTION/DATA_CLEANING/DATA_LABELING/DATA_SYNTHESIS/DATA_RATIO等';
COMMENT ON COLUMN t_lineage_edge.name IS '边名称';
COMMENT ON COLUMN t_lineage_edge.description IS '边描述';
COMMENT ON COLUMN t_lineage_edge.edge_metadata IS '边扩展信息（JSON）';
COMMENT ON COLUMN t_lineage_edge.from_node_id IS '源节点ID';
COMMENT ON COLUMN t_lineage_edge.to_node_id IS '目标节点ID';

CREATE INDEX IF NOT EXISTS idx_lineage_process_id ON t_lineage_edge(process_id);
CREATE INDEX IF NOT EXISTS idx_lineage_edge_graph_id ON t_lineage_edge(graph_id);
CREATE INDEX IF NOT EXISTS idx_lineage_edge_from ON t_lineage_edge(from_node_id);
CREATE INDEX IF NOT EXISTS idx_lineage_edge_to ON t_lineage_edge(to_node_id);