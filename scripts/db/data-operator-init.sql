USE datamate;

CREATE TABLE IF NOT EXISTS t_operator
(
    id          varchar(64) primary key,
    name        varchar(64) unique,
    description varchar(256),
    version     varchar(256),
    inputs      varchar(256),
    outputs     varchar(256),
    runtime     text,
    settings    text,
    file_name   text,
    is_star     bool,
    created_at  timestamp default current_timestamp,
    updated_at  timestamp default current_timestamp
);

CREATE TABLE IF NOT EXISTS t_operator_category
(
    id        varchar(64) primary key,
    name      varchar(64) unique ,
    value     varchar(64) unique ,
    type      varchar(64),
    parent_id varchar(64),
    created_at timestamp default current_timestamp
);

CREATE TABLE IF NOT EXISTS t_operator_category_relation
(
    category_id varchar(64),
    operator_id varchar(64),
    primary key (category_id, operator_id)
);

CREATE OR REPLACE VIEW v_operator AS
SELECT o.id     AS operator_id,
       o.name   AS operator_name,
       description,
       version,
       inputs,
       outputs,
       runtime,
       settings,
       is_star,
       o.created_at AS created_at,
       updated_at,
       toc.id   AS category_id,
       toc.name AS category_name
FROM t_operator_category_relation tocr
         LEFT JOIN t_operator o ON tocr.operator_id = o.id
         LEFT JOIN t_operator_category toc ON tocr.category_id = toc.id;

INSERT IGNORE INTO t_operator_category(id, name, value, type, parent_id)
VALUES ('64465bec-b46b-11f0-8291-00155d0e4808', '模态', 'modal',  'predefined', '0'),
       ('873000a2-65b3-474b-8ccc-4813c08c76fb', '语言', 'language', 'predefined', '0'),
       ('d8a5df7a-52a9-42c2-83c4-01062e60f597', '文本', 'text', 'predefined', '64465bec-b46b-11f0-8291-00155d0e4808'),
       ('de36b61c-9e8a-4422-8c31-d30585c7100f', '图片', 'image', 'predefined', '64465bec-b46b-11f0-8291-00155d0e4808'),
       ('42dd9392-73e4-458c-81ff-41751ada47b5', '音频', 'audio', 'predefined', '64465bec-b46b-11f0-8291-00155d0e4808'),
       ('a233d584-73c8-4188-ad5d-8f7c8dda9c27', '视频', 'video', 'predefined', '64465bec-b46b-11f0-8291-00155d0e4808'),
       ('4d7dbd77-0a92-44f3-9056-2cd62d4a71e4', '多模态', 'multimodal', 'predefined', '64465bec-b46b-11f0-8291-00155d0e4808'),
       ('9eda9d5d-072b-499b-916c-797a0a8750e1', 'Python', 'python', 'predefined', '873000a2-65b3-474b-8ccc-4813c08c76fb'),
       ('b5bfc548-8ef6-417c-b8a6-a4197c078249', 'Java', 'java', 'predefined', '873000a2-65b3-474b-8ccc-4813c08c76fb'),
       ('16e2d99e-eafb-44fc-acd0-f35a2bad28f8', '来源', 'origin', 'predefined', '0'),
       ('96a3b07a-3439-4557-a835-525faad60ca3', '系统预置', 'predefined', 'predefined', '16e2d99e-eafb-44fc-acd0-f35a2bad28f8'),
       ('ec2cdd17-8b93-4a81-88c4-ac9e98d10757', '用户上传', 'customized', 'predefined', '16e2d99e-eafb-44fc-acd0-f35a2bad28f8'),
       ('d8482257-7ee6-41a0-a914-8363c7db1db0', '收藏状态', 'starStatus', 'predefined', '0'),
       ('79f2d35a-3b6c-4846-a892-2f2015f48f24', '已收藏', 'isStar', 'predefined', 'd8482257-7ee6-41a0-a914-8363c7db1db0');

