-- 使用现有的datamate数据库
\c datamate;

-- 标注配置模板表
CREATE TABLE IF NOT EXISTS t_dm_annotation_templates (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    data_type VARCHAR(50) NOT NULL,
    labeling_type VARCHAR(50) NOT NULL,
    configuration JSONB NOT NULL,
    style VARCHAR(32) NOT NULL,
    category VARCHAR(50) DEFAULT 'custom',
    built_in BOOLEAN DEFAULT FALSE,
    version VARCHAR(20) DEFAULT '1.0',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
    );

-- 添加注释
COMMENT ON TABLE t_dm_annotation_templates IS '标注配置模板表';
COMMENT ON COLUMN t_dm_annotation_templates.id IS 'UUID';
COMMENT ON COLUMN t_dm_annotation_templates.name IS '模板名称';
COMMENT ON COLUMN t_dm_annotation_templates.description IS '模板描述';
COMMENT ON COLUMN t_dm_annotation_templates.data_type IS '数据类型: image/text/audio/video/timeseries';
COMMENT ON COLUMN t_dm_annotation_templates.labeling_type IS '标注类型: classification/detection/segmentation/ner/relation/etc';
COMMENT ON COLUMN t_dm_annotation_templates.configuration IS '标注配置（包含labels定义等）';
COMMENT ON COLUMN t_dm_annotation_templates.style IS '样式配置: horizontal/vertical';
COMMENT ON COLUMN t_dm_annotation_templates.category IS '模板分类: medical/general/custom/system';
COMMENT ON COLUMN t_dm_annotation_templates.built_in IS '是否系统内置模板';
COMMENT ON COLUMN t_dm_annotation_templates.version IS '模板版本';
COMMENT ON COLUMN t_dm_annotation_templates.created_at IS '创建时间';
COMMENT ON COLUMN t_dm_annotation_templates.updated_at IS '更新时间';
COMMENT ON COLUMN t_dm_annotation_templates.deleted_at IS '删除时间（软删除）';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_dm_ann_tpl_data_type ON t_dm_annotation_templates(data_type);
CREATE INDEX IF NOT EXISTS idx_dm_ann_tpl_labeling_type ON t_dm_annotation_templates(labeling_type);
CREATE INDEX IF NOT EXISTS idx_dm_ann_tpl_category ON t_dm_annotation_templates(category);
CREATE INDEX IF NOT EXISTS idx_dm_ann_tpl_built_in ON t_dm_annotation_templates(built_in);
CREATE INDEX IF NOT EXISTS idx_dm_ann_tpl_deleted_at ON t_dm_annotation_templates(deleted_at);

-- 标注项目表
CREATE TABLE IF NOT EXISTS t_dm_labeling_projects (
    id VARCHAR(36) PRIMARY KEY,
    dataset_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    labeling_project_id VARCHAR(8) NOT NULL,
    template_id VARCHAR(36),
    configuration JSONB,
    progress JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
    );

-- 添加注释
COMMENT ON TABLE t_dm_labeling_projects IS '标注项目表';
COMMENT ON COLUMN t_dm_labeling_projects.id IS 'UUID';
COMMENT ON COLUMN t_dm_labeling_projects.dataset_id IS '数据集ID';
COMMENT ON COLUMN t_dm_labeling_projects.name IS '项目名称';
COMMENT ON COLUMN t_dm_labeling_projects.labeling_project_id IS 'Label Studio项目ID';
COMMENT ON COLUMN t_dm_labeling_projects.template_id IS '使用的模板ID';
COMMENT ON COLUMN t_dm_labeling_projects.configuration IS '项目配置（可能包含对模板的自定义修改）';
COMMENT ON COLUMN t_dm_labeling_projects.progress IS '项目进度信息';
COMMENT ON COLUMN t_dm_labeling_projects.created_at IS '创建时间';
COMMENT ON COLUMN t_dm_labeling_projects.updated_at IS '更新时间';
COMMENT ON COLUMN t_dm_labeling_projects.deleted_at IS '删除时间（软删除）';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_dm_lp_dataset_id ON t_dm_labeling_projects(dataset_id);
CREATE INDEX IF NOT EXISTS idx_dm_lp_template_id ON t_dm_labeling_projects(template_id);
CREATE INDEX IF NOT EXISTS idx_dm_lp_labeling_project_id ON t_dm_labeling_projects(labeling_project_id);
CREATE INDEX IF NOT EXISTS idx_dm_lp_deleted_at ON t_dm_labeling_projects(deleted_at);

-- 外键约束
ALTER TABLE t_dm_labeling_projects ADD CONSTRAINT fk_dm_labeling_projects_template
FOREIGN KEY (template_id) REFERENCES t_dm_annotation_templates(id) ON DELETE SET NULL;

