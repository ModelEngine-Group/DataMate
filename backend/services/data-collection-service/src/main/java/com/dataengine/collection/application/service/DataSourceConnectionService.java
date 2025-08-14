package com.dataengine.collection.application.service;

import com.dataengine.collection.application.dto.ConnectionTestResultDTO;
import com.dataengine.collection.domain.model.DataSource;

/**
 * 数据源连接测试服务
 */
public interface DataSourceConnectionService {

    /**
     * 测试数据源连接
     */
    ConnectionTestResultDTO testConnection(DataSource dataSource);
}
