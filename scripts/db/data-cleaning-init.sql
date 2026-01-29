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

-- 插入初始数据 - 资产流水处理模板（将五个算子串成流水）
INSERT INTO t_clean_template (id, name, description)
VALUES
    ('5d7a8f20-0a1b-4c2d-8f3e-123456789abc', '资产流水处理模板', '基于 FlowDataGen -> FlowDocToImg -> FlowImgAug -> FlowSealAdd -> FlowQAGen 的处理流水')
ON CONFLICT (id) DO NOTHING;

-- 插入初始数据 - 操作员实例（资产流水处理模板）
INSERT INTO t_operator_instance (instance_id, operator_id, op_index, settings_override)
VALUES
    -- 1) 先生成带内容的 Word 文档（FlowDataGenOperator）
    ('5d7a8f20-0a1b-4c2d-8f3e-123456789abc', 'FlowDataGenOperator', 1, NULL),
    -- 2) 将生成的 Word 文档转为图片（FlowDocToImgOperator）
    ('5d7a8f20-0a1b-4c2d-8f3e-123456789abc', 'FlowDocToImgOperator', 2, NULL),
    -- 3) 对图片进行增强合成（FlowImgAugOperator）
    ('5d7a8f20-0a1b-4c2d-8f3e-123456789abc', 'FlowImgAugOperator', 3, NULL),
    -- 4) 在图片上添加印章（FlowSealAddOperator）
    ('5d7a8f20-0a1b-4c2d-8f3e-123456789abc', 'FlowSealAddOperator', 4, NULL),
    -- 5) 基于处理后的图片生成多模态 QA（FlowQAGenOperator）
    ('5d7a8f20-0a1b-4c2d-8f3e-123456789abc', 'FlowQAGenOperator', 5, NULL)
ON CONFLICT (instance_id, operator_id, op_index) DO NOTHING;

-- 插入初始数据 - 保险业务处理模板（Insurance flow）
INSERT INTO t_clean_template (id, name, description)
VALUES
    ('9b130084-538d-40f3-92f2-a9fab6af65ba', '社保参保处理模板', '社保参保文档生成 -> 转图片 -> 图片增强 -> QA生成 的流水模板')
ON CONFLICT (id) DO NOTHING;

-- 插入初始数据 - 操作员实例（保险业务模板）
INSERT INTO t_operator_instance (instance_id, operator_id, op_index, settings_override)
VALUES
    -- 1) 生成社保参保证明数据 CSV （InsuranceDataGenOperator）
    ('9b130084-538d-40f3-92f2-a9fab6af65ba', 'InsuranceDataGenOperator', 1, NULL),
    -- 2) 根据模板生成社保证明文档（InsuranceDocGenOperator）
    ('9b130084-538d-40f3-92f2-a9fab6af65ba', 'InsuranceDocGenOperator', 2, NULL),
    -- 3) 文档转图片（InsuranceDocToImgOperator）
    ('9b130084-538d-40f3-92f2-a9fab6af65ba', 'InsuranceDocToImgOperator', 3, NULL),
    -- 4) 图片增强合成（InsuranceImgAugOperator）
    ('9b130084-538d-40f3-92f2-a9fab6af65ba', 'InsuranceImgAugOperator', 4, NULL),
    -- 5) 生成 QA 对（InsuranceAnnotationGenOperator）
    ('9b130084-538d-40f3-92f2-a9fab6af65ba', 'InsuranceAnnotationGenOperator', 5, NULL)
ON CONFLICT (instance_id, operator_id, op_index) DO NOTHING;

-- 插入初始数据 - 收入处理模板（income flow）
INSERT INTO t_clean_template (id, name, description)
VALUES
    ('cd1eb467-08c2-4fa0-82b5-947124b5f965', '收入证明生成模板', '收入证明生成的流水模板')
ON CONFLICT (id) DO NOTHING;

INSERT INTO t_operator_instance (instance_id, operator_id, op_index, settings_override)
VALUES
    -- 1) 生成社保参保证明数据 CSV （IncomeCertificateGenerator）
    ('cd1eb467-08c2-4fa0-82b5-947124b5f965', 'IncomeCertificateGenerator', 1, NULL)
ON CONFLICT (instance_id, operator_id, op_index) DO NOTHING;

-- 插入初始数据 - 贷款调查报告合成模板（Loan Report flow）
INSERT INTO t_clean_template (id, name, description)
VALUES
    ('f25d4993-aa7b-4fd9-ad74-cbd7b0d8c468', '贷款调查报告合成模板', '贷款报告数据生成 -> 模板填充 -> 文档转图片 -> 场景合成 -> QA生成 的流水模板')
ON CONFLICT (id) DO NOTHING;