-- 自动标注任务表
CREATE TABLE IF NOT EXISTS t_dm_auto_annotation_tasks (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    dataset_id VARCHAR(36) NOT NULL,
    dataset_name VARCHAR(255),
    config JSONB NOT NULL,
    file_ids JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    total_images INTEGER DEFAULT 0,
    processed_images INTEGER DEFAULT 0,
    detected_objects INTEGER DEFAULT 0,
    output_path VARCHAR(500),
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    deleted_at TIMESTAMP
    );

-- 添加注释
COMMENT ON TABLE t_dm_auto_annotation_tasks IS '自动标注任务表';
COMMENT ON COLUMN t_dm_auto_annotation_tasks.id IS 'UUID';
COMMENT ON COLUMN t_dm_auto_annotation_tasks.name IS '任务名称';
COMMENT ON COLUMN t_dm_auto_annotation_tasks.dataset_id IS '数据集ID';
COMMENT ON COLUMN t_dm_auto_annotation_tasks.dataset_name IS '数据集名称（冗余字段，方便查询）';
COMMENT ON COLUMN t_dm_auto_annotation_tasks.config IS '任务配置（模型规模、置信度等）';
COMMENT ON COLUMN t_dm_auto_annotation_tasks.file_ids IS '要处理的文件ID列表，为空则处理数据集所有图像';
COMMENT ON COLUMN t_dm_auto_annotation_tasks.status IS '任务状态: pending/running/completed/failed';
COMMENT ON COLUMN t_dm_auto_annotation_tasks.progress IS '任务进度 0-100';
COMMENT ON COLUMN t_dm_auto_annotation_tasks.total_images IS '总图片数';
COMMENT ON COLUMN t_dm_auto_annotation_tasks.processed_images IS '已处理图片数';
COMMENT ON COLUMN t_dm_auto_annotation_tasks.detected_objects IS '检测到的对象总数';
COMMENT ON COLUMN t_dm_auto_annotation_tasks.output_path IS '输出路径';
COMMENT ON COLUMN t_dm_auto_annotation_tasks.error_message IS '错误信息';
COMMENT ON COLUMN t_dm_auto_annotation_tasks.created_at IS '创建时间';
COMMENT ON COLUMN t_dm_auto_annotation_tasks.updated_at IS '更新时间';
COMMENT ON COLUMN t_dm_auto_annotation_tasks.completed_at IS '完成时间';
COMMENT ON COLUMN t_dm_auto_annotation_tasks.deleted_at IS '删除时间（软删除）';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_dm_aat_dataset_id ON t_dm_auto_annotation_tasks(dataset_id);
CREATE INDEX IF NOT EXISTS idx_dm_aat_status ON t_dm_auto_annotation_tasks(status);
CREATE INDEX IF NOT EXISTS idx_dm_aat_created_at ON t_dm_auto_annotation_tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_dm_aat_deleted_at ON t_dm_auto_annotation_tasks(deleted_at);

-- 创建触发器用于自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
RETURN NEW;
END;
$$ language 'plpgsql';

-- 为各个表创建触发器
DROP TRIGGER IF EXISTS update_dm_annotation_templates_updated_at ON t_dm_annotation_templates;
CREATE TRIGGER update_dm_annotation_templates_updated_at
    BEFORE UPDATE ON t_dm_annotation_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_dm_labeling_projects_updated_at ON t_dm_labeling_projects;
CREATE TRIGGER update_dm_labeling_projects_updated_at
    BEFORE UPDATE ON t_dm_labeling_projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_dm_auto_annotation_tasks_updated_at ON t_dm_auto_annotation_tasks;
CREATE TRIGGER update_dm_auto_annotation_tasks_updated_at
    BEFORE UPDATE ON t_dm_auto_annotation_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 内置标注模板初始化数据

