package com.edatamate.domain.dataset.schedule;

import com.edatamate.common.schedule.SimpleCronTask;
import com.edatamate.domain.dataset.parser.datasetconfig.SyncConfig;
import org.springframework.stereotype.Service;

import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;

/**
 * 定时同步任务服务类
 *
 * @since: 2025-07-16
 */
@Service
public class ScheduleSyncService {
    private final ScheduledExecutorService pool = Executors.newScheduledThreadPool(5);

    /**
     * 创建一个新的定时任务
     *
     * @param job 任务的实际执行逻辑
     * @param syncConfig 定时配置
     * @return 返回一个 SimpleCronTask 实例
     */
    public SimpleCronTask addScheduleCornTask(Runnable job, SyncConfig syncConfig) {
        SimpleCronTask task = new SimpleCronTask(job, syncConfig.getCron(), syncConfig.getMaxExecuteTimes(), pool);
        if (syncConfig.isExecuteCurrent()) {
            task.runOnceNow();
        }
        task.start();
        return task;
    }
}
