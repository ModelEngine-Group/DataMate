package com.dataengine.collection.domain.service;

import com.dataengine.collection.domain.model.DataSource;
import com.dataengine.collection.domain.model.CollectionTask;

/**
 * DataX领域服务
 * 
 * 负责DataX作业的配置生成和执行管理
 */
public interface DataXDomainService {

    /**
     * 根据归集任务生成DataX配置
     */
    String generateDataXConfig(CollectionTask task, DataSource sourceDataSource, DataSource targetDataSource);

    /**
     * 验证DataX配置是否有效
     */
    boolean validateDataXConfig(String config);

    /**
     * 执行DataX作业
     */
    String executeDataXJob(String config);

    /**
     * 停止DataX作业
     */
    boolean stopDataXJob(String jobId);

    /**
     * 获取DataX作业状态
     */
    DataXJobStatus getJobStatus(String jobId);

    /**
     * 获取DataX作业日志
     */
    String getJobLogs(String jobId, int lines);
}