INSERT IGNORE INTO t_operator
(id, name, description, version, inputs, outputs, runtime, settings, file_name, is_star)
VALUES ('TextFormatter', 'TXT文本抽取', '抽取TXT中的文本。', '1.0.0', 'text', 'text', null, null, '', false),
       ('UnstructuredFormatter', '非结构化文本抽取', '抽取非结构化文件的文本，目前支持word文档。', '1.0.0', 'text', 'text', null, null, '', false),
       ('ExternalPDFFormatter', '外部PDF文本抽取', '基于外部API，抽取PDF中的文本。', '1.0.0', 'text', 'text', null, null, '', false),
       ('FileExporter', '落盘算子', '将文件保存到本地目录。', '1.0.0', 'all', 'all', null, null, '', false),
       ('FileWithHighRepeatPhraseRateFilter', '文档词重复率检查', '去除重复词过多的文档。', '1.0.0', 'text', 'text', null, '{"repeatPhraseRatio": {"name": "文档词重复率", "description": "某个词的统计数/文档总词数 > 设定值，该文档被去除。", "type": "slider", "defaultVal": 0.5, "min": 0, "max": 1, "step": 0.1}, "hitStopwords": {"name": "去除停用词", "description": "统计重复词时，选择是否要去除停用词。", "type": "switch", "defaultVal": false, "required": true, "checkedLabel": "去除", "unCheckedLabel": "不去除"}}', '', 'false'),
       ('FileWithHighRepeatWordRateFilter', '文档字重复率检查', '去除重复字过多的文档。', '1.0.0', 'text', 'text', null, '{"repeatWordRatio": {"name": "文档字重复率", "description": "某个字的统计数/文档总字数 > 设定值，该文档被去除。", "type": "slider", "defaultVal": 0.5, "min": 0, "max": 1, "step": 0.1}}', '', 'false'),
       ('FileWithHighSpecialCharRateFilter', '文档特殊字符率检查', '去除特殊字符过多的文档。', '1.0.0', 'text', 'text', null, '{"specialCharRatio": {"name": "文档特殊字符率", "description": "特殊字符的统计数/文档总字数 > 设定值，该文档被去除。", "type": "slider", "defaultVal": 0.3, "min": 0, "max": 1, "step": 0.1}}', '', 'false'),
       ('DuplicateFilesFilter', '相似文档去除', '相似文档去除。', '1.0.0', 'text', 'text', null, '{"fileDuplicateThreshold": {"name": "文档相似度", "description": "基于MinHash算法和Jaccard相似度，计算当前文档与数据集中其它文档相似性，超过设定值，该文档被去除。", "type": "slider", "defaultVal": 0.5, "min": 0, "max": 1, "step": 0.1}}', '', 'false'),
       ('FileWithManySensitiveWordsFilter', '文档敏感词率检查', '去除敏感词过多的文档。', '1.0.0', 'text', 'text', null, '{"sensitiveWordsRate": {"name": "文档敏感词率", "description": "敏感词的字数/文档总字数 > 设定值，该文档被去除。", "type": "slider", "defaultVal": 0.01, "min": 0, "max": 1, "step": 0.01}}', '', 'false'),
       ('FileWithShortOrLongLengthFilter', '文档字数检查', '字数不在指定范围会被过滤掉。', '1.0.0', 'text', 'text', null, '{"fileLength": {"name": "文档字数", "description": "过滤字数不在指定范围内的文档，如[10,10000000]。若输入为空，则不对字数上/下限做限制。", "type": "range", "defaultVal": [10, 10000000], "min": 0, "max": 10000000000000000, "step": 1}}', '', 'false'),
       ('ContentCleaner', '文档目录去除', '去除文档中的目录。', '1.0.0', 'text', 'text', null, null, '', 'false'),
       ('AnonymizedCreditCardNumber', '信用卡号匿名化', '信用卡号匿名化', '1.0.0', 'text', 'text', null, null, '', 'false'),
       ('EmailNumberCleaner', '邮件地址匿名化', '邮件地址匿名化', '1.0.0', 'text', 'text', null, null, '', 'false'),
       ('EmojiCleaner', '文档表情去除', '去除文档中表情字符或者emoji符号。', '1.0.0', 'text', 'text', null, null, '', 'false'),
       ('ExtraSpaceCleaner', '多余空格去除', '移除文档首尾、句中或标点符号附近多余空格和 tab 等。', '1.0.0', 'text', 'text', null, null, '', 'false'),
       ('FullWidthCharacterCleaner', '全角转半角', '将文档中的所有全角字符转换成半角字符。', '1.0.0', 'text', 'text', null, null, '', 'false'),
       ('GrableCharactersCleaner', '文档乱码去除', '去除文档中的乱码和无意义的unicode。', '1.0.0', 'text', 'text', null, null, '', 'false'),
       ('HtmlTagCleaner', 'HTML标签去除', '移除文档中HTML标签，如 <html>、<dev>、<p> 等。', '1.0.0', 'text', 'text', null, null, '', 'false'),
       ('AnonymizedIdNumber', '身份证号匿名化', '身份证号匿名化。', '1.0.0', 'text', 'text', null, null, '', 'false'),
       ('InvisibleCharactersCleaner', '不可见字符去除', '去除文档中的不可见字符，例如 0-31 号字符中的部分字符。', '1.0.0', 'text', 'text', null, null, '', 'false'),
       ('AnonymizedIpAddress', 'IP地址匿名化', 'IP地址匿名化', '1.0.0', 'text', 'text', null, null, '', 'false'),
       ('LegendCleaner', '图注表注去除', '去除文档中的图注、表注等内容。', '1.0.0', 'text', 'text', null, null, '', 'false'),
       ('AnonymizedPhoneNumber', '电话号码匿名化', '电话号码匿名化', '1.0.0', 'text', 'text', null, null, '', 'false'),
       ('PoliticalWordCleaner', '政治文本匿名化', '将政治文本进行匿名化。', '1.0.0', 'text', 'text', null, null, '', 'false'),
       ('DuplicateSentencesFilter', '文档局部内容去重', '文档局部内容去重。', '1.0.0', 'text', 'text', null, null, '', 'false'),
       ('SexualAndViolentWordCleaner', '暴力色情文本匿名化', '将暴力、色情文本进行匿名化。', '1.0.0', 'text', 'text', null, null, '', 'false'),
       ('TraditionalChineseCleaner', '繁体转简体', '将繁体转换为简体。', '1.0.0', 'text', 'text', null, null, '', 'false'),
       ('UnicodeSpaceCleaner', '空格标准化', '将文档中不同的 unicode 空格，如 u2008，转换为正常空格\\u0020。', '1.0.0', 'text', 'text', null, null, '', 'false'),
       ('AnonymizedUrlCleaner', 'URL网址匿名化', '将文档中的url网址匿名化。', '1.0.0', 'text', 'text', null, null, '', 'false'),
       ('XMLTagCleaner', 'XML标签去除', '去除XML中的标签。', '1.0.0', 'text', 'text', null, null, '', 'false'),
       ('ImgFormatter', '读取图片文件', '读取图片文件。', '1.0.0', 'image', 'image', null, null, '', 'false'),
       ('ImgBlurredImagesCleaner', '模糊图片过滤', '去除模糊的图片。', '1.0.0', 'image', 'image', '{"blurredThreshold": {"name": "梯度函数值", "name_en": "Gradient Value", "description": "梯度函数值取值越小，图片模糊度越高。", "description_en": "A smaller gradient value indicates a higher image blur.", "type": "slider", "defaultVal": 1000, "min": 1, "max": 10000, "step": 1}}', null, '', 'false'),
       ('ImgBrightness', '图片亮度增强', '自适应调节图片的亮度。', '1.0.0', 'image', 'image', null, null, '', 'false'),
       ('ImgContrast', '图片对比度增强', '自适应调节图片的对比度。', '1.0.0', 'image', 'image', null, null, '', 'false'),
       ('ImgDenoise', '图片噪点去除', '去除图片中的噪点，主要适用于自然场景。', '1.0.0', 'image', 'image', null, null, '', 'false'),
       ('ImgDuplicatedImagesCleaner', '重复图片去除', '去除重复的图片。', '1.0.0', 'image', 'image', null, null, '', 'false'),
       ('ImgPerspectiveTransformation', '图片透视变换', '自适应校正图片的视角，主要适用于文档校正场景。', '1.0.0', 'image', 'image', null, null, '', 'false'),
       ('ImgResize', '图片重采样', '将图片放大或缩小到指定像素。', '1.0.0', 'image', 'image', '{"targetSize": {"name": "重采样尺寸", "name_en": "Resample Size", "type": "multiple", "properties": [{"type": "inputNumber", "name": "宽度", "name_en": "Width", "description": "像素", "description_en": "Pixel", "defaultVal": 256, "min": 1, "max": 4096, "step": 1}, {"type": "inputNumber", "name": "高度", "name_en": "Height", "description": "像素", "description_en": "Pixel", "defaultVal": 256, "min": 1, "max": 4096, "step": 1}]}}', null, '', 'false'),
       ('ImgSaturation', '图片饱和度增强', '自适应调节图片的饱和度，主要适用于自然场景图片。', '1.0.0', 'image', 'image', null, null, '', 'false'),
       ('ImgShadowRemove', '图片阴影去除', '去除图片中的阴影，主要适用于文档场景。', '1.0.0', 'image', 'image', null, null, '', 'false'),
       ('ImgSharpness', '图片锐度增强', '自适应调节图片的锐度，主要适用于自然场景图片。', '1.0.0', 'image', 'image', null, null, '', 'false'),
       ('ImgSimilarImagesCleaner', '相似图片去除', '去除相似的图片。', '1.0.0', 'image', 'image', '{"similarThreshold": {"name": "相似度", "name_en": "Similarity", "description": "相似度取值越大，图片相似度越高。", "description_en": "A larger similarity value indicates a higher image similarity.", "type": "slider", "defaultVal": 0.8, "min": 0, "max": 1, "step": 0.01}}', null, '', 'false'),
       ('ImgTypeUnify', '图片格式转换', '将图片编码格式统一为jpg、jpeg、png、bmp格式。', '1.0.0', 'image', 'image', '{"imgType": {"name": "图片编码格式", "name_en": "Image Encoding Format", "type": "select", "defaultVal": "jpg", "options": [{"label": "jpg", "label_en": "jpg", "value": "jpg"}, {"label": "png", "label_en": "png", "value": "png"}, {"label": "jpeg", "label_en": "jpeg", "value": "jpeg"}, {"label": "bmp", "label_en": "bmp", "value": "bmp"}]}}', null, '', 'false');