-- 1. 图像分类模板
INSERT INTO t_dm_annotation_templates (id, name, description, data_type, labeling_type, configuration, style, category, built_in, version)
VALUES ('tpl-image-classification-001', '图像分类', '简单的多标签图像分类模板', '图像', '分类', '{
                 "labels": [
                     {
                         "fromName": "choice",
                         "toName": "image",
                         "type": "Choices",
                         "options": ["Cat", "Dog", "Bird", "Other"],
                         "required": true,
                         "description": "选择最符合图像内容的标签"
                     }
                 ],
                 "objects": [
                     {
                         "name": "image",
                         "type": "Image",
                         "value": "$image"
                     }
                 ]
             }',
             'horizontal',
             '计算机视觉',
             TRUE,
             '1.0.0'
         ),
      (
             'tpl-object-detection-001',
             '目标检测（边界框）',
             '使用矩形边界框进行目标检测',
             '图像',
             '目标检测',
             '{
                 "labels": [
                     {
                         "fromName": "label",
                         "toName": "image",
                         "type": "RectangleLabels",
                         "labels": ["Person", "Vehicle", "Animal", "Object"],
                         "required": false,
                         "description": "在图像中框出目标并标注类别"
                     }
                 ],
                 "objects": [
                     {
                         "name": "image",
                         "type": "Image",
                         "value": "$image"
                     }
                 ]
             }',
             'horizontal',
             '计算机视觉',
             TRUE,
             '1.0.0'
      ),
      (
             'tpl-image-segmentation-001',
             '图像分割（多边形）',
             '使用多边形标注进行语义分割',
             '图像',
             '分割',
             '{
                 "labels": [
                     {
                         "fromName": "label",
                         "toName": "image",
                         "type": "PolygonLabels",
                         "labels": ["Background", "Foreground", "Person", "Car"],
                         "required": false,
                         "description": "使用多边形框选需要分割的区域"
                     }
                 ],
                 "objects": [
                     {
                         "name": "image",
                         "type": "Image",
                         "value": "$image"
                     }
                 ]
             }',
             'horizontal',
             '计算机视觉',
             TRUE,
             '1.0.0'
         ),
      (
             'tpl-text-classification-001',
             '文本情感分类',
             '将文本中表达的情感划分到预定义的类别',
             '文本',
             '分类',
             '{
                 "labels": [
                     {
                         "fromName": "choice",
                         "toName": "text",
                         "type": "Choices",
                         "options": ["Positive", "Negative", "Neutral"],
                         "required": true,
                         "description": "对文本的情感或类别进行选择"
                     }
                 ],
                 "objects": [
                     {
                         "name": "text",
                         "type": "Text",
                         "value": "$text"
                     }
                 ]
             }',
             'vertical',
             '自然语言处理',
             TRUE,
             '1.0.0'
         ),
      (
             'tpl-ner-001',
             '命名实体识别',
             '从文本中抽取并标注命名实体',
             '文本',
             '实体识别',
             '{
                 "labels": [
                     {
                         "fromName": "label",
                         "toName": "text",
                         "type": "Labels",
                         "labels": ["PERSON", "ORG", "LOC", "DATE", "MISC"],
                         "required": false,
                         "description": "在文本中标注人物、地点等实体"
                     }
                 ],
                 "objects": [
                     {
                         "name": "text",
                         "type": "Text",
                         "value": "$text"
                     }
                 ]
             }',
             'vertical',
             '自然语言处理',
             TRUE,
             '1.0.0'
         ),
      (
             'tpl-audio-classification-001',
             '音频分类',
             '将音频片段划分到不同类别',
             '音频',
             '分类',
             '{
                 "labels": [
                     {
                         "fromName": "choice",
                         "toName": "audio",
                         "type": "Choices",
                         "options": ["Speech", "Music", "Noise", "Silence"],
                         "required": true,
                         "description": "选择音频片段对应的类别"
                     }
                 ],
                 "objects": [
                     {
                         "name": "audio",
                         "type": "Audio",
                         "value": "$audio"
                     }
                 ]
             }',
             'horizontal',
             '音频',
             TRUE,
             '1.0.0'
         ),
      (
             'tpl-text-multilabel-001',
             '文本多标签分类',
             '可为文本选择多个标签，适用于主题、内容类别等多标签任务',
             '文本',
             '分类',
             '{
                 "labels": [
                     {
                         "fromName": "labels",
                         "toName": "text",
                         "type": "Choices",
                         "options": ["Sports", "Politics", "Tech", "Entertainment"],
                         "required": true,
                         "choice": "multiple",
                         "description": "可选择多个标签"
                     }
                 ],
                 "objects": [
                     {
                         "name": "text",
                         "type": "Text",
                         "value": "$text"
                     }
                 ]
             }',
             'vertical',
             '自然语言处理',
             TRUE,
             '1.0.0'
         ),
      (
             'tpl-text-summarization-001',
             '文本摘要',
             '根据原文撰写简要摘要',
             '文本',
             '摘要',
             '{
                 "labels": [
                     {
                         "fromName": "summary",
                         "toName": "text",
                         "type": "TextArea",
                         "required": true,
                         "description": "在此填写摘要内容"
                     }
                 ],
                 "objects": [
                     {
                         "name": "text",
                         "type": "Text",
                         "value": "$text"
                     }
                 ]
             }',
             'vertical',
             '自然语言处理',
             TRUE,
             '1.0.0'
         ),
      (
             'tpl-keyword-extract-001',
             '关键词抽取',
             '从文本中选出关键词或关键短语',
             '文本',
             '实体识别',
             '{
                 "labels": [
                     {
                         "fromName": "kw",
                         "toName": "text",
                         "type": "Labels",
                         "labels": ["Keyword"],
                         "required": false,
                         "description": "高亮文本并标注关键词"
                     }
                 ],
                 "objects": [
                     {
                         "name": "text",
                         "type": "Text",
                         "value": "$text"
                     }
                 ]
             }',
             'vertical',
             '自然语言处理',
             TRUE,
             '1.0.0'
         )
    ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    data_type = EXCLUDED.data_type,
    labeling_type = EXCLUDED.labeling_type,
    configuration = EXCLUDED.configuration,
    style = EXCLUDED.style,
    category = EXCLUDED.category,
    built_in = EXCLUDED.built_in,
    version = EXCLUDED.version,
    updated_at = CURRENT_TIMESTAMP;