-- 插入初始数据 - 操作员实例（贷款调查报告模板）
INSERT INTO t_operator_instance (instance_id, operator_id, op_index, settings_override)
VALUES
    -- 1) 生成贷款报告数据
    ('f25d4993-aa7b-4fd9-ad74-cbd7b0d8c468', 'LoanReportDataGenerator', 1, '{"batchCount":10, "startSequence":0}'),
    -- 2) 将数据填充到Word模板
    ('f25d4993-aa7b-4fd9-ad74-cbd7b0d8c468', 'LoanReportFiller', 2, NULL),
    -- 3) 将生成的 Word 转为图片（DPI/保留PDF 设置）
    ('f25d4993-aa7b-4fd9-ad74-cbd7b0d8c468', 'LoanReportWordToImageConverter', 3, '{"dpi":300, "keep_pdf": false}'),
    -- 4) 将文档与实景背景合成（场景模式）
    ('f25d4993-aa7b-4fd9-ad74-cbd7b0d8c468', 'LoanReportDocumentSynthesizer', 4, '{"enable_watermark": false, "enable_shadow": false, "scene_mode": "auto"}'),
    -- 5) 基于图片/文本生成 QA 数据集
    ('f25d4993-aa7b-4fd9-ad74-cbd7b0d8c468', 'LoanReportQADatasetGenerator', 5, '{"train_ratio":80, "val_ratio":10, "test_ratio":10, "doc_type":"个人贷款调查报告"}')
ON CONFLICT (instance_id, operator_id, op_index) DO NOTHING;

-- 1. 插入营业执照全流程处理模板 (t_clean_template)
INSERT INTO t_clean_template (id, name, description)
VALUES (
    'd06eaa82-19c8-4783-bf55-eaed889ad533',
    '营业执照全流程生成模板',
    '包含：数据随机生成 -> 模板图像合成 -> 真实场景模拟 -> 多模态标注生成 的全自动流水线',
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    updated_at = CURRENT_TIMESTAMP;

-- 2. 插入操作员实例，串联算子流水 (t_operator_instance)
-- 逻辑顺序：
INSERT INTO t_operator_instance (instance_id, operator_id, op_index, settings_override)
VALUES
    -- 步骤1: 随机数据生成
    ('d06eaa82-19c8-4783-bf55-eaed889ad533', 'LicenseDataGeneratorOperator', 1, NULL),
    -- 步骤2: 图像合成渲染
    ('d06eaa82-19c8-4783-bf55-eaed889ad533', 'LicenseImageComposerOperator', 2, NULL),
    -- 步骤3: 真实场景模拟（阴影、斜拍、背景融合）
    ('d06eaa82-19c8-4783-bf55-eaed889ad533', 'LicenseSceneSimulatorOperator', 3, NULL),
    -- 步骤4: 自动化标注生成（生成训练用的对话数据）
    ('d06eaa82-19c8-4783-bf55-eaed889ad533', 'LicenseAnnotationGeneratorOperator', 4, NULL)
ON CONFLICT (instance_id, operator_id, op_index) DO NOTHING;

-- ============================================================
-- 个人所得税（Tax）业务模板定义
-- 包含：DataGen -> DocGen -> DocToImg -> ImgAug -> QAGen 全流程
-- ============================================================

-- 1. 插入清洗模板定义
INSERT INTO t_clean_template (id, name, description)
VALUES
    ('a8b9c0d1-e2f3-4455-6677-8899aabbccdd', '个人所得税数据生成模板', '个人所得税完税证明全流程：数据生成 -> 文档生成 -> 图片转换 -> 图片增强 -> QA生成')
ON CONFLICT (id) DO NOTHING;

-- 2. 插入操作员实例（定义流水线步骤）
INSERT INTO t_operator_instance (instance_id, operator_id, op_index, settings_override)
VALUES
    -- 1) 生成模拟数据 (CSV/JSON)
    ('a8b9c0d1-e2f3-4455-6677-8899aabbccdd', 'TaxDataGeneratorOperator', 1, NULL),

    -- 2) 基于数据填充 Word 模板
    ('a8b9c0d1-e2f3-4455-6677-8899aabbccdd', 'TaxDocGenOperator', 2, NULL),

    -- 3) 将 Word 文档转换为图片
    ('a8b9c0d1-e2f3-4455-6677-8899aabbccdd', 'TaxDocToImgOperator', 3, NULL),

    -- 4) 图片增强（背景合成、阴影、扭曲等）
    ('a8b9c0d1-e2f3-4455-6677-8899aabbccdd', 'TaxImgAugOperator', 4, NULL),

    -- 5) 生成 QA 问答对和训练集
    ('a8b9c0d1-e2f3-4455-6677-8899aabbccdd', 'TaxQAGenOperator', 5, NULL)
ON CONFLICT (instance_id, operator_id, op_index) DO NOTHING;

