-- 使用现有的datamate数据库
\c datamate;

-- 清洗模板表
CREATE TABLE IF NOT EXISTS t_clean_template
(
    id          VARCHAR(64) PRIMARY KEY,
    name        VARCHAR(64) UNIQUE,
    description VARCHAR(256),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by  VARCHAR(256)
    );

COMMENT ON TABLE t_clean_template IS '清洗模板表';
COMMENT ON COLUMN t_clean_template.id IS '主键ID';
COMMENT ON COLUMN t_clean_template.name IS '模板名称';
COMMENT ON COLUMN t_clean_template.description IS '模板描述';
COMMENT ON COLUMN t_clean_template.created_at IS '创建时间';
COMMENT ON COLUMN t_clean_template.updated_at IS '更新时间';
COMMENT ON COLUMN t_clean_template.created_by IS '创建者';

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
    ('26ae585c-8310-4679-adc0-e53215e6e69b', '文本清洗模板', '文本清洗模板'),
    ('4421504e-c6c9-4760-b55a-509d17429597', '图片清洗模板', '图片清洗模板')
    ON CONFLICT (id) DO NOTHING;

-- 插入初始数据 - 操作员实例（文本清洗模板）
INSERT INTO t_operator_instance (instance_id, operator_id, op_index, settings_override)
VALUES
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'FileWithShortOrLongLengthFilter', 1, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'FileWithHighRepeatWordRateFilter', 2, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'FileWithHighRepeatPhraseRateFilter', 3, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'FileWithHighSpecialCharRateFilter', 4, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'FileWithManySensitiveWordsFilter', 5, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'UnicodeSpaceCleaner', 6, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'ExtraSpaceCleaner', 7, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'FullWidthCharacterCleaner', 8, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'InvisibleCharactersCleaner', 9, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'ContentCleaner', 10, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'LegendCleaner', 11, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'EmojiCleaner', 12, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'HtmlTagCleaner', 13, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'TraditionalChineseCleaner', 14, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'GrableCharactersCleaner', 15, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'XMLTagCleaner', 16, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'DuplicateSentencesFilter', 17, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'DuplicateFilesFilter', 18, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'SexualAndViolentWordCleaner', 19, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'PoliticalWordCleaner', 20, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'AnonymizedPhoneNumber', 21, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'AnonymizedCreditCardNumber', 22, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'EmailNumberCleaner', 23, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'AnonymizedIpAddress', 24, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'AnonymizedIdNumber', 25, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'AnonymizedUrlCleaner', 26, NULL),
    ('26ae585c-8310-4679-adc0-e53215e6e69b', 'PiiDetector', 27, NULL)
    ON CONFLICT (instance_id, operator_id, op_index) DO NOTHING;

-- 插入初始数据 - 操作员实例（图片清洗模板）
INSERT INTO t_operator_instance (instance_id, operator_id, op_index, settings_override)
VALUES
    ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgBlurredImagesCleaner', 1, NULL),
    ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgDuplicatedImagesCleaner', 2, NULL),
    ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgSimilarImagesCleaner', 3, NULL),
    ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgBrightness', 4, NULL),
    ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgContrast', 5, NULL),
    ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgSaturation', 6, NULL),
    ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgSharpness', 7, NULL),
    ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgDenoise', 8, NULL),
    ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgShadowRemove', 9, NULL),
    ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgPerspectiveTransformation', 10, NULL),
    ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgDirectionCorrect', 11, NULL),
    ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgResize', 12, NULL),
    ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgTypeUnify', 13, NULL)
    ON CONFLICT (instance_id, operator_id, op_index) DO NOTHING;