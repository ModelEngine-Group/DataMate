-- 使用现有的datamate数据库
\c datamate;

-- 算子表
CREATE TABLE IF NOT EXISTS t_operator
(
    id          VARCHAR(64) PRIMARY KEY,
    name        VARCHAR(64) UNIQUE,
    description VARCHAR(255),
    version     VARCHAR(255),
    inputs      VARCHAR(255),
    outputs     VARCHAR(255),
    runtime     TEXT,
    settings    TEXT,
    file_name   TEXT,
    file_size   BIGINT,
    metrics     TEXT,
    is_star     BOOLEAN,
    usage_count INT DEFAULT 0,
    created_by  VARCHAR(255),
    updated_by  VARCHAR(255),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE t_operator IS '算子表';
COMMENT ON COLUMN t_operator.id IS '主键ID';
COMMENT ON COLUMN t_operator.name IS '算子名称';
COMMENT ON COLUMN t_operator.description IS '描述';
COMMENT ON COLUMN t_operator.version IS '版本';
COMMENT ON COLUMN t_operator.inputs IS '输入类型';
COMMENT ON COLUMN t_operator.outputs IS '输出类型';
COMMENT ON COLUMN t_operator.runtime IS '运行时信息';
COMMENT ON COLUMN t_operator.settings IS '设置信息';
COMMENT ON COLUMN t_operator.file_name IS '文件名';
COMMENT ON COLUMN t_operator.file_size IS '文件大小';
COMMENT ON COLUMN t_operator.metrics IS '性能指标';
COMMENT ON COLUMN t_operator.usage_count IS '使用次数';
COMMENT ON COLUMN t_operator.is_star IS '是否收藏';
COMMENT ON COLUMN t_operator.created_by IS '创建者';
COMMENT ON COLUMN t_operator.updated_by IS '更新者';
COMMENT ON COLUMN t_operator.created_at IS '创建时间';
COMMENT ON COLUMN t_operator.updated_at IS '更新时间';

-- 算子版本表
CREATE TABLE IF NOT EXISTS t_operator_release
(
    id           VARCHAR(64),
    version      VARCHAR(255),
    release_date TIMESTAMP,
    changelog    JSON,
    PRIMARY KEY (id, version)
);

-- 算子分类表
CREATE TABLE IF NOT EXISTS t_operator_category
(
    id        VARCHAR(64) PRIMARY KEY,
    name      VARCHAR(64) UNIQUE,
    value     VARCHAR(64) UNIQUE,
    type      VARCHAR(64),
    parent_id VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE t_operator_category IS '算子分类表';
COMMENT ON COLUMN t_operator_category.id IS '主键ID';
COMMENT ON COLUMN t_operator_category.name IS '分类名称';
COMMENT ON COLUMN t_operator_category.value IS '分类值';
COMMENT ON COLUMN t_operator_category.type IS '分类类型';
COMMENT ON COLUMN t_operator_category.parent_id IS '父分类ID';
COMMENT ON COLUMN t_operator_category.created_at IS '创建时间';

-- 算子分类关联表
CREATE TABLE IF NOT EXISTS t_operator_category_relation
(
    category_id VARCHAR(64),
    operator_id VARCHAR(64),
    PRIMARY KEY (category_id, operator_id)
);

COMMENT ON TABLE t_operator_category_relation IS '算子分类关联表';
COMMENT ON COLUMN t_operator_category_relation.category_id IS '分类ID';
COMMENT ON COLUMN t_operator_category_relation.operator_id IS '算子ID';

-- 外键约束
ALTER TABLE t_operator_category_relation
    ADD CONSTRAINT fk_operator_category_relation_category
    FOREIGN KEY (category_id)
    REFERENCES t_operator_category(id)
    ON DELETE CASCADE;

ALTER TABLE t_operator_category_relation
    ADD CONSTRAINT fk_operator_category_relation_operator
    FOREIGN KEY (operator_id)
    REFERENCES t_operator(id)
    ON DELETE CASCADE;

-- 创建触发器用于自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_t_operator_updated_at ON t_operator;
CREATE TRIGGER update_t_operator_updated_at
    BEFORE UPDATE ON t_operator
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 算子视图
CREATE OR REPLACE VIEW v_operator AS
SELECT
    o.id AS operator_id,
    o.name AS operator_name,
    o.description,
    o.version,
    o.inputs,
    o.outputs,
    o.runtime,
    o.settings,
    o.is_star,
    o.file_name,
    o.file_size,
    o.usage_count,
    o.metrics,
    o.created_at,
    o.updated_at,
    o.created_by,
    o.updated_by,
    toc.id AS category_id,
    toc.name AS category_name
FROM t_operator_category_relation tocr
LEFT JOIN t_operator o ON tocr.operator_id = o.id
LEFT JOIN t_operator_category toc ON tocr.category_id = toc.id;

COMMENT ON VIEW v_operator IS '算子视图';

INSERT INTO t_operator_category(id, name, value, type, parent_id)
VALUES ('64465bec-b46b-11f0-8291-00155d0e4808', '模态', 'modal',  'predefined', '0'),
       ('873000a2-65b3-474b-8ccc-4813c08c76fb', '语言', 'language', 'predefined', '0'),
       ('d8a5df7a-52a9-42c2-83c4-01062e60f597', '文本', 'text', 'predefined', '64465bec-b46b-11f0-8291-00155d0e4808'),
       ('de36b61c-9e8a-4422-8c31-d30585c7100f', '图片', 'image', 'predefined', '64465bec-b46b-11f0-8291-00155d0e4808'),
       ('42dd9392-73e4-458c-81ff-41751ada47b5', '音频', 'audio', 'predefined', '64465bec-b46b-11f0-8291-00155d0e4808'),
       ('a233d584-73c8-4188-ad5d-8f7c8dda9c27', '视频', 'video', 'predefined', '64465bec-b46b-11f0-8291-00155d0e4808'),
       ('4d7dbd77-0a92-44f3-9056-2cd62d4a71e4', '多模态', 'multimodal', 'predefined', '64465bec-b46b-11f0-8291-00155d0e4808'),
       ('9eda9d5d-072b-499b-916c-797a0a8750e1', 'Python', 'python', 'predefined', '873000a2-65b3-474b-8ccc-4813c08c76fb'),
       ('16e2d99e-eafb-44fc-acd0-f35a2bad28f8', '来源', 'origin', 'predefined', '0'),
       ('96a3b07a-3439-4557-a835-525faad60ca3', '系统预置', 'predefined', 'predefined', '16e2d99e-eafb-44fc-acd0-f35a2bad28f8'),
       ('ec2cdd17-8b93-4a81-88c4-ac9e98d10757', '用户上传', 'customized', 'predefined', '16e2d99e-eafb-44fc-acd0-f35a2bad28f8'),
       ('0ed75eea-e20b-11f0-88e6-00155d5c9528', '归属', 'vendor',  'predefined', '0'),
       ('431e7798-5426-4e1a-aae6-b9905a836b34', 'DataMate', 'datamate',  'predefined', '0ed75eea-e20b-11f0-88e6-00155d5c9528'),
       ('79b385b4-fde8-4617-bcba-02a176938996', 'DataJuicer', 'data-juicer',  'predefined', '0ed75eea-e20b-11f0-88e6-00155d5c9528'),
       ('f00eaa3e-96c1-4de4-96cd-9848ef5429ec', '其他', 'others',  'predefined', '0ed75eea-e20b-11f0-88e6-00155d5c9528')
ON CONFLICT DO NOTHING;

INSERT INTO t_operator
(id, name, description, version, inputs, outputs, runtime, settings, file_name, file_size, is_star, created_by, updated_by)
VALUES
('MineruFormatter', 'MinerU PDF文本抽取', '基于MinerU API，抽取PDF中的文本。', '1.0.0', 'text', 'text', null, '{"mineruApi":{"name":"Mineru Api地址","description":"指定mineru服务的api地址，默认为本地同一集群内地址。","type":"input","defaultVal":"http://datamate-mineru:8000","required":false},"exportType":{"name":"导出类型","description":"指定清洗结果文件类型。若指定为md且后续存在其他清洗算子，可能导致文件格式错乱。","type":"select","defaultVal":"markdown","required":false,"options":[{"label":"markdown","value":"md"},{"label":"txt","value":"txt"}]}}', '', 12288, false, 'system', 'system'),
('FileWithHighRepeatPhraseRateFilter', '文档词重复率检查', '去除重复词过多的文档。', '1.0.0', 'text', 'text', null, '{"repeatPhraseRatio": {"name": "文档词重复率", "description": "某个词的统计数/文档总词数 > 设定值，该文档被去除。", "type": "slider", "defaultVal": 0.5, "min": 0, "max": 1, "step": 0.1}, "hitStopwords": {"name": "去除停用词", "description": "统计重复词时，选择是否要去除停用词。", "type": "switch", "defaultVal": false, "required": true, "checkedLabel": "去除", "unCheckedLabel": "不去除"}}', '', 16384, false, 'system', 'system'),
('FileWithHighRepeatWordRateFilter', '文档字重复率检查', '去除重复字过多的文档。', '1.0.0', 'text', 'text', null, '{"repeatWordRatio": {"name": "文档字重复率", "description": "某个字的统计数/文档总字数 > 设定值，该文档被去除。", "type": "slider", "defaultVal": 0.5, "min": 0, "max": 1, "step": 0.1}}', '', 8192, false, 'system', 'system'),
('FileWithHighSpecialCharRateFilter', '文档特殊字符率检查', '去除特殊字符过多的文档。', '1.0.0', 'text', 'text', null, '{"specialCharRatio": {"name": "文档特殊字符率", "description": "特殊字符的统计数/文档总字数 > 设定值，该文档被去除。", "type": "slider", "defaultVal": 0.3, "min": 0, "max": 1, "step": 0.1}}', '', 5120, false, 'system', 'system'),
('DuplicateFilesFilter', '相似文档去除', '相似文档去除。', '1.0.0', 'text', 'text', null, '{"fileDuplicateThreshold": {"name": "文档相似度", "description": "基于MinHash算法和Jaccard相似度，计算当前文档与数据集中其它文档相似性，超过设定值，该文档被去除。", "type": "slider", "defaultVal": 0.5, "min": 0, "max": 1, "step": 0.1}}', '', 13312, false, 'system', 'system'),
('FileWithManySensitiveWordsFilter', '文档敏感词率检查', '去除敏感词过多的文档。', '1.0.0', 'text', 'text', null, '{"sensitiveWordsRate": {"name": "文档敏感词率", "description": "敏感词的字数/文档总字数 > 设定值，该文档被去除。", "type": "slider", "defaultVal": 0.01, "min": 0, "max": 1, "step": 0.01}}', '', 29696, false, 'system', 'system'),
('FileWithShortOrLongLengthFilter', '文档字数检查', '字数不在指定范围会被过滤掉。', '1.0.0', 'text', 'text', null, '{"fileLength": {"name": "文档字数", "description": "过滤字数不在指定范围内的文档，如[10,10000000]。若输入为空，则不对字数上/下限做限制。", "type": "range", "defaultVal": [10, 10000000], "min": 0, "max": 10000000000000000, "step": 1}}', '', 8192, false, 'system', 'system'),
('ContentCleaner', '文档目录去除', '去除文档中的目录。', '1.0.0', 'text', 'text', null, null, '', 4096, false, 'system', 'system'),
('AnonymizedCreditCardNumber', '信用卡号匿名化', '信用卡号匿名化', '1.0.0', 'text', 'text', null, null, '', 8192, false, 'system', 'system'),
('EmailNumberCleaner', '邮件地址匿名化', '邮件地址匿名化', '1.0.0', 'text', 'text', null, null, '', 4096, false, 'system', 'system'),
('EmojiCleaner', '文档表情去除', '去除文档中表情字符或者emoji符号。', '1.0.0', 'text', 'text', null, null, '', 5120, false, 'system', 'system'),
('ExtraSpaceCleaner', '多余空格去除', '移除文档首尾、句中或标点符号附近多余空格和 tab 等。', '1.0.0', 'text', 'text', null, null, '', 8192, false, 'system', 'system'),
('FullWidthCharacterCleaner', '全角转半角', '将文档中的所有全角字符转换成半角字符。', '1.0.0', 'text', 'text', null, null, '', 8192, false, 'system', 'system'),
('GrableCharactersCleaner', '文档乱码去除', '去除文档中的乱码和无意义的unicode。', '1.0.0', 'text', 'text', null, null, '', 4096, false, 'system', 'system'),
('HtmlTagCleaner', 'HTML标签去除', '移除文档中HTML标签，如 <html>、<dev>、<p> 等。', '1.0.0', 'text', 'text', null, '{"removeTableTags":{"name":"是否去除表格标签","description":"若为是，则会去除表格标签<tr><td>等。","type":"switch","defaultVal":"false","required":false,"checkedLabel":"是","unCheckedLabel":"否"}}', '', 12288, false, 'system', 'system'),
('AnonymizedIdNumber', '身份证号匿名化', '身份证号匿名化。', '1.0.0', 'text', 'text', null, null, '', 36864, false, 'system', 'system'),
('InvisibleCharactersCleaner', '不可见字符去除', '去除文档中的不可见字符，例如 0-31 号字符中的部分字符。', '1.0.0', 'text', 'text', null, null, '', 5120, false, 'system', 'system'),
('AnonymizedIpAddress', 'IP地址匿名化', 'IP地址匿名化', '1.0.0', 'text', 'text', null, null, '', 4096, false, 'system', 'system'),
('LegendCleaner', '图注表注去除', '去除文档中的图注、表注等内容。', '1.0.0', 'text', 'text', null, null, '', 4096, false, 'system', 'system'),
('AnonymizedPhoneNumber', '电话号码匿名化', '电话号码匿名化', '1.0.0', 'text', 'text', null, null, '', 4096, false, 'system', 'system'),
('PoliticalWordCleaner', '政治文本匿名化', '将政治文本进行匿名化。', '1.0.0', 'text', 'text', null, null, '', 8192, false, 'system', 'system'),
('DuplicateSentencesFilter', '文档局部内容去重', '文档局部内容去重。', '1.0.0', 'text', 'text', null, null, '', 5120, false, 'system', 'system'),
('SexualAndViolentWordCleaner', '暴力色情文本匿名化', '将暴力、色情文本进行匿名化。', '1.0.0', 'text', 'text', null, null, '', 20480, false, 'system', 'system'),
('TraditionalChineseCleaner', '繁体转简体', '将繁体转换为简体。', '1.0.0', 'text', 'text', null, null, '', 5120, false, 'system', 'system'),
('UnicodeSpaceCleaner', '空格标准化', '将文档中不同的 unicode 空格，如 u2008，转换为正常空格\\u0020。', '1.0.0', 'text', 'text', null, null, '', 8192, false, 'system', 'system'),
('AnonymizedUrlCleaner', 'URL网址匿名化', '将文档中的url网址匿名化。', '1.0.0', 'text', 'text', null, null, '', 4096, false, 'system', 'system'),
('XMLTagCleaner', 'XML标签去除', '去除XML中的标签。', '1.0.0', 'text', 'text', null, null, '', 4096, false, 'system', 'system'),
('ImgBlurredImagesCleaner', '模糊图片过滤', '去除模糊的图片。', '1.0.0', 'image', 'image', null, '{"blurredThreshold": {"name": "梯度函数值", "description": "梯度函数值取值越小，图片模糊度越高。", "type": "slider", "defaultVal": 1000, "min": 1, "max": 10000, "step": 1}}', '', 5120, false, 'system', 'system'),
('ImgBrightness', '图片亮度增强', '自适应调节图片的亮度。', '1.0.0', 'image', 'image', null, null, '', 4096, false, 'system', 'system'),
('ImgContrast', '图片对比度增强', '自适应调节图片的对比度。', '1.0.0', 'image', 'image', null, null, '', 4096, false, 'system', 'system'),
('ImgDenoise', '图片噪点去除', '去除图片中的噪点，主要适用于自然场景。', '1.0.0', 'image', 'image', null, null, '', 4096, false, 'system', 'system'),
('ImgDuplicatedImagesCleaner', '重复图片去除', '去除重复的图片。', '1.0.0', 'image', 'image', null, null, '', 8192, false, 'system', 'system'),
('ImgPerspectiveTransformation', '图片透视变换', '自适应校正图片的视角，主要适用于文档校正场景。', '1.0.0', 'image', 'image', null, null, '', 8192, false, 'system', 'system'),
('ImgResize', '图片重采样', '将图片放大或缩小到指定像素。', '1.0.0', 'image', 'image', null, '{"targetSize": {"name": "重采样尺寸", "name_en": "Resample Size", "type": "multiple", "properties": [{"type": "inputNumber", "name": "宽度", "description": "像素", "defaultVal": 256, "min": 1, "max": 4096, "step": 1}, {"type": "inputNumber", "name": "高度", "description": "像素", "defaultVal": 256, "min": 1, "max": 4096, "step": 1}]}}', '', 8192, false, 'system', 'system'),
('ImgSaturation', '图片饱和度增强', '自适应调节图片的饱和度，主要适用于自然场景图片。', '1.0.0', 'image', 'image', null, null, '', 4096, false, 'system', 'system'),
('ImgShadowRemove', '图片阴影去除', '去除图片中的阴影，主要适用于文档场景。', '1.0.0', 'image', 'image', null, null, '', 4096, false, 'system', 'system'),
('ImgSharpness', '图片锐度增强', '自适应调节图片的锐度，主要适用于自然场景图片。', '1.0.0', 'image', 'image', null, null, '', 4096, false, 'system', 'system'),
('ImgSimilarImagesCleaner', '相似图片去除', '去除相似的图片。', '1.0.0', 'image', 'image', null, '{"similarThreshold": {"name": "相似度", "description": "相似度取值越大，图片相似度越高。", "type": "slider", "defaultVal": 0.8, "min": 0, "max": 1, "step": 0.01}}', '', 14336, false, 'system', 'system'),
('ImgTypeUnify', '图片格式转换', '将图片编码格式统一为jpg、jpeg、png、bmp格式。', '1.0.0', 'image', 'image', null, '{"imgType": {"name": "图片编码格式", "type": "select", "defaultVal": "jpg", "options": [{"label": "jpg", "value": "jpg"}, {"label": "png", "value": "png"}, {"label": "jpeg", "value": "jpeg"}, {"label": "bmp", "value": "bmp"}]}}', '', 5120, false, 'system', 'system'),
('ImgDirectionCorrect', '图片方向校正', '将含有文字的图片校正到文字水平方向，主要适用于文档场景。', '1.0.0', 'image', 'image', null, null, '', 8192, false, 'system', 'system'),
('PiiDetector', '高级匿名化', '高级匿名化算子，检测命名实体并匿名化。', '1.0.0', 'text', 'text', null, null, '', 8192, false, 'system', 'system'),
('ObjectDetectionRectangle', '图像目标检测与预标注', '基于 YOLOv8 的图像目标检测算子。对输入图像进行目标检测，输出带矩形框与类别标签的标注图像，并生成结构化标注 JSON（包含类别、置信度与边界框坐标）。支持将检测结果导出为 Label Studio 兼容的 predictions 预标注格式（rectanglelabels），可在标注任务中直接加载并进行人工校正，从而显著降低人工标注成本并提升标注效率。', '1.0.0', 'image', 'image,json', null, null, '', 12288, false, 'system', 'system')
ON CONFLICT DO NOTHING;

INSERT INTO t_operator_release(id, version, release_date, changelog)
VALUES ('MineruFormatter', '1.0.0', '2026-03-30', '["aaa","bbb"]');

INSERT INTO t_operator_category_relation(category_id, operator_id)
SELECT c.id, o.id
FROM t_operator_category c
CROSS JOIN t_operator o
WHERE c.id IN ('d8a5df7a-52a9-42c2-83c4-01062e60f597', '9eda9d5d-072b-499b-916c-797a0a8750e1', '96a3b07a-3439-4557-a835-525faad60ca3', '431e7798-5426-4e1a-aae6-b9905a836b34')
AND o.id IN ('FileWithShortOrLongLengthFilter', 'FileWithHighRepeatPhraseRateFilter',
            'FileWithHighRepeatWordRateFilter', 'FileWithHighSpecialCharRateFilter', 'FileWithManySensitiveWordsFilter',
            'DuplicateFilesFilter', 'DuplicateSentencesFilter', 'AnonymizedCreditCardNumber', 'AnonymizedIdNumber',
            'AnonymizedIpAddress', 'AnonymizedPhoneNumber', 'AnonymizedUrlCleaner', 'HtmlTagCleaner', 'XMLTagCleaner',
            'ContentCleaner', 'EmailNumberCleaner', 'EmojiCleaner', 'ExtraSpaceCleaner', 'FullWidthCharacterCleaner',
            'GrableCharactersCleaner', 'InvisibleCharactersCleaner', 'LegendCleaner', 'PoliticalWordCleaner',
            'SexualAndViolentWordCleaner', 'TraditionalChineseCleaner', 'UnicodeSpaceCleaner', 'MineruFormatter',
            'PiiDetector')
ON CONFLICT DO NOTHING;

INSERT INTO t_operator_category_relation(category_id, operator_id)
SELECT c.id, o.id
FROM t_operator_category c
       CROSS JOIN t_operator o
WHERE c.id IN ('de36b61c-9e8a-4422-8c31-d30585c7100f', '9eda9d5d-072b-499b-916c-797a0a8750e1', '96a3b07a-3439-4557-a835-525faad60ca3', '431e7798-5426-4e1a-aae6-b9905a836b34')
    AND o.id IN ('ImgBlurredImagesCleaner', 'ImgBrightness', 'ImgContrast', 'ImgDenoise',
                 'ImgDuplicatedImagesCleaner', 'ImgPerspectiveTransformation', 'ImgResize', 'ImgSaturation',
                 'ImgShadowRemove', 'ImgSharpness', 'ImgSimilarImagesCleaner', 'ImgTypeUnify', 'ImgDirectionCorrect',
                 'ObjectDetectionRectangle')
ON CONFLICT DO NOTHING;


INSERT INTO t_operator
(id, name, description, version, inputs, outputs, runtime, settings, file_name, is_star, created_by, updated_by)
VALUES
    ('entity_attribute_aggregator', '实体属性聚合器', 'Summarizes a given attribute of an entity from a set of documents. 汇总一组文档中实体的给定属性。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('meta_tags_aggregator', '元标签聚合器', 'Merge similar meta tags into a single, unified tag. 将类似的元标记合并到一个统一的标记中。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('most_relevant_entities_aggregator', '最相关实体聚合器', 'Extracts and ranks entities closely related to a given entity from provided texts. 从提供的文本中提取与给定实体密切相关的实体并对其进行排名。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('nested_aggregator', '嵌套聚合器', 'Aggregates nested content from multiple samples into a single summary. 将多个示例中的嵌套内容聚合到单个摘要中。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('document_deduplicator', '文档去重器', 'Deduplicates samples at the document level using exact matching. 使用完全匹配在文档级别删除重复的样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('document_minhash_deduplicator', '文档MinHash去重器', 'Deduplicates samples at the document level using MinHash LSH. 使用MinHash LSH在文档级别删除重复样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('document_simhash_deduplicator', '文档SimHash去重器', 'Deduplicates samples at the document level using SimHash. 使用SimHash在文档级别删除重复的样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('image_deduplicator', '图像去重器', 'Deduplicates samples at the document level by exact matching of images. 通过图像的精确匹配在文档级别删除重复的样本。', '1.4.4', 'image', 'image', NULL, NULL, '', false, 'system', 'system'),
    ('ray_basic_deduplicator', 'Ray基础去重器', 'Backend for deduplicator. deduplicator的后端。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('ray_bts_minhash_deduplicator', 'Ray BTS MinHash去重器', 'A distributed implementation of Union-Find with load balancing. 具有负载平衡的Union-Find的分布式实现。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('ray_document_deduplicator', 'Ray文档去重器', 'Deduplicates samples at the document level using exact matching in Ray distributed mode. 在Ray分布式模式下使用精确匹配在文档级别删除重复的样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('ray_image_deduplicator', 'Ray图像去重器', 'Deduplicates samples at the document level using exact matching of images in Ray distributed mode. 在光线分布模式下使用图像的精确匹配在文档级别删除重复样本。', '1.4.4', 'image', 'image', NULL, NULL, '', false, 'system', 'system'),
    ('ray_video_deduplicator', 'Ray视频去重器', 'Deduplicates samples at document-level using exact matching of videos in Ray distributed mode. 在Ray分布式模式下使用视频的精确匹配在文档级删除重复样本。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('video_deduplicator', '视频去重器', 'Deduplicates samples at the document level using exact matching of videos. 使用视频的精确匹配在文档级别删除重复的样本。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('alphanumeric_filter', '字母数字过滤器', 'Filter to keep samples with an alphabet/numeric ratio within a specific range. 过滤器，以保持具有特定范围内的字母/数字比率的样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('audio_duration_filter', '音频时长过滤器', 'Keep data samples whose audio durations are within a specified range. 保留音频持续时间在指定范围内的数据样本。', '1.4.4', 'audio', 'audio', NULL, NULL, '', false, 'system', 'system'),
    ('audio_nmf_snr_filter', '音频NMF信噪比过滤器', 'Keep data samples whose audio Signal-to-Noise Ratios (SNRs) are within a specified range. 保留音频信噪比 (snr) 在指定范围内的数据样本。', '1.4.4', 'audio', 'audio', NULL, NULL, '', false, 'system', 'system'),
    ('audio_size_filter', '音频大小过滤器', 'Keep data samples based on the size of their audio files. 根据音频文件的大小保留数据样本。', '1.4.4', 'audio', 'audio', NULL, NULL, '', false, 'system', 'system'),
    ('average_line_length_filter', '平均行长过滤器', 'Filter to keep samples with average line length within a specific range. 过滤器，以保持平均线长度在特定范围内的样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('character_repetition_filter', '字符重复过滤器', 'Filter to keep samples with character-level n-gram repetition ratio within a specific range. 过滤器将具有字符级n-gram重复比的样本保持在特定范围内。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('flagged_words_filter', '标记词过滤器', 'Filter to keep samples with flagged-word ratio in a specified range. 过滤器将标记词比率的样本保留在指定范围内。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('general_field_filter', '通用字段过滤器', 'Filter to keep samples based on a general field filter condition. 根据常规字段筛选条件保留样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('image_aesthetics_filter', '图像美学过滤器', 'Filter to keep samples with aesthetics scores within a specific range. 过滤以保持美学分数在特定范围内的样品。', '1.4.4', 'image', 'image', NULL, NULL, '', false, 'system', 'system'),
    ('image_aspect_ratio_filter', '图像长宽比过滤器', 'Filter to keep samples with image aspect ratio within a specific range. 过滤器，以保持样本的图像纵横比在特定范围内。', '1.4.4', 'image', 'image', NULL, NULL, '', false, 'system', 'system'),
    ('image_face_count_filter', '图像人脸计数过滤器', 'Filter to keep samples with the number of faces within a specific range. 过滤以保持样本的面数在特定范围内。', '1.4.4', 'image', 'image', NULL, NULL, '', false, 'system', 'system'),
    ('image_face_ratio_filter', '图像人脸占比过滤器', 'Filter to keep samples with face area ratios within a specific range. 过滤以保持面面积比在特定范围内的样本。', '1.4.4', 'image', 'image', NULL, NULL, '', false, 'system', 'system'),
    ('image_nsfw_filter', '图像NSFW过滤器', 'Filter to keep samples whose images have nsfw scores in a specified range. 过滤器保留其图像的nsfw分数在指定范围内的样本。', '1.4.4', 'image', 'image', NULL, NULL, '', false, 'system', 'system'),
    ('image_pair_similarity_filter', '图像对相似度过滤器', 'Filter to keep image pairs with similarities between images within a specific range. 过滤器将图像之间具有相似性的图像对保持在特定范围内。', '1.4.4', 'image', 'image', NULL, NULL, '', false, 'system', 'system'),
    ('image_shape_filter', '图像形状过滤器', 'Filter to keep samples with image shape (width, height) within specific ranges. 过滤器，以保持样本的图像形状 (宽度，高度) 在特定的范围内。', '1.4.4', 'image', 'image', NULL, NULL, '', false, 'system', 'system'),
    ('image_size_filter', '图像大小过滤器', 'Keep data samples whose image size (in Bytes/KB/MB/...) is within a specific range. 保留图像大小 (以字节/KB/MB/... 为单位) 在特定范围内的数据样本。', '1.4.4', 'image', 'image', NULL, NULL, '', false, 'system', 'system'),
    ('image_text_matching_filter', '图文匹配过滤器', 'Filter to keep samples with image-text matching scores within a specific range. 过滤器将图像文本匹配分数的样本保持在特定范围内。', '1.4.4', 'multimodal', 'multimodal', NULL, NULL, '', false, 'system', 'system'),
    ('image_text_similarity_filter', '图文相似度过滤器', 'Filter to keep samples with image-text similarity within a specified range. 过滤器将具有图像-文本相似性的样本保持在指定范围内。', '1.4.4', 'multimodal', 'multimodal', NULL, NULL, '', false, 'system', 'system'),
    ('image_watermark_filter', '图像水印过滤器', 'Filter to keep samples whose images have no watermark with high probability. 过滤器以保持其图像没有水印的样本具有高概率。', '1.4.4', 'image', 'image', NULL, NULL, '', false, 'system', 'system'),
    ('in_context_influence_filter', '上下文影响过滤器', 'Filter to keep texts based on their in-context influence on a validation set. 过滤以根据文本在上下文中对验证集的影响来保留文本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('instruction_following_difficulty_filter', '指令跟随难度过滤器', 'Filter to keep texts based on their instruction following difficulty (IFD, https://arxiv.org/abs/2308.12032) score. 过滤以保持文本基于他们的指令跟随难度 (IFD， https://arxiv.org/abs/ 2308.12032) 分数。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('language_id_score_filter', '语种识别得分过滤器', 'Filter to keep samples in a specific language with a confidence score above a threshold. 过滤器以保留置信度高于阈值的特定语言的样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('llm_analysis_filter', 'LLM分析过滤器', 'Base filter class for leveraging LLMs to analyze and filter data samples. 用于利用LLMs分析和过滤数据样本的基本筛选器类。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('llm_difficulty_score_filter', 'LLM难度得分过滤器', 'Filter to keep samples with high difficulty scores estimated by an LLM. 过滤器以保留由LLM估计的高难度分数的样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('llm_perplexity_filter', 'LLM困惑度过滤器', 'Filter to keep samples with perplexity scores within a specified range, computed using a specified LLM. 过滤器将困惑分数的样本保留在指定范围内，使用指定的LLM计算。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('llm_quality_score_filter', 'LLM质量得分过滤器', 'Filter to keep samples with a high quality score estimated by a language model. 过滤器，以保留具有语言模型估计的高质量分数的样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('llm_task_relevance_filter', 'LLM任务相关性过滤器', 'Filter to keep samples with high relevance scores to validation tasks estimated by an LLM. 过滤器以保留与LLM估计的验证任务具有高相关性分数的样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('maximum_line_length_filter', '最大行长过滤器', 'Filter to keep samples with a maximum line length within a specified range. 筛选器将最大行长度的样本保持在指定范围内。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('perplexity_filter', '困惑度过滤器', 'Filter to keep samples with perplexity score in a specified range. 过滤以保持困惑分数在指定范围内的样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('phrase_grounding_recall_filter', '短语定位召回过滤器', 'Filter to keep samples based on the phrase grounding recall of phrases extracted from text in images. 根据从图像中的文本中提取的短语接地召回来过滤以保留样本。', '1.4.4', 'multimodal', 'multimodal', NULL, NULL, '', false, 'system', 'system'),
    ('special_characters_filter', '特殊字符过滤器', 'Filter to keep samples with special-character ratio within a specific range. 过滤器，以将具有特殊字符比率的样本保持在特定范围内。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('specified_field_filter', '指定字段过滤器', 'Filter samples based on the specified field information. 根据指定的字段信息筛选样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('specified_numeric_field_filter', '指定数值字段过滤器', 'Filter samples based on a specified numeric field value. 根据指定的数值字段值筛选样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('stopwords_filter', '停用词过滤器', 'Filter to keep samples with stopword ratio within a specified range. 过滤器将停止词比率的样本保持在指定范围内。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('suffix_filter', '后缀过滤器', 'Filter to keep samples with specified suffix. 过滤器以保留具有指定后缀的样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('text_action_filter', '文本动作过滤器', 'Filter to keep texts that contain a minimum number of actions. 过滤以保留包含最少数量操作的文本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('text_embd_similarity_filter', '文本嵌入相似度过滤器', 'Filter to keep texts whose average embedding similarity to a set of given validation texts falls within a specific range. 过滤器，以保留与一组给定验证文本的平均嵌入相似度在特定范围内的文本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('text_entity_dependency_filter', '文本实体依赖过滤器', 'Identify and filter text samples based on entity dependencies. 根据实体依赖关系识别和过滤文本样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('text_length_filter', '文本长度过滤器', 'Filter to keep samples with total text length within a specific range. 过滤以保持文本总长度在特定范围内的样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('text_pair_similarity_filter', '文本对相似度过滤器', 'Filter to keep text pairs with similarities within a specific range. 过滤以将具有相似性的文本对保持在特定范围内。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('token_num_filter', 'Token数量过滤器', 'Filter to keep samples with a total token number within a specified range. 筛选器将总令牌数的样本保留在指定范围内。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('video_aesthetics_filter', '视频美学过滤器', 'Filter to keep data samples with aesthetics scores for specified frames in the videos within a specific range. 过滤器将视频中指定帧的美学得分数据样本保留在特定范围内。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('video_aspect_ratio_filter', '视频长宽比过滤器', 'Filter to keep samples with video aspect ratio within a specific range. 过滤器将视频纵横比的样本保持在特定范围内。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('video_duration_filter', '视频时长过滤器', 'Keep data samples whose videos'' durations are within a specified range. 保留视频持续时间在指定范围内的数据样本。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('video_frames_text_similarity_filter', '视频帧文本相似度过滤器', 'Filter to keep samples based on the similarity between video frame images and text within a specific range. 根据视频帧图像和文本之间的相似性进行过滤，以保持样本在特定范围内。', '1.4.4', 'multimodal', 'multimodal', NULL, NULL, '', false, 'system', 'system'),
    ('video_motion_score_filter', '视频运动得分过滤器', 'Filter to keep samples with video motion scores within a specific range. 过滤器将视频运动分数的样本保持在特定范围内。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('video_motion_score_raft_filter', '视频RAFT运动得分过滤器', 'Filter to keep samples with video motion scores within a specified range. 过滤器将视频运动分数的样本保持在指定范围内。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('video_nsfw_filter', '视频NSFW过滤器', 'Filter to keep samples whose videos have nsfw scores in a specified range. 过滤器以保留其视频的nsfw分数在指定范围内的样本。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('video_ocr_area_ratio_filter', '视频OCR面积占比过滤器', 'Keep data samples whose detected text area ratios for specified frames in the video are within a specified range. 保留检测到的视频中指定帧的文本面积比率在指定范围内的数据样本。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('video_resolution_filter', '视频分辨率过滤器', 'Keep data samples whose videos'' resolutions are within a specified range. 保留视频分辨率在指定范围内的数据样本。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('video_tagging_from_frames_filter', '视频帧标签过滤器', 'Filter to keep samples whose videos contain specified tags. 过滤器以保留其视频包含指定标签的样本。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('video_watermark_filter', '视频水印过滤器', 'Filter to keep samples whose videos have no watermark with high probability. 过滤器以保持其视频具有高概率没有水印的样本。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('word_repetition_filter', '单词重复过滤器', 'Filter to keep samples with word-level n-gram repetition ratio within a specific range. 过滤器将单词级n-gram重复比率的样本保持在特定范围内。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('words_num_filter', '词数过滤器', 'Filter to keep samples with a total word count within a specified range. 过滤器将样本的总字数保持在指定范围内。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('key_value_grouper', '键值分组器', 'Groups samples into batches based on values in specified keys. 根据指定键中的值将样本分组为批处理。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('naive_grouper', '朴素分组器', 'Group all samples in a dataset into a single batched sample. 将数据集中的所有样本分组为单个批处理样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('naive_reverse_grouper', '朴素反向分组器', 'Split batched samples into individual samples. 将批处理的样品分成单个样品。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('audio_add_gaussian_noise_mapper', '音频高斯噪声添加映射器', 'Mapper to add Gaussian noise to audio samples. 映射器将高斯噪声添加到音频样本。', '1.4.4', 'audio', 'audio', NULL, NULL, '', false, 'system', 'system'),
    ('audio_ffmpeg_wrapped_mapper', '音频FFmpeg封装映射器', 'Wraps FFmpeg audio filters for processing audio files in a dataset. 包装FFmpeg音频过滤器，用于处理数据集中的音频文件。', '1.4.4', 'audio', 'audio', NULL, NULL, '', false, 'system', 'system'),
    ('calibrate_qa_mapper', 'QA校准映射器', 'Calibrates question-answer pairs based on reference text using an API model. 使用API模型根据参考文本校准问答对。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('calibrate_query_mapper', '查询校准映射器', 'Calibrate query in question-answer pairs based on reference text. 基于参考文本校准问答对中的查询。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('calibrate_response_mapper', '回复校准映射器', 'Calibrate response in question-answer pairs based on reference text. 根据参考文本校准问答对中的回答。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('chinese_convert_mapper', '中文简繁转换映射器', 'Mapper to convert Chinese text between Traditional, Simplified, and Japanese Kanji. 映射器在繁体、简体和日文汉字之间转换中文文本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('clean_copyright_mapper', '版权清洗映射器', 'Cleans copyright comments at the beginning of text samples. 清除文本示例开头的版权注释。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('clean_email_mapper', '邮箱清洗映射器', 'Cleans email addresses from text samples using a regular expression. 使用正则表达式从文本示例中清除电子邮件地址。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('clean_html_mapper', 'HTML清洗映射器', 'Cleans HTML code from text samples, converting HTML to plain text. 从文本示例中清除HTML代码，将HTML转换为纯文本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('clean_ip_mapper', 'IP清洗映射器', 'Cleans IPv4 and IPv6 addresses from text samples. 从文本示例中清除IPv4和IPv6地址。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('clean_links_mapper', '链接清洗映射器', 'Mapper to clean links like http/https/ftp in text samples. 映射器来清理链接，如文本示例中的http/https/ftp。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('detect_character_attributes_mapper', '角色属性检测映射器', 'Takes an image, a caption, and main character names as input to extract the characters'' attributes. 根据给定的图像、图像描述信息和（多个）角色名称，提取图像中主要角色的属性。', '1.4.4', 'multimodal', 'multimodal', NULL, NULL, '', false, 'system', 'system'),
    ('detect_character_locations_mapper', '角色位置检测映射器', 'Given an image and a list of main character names, extract the bounding boxes for each present character. 给定一张图像和主要角色的名称列表，提取每个在场角色的边界框。(YOLOE + MLLM)', '1.4.4', 'multimodal', 'multimodal', NULL, NULL, '', false, 'system', 'system'),
    ('detect_main_character_mapper', '主要角色检测映射器', 'Extract all main character names based on the given image and its caption. 根据给定的图像及其图像描述，提取所有主要角色的名字。', '1.4.4', 'multimodal', 'multimodal', NULL, NULL, '', false, 'system', 'system'),
    ('dialog_intent_detection_mapper', '对话意图检测映射器', 'Generates user''s intent labels in a dialog by analyzing the history, query, and response. 通过分析历史记录、查询和响应，在对话框中生成用户的意图标签。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('dialog_sentiment_detection_mapper', '对话情感检测映射器', 'Generates sentiment labels and analysis for user queries in a dialog. 在对话框中为用户查询生成情绪标签和分析。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('dialog_sentiment_intensity_mapper', '对话情感强度映射器', 'Mapper to predict user''s sentiment intensity in a dialog, ranging from -5 to 5. Mapper预测用户在对话框中的情绪强度，范围从-5到5。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('dialog_topic_detection_mapper', '对话主题检测映射器', 'Generates user''s topic labels and analysis in a dialog. 在对话框中生成用户的主题标签和分析。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('download_file_mapper', '文件下载映射器', 'Mapper to download URL files to local files or load them into memory. 映射器将URL文件下载到本地文件或将其加载到内存中。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('expand_macro_mapper', '宏展开映射器', 'Expands macro definitions in the document body of LaTeX samples. 展开LaTeX示例文档主体中的宏定义。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('extract_entity_attribute_mapper', '实体属性提取映射器', 'Extracts attributes for given entities from the text and stores them in the sample''s metadata. 从文本中提取给定实体的属性，并将其存储在示例的元数据中。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('extract_entity_relation_mapper', '实体关系提取映射器', 'Extracts entities and relations from text to build a knowledge graph. 从文本中提取实体和关系以构建知识图谱。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('extract_event_mapper', '事件提取映射器', 'Extracts events and relevant characters from the text. 从文本中提取事件和相关字符。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('extract_keyword_mapper', '关键词提取映射器', 'Generate keywords for the text. 为文本生成关键字。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('extract_nickname_mapper', '昵称提取映射器', 'Extracts nickname relationships in the text using a language model. 使用语言模型提取文本中的昵称关系。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('extract_support_text_mapper', '支撑文本提取映射器', 'Extracts a supporting sub-text from the original text based on a given summary. 根据给定的摘要从原始文本中提取支持子文本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('extract_tables_from_html_mapper', 'HTML表格提取映射器', 'Extracts tables from HTML content and stores them in a specified field. 从HTML内容中提取表并将其存储在指定字段中。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('fix_unicode_mapper', 'Unicode修复映射器', 'Fixes unicode errors in text samples. 修复文本示例中的unicode错误。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('generate_qa_from_examples_mapper', '示例生成QA映射器', 'Generates question and answer pairs from examples using a Hugging Face model. 使用拥抱面部模型从示例生成问题和答案对。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('generate_qa_from_text_mapper', '文本生成QA映射器', 'Generates question and answer pairs from text using a specified model. 使用指定的模型从文本生成问题和答案对。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('image_blur_mapper', '图像模糊映射器', 'Blurs images in the dataset with a specified probability and blur type. 使用指定的概率和模糊类型对数据集中的图像进行模糊处理。', '1.4.4', 'image', 'image', NULL, NULL, '', false, 'system', 'system'),
    ('image_captioning_from_gpt4v_mapper', 'GPT4V图像描述映射器', 'Generates text captions for images using the GPT-4 Vision model. 使用GPT-4视觉模型为图像生成文本标题。', '1.4.4', 'multimodal', 'multimodal', NULL, NULL, '', false, 'system', 'system'),
    ('image_captioning_mapper', '图像描述映射器', 'Generates image captions using a Hugging Face model and appends them to samples. 使用拥抱面部模型生成图像标题，并将其附加到样本中。', '1.4.4', 'multimodal', 'multimodal', NULL, NULL, '', false, 'system', 'system'),
    ('image_detection_yolo_mapper', 'YOLO图像检测映射器', 'Perform object detection using YOLO on images and return bounding boxes and class labels. 使用YOLO对图像执行对象检测，并返回边界框和类标签。', '1.4.4', 'image', 'image', NULL, NULL, '', false, 'system', 'system'),
    ('image_diffusion_mapper', '图像扩散生成映射器', 'Generate images using a diffusion model based on provided captions. 使用基于提供的字幕的扩散模型生成图像。', '1.4.4', 'multimodal', 'multimodal', NULL, NULL, '', false, 'system', 'system'),
    ('image_face_blur_mapper', '图像人脸模糊映射器', 'Mapper to blur faces detected in images. 映射器模糊图像中检测到的人脸。', '1.4.4', 'image', 'image', NULL, NULL, '', false, 'system', 'system'),
    ('image_remove_background_mapper', '图像去背景映射器', 'Mapper to remove the background of images. 映射器删除图像的背景。', '1.4.4', 'image', 'image', NULL, NULL, '', false, 'system', 'system'),
    ('image_segment_mapper', '图像分割映射器', 'Perform segment-anything on images and return the bounding boxes. 对图像执行segment-任何操作并返回边界框。', '1.4.4', 'image', 'image', NULL, NULL, '', false, 'system', 'system'),
    ('image_tagging_mapper', '图像打标映射器', 'Generates image tags for each image in the sample. 为样本中的每个图像生成图像标记。', '1.4.4', 'image', 'image', NULL, NULL, '', false, 'system', 'system'),
    ('imgdiff_difference_area_generator_mapper', 'ImgDiff差异区域生成映射器', 'Generates and filters bounding boxes for image pairs based on similarity, segmentation, and text matching. 根据相似性、分割和文本匹配生成和过滤图像对的边界框。', '1.4.4', 'image', 'image', NULL, NULL, '', false, 'system', 'system'),
    ('imgdiff_difference_caption_generator_mapper', 'ImgDiff差异描述生成映射器', 'Generates difference captions for bounding box regions in two images. 为两个图像中的边界框区域生成差异字幕。', '1.4.4', 'multimodal', 'multimodal', NULL, NULL, '', false, 'system', 'system'),
    ('mllm_mapper', 'MLLM视觉问答映射器', 'Mapper to use MLLMs for visual question answering tasks. Mapper使用MLLMs进行视觉问答任务。', '1.4.4', 'multimodal', 'multimodal', NULL, NULL, '', false, 'system', 'system'),
    ('nlpaug_en_mapper', 'NLPAug英语增强映射器', 'Augments English text samples using various methods from the nlpaug library. 使用nlpaug库中的各种方法增强英语文本样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('nlpcda_zh_mapper', 'NLPCDA中文增强映射器', 'Augments Chinese text samples using the nlpcda library. 使用nlpcda库扩充中文文本样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('optimize_prompt_mapper', 'Prompt优化映射器', 'Optimize prompts based on existing ones in the same batch. 根据同一批次中的现有提示优化提示。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('optimize_qa_mapper', 'QA优化映射器', 'Mapper to optimize question-answer pairs. 映射器来优化问题-答案对。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('optimize_query_mapper', '查询优化映射器', 'Optimize queries in question-answer pairs to make them more specific and detailed. 优化问答对中的查询，使其更加具体和详细。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('optimize_response_mapper', '回复优化映射器', 'Optimize response in question-answer pairs to be more detailed and specific. 优化问答对中的响应，使其更加详细和具体。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('pair_preference_mapper', '配对偏好映射器', 'Mapper to construct paired preference samples by generating a rejected response and its reason. Mapper通过生成拒绝响应及其原因来构造成对的偏好样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('punctuation_normalization_mapper', '标点归一化映射器', 'Normalizes unicode punctuations to their English equivalents in text samples. 将unicode标点规范化为文本示例中的英语等效项。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('python_file_mapper', 'Python文件映射器', 'Executes a Python function defined in a file on input data. 对输入数据执行文件中定义的Python函数。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('python_lambda_mapper', 'Python Lambda映射器', 'Mapper for applying a Python lambda function to data samples. Mapper，用于将Python lambda函数应用于数据样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('query_intent_detection_mapper', '查询意图检测映射器', 'Predicts the user''s intent label and corresponding score for a given query. 为给定查询预测用户的意图标签和相应的分数。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('query_sentiment_detection_mapper', '查询情感检测映射器', 'Predicts user''s sentiment label (''negative'', ''neutral'', ''positive'') in a query. 在查询中预测用户的情绪标签 (“负面” 、 “中性” 、 “正面”)。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('query_topic_detection_mapper', '查询主题检测映射器', 'Predicts the topic label and its corresponding score for a given query. 预测给定查询的主题标签及其相应的分数。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('relation_identity_mapper', '关系识别映射器', 'Identify the relation between two entities in a given text. 确定给定文本中两个实体之间的关系。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('remove_bibliography_mapper', '参考书目移除映射器', 'Removes bibliography sections at the end of LaTeX documents. 删除LaTeX文档末尾的参考书目部分。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('remove_comments_mapper', '注释移除映射器', 'Removes comments from documents, currently supporting only ''tex'' format. 从文档中删除注释，当前仅支持 “文本” 格式。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('remove_header_mapper', '页眉移除映射器', 'Removes headers at the beginning of documents in LaTeX samples. 删除LaTeX示例中文档开头的标题。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('remove_long_words_mapper', '长词移除映射器', 'Mapper to remove long words within a specific range. 映射器删除特定范围内的长词。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('remove_non_chinese_character_mapper', '非中文字符移除映射器', 'Removes non-Chinese characters from text samples. 从文本样本中删除非中文字符。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('remove_repeat_sentences_mapper', '重复句移除映射器', 'Mapper to remove repeat sentences in text samples. 映射器删除文本样本中的重复句子。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('remove_specific_chars_mapper', '指定字符移除映射器', 'Removes specific characters from text samples. 从文本示例中删除特定字符。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('remove_table_text_mapper', '表格文本移除映射器', 'Mapper to remove table texts from text samples. 映射器从文本样本中删除表文本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('remove_words_with_incorrect_substrings_mapper', '错误子串单词移除映射器', 'Mapper to remove words containing specified incorrect substrings. 映射程序删除包含指定的不正确子字符串的单词。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('replace_content_mapper', '内容替换映射器', 'Replaces content in the text that matches a specific regular expression pattern with a designated replacement string. 用指定的替换字符串替换与特定正则表达式模式匹配的文本中的内容。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('sdxl_prompt2prompt_mapper', 'SDXL Prompt2Prompt映射器', 'Generates pairs of similar images using the SDXL model. 使用SDXL模型生成成对的相似图像。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('sentence_augmentation_mapper', '句子增强映射器', 'Augments sentences by generating enhanced versions using a Hugging Face model. 通过使用拥抱面部模型生成增强版本来增强句子。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('sentence_split_mapper', '句子切分映射器', 'Splits text samples into individual sentences based on the specified language. 根据指定的语言将文本样本拆分为单个句子。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('text_chunk_mapper', '文本分块映射器', 'Split input text into chunks based on specified criteria. 根据指定的条件将输入文本拆分为块。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('text_tagging_by_prompt_mapper', 'Prompt文本打标映射器', 'Mapper to generate text tags using prompt with LLM. Mapper使用带有LLM的prompt生成文本标记。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('vggt_mapper', 'VGGT视频提取映射器', 'Input a video of a single scene, and use VGGT to extract information including Camera Pose, Depth Maps, Point Maps, and 3D Point Tracks. 输入单个场景的视频，并使用VGGT提取包括相机姿态、深度图、点图和3D点轨迹的信息。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('video_captioning_from_audio_mapper', '音频生成视频描述映射器', 'Mapper to caption a video according to its audio streams based on Qwen-Audio model. 映射器根据基于qwen-audio模型的音频流为视频添加字幕。', '1.4.4', 'multimodal', 'multimodal', NULL, NULL, '', false, 'system', 'system'),
    ('video_captioning_from_frames_mapper', '帧生成视频描述映射器', 'Generates video captions from sampled frames using an image-to-text model. 使用图像到文本模型从采样帧生成视频字幕。', '1.4.4', 'multimodal', 'multimodal', NULL, NULL, '', false, 'system', 'system'),
    ('video_captioning_from_summarizer_mapper', '摘要生成视频描述映射器', 'Mapper to generate video captions by summarizing several kinds of generated texts (captions from video/audio/frames, tags from audio/frames, ...). 映射器通过总结几种生成的文本 (来自视频/音频/帧的字幕，来自音频/帧的标签，...) 来生成视频字幕。', '1.4.4', 'multimodal', 'multimodal', NULL, NULL, '', false, 'system', 'system'),
    ('video_captioning_from_video_mapper', '视频生成视频描述映射器', 'Generates video captions using a Hugging Face video-to-text model and sampled video frames. 使用拥抱面部视频到文本模型和采样视频帧生成视频字幕。', '1.4.4', 'multimodal', 'multimodal', NULL, NULL, '', false, 'system', 'system'),
    ('video_captioning_from_vlm_mapper', 'VLM视频描述映射器', 'Generates video captions using a VLM that accepts videos as inputs. 使用接受视频作为输入的VLM生成视频字幕。', '1.4.4', 'multimodal', 'multimodal', NULL, NULL, '', false, 'system', 'system'),
    ('video_depth_estimation_mapper', '视频深度估计映射器', 'Perform depth estimation on the video. 对视频进行深度估计。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('video_extract_frames_mapper', '视频抽帧映射器', 'Mapper to extract frames from video files according to specified methods. 映射器根据指定的方法从视频文件中提取帧。', '1.4.4', 'multimodal', 'multimodal', NULL, NULL, '', false, 'system', 'system'),
    ('video_face_blur_mapper', '视频人脸模糊映射器', 'Mapper to blur faces detected in videos. 映射器模糊在视频中检测到的人脸。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('video_ffmpeg_wrapped_mapper', '视频FFmpeg封装映射器', 'Wraps FFmpeg video filters for processing video files in a dataset. 包装FFmpeg视频过滤器，用于处理数据集中的视频文件。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('video_hand_reconstruction_mapper', '视频手部重建映射器', 'Use the WiLoR model for hand localization and reconstruction. 使用WiLoR模型进行手部定位和重建。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('video_object_segmenting_mapper', '视频对象分割映射器', 'Text-guided semantic segmentation of valid objects throughout the video (YOLOE + SAM2). 在整个视频中对有效对象进行文本引导的语义分割 (YOLOE SAM2)。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('video_remove_watermark_mapper', '视频去水印映射器', 'Remove watermarks from videos based on specified regions. 根据指定区域从视频中删除水印。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('video_resize_aspect_ratio_mapper', '视频宽高比调整映射器', 'Resizes videos to fit within a specified aspect ratio range. 调整视频大小以适应指定的宽高比范围。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('video_resize_resolution_mapper', '视频分辨率调整映射器', 'Resizes video resolution based on specified width and height constraints. 根据指定的宽度和高度限制调整视频分辨率。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('video_split_by_duration_mapper', '视频按时长切分映射器', 'Splits videos into segments based on a specified duration. 根据指定的持续时间将视频拆分为多个片段。', '1.4.4', 'multimodal', 'multimodal', NULL, NULL, '', false, 'system', 'system'),
    ('video_split_by_key_frame_mapper', '视频关键帧切分映射器', 'Splits a video into segments based on key frames. 根据关键帧将视频分割为多个片段。', '1.4.4', 'multimodal', 'multimodal', NULL, NULL, '', false, 'system', 'system'),
    ('video_split_by_scene_mapper', '视频场景切分映射器', 'Splits videos into scene clips based on detected scene changes. 根据检测到的场景变化将视频拆分为场景剪辑。', '1.4.4', 'multimodal', 'multimodal', NULL, NULL, '', false, 'system', 'system'),
    ('video_tagging_from_audio_mapper', '音频视频打标映射器', 'Generates video tags from audio streams using the Audio Spectrogram Transformer. 使用音频频谱图转换器从音频流生成视频标签。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('video_tagging_from_frames_mapper', '帧视频打标映射器', 'Generates video tags from frames extracted from videos. 从视频中提取的帧生成视频标签。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('video_whole_body_pose_estimation_mapper', '视频全身姿态估计映射器', 'Input a video containing people, and use the DWPose model to extract the body, hand, feet, and face keypoints of the human subjects in the video, i.e., 2D Whole-body Pose Estimation. 输入包含人的视频，并使用DWPose模型来提取视频中人类主体的身体、手、脚和面部关键点，即2D全身姿态估计。', '1.4.4', 'video', 'video', NULL, NULL, '', false, 'system', 'system'),
    ('whitespace_normalization_mapper', '空白字符归一化映射器', 'Normalizes various types of whitespace characters to standard spaces in text samples. 将文本样本中各种类型的空白字符规范化为标准空格。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('frequency_specified_field_selector', '频率指定字段选择器', 'Selector to filter samples based on the frequency of a specified field. 选择器根据指定字段的频率过滤样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('random_selector', '随机选择器', 'Randomly selects a subset of samples from the dataset. 从数据集中随机选择样本子集。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('range_specified_field_selector', '范围指定字段选择器', 'Selects a range of samples based on the sorted values of a specified field. 根据指定字段的排序值选择采样范围。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('tags_specified_field_selector', '标签指定字段选择器', 'Selector to filter samples based on the tags of a specified field. 选择器根据指定字段的标签过滤样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system'),
    ('topk_specified_field_selector', 'TopK指定字段选择器', 'Selects top samples based on the sorted values of a specified field. 根据指定字段的排序值选择顶部样本。', '1.4.4', 'text', 'text', NULL, NULL, '', false, 'system', 'system')
ON CONFLICT DO NOTHING;

INSERT INTO t_operator_category_relation(category_id, operator_id)
SELECT c.id, o.id
FROM t_operator_category c
         CROSS JOIN t_operator o
WHERE c.id IN ('d8a5df7a-52a9-42c2-83c4-01062e60f597', '9eda9d5d-072b-499b-916c-797a0a8750e1',
               '96a3b07a-3439-4557-a835-525faad60ca3', '79b385b4-fde8-4617-bcba-02a176938996')
  AND o.id IN
      ('entity_attribute_aggregator', 'meta_tags_aggregator', 'most_relevant_entities_aggregator', 'nested_aggregator',
       'document_deduplicator', 'document_minhash_deduplicator', 'document_simhash_deduplicator',
       'ray_basic_deduplicator', 'ray_bts_minhash_deduplicator', 'ray_document_deduplicator', 'alphanumeric_filter',
       'average_line_length_filter', 'character_repetition_filter', 'flagged_words_filter', 'general_field_filter',
       'in_context_influence_filter', 'instruction_following_difficulty_filter', 'language_id_score_filter',
       'llm_analysis_filter', 'llm_difficulty_score_filter', 'llm_perplexity_filter', 'llm_quality_score_filter',
       'llm_task_relevance_filter', 'maximum_line_length_filter', 'perplexity_filter', 'special_characters_filter',
       'specified_field_filter', 'specified_numeric_field_filter', 'stopwords_filter', 'suffix_filter',
       'text_action_filter', 'text_embd_similarity_filter', 'text_entity_dependency_filter', 'text_length_filter',
       'text_pair_similarity_filter', 'token_num_filter', 'word_repetition_filter', 'words_num_filter',
       'key_value_grouper', 'naive_grouper', 'naive_reverse_grouper', 'calibrate_qa_mapper', 'calibrate_query_mapper',
       'calibrate_response_mapper', 'chinese_convert_mapper', 'clean_copyright_mapper', 'clean_email_mapper',
       'clean_html_mapper', 'clean_ip_mapper', 'clean_links_mapper', 'dialog_intent_detection_mapper',
       'dialog_sentiment_detection_mapper', 'dialog_sentiment_intensity_mapper', 'dialog_topic_detection_mapper',
       'download_file_mapper', 'expand_macro_mapper', 'extract_entity_attribute_mapper',
       'extract_entity_relation_mapper', 'extract_event_mapper', 'extract_keyword_mapper', 'extract_nickname_mapper',
       'extract_support_text_mapper', 'extract_tables_from_html_mapper', 'fix_unicode_mapper',
       'generate_qa_from_examples_mapper', 'generate_qa_from_text_mapper', 'nlpaug_en_mapper', 'nlpcda_zh_mapper',
       'optimize_prompt_mapper', 'optimize_qa_mapper', 'optimize_query_mapper', 'optimize_response_mapper',
       'pair_preference_mapper', 'punctuation_normalization_mapper', 'python_file_mapper', 'python_lambda_mapper',
       'query_intent_detection_mapper', 'query_sentiment_detection_mapper', 'query_topic_detection_mapper',
       'relation_identity_mapper', 'remove_bibliography_mapper', 'remove_comments_mapper', 'remove_header_mapper',
       'remove_long_words_mapper', 'remove_non_chinese_character_mapper', 'remove_repeat_sentences_mapper',
       'remove_specific_chars_mapper', 'remove_table_text_mapper', 'remove_words_with_incorrect_substrings_mapper',
       'replace_content_mapper', 'sdxl_prompt2prompt_mapper', 'sentence_augmentation_mapper', 'sentence_split_mapper',
       'text_chunk_mapper', 'text_tagging_by_prompt_mapper', 'whitespace_normalization_mapper',
       'frequency_specified_field_selector', 'random_selector', 'range_specified_field_selector',
       'tags_specified_field_selector', 'topk_specified_field_selector')
ON CONFLICT DO NOTHING;

INSERT INTO t_operator_category_relation(category_id, operator_id)
SELECT c.id, o.id
FROM t_operator_category c
         CROSS JOIN t_operator o
WHERE c.id IN ('de36b61c-9e8a-4422-8c31-d30585c7100f', '9eda9d5d-072b-499b-916c-797a0a8750e1',
               '96a3b07a-3439-4557-a835-525faad60ca3', '79b385b4-fde8-4617-bcba-02a176938996')
  AND o.id IN ('image_deduplicator', 'ray_image_deduplicator', 'image_aesthetics_filter', 'image_aspect_ratio_filter',
               'image_face_count_filter', 'image_face_ratio_filter', 'image_nsfw_filter',
               'image_pair_similarity_filter', 'image_shape_filter', 'image_size_filter', 'image_watermark_filter',
               'image_blur_mapper', 'image_detection_yolo_mapper', 'image_face_blur_mapper',
               'image_remove_background_mapper', 'image_segment_mapper', 'image_tagging_mapper',
               'imgdiff_difference_area_generator_mapper')
ON CONFLICT DO NOTHING;

INSERT INTO t_operator_category_relation(category_id, operator_id)
SELECT c.id, o.id
FROM t_operator_category c
         CROSS JOIN t_operator o
WHERE c.id IN ('42dd9392-73e4-458c-81ff-41751ada47b5', '9eda9d5d-072b-499b-916c-797a0a8750e1',
               '96a3b07a-3439-4557-a835-525faad60ca3', '79b385b4-fde8-4617-bcba-02a176938996')
  AND o.id IN ('audio_duration_filter', 'audio_nmf_snr_filter', 'audio_size_filter', 'audio_add_gaussian_noise_mapper',
               'audio_ffmpeg_wrapped_mapper')
ON CONFLICT DO NOTHING;

INSERT INTO t_operator_category_relation(category_id, operator_id)
SELECT c.id, o.id
FROM t_operator_category c
         CROSS JOIN t_operator o
WHERE c.id IN ('a233d584-73c8-4188-ad5d-8f7c8dda9c27', '9eda9d5d-072b-499b-916c-797a0a8750e1',
               '96a3b07a-3439-4557-a835-525faad60ca3', '79b385b4-fde8-4617-bcba-02a176938996')
  AND o.id IN ('ray_video_deduplicator', 'video_deduplicator', 'video_aesthetics_filter', 'video_aspect_ratio_filter',
               'video_duration_filter', 'video_motion_score_filter', 'video_motion_score_raft_filter',
               'video_nsfw_filter', 'video_ocr_area_ratio_filter', 'video_resolution_filter',
               'video_tagging_from_frames_filter', 'video_watermark_filter', 'vggt_mapper',
               'video_depth_estimation_mapper', 'video_face_blur_mapper', 'video_ffmpeg_wrapped_mapper',
               'video_hand_reconstruction_mapper', 'video_object_segmenting_mapper', 'video_remove_watermark_mapper',
               'video_resize_aspect_ratio_mapper', 'video_resize_resolution_mapper', 'video_tagging_from_audio_mapper',
               'video_tagging_from_frames_mapper', 'video_whole_body_pose_estimation_mapper')
ON CONFLICT DO NOTHING;

INSERT INTO t_operator_category_relation(category_id, operator_id)
SELECT c.id, o.id
FROM t_operator_category c
         CROSS JOIN t_operator o
WHERE c.id IN ('4d7dbd77-0a92-44f3-9056-2cd62d4a71e4', '9eda9d5d-072b-499b-916c-797a0a8750e1',
               '96a3b07a-3439-4557-a835-525faad60ca3', '79b385b4-fde8-4617-bcba-02a176938996')
  AND o.id IN ('image_text_matching_filter', 'image_text_similarity_filter', 'phrase_grounding_recall_filter',
               'video_frames_text_similarity_filter', 'detect_character_attributes_mapper',
               'detect_character_locations_mapper', 'detect_main_character_mapper',
               'image_captioning_from_gpt4v_mapper', 'image_captioning_mapper', 'image_diffusion_mapper',
               'imgdiff_difference_caption_generator_mapper', 'mllm_mapper', 'video_captioning_from_audio_mapper',
               'video_captioning_from_frames_mapper', 'video_captioning_from_summarizer_mapper',
               'video_captioning_from_video_mapper', 'video_captioning_from_vlm_mapper', 'video_extract_frames_mapper',
               'video_split_by_duration_mapper', 'video_split_by_key_frame_mapper', 'video_split_by_scene_mapper')
ON CONFLICT DO NOTHING;
