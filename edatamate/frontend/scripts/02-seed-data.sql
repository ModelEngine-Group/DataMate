-- 插入示例数据

-- 插入处理步骤模板
INSERT INTO processing_templates (name, description, steps) VALUES
('图像预处理', '标准图像预处理流程', '[
    {"id": "resize", "name": "调整尺寸", "params": {"width": 224, "height": 224}},
    {"id": "normalize", "name": "归一化", "params": {"mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]}},
    {"id": "augment", "name": "数据增强", "params": {"rotation": 15, "flip": true}}
]'),
('文本清洗', '文本数据清洗流程', '[
    {"id": "remove_html", "name": "移除HTML标签", "params": {}},
    {"id": "normalize_whitespace", "name": "规范化空白字符", "params": {}},
    {"id": "remove_special_chars", "name": "移除特殊字符", "params": {"keep_punctuation": true}}
]'),
('QA对处理', 'QA数据对处理流程', '[
    {"id": "validate_qa", "name": "验证QA格式", "params": {}},
    {"id": "filter_length", "name": "过滤长度", "params": {"min_question_length": 5, "min_answer_length": 10}},
    {"id": "deduplicate", "name": "去重", "params": {"similarity_threshold": 0.9}}
]');

-- 插入示例数据集
INSERT INTO datasets (name, description, type, status) VALUES
('图像分类数据集', '用于训练图像分类模型的数据集', 'image_text', 'draft'),
('问答对数据集', '用于训练问答模型的QA数据集', 'qa', 'draft'),
('多模态数据集', '包含图像和文本的多模态数据集', 'image_text', 'processing'),
('肺癌WSI病理图像数据集', '来自三甲医院的肺癌全切片病理图像，包含详细的病理标签和分级信息', 'image', '医学影像', '1.2TB', 1247, 'active', ARRAY['WSI', '病理', '肺癌', '分类', '分级'], 94.2, 1247, 1205, 96.8, '三甲医院病理科', ARRAY['质量检查', '格式标准化', '数据增强', '标签验证'], 'ResNet-50', 92.4, 91.8),
('乳腺癌组织病理数据集', '乳腺癌组织切片图像，包含良性和恶性分类标签', 'image', '医学影像', '856GB', 892, 'processing', ARRAY['组织病理', '乳腺癌', '二分类'], 91.5, 892, 756, 94.2, '多中心医院联合', ARRAY['图像预处理', '质量筛选', '标准化'], NULL, NULL, NULL),
('皮肤镜图像数据集', '皮肤病变筛查图像，用于皮肤癌早期检测', 'image', '医学影像', '234GB', 2156, 'active', ARRAY['皮肤镜', '皮肤癌', '筛查'], 88.7, 2156, 2156, 92.1, '皮肤科专科医院', ARRAY['图像增强', '噪声去除', '标准化'], 'EfficientNet-B4', 89.3, 87.6),
('CT影像数据集', '胸部CT影像，用于肺部疾病诊断和分析', 'image', '放射影像', '1.8TB', 3421, 'active', ARRAY['CT', '胸部', '肺部疾病'], 96.1, 3421, 3421, 98.2, '放射科影像中心', ARRAY['DICOM转换', '窗宽窗位调整', '分割标注'], '3D U-Net', 94.7, 93.2),
('内镜图像数据集', '消化道内镜检查图像，用于消化道疾病诊断', 'image', '内镜影像', '445GB', 1876, 'processing', ARRAY['内镜', '消化道', '病变检测'], 87.3, 1876, 1234, 91.5, '消化内科', ARRAY['图像分割', '病变标注', '质量评估'], NULL, NULL, NULL);
</merged_code>
