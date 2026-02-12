-- 使用现有的datamate数据库
\c datamate;

-- 清洗模板表
CREATE TABLE IF NOT EXISTS t_clean_template
(
    id          VARCHAR(64) PRIMARY KEY,
    name        VARCHAR(64) UNIQUE,
    description VARCHAR(256),
    created_by        VARCHAR(256),
    updated_by        VARCHAR(256),
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

COMMENT ON TABLE t_clean_template IS '清洗模板表';
COMMENT ON COLUMN t_clean_template.id IS '主键ID';
COMMENT ON COLUMN t_clean_template.name IS '模板名称';
COMMENT ON COLUMN t_clean_template.description IS '模板描述';
COMMENT ON COLUMN t_clean_template.created_at IS '创建时间';
COMMENT ON COLUMN t_clean_template.updated_at IS '更新时间';
COMMENT ON COLUMN t_clean_template.created_by IS '创建者';
COMMENT ON COLUMN t_clean_template.updated_by IS '更新者';

-- 清洗任务表
CREATE TABLE IF NOT EXISTS t_clean_task
(
    id                VARCHAR(64) PRIMARY KEY,
    name              VARCHAR(64) UNIQUE,
    description       VARCHAR(256),
    status            VARCHAR(256),
    src_dataset_id    VARCHAR(64),
    src_dataset_name  VARCHAR(64),
    dest_dataset_id   VARCHAR(64),
    dest_dataset_name VARCHAR(64),
    before_size       BIGINT,
    after_size        BIGINT,
    file_count        INTEGER,
    retry_count       INTEGER,
    started_at        TIMESTAMP,
    finished_at       TIMESTAMP,
    created_by        VARCHAR(256),
    updated_by        VARCHAR(256),
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE t_clean_task IS '清洗任务表';
COMMENT ON COLUMN t_clean_task.id IS '主键ID';
COMMENT ON COLUMN t_clean_task.name IS '任务名称';
COMMENT ON COLUMN t_clean_task.description IS '任务描述';
COMMENT ON COLUMN t_clean_task.status IS '任务状态';
COMMENT ON COLUMN t_clean_task.src_dataset_id IS '源数据集ID';
COMMENT ON COLUMN t_clean_task.src_dataset_name IS '源数据集名称';
COMMENT ON COLUMN t_clean_task.dest_dataset_id IS '目标数据集ID';
COMMENT ON COLUMN t_clean_task.dest_dataset_name IS '目标数据集名称';
COMMENT ON COLUMN t_clean_task.before_size IS '清洗前大小';
COMMENT ON COLUMN t_clean_task.after_size IS '清洗后大小';
COMMENT ON COLUMN t_clean_task.file_count IS '文件数量';
COMMENT ON COLUMN t_clean_task.retry_count IS '重试次数';
COMMENT ON COLUMN t_clean_task.started_at IS '开始时间';
COMMENT ON COLUMN t_clean_task.finished_at IS '完成时间';
COMMENT ON COLUMN t_clean_task.created_at IS '创建时间';
COMMENT ON COLUMN t_clean_task.updated_at IS '更新时间';
COMMENT ON COLUMN t_clean_task.created_by IS '创建者';
COMMENT ON COLUMN t_clean_task.updated_by IS '更新者';

-- 操作员实例表
CREATE TABLE IF NOT EXISTS t_operator_instance
(
    instance_id       VARCHAR(256),
    operator_id       VARCHAR(256),
    op_index          INTEGER,
    settings_override TEXT,
    PRIMARY KEY (instance_id, operator_id, op_index)
    );

COMMENT ON TABLE t_operator_instance IS '操作员实例表';
COMMENT ON COLUMN t_operator_instance.instance_id IS '实例ID';
COMMENT ON COLUMN t_operator_instance.operator_id IS '操作员ID';
COMMENT ON COLUMN t_operator_instance.op_index IS '操作序号';
COMMENT ON COLUMN t_operator_instance.settings_override IS '设置覆盖';

-- 清洗结果表
CREATE TABLE IF NOT EXISTS t_clean_result
(
    instance_id  VARCHAR(64),
    src_file_id  VARCHAR(64),
    dest_file_id VARCHAR(64),
    src_name     VARCHAR(256),
    dest_name    VARCHAR(256),
    src_type     VARCHAR(256),
    dest_type    VARCHAR(256),
    src_size     BIGINT,
    dest_size    BIGINT,
    status       VARCHAR(256),
    result       TEXT,
    PRIMARY KEY (instance_id, dest_file_id)
    );

COMMENT ON TABLE t_clean_result IS '清洗结果表';
COMMENT ON COLUMN t_clean_result.instance_id IS '实例ID';
COMMENT ON COLUMN t_clean_result.src_file_id IS '源文件ID';
COMMENT ON COLUMN t_clean_result.dest_file_id IS '目标文件ID';
COMMENT ON COLUMN t_clean_result.src_name IS '源文件名';
COMMENT ON COLUMN t_clean_result.dest_name IS '目标文件名';
COMMENT ON COLUMN t_clean_result.src_type IS '源文件类型';
COMMENT ON COLUMN t_clean_result.dest_type IS '目标文件类型';
COMMENT ON COLUMN t_clean_result.src_size IS '源文件大小';
COMMENT ON COLUMN t_clean_result.dest_size IS '目标文件大小';
COMMENT ON COLUMN t_clean_result.status IS '状态';
COMMENT ON COLUMN t_clean_result.result IS '结果';

-- 创建触发器用于自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
RETURN NEW;
END;
$$ language 'plpgsql';

-- 为 t_clean_template 表创建触发器
DROP TRIGGER IF EXISTS update_clean_template_updated_at ON t_clean_template;
CREATE TRIGGER update_clean_template_updated_at
    BEFORE UPDATE ON t_clean_template
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 插入初始数据 - 清洗模板
INSERT INTO t_clean_template (id, name, description)
VALUES
    ('550e8400-e29b-41d4-a716-446655440001', '安全与隐私合规处理模板', '针对敏感数据进行严格清洗，移除PII（个人身份信息）、政治敏感、暴力色情内容，适用于模型对外发布前的安全合规检查。'),
    ('661f9500-f3ac-52e5-b827-557766550002', 'LLM SFT高质量文本清洗模板', '旨在生成高质量、低噪声的训练数据。包含去除乱码、重复内容、繁简转换、全角转半角以及格式标准化处理。'),
    ('772a0611-a4bd-63f6-c938-668877660003', 'RAG知识库构建预处理模板', '专为RAG场景设计。重点去除目录、图注、XML/HTML标签等对向量检索无意义的噪声，并进行段落级去重以优化切片质量。'),
    ('883b1722-b5ce-7407-d049-779988770004', '原始Web爬虫数据清洗模板', '针对互联网爬取的脏数据进行清洗。重点去除Emoji表情、URL链接、HTML标签以及不可见字符。'),
    ('994c2833-c6df-8518-e150-880099880005', '多模态/CV模型训练预处理模板', '针对图像数据集处理。包含去除模糊/重复/相似图片，图片方向校正，目标检测预标注，以及尺寸和格式的统一化。')
ON CONFLICT (id) DO NOTHING;

INSERT INTO t_operator_instance (instance_id, operator_id, op_index, settings_override)
VALUES
    ('550e8400-e29b-41d4-a716-446655440001', 'PoliticalWordCleaner', 1, NULL),
    ('550e8400-e29b-41d4-a716-446655440001', 'SexualAndViolentWordCleaner', 2, NULL),
    ('550e8400-e29b-41d4-a716-446655440001', 'PiiDetector', 3, NULL),
    ('550e8400-e29b-41d4-a716-446655440001', 'AnonymizedIdNumber', 4, NULL),
    ('550e8400-e29b-41d4-a716-446655440001', 'AnonymizedCreditCardNumber', 5, NULL),
    ('550e8400-e29b-41d4-a716-446655440001', 'AnonymizedPhoneNumber', 6, NULL),
    ('550e8400-e29b-41d4-a716-446655440001', 'EmailNumberCleaner', 7, NULL),
    ('550e8400-e29b-41d4-a716-446655440001', 'AnonymizedIpAddress', 8, NULL)
ON CONFLICT (instance_id, operator_id, op_index) DO NOTHING;

INSERT INTO t_operator_instance (instance_id, operator_id, op_index, settings_override)
VALUES
    ('661f9500-f3ac-52e5-b827-557766550002', 'GrableCharactersCleaner', 1, NULL),
    ('661f9500-f3ac-52e5-b827-557766550002', 'InvisibleCharactersCleaner', 2, NULL),
    ('661f9500-f3ac-52e5-b827-557766550002', 'FullWidthCharacterCleaner', 3, NULL),
    ('661f9500-f3ac-52e5-b827-557766550002', 'TraditionalChineseCleaner', 4, NULL),
    ('661f9500-f3ac-52e5-b827-557766550002', 'FileWithShortOrLongLengthFilter', 5, '{"fileLength": [50, 8192]}'),
    ('661f9500-f3ac-52e5-b827-557766550002', 'FileWithHighRepeatPhraseRateFilter', 6, NULL),
    ('661f9500-f3ac-52e5-b827-557766550002', 'FileWithHighSpecialCharRateFilter', 7, NULL),
    ('661f9500-f3ac-52e5-b827-557766550002', 'DuplicateFilesFilter', 8, NULL)
ON CONFLICT (instance_id, operator_id, op_index) DO NOTHING;


INSERT INTO t_operator_instance (instance_id, operator_id, op_index, settings_override)
VALUES
    ('772a0611-a4bd-63f6-c938-668877660003', 'HtmlTagCleaner', 1, '{"removeTableTags": "false"}'), -- 表格对RAG可能有价值，暂不去除表格
    ('772a0611-a4bd-63f6-c938-668877660003', 'ContentCleaner', 2, NULL),
    ('772a0611-a4bd-63f6-c938-668877660003', 'LegendCleaner', 3, NULL),
    ('772a0611-a4bd-63f6-c938-668877660003', 'XMLTagCleaner', 4, NULL),
    ('772a0611-a4bd-63f6-c938-668877660003', 'UnicodeSpaceCleaner', 5, NULL),
    ('772a0611-a4bd-63f6-c938-668877660003', 'ExtraSpaceCleaner', 6, NULL),
    ('772a0611-a4bd-63f6-c938-668877660003', 'DuplicateSentencesFilter', 7, NULL),
    ('772a0611-a4bd-63f6-c938-668877660003', 'FileWithShortOrLongLengthFilter', 8, '{"fileLength": [20, 100000]}')
ON CONFLICT (instance_id, operator_id, op_index) DO NOTHING;

INSERT INTO t_operator_instance (instance_id, operator_id, op_index, settings_override)
VALUES
    ('883b1722-b5ce-7407-d049-779988770004', 'HtmlTagCleaner', 1, '{"removeTableTags": "true"}'),
    ('883b1722-b5ce-7407-d049-779988770004', 'AnonymizedUrlCleaner', 2, NULL),
    ('883b1722-b5ce-7407-d049-779988770004', 'EmojiCleaner', 3, NULL),
    ('883b1722-b5ce-7407-d049-779988770004', 'InvisibleCharactersCleaner', 4, NULL),
    ('883b1722-b5ce-7407-d049-779988770004', 'ExtraSpaceCleaner', 5, NULL),
    ('883b1722-b5ce-7407-d049-779988770004', 'DuplicateFilesFilter', 6, '{"fileDuplicateThreshold": 0.6}')
ON CONFLICT (instance_id, operator_id, op_index) DO NOTHING;

INSERT INTO t_operator_instance (instance_id, operator_id, op_index, settings_override)
VALUES
    ('994c2833-c6df-8518-e150-880099880005', 'ImgBlurredImagesCleaner', 1, NULL),
    ('994c2833-c6df-8518-e150-880099880005', 'ImgDuplicatedImagesCleaner', 2, NULL),
    ('994c2833-c6df-8518-e150-880099880005', 'ImgSimilarImagesCleaner', 3, NULL),
    ('994c2833-c6df-8518-e150-880099880005', 'ImgDirectionCorrect', 4, NULL),
    ('994c2833-c6df-8518-e150-880099880005', 'ImgResize', 5, '{"widthSize": 512, "heightSize": 512}'),
    ('994c2833-c6df-8518-e150-880099880005', 'ImgTypeUnify', 6, '{"imgType": "jpg"}')
ON CONFLICT (instance_id, operator_id, op_index) DO NOTHING;