INSERT IGNORE INTO t_operator_category_relation(category_id, operator_id)
SELECT c.id, o.id
FROM t_operator_category c
CROSS JOIN t_operator o
WHERE c.id IN ('d8a5df7a-52a9-42c2-83c4-01062e60f597', '9eda9d5d-072b-499b-916c-797a0a8750e1', '96a3b07a-3439-4557-a835-525faad60ca3')
AND o.id IN ('TextFormatter', 'FileWithShortOrLongLengthFilter', 'FileWithHighRepeatPhraseRateFilter',
            'FileWithHighRepeatWordRateFilter', 'FileWithHighSpecialCharRateFilter', 'FileWithManySensitiveWordsFilter',
            'DuplicateFilesFilter', 'DuplicateSentencesFilter', 'AnonymizedCreditCardNumber', 'AnonymizedIdNumber',
            'AnonymizedIpAddress', 'AnonymizedPhoneNumber', 'AnonymizedUrlCleaner', 'HtmlTagCleaner', 'XMLTagCleaner',
            'ContentCleaner', 'EmailNumberCleaner', 'EmojiCleaner', 'ExtraSpaceCleaner', 'FullWidthCharacterCleaner',
            'GrableCharactersCleaner', 'InvisibleCharactersCleaner', 'LegendCleaner', 'PoliticalWordCleaner',
            'SexualAndViolentWordCleaner', 'TraditionalChineseCleaner', 'UnicodeSpaceCleaner');

