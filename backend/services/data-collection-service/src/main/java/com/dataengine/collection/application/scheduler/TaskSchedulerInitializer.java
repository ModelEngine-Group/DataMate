package com.dataengine.collection.application.scheduler;

import com.dataengine.collection.application.service.DataxExecutionService;
import com.dataengine.collection.domain.model.CollectionTask;
import com.dataengine.collection.domain.model.TaskStatus;
import com.dataengine.collection.domain.model.TaskExecution;
import com.dataengine.collection.infrastructure.persistence.mapper.CollectionTaskMapper;
import com.dataengine.collection.infrastructure.persistence.mapper.TaskExecutionMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.scheduling.support.CronExpression;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import java.time.LocalDateTime;
import java.util.List;

@Slf4j
@Component
@RequiredArgsConstructor
public class TaskSchedulerInitializer {

    private final CollectionTaskMapper taskMapper;
    private final TaskExecutionMapper executionMapper;
    private final DataxExecutionService dataxExecutionService;

    // 定期扫描激活的采集任务，根据 Cron 判断是否到期执行
    @Scheduled(fixedDelayString = "${dataengine.data-collection.scheduler.scan-interval-ms:10000}")
    public void scanAndTrigger() {
        List<CollectionTask> tasks = taskMapper.selectActiveTasks();
        if (tasks == null || tasks.isEmpty()) {
            return;
        }
        LocalDateTime now = LocalDateTime.now();
        for (CollectionTask task : tasks) {
            String cronExpr = task.getScheduleExpression();
            if (!StringUtils.hasText(cronExpr)) {
                continue;
            }
            try {
                // 如果最近一次执行仍在运行，则跳过
                TaskExecution latest = executionMapper.selectLatestByTaskId(task.getId());
                if (latest != null && latest.getStatus() == TaskStatus.RUNNING) {
                    continue;
                }

                CronExpression cron = CronExpression.parse(cronExpr);
                LocalDateTime base = latest != null && latest.getStartedAt() != null
                        ? latest.getStartedAt()
                        : now.minusYears(1); // 没有历史记录时，拉长基准时间确保到期判定
                LocalDateTime nextTime = cron.next(base);

                if (nextTime != null && !nextTime.isAfter(now)) {
                    // 到期，触发一次执行
                    TaskExecution exec = dataxExecutionService.createExecution(task);
                    int timeout = task.getTimeoutSeconds() == null ? 3600 : task.getTimeoutSeconds();
                    dataxExecutionService.runAsync(task, exec.getId(), timeout);
                    log.info("Triggered DataX execution for task {} at {}, execId={}", task.getId(), now, exec.getId());
                }
            } catch (Exception ex) {
                log.warn("Skip task {} due to invalid cron or scheduling error: {}", task.getId(), ex.getMessage());
            }
        }
    }
}
