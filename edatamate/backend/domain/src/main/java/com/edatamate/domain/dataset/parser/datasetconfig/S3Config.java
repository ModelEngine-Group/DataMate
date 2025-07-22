package com.edatamate.domain.dataset.parser.datasetconfig;

/**
 * S3配置类,用于存储S3相关的配置信息
 */
public class S3Config extends CommonConfig{
    private String endpoint;

    private String bucketName;

    private String accessKey;

    private String secretKey;

    private String keyPrefix;

    private String keySuffix;





    private String region;



    private String roleArn; // 可选，IAM角色ARN，用于临时凭证

    private String sessionToken; // 可选，临时凭证的会话令
}
