package com.dataengine.collection.domain.model;

/**
 * 数据源类型枚举
 */
public enum DataSourceType {
    MYSQL("MySQL数据库"),
    POSTGRESQL("PostgreSQL数据库"),
    ORACLE("Oracle数据库"),
    SQLSERVER("SQL Server数据库"),
    MONGODB("MongoDB文档数据库"),
    REDIS("Redis缓存数据库"),
    ELASTICSEARCH("Elasticsearch搜索引擎"),
    HIVE("Hive数据仓库"),
    HDFS("Hadoop分布式文件系统"),
    KAFKA("Apache Kafka消息队列"),
    HTTP("HTTP API接口"),
    FILE("文件系统");

    private final String description;

    DataSourceType(String description) {
        this.description = description;
    }

    public String getDescription() {
        return description;
    }

    /**
     * 判断是否为关系型数据库
     */
    public boolean isRelationalDatabase() {
        return this == MYSQL || this == POSTGRESQL || this == ORACLE || this == SQLSERVER;
    }

    /**
     * 判断是否为NoSQL数据库
     */
    public boolean isNoSqlDatabase() {
        return this == MONGODB || this == REDIS || this == ELASTICSEARCH;
    }

    /**
     * 判断是否为大数据存储
     */
    public boolean isBigDataStorage() {
        return this == HIVE || this == HDFS;
    }

    /**
     * 判断是否为流式数据源
     */
    public boolean isStreamingSource() {
        return this == KAFKA;
    }
}
