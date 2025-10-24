package com.datamate.collection.domain.process;

import com.datamate.collection.domain.model.entity.CollectionTask;

/**
 * 归集执行器接口
 *
 * @since 2025/10/23
 */
public interface ProcessRunner {
    /**
     * 执行归集任务
     *
     * @param task 任务
     * @param executionId 执行ID
     * @param timeoutSeconds 超时时间（秒）
     * @return 执行结果
     * @throws Exception 执行异常
     */
    int runJob(CollectionTask task, String executionId, int timeoutSeconds) throws Exception;
}
