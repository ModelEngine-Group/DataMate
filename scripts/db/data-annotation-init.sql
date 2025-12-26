use datamate;

CREATE TABLE t_dm_annotation_templates (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID',
    name VARCHAR(100) NOT NULL COMMENT '模板名称',
    description VARCHAR(500) COMMENT '模板描述',
    data_type VARCHAR(50) NOT NULL COMMENT '数据类型: image/text/audio/video/timeseries',
    labeling_type VARCHAR(50) NOT NULL COMMENT '标注类型: classification/detection/segmentation/ner/relation/etc',
    configuration JSON NOT NULL COMMENT '标注配置（包含labels定义等）',
    style VARCHAR(32) NOT NULL COMMENT '样式配置: horizontal/vertical',
    category VARCHAR(50) DEFAULT 'custom' COMMENT '模板分类: medical/general/custom/system',
    built_in BOOLEAN DEFAULT FALSE COMMENT '是否系统内置模板',
    version VARCHAR(20) DEFAULT '1.0' COMMENT '模板版本',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted_at TIMESTAMP NULL COMMENT '删除时间（软删除）',
    INDEX idx_data_type (data_type),
    INDEX idx_labeling_type (labeling_type),
    INDEX idx_category (category),
    INDEX idx_built_in (built_in)
) COMMENT='标注配置模板表';

CREATE TABLE t_dm_labeling_projects (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID',
    dataset_id VARCHAR(36) NOT NULL COMMENT '数据集ID',
    name VARCHAR(100) NOT NULL COMMENT '项目名称',
    labeling_project_id VARCHAR(8) NOT NULL COMMENT 'Label Studio项目ID',
    template_id VARCHAR(36) NULL COMMENT '使用的模板ID',
    configuration JSON COMMENT '项目配置（可能包含对模板的自定义修改）',
    progress JSON COMMENT '项目进度信息',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted_at TIMESTAMP NULL COMMENT '删除时间（软删除）',
    FOREIGN KEY (template_id) REFERENCES t_dm_annotation_templates(id) ON DELETE SET NULL,
    INDEX idx_dataset_id (dataset_id),
    INDEX idx_template_id (template_id),
    INDEX idx_labeling_project_id (labeling_project_id)
) COMMENT='标注项目表';


-- 内置标注模板初始化数据
-- 这些模板将在系统首次启动时自动创建
-- 使用 INSERT ... ON DUPLICATE KEY UPDATE 来覆盖已存在的记录

-- 1. 图像分类模板
INSERT INTO t_dm_annotation_templates (
    id, name, description, data_type, labeling_type,
    configuration, style, category, built_in, version, created_at
) VALUES (
    'tpl-image-classification-001',
    '图像分类',
    '简单的多标签图像分类模板',
    '图像',
    '分类',
    JSON_OBJECT(
        'labels', JSON_ARRAY(
            JSON_OBJECT(
                'fromName', 'choice',
                'toName', 'image',
                'type', 'Choices',
                'options', JSON_ARRAY('Cat', 'Dog', 'Bird', 'Other'),
                'required', true,
                'description', '选择最符合图像内容的标签'
            )
        ),
        'objects', JSON_ARRAY(
            JSON_OBJECT(
                'name', 'image',
                'type', 'Image',
                'value', '$image'
            )
        )
    ),
    'horizontal',
    '计算机视觉',
    1,
    '1.0.0',
    NOW()
)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description),
    data_type = VALUES(data_type),
    labeling_type = VALUES(labeling_type),
    configuration = VALUES(configuration),
    style = VALUES(style),
    category = VALUES(category),
    built_in = VALUES(built_in),
    version = VALUES(version),
    updated_at = NOW();


-- 2. 目标检测模板（矩形框）
INSERT INTO t_dm_annotation_templates (
    id, name, description, data_type, labeling_type,
    configuration, style, category, built_in, version, created_at
) VALUES (
    'tpl-object-detection-001',
    '目标检测（边界框）',
    '使用矩形边界框进行目标检测',
    '图像',
    '目标检测',
    JSON_OBJECT(
        'labels', JSON_ARRAY(
            JSON_OBJECT(
                'fromName', 'label',
                'toName', 'image',
                'type', 'RectangleLabels',
                'labels', JSON_ARRAY('Person', 'Vehicle', 'Animal', 'Object'),
                'required', false,
                'description', '在图像中框出目标并标注类别'
            )
        ),
        'objects', JSON_ARRAY(
            JSON_OBJECT(
                'name', 'image',
                'type', 'Image',
                'value', '$image'
            )
        )
    ),
    'horizontal',
    '计算机视觉',
    1,
    '1.0.0',
    NOW()
)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description),
    data_type = VALUES(data_type),
    labeling_type = VALUES(labeling_type),
    configuration = VALUES(configuration),
    style = VALUES(style),
    category = VALUES(category),
    built_in = VALUES(built_in),
    version = VALUES(version),
    updated_at = NOW();


