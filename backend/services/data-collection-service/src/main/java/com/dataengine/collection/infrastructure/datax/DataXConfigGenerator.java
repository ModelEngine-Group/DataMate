package com.dataengine.collection.infrastructure.datax;

import com.dataengine.collection.domain.model.DataSource;
import com.dataengine.collection.domain.model.DataSourceType;
import com.dataengine.collection.domain.model.CollectionTask;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.springframework.stereotype.Component;

import java.util.Map;

/**
 * DataX配置生成器
 * 
 * 根据数据源和归集任务配置生成DataX作业JSON配置
 */
@Component
public class DataXConfigGenerator {

    private final ObjectMapper objectMapper;

    public DataXConfigGenerator(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    /**
     * 生成DataX作业配置
     */
    public String generateConfig(CollectionTask task, DataSource sourceDataSource, DataSource targetDataSource) {
        ObjectNode jobConfig = objectMapper.createObjectNode();
        ObjectNode job = objectMapper.createObjectNode();
        
        // 作业设置
        ObjectNode setting = generateSetting(task);
        job.set("setting", setting);
        
        // 内容配置
        ArrayNode content = objectMapper.createArrayNode();
        ObjectNode contentItem = objectMapper.createObjectNode();
        
        // Reader配置
        ObjectNode reader = generateReader(sourceDataSource, task);
        contentItem.set("reader", reader);
        
        // Writer配置
        ObjectNode writer = generateWriter(targetDataSource, task);
        contentItem.set("writer", writer);
        
        content.add(contentItem);
        job.set("content", content);
        
        jobConfig.set("job", job);
        
        try {
            return objectMapper.writerWithDefaultPrettyPrinter().writeValueAsString(jobConfig);
        } catch (Exception e) {
            throw new RuntimeException("Failed to generate DataX config", e);
        }
    }

    /**
     * 生成作业设置配置
     */
    private ObjectNode generateSetting(CollectionTask task) {
        ObjectNode setting = objectMapper.createObjectNode();
        
        // 速度配置
        ObjectNode speed = objectMapper.createObjectNode();
        Map<String, String> config = task.getConfig();
        int channel = Integer.parseInt(config.getOrDefault("channel", "1"));
        speed.put("channel", channel);
        
        if (config.containsKey("batchSize")) {
            speed.put("record", Integer.parseInt(config.get("batchSize")));
        }
        
        if (config.containsKey("bandwidth")) {
            speed.put("byte", Long.parseLong(config.get("bandwidth")));
        }
        
        setting.set("speed", speed);
        
        // 错误控制
        ObjectNode errorLimit = objectMapper.createObjectNode();
        errorLimit.put("record", Integer.parseInt(config.getOrDefault("errorLimit", "0")));
        errorLimit.put("percentage", Double.parseDouble(config.getOrDefault("errorPercentage", "0.02")));
        setting.set("errorLimit", errorLimit);
        
        return setting;
    }

    /**
     * 生成Reader配置
     */
    private ObjectNode generateReader(DataSource dataSource, CollectionTask task) {
        ObjectNode reader = objectMapper.createObjectNode();
        DataSourceType type = dataSource.getType();
        Map<String, String> dsConfig = dataSource.getConfig();
        Map<String, String> taskConfig = task.getConfig();
        
        reader.put("name", getReaderName(type));
        
        ObjectNode parameter = objectMapper.createObjectNode();
        
        switch (type) {
            case MYSQL:
            case POSTGRESQL:
            case ORACLE:
            case SQLSERVER:
                generateRelationalReaderConfig(parameter, dsConfig, taskConfig, type);
                break;
            case MONGODB:
                generateMongoReaderConfig(parameter, dsConfig, taskConfig);
                break;
            case REDIS:
                generateRedisReaderConfig(parameter, dsConfig, taskConfig);
                break;
            case ELASTICSEARCH:
                generateElasticsearchReaderConfig(parameter, dsConfig, taskConfig);
                break;
            case HDFS:
                generateHdfsReaderConfig(parameter, dsConfig, taskConfig);
                break;
            case FILE:
                generateFileReaderConfig(parameter, dsConfig, taskConfig);
                break;
            default:
                throw new UnsupportedOperationException("Unsupported source type: " + type);
        }
        
        reader.set("parameter", parameter);
        return reader;
    }

    /**
     * 生成Writer配置
     */
    private ObjectNode generateWriter(DataSource dataSource, CollectionTask task) {
        ObjectNode writer = objectMapper.createObjectNode();
        DataSourceType type = dataSource.getType();
        Map<String, String> dsConfig = dataSource.getConfig();
        Map<String, String> taskConfig = task.getConfig();
        
        writer.put("name", getWriterName(type));
        
        ObjectNode parameter = objectMapper.createObjectNode();
        
        switch (type) {
            case MYSQL:
            case POSTGRESQL:
            case ORACLE:
            case SQLSERVER:
                generateRelationalWriterConfig(parameter, dsConfig, taskConfig, type);
                break;
            case MONGODB:
                generateMongoWriterConfig(parameter, dsConfig, taskConfig);
                break;
            case REDIS:
                generateRedisWriterConfig(parameter, dsConfig, taskConfig);
                break;
            case ELASTICSEARCH:
                generateElasticsearchWriterConfig(parameter, dsConfig, taskConfig);
                break;
            case HDFS:
                generateHdfsWriterConfig(parameter, dsConfig, taskConfig);
                break;
            case FILE:
                generateFileWriterConfig(parameter, dsConfig, taskConfig);
                break;
            default:
                throw new UnsupportedOperationException("Unsupported target type: " + type);
        }
        
        writer.set("parameter", parameter);
        return writer;
    }

    /**
     * 生成关系型数据库Reader配置
     */
    private void generateRelationalReaderConfig(ObjectNode parameter, Map<String, String> dsConfig, 
                                              Map<String, String> taskConfig, DataSourceType type) {
        parameter.put("username", dsConfig.get("username"));
        parameter.put("password", dsConfig.get("password"));
        
        // 连接配置
        ArrayNode connections = objectMapper.createArrayNode();
        ObjectNode connection = objectMapper.createObjectNode();
        
        String jdbcUrl = buildJdbcUrl(type, dsConfig);
        ArrayNode jdbcUrls = objectMapper.createArrayNode();
        jdbcUrls.add(jdbcUrl);
        connection.set("jdbcUrl", jdbcUrls);
        
        ArrayNode tables = objectMapper.createArrayNode();
        tables.add(taskConfig.getOrDefault("sourceTable", "*"));
        connection.set("table", tables);
        
        connections.add(connection);
        parameter.set("connection", connections);
        
        // 列配置
        ArrayNode columns = objectMapper.createArrayNode();
        String columnConfig = taskConfig.getOrDefault("columns", "*");
        if ("*".equals(columnConfig)) {
            columns.add("*");
        } else {
            String[] cols = columnConfig.split(",");
            for (String col : cols) {
                columns.add(col.trim());
            }
        }
        parameter.set("column", columns);
        
        // 查询条件
        if (taskConfig.containsKey("where")) {
            parameter.put("where", taskConfig.get("where"));
        }
        
        // 分片配置
        if (taskConfig.containsKey("splitPk")) {
            parameter.put("splitPk", taskConfig.get("splitPk"));
        }
    }

    /**
     * 生成关系型数据库Writer配置
     */
    private void generateRelationalWriterConfig(ObjectNode parameter, Map<String, String> dsConfig, 
                                              Map<String, String> taskConfig, DataSourceType type) {
        parameter.put("username", dsConfig.get("username"));
        parameter.put("password", dsConfig.get("password"));
        
        // 连接配置
        ArrayNode connections = objectMapper.createArrayNode();
        ObjectNode connection = objectMapper.createObjectNode();
        
        String jdbcUrl = buildJdbcUrl(type, dsConfig);
        connection.put("jdbcUrl", jdbcUrl);
        
        ArrayNode tables = objectMapper.createArrayNode();
        tables.add(taskConfig.getOrDefault("targetTable", "target_table"));
        connection.set("table", tables);
        
        connections.add(connection);
        parameter.set("connection", connections);
        
        // 列配置
        ArrayNode columns = objectMapper.createArrayNode();
        String columnConfig = taskConfig.getOrDefault("columns", "*");
        if ("*".equals(columnConfig)) {
            columns.add("*");
        } else {
            String[] cols = columnConfig.split(",");
            for (String col : cols) {
                columns.add(col.trim());
            }
        }
        parameter.set("column", columns);
        
        // 写入模式
        String writeMode = taskConfig.getOrDefault("writeMode", "insert");
        parameter.put("writeMode", writeMode);
        
        // 预处理SQL
        if (taskConfig.containsKey("preSql")) {
            ArrayNode preSqls = objectMapper.createArrayNode();
            preSqls.add(taskConfig.get("preSql"));
            parameter.set("preSql", preSqls);
        }
        
        // 后处理SQL
        if (taskConfig.containsKey("postSql")) {
            ArrayNode postSqls = objectMapper.createArrayNode();
            postSqls.add(taskConfig.get("postSql"));
            parameter.set("postSql", postSqls);
        }
    }

    /**
     * 生成MongoDB Reader配置
     */
    private void generateMongoReaderConfig(ObjectNode parameter, Map<String, String> dsConfig, Map<String, String> taskConfig) {
        ArrayNode address = objectMapper.createArrayNode();
        address.add(dsConfig.get("host") + ":" + dsConfig.getOrDefault("port", "27017"));
        parameter.set("address", address);
        
        parameter.put("userName", dsConfig.get("username"));
        parameter.put("userPassword", dsConfig.get("password"));
        parameter.put("dbName", dsConfig.get("database"));
        parameter.put("collectionName", taskConfig.getOrDefault("sourceCollection", "collection"));
        
        if (taskConfig.containsKey("query")) {
            parameter.put("query", taskConfig.get("query"));
        }
        
        ArrayNode columns = objectMapper.createArrayNode();
        ObjectNode column = objectMapper.createObjectNode();
        column.put("name", "*");
        column.put("type", "string");
        columns.add(column);
        parameter.set("column", columns);
    }

    /**
     * 生成MongoDB Writer配置
     */
    private void generateMongoWriterConfig(ObjectNode parameter, Map<String, String> dsConfig, Map<String, String> taskConfig) {
        ArrayNode address = objectMapper.createArrayNode();
        address.add(dsConfig.get("host") + ":" + dsConfig.getOrDefault("port", "27017"));
        parameter.set("address", address);
        
        parameter.put("userName", dsConfig.get("username"));
        parameter.put("userPassword", dsConfig.get("password"));
        parameter.put("dbName", dsConfig.get("database"));
        parameter.put("collectionName", taskConfig.getOrDefault("targetCollection", "collection"));
        
        String writeMode = taskConfig.getOrDefault("writeMode", "insert");
        parameter.put("writeMode", writeMode);
        
        ArrayNode columns = objectMapper.createArrayNode();
        ObjectNode column = objectMapper.createObjectNode();
        column.put("name", "*");
        column.put("type", "string");
        columns.add(column);
        parameter.set("column", columns);
    }

    // 其他数据源配置方法...
    private void generateRedisReaderConfig(ObjectNode parameter, Map<String, String> dsConfig, Map<String, String> taskConfig) {
        // Redis Reader配置实现
    }

    private void generateRedisWriterConfig(ObjectNode parameter, Map<String, String> dsConfig, Map<String, String> taskConfig) {
        // Redis Writer配置实现
    }

    private void generateElasticsearchReaderConfig(ObjectNode parameter, Map<String, String> dsConfig, Map<String, String> taskConfig) {
        // Elasticsearch Reader配置实现
    }

    private void generateElasticsearchWriterConfig(ObjectNode parameter, Map<String, String> dsConfig, Map<String, String> taskConfig) {
        // Elasticsearch Writer配置实现
    }

    private void generateHdfsReaderConfig(ObjectNode parameter, Map<String, String> dsConfig, Map<String, String> taskConfig) {
        // HDFS Reader配置实现
    }

    private void generateHdfsWriterConfig(ObjectNode parameter, Map<String, String> dsConfig, Map<String, String> taskConfig) {
        // HDFS Writer配置实现
    }

    private void generateFileReaderConfig(ObjectNode parameter, Map<String, String> dsConfig, Map<String, String> taskConfig) {
        // File Reader配置实现
    }

    private void generateFileWriterConfig(ObjectNode parameter, Map<String, String> dsConfig, Map<String, String> taskConfig) {
        // File Writer配置实现
    }

    /**
     * 构建JDBC URL
     */
    private String buildJdbcUrl(DataSourceType type, Map<String, String> config) {
        String host = config.get("host");
        String port = config.get("port");
        String database = config.get("database");
        
        switch (type) {
            case MYSQL:
                return String.format("jdbc:mysql://%s:%s/%s?useUnicode=true&characterEncoding=utf8&serverTimezone=UTC", 
                                    host, port != null ? port : "3306", database);
            case POSTGRESQL:
                return String.format("jdbc:postgresql://%s:%s/%s", 
                                    host, port != null ? port : "5432", database);
            case ORACLE:
                return String.format("jdbc:oracle:thin:@%s:%s:%s", 
                                    host, port != null ? port : "1521", database);
            case SQLSERVER:
                return String.format("jdbc:sqlserver://%s:%s;DatabaseName=%s", 
                                    host, port != null ? port : "1433", database);
            default:
                throw new UnsupportedOperationException("Unsupported database type: " + type);
        }
    }

    /**
     * 获取Reader名称
     */
    private String getReaderName(DataSourceType type) {
        switch (type) {
            case MYSQL: return "mysqlreader";
            case POSTGRESQL: return "postgresqlreader";
            case ORACLE: return "oraclereader";
            case SQLSERVER: return "sqlserverreader";
            case MONGODB: return "mongodbreader";
            case REDIS: return "redisreader";
            case ELASTICSEARCH: return "elasticsearchreader";
            case HDFS: return "hdfsreader";
            case FILE: return "txtfilereader";
            default: throw new UnsupportedOperationException("Unsupported reader type: " + type);
        }
    }

    /**
     * 获取Writer名称
     */
    private String getWriterName(DataSourceType type) {
        switch (type) {
            case MYSQL: return "mysqlwriter";
            case POSTGRESQL: return "postgresqlwriter";
            case ORACLE: return "oraclewriter";
            case SQLSERVER: return "sqlserverwriter";
            case MONGODB: return "mongodbwriter";
            case REDIS: return "rediswriter";
            case ELASTICSEARCH: return "elasticsearchwriter";
            case HDFS: return "hdfswriter";
            case FILE: return "txtfilewriter";
            default: throw new UnsupportedOperationException("Unsupported writer type: " + type);
        }
    }
}
