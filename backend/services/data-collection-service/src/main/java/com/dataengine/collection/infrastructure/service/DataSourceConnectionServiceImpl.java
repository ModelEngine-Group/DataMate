package com.dataengine.collection.infrastructure.service;

import com.dataengine.collection.application.dto.ConnectionTestResultDTO;
import com.dataengine.collection.application.service.DataSourceConnectionService;
import com.dataengine.collection.domain.model.DataSource;
import com.dataengine.collection.domain.model.DataSourceType;
import org.springframework.stereotype.Service;

import java.sql.Connection;
import java.sql.DriverManager;
import java.util.Map;

/**
 * 数据源连接测试服务实现
 */
@Service
public class DataSourceConnectionServiceImpl implements DataSourceConnectionService {

    @Override
    public ConnectionTestResultDTO testConnection(DataSource dataSource) {
        try {
            long startTime = System.currentTimeMillis();
            boolean isConnected = testConnectionInternal(dataSource);
            long latency = (int) (System.currentTimeMillis() - startTime);
            
            return new ConnectionTestResultDTO(
                isConnected,
                isConnected ? "Connection successful" : "Connection failed",
                (int) latency,
                java.time.LocalDateTime.now()
            );
        } catch (Exception e) {
            return new ConnectionTestResultDTO(
                false,
                "Connection failed: " + e.getMessage(),
                null,
                java.time.LocalDateTime.now()
            );
        }
    }

    private boolean testConnectionInternal(DataSource dataSource) throws Exception {
        DataSourceType type = dataSource.getType();
        Map<String, String> config = dataSource.getConfig();

        switch (type) {
            case MYSQL:
                return testMySQLConnection(config);
            case POSTGRESQL:
                return testPostgreSQLConnection(config);
            case FILE:
                return testFileConnection(config);
            case HTTP:
                return testHttpConnection(config);
            default:
                throw new UnsupportedOperationException("Unsupported data source type: " + type);
        }
    }

    private boolean testMySQLConnection(Map<String, String> config) throws Exception {
        String host = config.get("host");
        String port = config.getOrDefault("port", "3306");
        String database = config.get("database");
        String username = config.get("username");
        String password = config.get("password");

        String url = String.format("jdbc:mysql://%s:%s/%s", host, port, database);
        
        try (Connection connection = DriverManager.getConnection(url, username, password)) {
            return connection.isValid(5); // 5 seconds timeout
        }
    }

    private boolean testPostgreSQLConnection(Map<String, String> config) throws Exception {
        String host = config.get("host");
        String port = config.getOrDefault("port", "5432");
        String database = config.get("database");
        String username = config.get("username");
        String password = config.get("password");

        String url = String.format("jdbc:postgresql://%s:%s/%s", host, port, database);
        
        try (Connection connection = DriverManager.getConnection(url, username, password)) {
            return connection.isValid(5); // 5 seconds timeout
        }
    }

    private boolean testFileConnection(Map<String, String> config) throws Exception {
        String filePath = config.get("path");
        if (filePath == null || filePath.trim().isEmpty()) {
            return false;
        }
        
        java.io.File file = new java.io.File(filePath);
        return file.exists() && file.canRead();
    }

    private boolean testHttpConnection(Map<String, String> config) throws Exception {
        String url = config.get("url");
        if (url == null || url.trim().isEmpty()) {
            return false;
        }
        
        java.net.HttpURLConnection connection = (java.net.HttpURLConnection) 
            new java.net.URL(url).openConnection();
        connection.setRequestMethod("HEAD");
        connection.setConnectTimeout(5000); // 5 seconds
        connection.setReadTimeout(5000); // 5 seconds
        
        int responseCode = connection.getResponseCode();
        return responseCode >= 200 && responseCode < 400;
    }
}
