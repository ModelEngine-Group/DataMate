USE datamate;

CREATE TABLE IF NOT EXISTS t_clean_template
(
    id          varchar(64) primary key not null unique,
    name        varchar(64),
    description varchar(256),
    created_at  timestamp default current_timestamp,
    updated_at  timestamp default current_timestamp,
    created_by  varchar(256)
);

CREATE TABLE IF NOT EXISTS t_clean_task
(
    id                varchar(64) primary key,
    name              varchar(64),
    description       varchar(256),
    status            varchar(256),
    src_dataset_id    varchar(64),
    src_dataset_name  varchar(64),
    dest_dataset_id   varchar(64),
    dest_dataset_name varchar(64),
    before_size       bigint,
    after_size        bigint,
    file_count        int,
    created_at        timestamp default current_timestamp,
    started_at        timestamp,
    finished_at       timestamp,
    created_by        varchar(256)
);

CREATE TABLE IF NOT EXISTS t_operator_instance
(
    instance_id       varchar(256),
    operator_id       varchar(256),
    op_index          int,
    settings_override text,
    PRIMARY KEY (instance_id, operator_id, op_index)
);

CREATE TABLE IF NOT EXISTS t_clean_result
(
    instance_id varchar(64),
    src_file_id varchar(64),
    dest_file_id varchar(64),
    src_name    varchar(256),
    dest_name    varchar(256),
    src_type    varchar(256),
    dest_type    varchar(256),
    src_size    bigint,
    dest_size    bigint,
    status      varchar(256),
    result      TEXT,
    primary key (instance_id, dest_file_id)
);

INSERT IGNORE INTO t_clean_template(id, name, description)
VALUES ('26ae585c-8310-4679-adc0-e53215e6e69b', '文本清洗模板', '文本清洗模板'),
       ('4421504e-c6c9-4760-b55a-509d17429597', '图片清洗模板', '图片清洗模板');

INSERT IGNORE INTO t_operator_instance(instance_id, operator_id, op_index, settings_override)
VALUES ('26ae585c-8310-4679-adc0-e53215e6e69b', 'TextFormatter', 1, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'FileWithShortOrLongLengthFilter', 2, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'FileWithHighRepeatWordRateFilter', 3, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'FileWithHighRepeatPhraseRateFilter', 4, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'FileWithHighSpecialCharRateFilter', 5, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'FileWithManySensitiveWordsFilter', 6, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'UnicodeSpaceCleaner', 7, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'ExtraSpaceCleaner', 8, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'FullWidthCharacterCleaner', 9, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'InvisibleCharactersCleaner', 10, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'ContentCleaner', 11, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'LegendCleaner', 12, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'EmojiCleaner', 13, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'HtmlTagCleaner', 14, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'TraditionalChineseCleaner', 15, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'GrableCharactersCleaner', 16, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'XMLTagCleaner', 17, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'DuplicateSentencesFilter', 18, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'DuplicateFilesFilter', 19, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'SexualAndViolentWordCleaner', 20, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'PoliticalWordCleaner', 21, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'AnonymizedPhoneNumber', 22, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'AnonymizedCreditCardNumber', 23, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'EmailNumberCleaner', 24, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'AnonymizedIpAddress', 25, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'AnonymizedIdNumber', 26, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'AnonymizedUrlCleaner', 27, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'FileExporter', 28, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgFormatter', 1, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgBlurredImagesCleaner', 2, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgDuplicatedImagesCleaner', 3, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgSimilarImagesCleaner', 4, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgBrightness', 5, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgContrast', 6, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgSaturation', 7, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgSharpness', 8, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgDenoise', 9, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgShadowRemove', 10, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgPerspectiveTransformation', 11, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgResize', 12, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgTypeUnify', 13, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'FileExporter', 14, null);