INSERT IGNORE INTO t_operator_category_relation(category_id, operator_id)
SELECT c.id, o.id
FROM t_operator_category c
       CROSS JOIN t_operator o
WHERE c.id IN ('de36b61c-9e8a-4422-8c31-d30585c7100f', '9eda9d5d-072b-499b-916c-797a0a8750e1', '96a3b07a-3439-4557-a835-525faad60ca3')
  AND o.id IN ('ImgFormatter', 'ImgBlurredImagesCleaner', 'ImgBrightness', 'ImgContrast', 'ImgDenoise',
               'ImgDuplicatedImagesCleaner', 'ImgPerspectiveTransformation', 'ImgResize', 'ImgSaturation',
               'ImgShadowRemove', 'ImgSharpness', 'ImgSimilarImagesCleaner', 'ImgTypeUnify');

INSERT IGNORE INTO t_operator_category_relation(category_id, operator_id)
SELECT c.id, o.id
FROM t_operator_category c
       CROSS JOIN t_operator o
WHERE c.id IN ('4d7dbd77-0a92-44f3-9056-2cd62d4a71e4', '9eda9d5d-072b-499b-916c-797a0a8750e1', '96a3b07a-3439-4557-a835-525faad60ca3')
  AND o.id IN ('FileExporter', 'UnstructuredFormatter');