-- 3. 图像分割模板（多边形）
INSERT INTO t_dm_annotation_templates (
    id, name, description, data_type, labeling_type,
    configuration, style, category, built_in, version, created_at
) VALUES (
    'tpl-image-segmentation-001',
    '图像分割（多边形）',
    '使用多边形标注进行语义分割',
    '图像',
    '分割',
    JSON_OBJECT(
        'labels', JSON_ARRAY(
            JSON_OBJECT(
                'fromName', 'label',
                'toName', 'image',
                'type', 'PolygonLabels',
                'labels', JSON_ARRAY('Background', 'Foreground', 'Person', 'Car'),
                'required', false,
                'description', '使用多边形框选需要分割的区域'
            )
        ),
        'objects', JSON_ARRAY(
            JSON_OBJECT(
                'name', 'image',
                'type', 'Image',
                'value', '$image'
            )
        )
    ),
    'horizontal',
    '计算机视觉',
    1,
    '1.0.0',
    NOW()
)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description),
    data_type = VALUES(data_type),
    labeling_type = VALUES(labeling_type),
    configuration = VALUES(configuration),
    style = VALUES(style),
    category = VALUES(category),
    built_in = VALUES(built_in),
    version = VALUES(version),
    updated_at = NOW();


-- 4. 文本分类模板
INSERT INTO t_dm_annotation_templates (
    id, name, description, data_type, labeling_type,
    configuration, style, category, built_in, version, created_at
) VALUES (
    'tpl-text-classification-001',
    '文本情感分类',
    '将文本中表达的情感划分到预定义的类别',
    '文本',
    '分类',
    JSON_OBJECT(
        'labels', JSON_ARRAY(
            JSON_OBJECT(
                'fromName', 'choice',
                'toName', 'text',
                'type', 'Choices',
                'options', JSON_ARRAY('Positive', 'Negative', 'Neutral'),
                'required', true,
                'description', '对文本的情感或类别进行选择'
            )
        ),
        'objects', JSON_ARRAY(
            JSON_OBJECT(
                'name', 'text',
                'type', 'Text',
                'value', '$text'
            )
        )
    ),
    'vertical',
    '自然语言处理',
    1,
    '1.0.0',
    NOW()
)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description),
    data_type = VALUES(data_type),
    labeling_type = VALUES(labeling_type),
    configuration = VALUES(configuration),
    style = VALUES(style),
    category = VALUES(category),
    built_in = VALUES(built_in),
    version = VALUES(version),
    updated_at = NOW();


-- 5. 命名实体识别（NER）
INSERT INTO t_dm_annotation_templates (
    id, name, description, data_type, labeling_type,
    configuration, style, category, built_in, version, created_at
) VALUES (
    'tpl-ner-001',
    '命名实体识别',
    '从文本中抽取并标注命名实体',
    '文本',
    '实体识别',
    JSON_OBJECT(
        'labels', JSON_ARRAY(
            JSON_OBJECT(
                'fromName', 'label',
                'toName', 'text',
                'type', 'Labels',
                'labels', JSON_ARRAY('PERSON', 'ORG', 'LOC', 'DATE', 'MISC'),
                'required', false,
                'description', '在文本中标注人物、地点等实体'
            )
        ),
        'objects', JSON_ARRAY(
            JSON_OBJECT(
                'name', 'text',
                'type', 'Text',
                'value', '$text'
            )
        )
    ),
    'vertical',
    '自然语言处理',
    1,
    '1.0.0',
    NOW()
)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description),
    data_type = VALUES(data_type),
    labeling_type = VALUES(labeling_type),
    configuration = VALUES(configuration),
    style = VALUES(style),
    category = VALUES(category),
    built_in = VALUES(built_in),
    version = VALUES(version),
    updated_at = NOW();


