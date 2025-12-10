USE datamate;

CREATE TABLE IF NOT EXISTS t_clean_template
(
    id          varchar(64) primary key not null unique,
    name        varchar(64) unique,
    description varchar(256),
    created_at  timestamp default current_timestamp,
    updated_at  timestamp default current_timestamp,
    created_by  varchar(256)
);

CREATE TABLE IF NOT EXISTS t_clean_task
(
    id                varchar(64) primary key,
    name              varchar(64) unique,
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
VALUES ('26ae585c-8310-4679-adc0-e53215e6e69b', 'FileWithShortOrLongLengthFilter', 1, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'FileWithHighRepeatWordRateFilter', 2, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'FileWithHighRepeatPhraseRateFilter', 3, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'FileWithHighSpecialCharRateFilter', 4, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'FileWithManySensitiveWordsFilter', 5, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'UnicodeSpaceCleaner', 6, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'ExtraSpaceCleaner', 7, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'FullWidthCharacterCleaner', 8, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'InvisibleCharactersCleaner', 9, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'ContentCleaner', 10, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'LegendCleaner', 11, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'EmojiCleaner', 12, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'HtmlTagCleaner', 13, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'TraditionalChineseCleaner', 14, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'GrableCharactersCleaner', 15, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'XMLTagCleaner', 16, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'DuplicateSentencesFilter', 17, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'DuplicateFilesFilter', 18, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'SexualAndViolentWordCleaner', 19, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'PoliticalWordCleaner', 20, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'AnonymizedPhoneNumber', 21, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'AnonymizedCreditCardNumber', 22, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'EmailNumberCleaner', 23, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'AnonymizedIpAddress', 24, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'AnonymizedIdNumber', 25, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'AnonymizedUrlCleaner', 26, null),
       ('26ae585c-8310-4679-adc0-e53215e6e69b', 'PiiDetector', 27, null);

INSERT IGNORE INTO t_operator_instance(instance_id, operator_id, op_index, settings_override)
VALUES ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgBlurredImagesCleaner', 1, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgDuplicatedImagesCleaner', 2, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgSimilarImagesCleaner', 3, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgBrightness', 4, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgContrast', 5, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgSaturation', 6, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgSharpness', 7, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgDenoise', 8, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgShadowRemove', 9, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgPerspectiveTransformation', 10, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgDirectionCorrect', 11, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgResize', 12, null),
       ('4421504e-c6c9-4760-b55a-509d17429597', 'ImgTypeUnify', 13, null);