-- 6. 音频分类模板
INSERT INTO t_dm_annotation_templates (
    id, name, description, data_type, labeling_type,
    configuration, style, category, built_in, version, created_at
) VALUES (
    'tpl-audio-classification-001',
    '音频分类',
    '将音频片段划分到不同类别',
    '音频',
    '分类',
    JSON_OBJECT(
        'labels', JSON_ARRAY(
            JSON_OBJECT(
                'fromName', 'choice',
                'toName', 'audio',
                'type', 'Choices',
                'options', JSON_ARRAY('Speech', 'Music', 'Noise', 'Silence'),
                'required', true,
                'description', '选择音频片段对应的类别'
            )
        ),
        'objects', JSON_ARRAY(
            JSON_OBJECT(
                'name', 'audio',
                'type', 'Audio',
                'value', '$audio'
            )
        )
    ),
    'horizontal',
    '音频',
    1,
    '1.0.0',
    NOW()
)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description),
    data_type = VALUES(data_type),
    labeling_type = VALUES(labeling_type),
    configuration = VALUES(configuration),
    style = VALUES(style),
    category = VALUES(category),
    built_in = VALUES(built_in),
    version = VALUES(version),
    updated_at = NOW();


-- 7. 文本多标签分类模板
INSERT INTO t_dm_annotation_templates (
    id, name, description, data_type, labeling_type,
    configuration, style, category, built_in, version, created_at
) VALUES (
    'tpl-text-multilabel-001',
    '文本多标签分类',
    '可为文本选择多个标签，适用于主题、内容类别等多标签任务',
    '文本',
    '分类',
    JSON_OBJECT(
        'labels', JSON_ARRAY(
            JSON_OBJECT(
                'fromName', 'labels',
                'toName', 'text',
                'type', 'Choices',
                'options', JSON_ARRAY('Sports','Politics','Tech','Entertainment'),
                'required', true,
                'choice', 'multiple',
                'description', '可选择多个标签'
            )
        ),
        'objects', JSON_ARRAY(
            JSON_OBJECT(
                'name', 'text',
                'type', 'Text',
                'value', '$text'
            )
        )
    ),
    'vertical',
    '自然语言处理',
    1,
    '1.0.0',
    NOW()
)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description),
    data_type = VALUES(data_type),
    labeling_type = VALUES(labeling_type),
    configuration = VALUES(configuration),
    style = VALUES(style),
    category = VALUES(category),
    built_in = VALUES(built_in),
    version = VALUES(version),
    updated_at = NOW();


-- 8. 文本摘要模板
INSERT INTO t_dm_annotation_templates (
    id, name, description, data_type, labeling_type,
    configuration, style, category, built_in, version, created_at
) VALUES (
    'tpl-text-summarization-001',
    '文本摘要',
    '根据原文撰写简要摘要',
    '文本',
    '摘要',
    JSON_OBJECT(
        'labels', JSON_ARRAY(
            JSON_OBJECT(
                'fromName', 'summary',
                'toName', 'text',
                'type', 'TextArea',
                'required', true,
                'description', '在此填写摘要内容'
            )
        ),
        'objects', JSON_ARRAY(
            JSON_OBJECT(
                'name', 'text',
                'type', 'Text',
                'value', '$text'
            )
        )
    ),
    'vertical',
    '自然语言处理',
    1,
    '1.0.0',
    NOW()
)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description),
    data_type = VALUES(data_type),
    labeling_type = VALUES(labeling_type),
    configuration = VALUES(configuration),
    style = VALUES(style),
    category = VALUES(category),
    built_in = VALUES(built_in),
    version = VALUES(version),
    updated_at = NOW();

-- 9. 关键词抽取模板
INSERT INTO t_dm_annotation_templates (
    id, name, description, data_type, labeling_type,
    configuration, style, category, built_in, version, created_at
) VALUES (
    'tpl-keyword-extract-001',
    '关键词抽取',
    '从文本中选出关键词或关键短语',
    '文本',
    '实体识别',
    JSON_OBJECT(
        'labels', JSON_ARRAY(
            JSON_OBJECT(
                'fromName', 'kw',
                'toName', 'text',
                'type', 'Labels',
                'labels', JSON_ARRAY('Keyword'),
                'required', false,
                'description', '高亮文本并标注关键词'
            )
        ),
        'objects', JSON_ARRAY(
            JSON_OBJECT(
                'name', 'text',
                'type', 'Text',
                'value', '$text'
            )
        )
    ),
    'vertical',
    '自然语言处理',
    1,
    '1.0.0',
    NOW()
)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    description = VALUES(description),
    data_type = VALUES(data_type),
    labeling_type = VALUES(labeling_type),
    configuration = VALUES(configuration),
    style = VALUES(style),
    category = VALUES(category),
    built_in = VALUES(built_in),
    version = VALUES(version),
    updated_at = NOW();
