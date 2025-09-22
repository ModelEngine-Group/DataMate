package com.dataengine.collection.application.service;

import com.dataengine.collection.application.dto.*;
import com.dataengine.collection.domain.model.*;
import com.dataengine.collection.domain.repository.CollectionTaskRepository;
import com.dataengine.collection.domain.repository.DataSourceRepository;
import com.dataengine.collection.domain.service.DataXDomainService;
import com.dataengine.collection.domain.service.DataXJobStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

/**
 * 归集任务应用服务
 */
@Service
@Transactional
public class CollectionTaskApplicationService {

    private final CollectionTaskRepository taskRepository;
    private final DataSourceRepository dataSourceRepository;
    private final DataXDomainService dataXDomainService;

    public CollectionTaskApplicationService(
            CollectionTaskRepository taskRepository,
            DataSourceRepository dataSourceRepository,
            DataXDomainService dataXDomainService) {
        this.taskRepository = taskRepository;
        this.dataSourceRepository = dataSourceRepository;
        this.dataXDomainService = dataXDomainService;
    }

    /**
     * 创建归集任务
     */
    public CollectionTaskDTO createTask(CollectionTaskCreateDTO createDTO) {
        // 验证数据源存在
        DataSourceId sourceId = DataSourceId.of(createDTO.getSourceDataSourceId());
        DataSourceId targetId = DataSourceId.of(createDTO.getTargetDataSourceId());

        DataSource sourceDataSource = dataSourceRepository.findById(sourceId)
            .orElseThrow(() -> new IllegalArgumentException("Source data source not found: " + createDTO.getSourceDataSourceId()));

        DataSource targetDataSource = dataSourceRepository.findById(targetId)
            .orElseThrow(() -> new IllegalArgumentException("Target data source not found: " + createDTO.getTargetDataSourceId()));

        // 验证数据源状态
        if (!sourceDataSource.isActive()) {
            throw new IllegalStateException("Source data source is not active");
        }
        if (!targetDataSource.isActive()) {
            throw new IllegalStateException("Target data source is not active");
        }

        // 创建任务
        CollectionTaskId taskId = CollectionTaskId.generate();
        CollectionTask task = new CollectionTask(
            taskId,
            createDTO.getName(),
            createDTO.getDescription(),
            sourceId,
            targetId,
            createDTO.getConfig(),
            createDTO.getSchedule()
        );

        // 验证DataX配置
        String dataXConfig = dataXDomainService.generateDataXConfig(task, sourceDataSource, targetDataSource);
        if (!dataXDomainService.validateDataXConfig(dataXConfig)) {
            throw new IllegalArgumentException("Invalid DataX configuration generated");
        }

        // 设置为就绪状态
        task.ready();

        CollectionTask savedTask = taskRepository.save(task);
        return convertToDTO(savedTask, sourceDataSource, targetDataSource);
    }

    /**
     * 更新归集任务
     */
    public CollectionTaskDTO updateTask(String id, CollectionTaskUpdateDTO updateDTO) {
        CollectionTaskId taskId = CollectionTaskId.of(id);
        CollectionTask task = taskRepository.findById(taskId)
            .orElseThrow(() -> new IllegalArgumentException("Task not found: " + id));

        if (updateDTO.getConfig() != null) {
            task.updateConfig(updateDTO.getConfig());
        }

        if (updateDTO.getSchedule() != null) {
            task.updateSchedule(updateDTO.getSchedule());
        }

        CollectionTask savedTask = taskRepository.save(task);

        // 获取数据源信息
        DataSource sourceDataSource = dataSourceRepository.findById(task.getSourceDataSourceId()).orElse(null);
        DataSource targetDataSource = dataSourceRepository.findById(task.getTargetDataSourceId()).orElse(null);

        return convertToDTO(savedTask, sourceDataSource, targetDataSource);
    }

    /**
     * 获取归集任务详情
     */
    @Transactional(readOnly = true)
    public Optional<CollectionTaskDTO> getTask(String id) {
        CollectionTaskId taskId = CollectionTaskId.of(id);
        return taskRepository.findById(taskId)
            .map(task -> {
                DataSource sourceDataSource = dataSourceRepository.findById(task.getSourceDataSourceId()).orElse(null);
                DataSource targetDataSource = dataSourceRepository.findById(task.getTargetDataSourceId()).orElse(null);
                return convertToDTO(task, sourceDataSource, targetDataSource);
            });
    }

    /**
     * 分页查询归集任务
     */
    @Transactional(readOnly = true)
    public Page<CollectionTaskDTO> getTasks(Pageable pageable, TaskStatus status) {
        Page<CollectionTask> page = status != null
            ? taskRepository.findByStatus(status, pageable)
            : taskRepository.findAll(pageable);

        return page.map(task -> {
            DataSource sourceDataSource = dataSourceRepository.findById(task.getSourceDataSourceId()).orElse(null);
            DataSource targetDataSource = dataSourceRepository.findById(task.getTargetDataSourceId()).orElse(null);
            return convertToDTO(task, sourceDataSource, targetDataSource);
        });
    }

    /**
     * 执行归集任务
     */
    public TaskExecutionDTO executeTask(String id) {
        CollectionTaskId taskId = CollectionTaskId.of(id);
        CollectionTask task = taskRepository.findById(taskId)
            .orElseThrow(() -> new IllegalArgumentException("Task not found: " + id));

        if (!task.canExecute()) {
            throw new IllegalStateException("Task cannot be executed in current status: " + task.getStatus());
        }

        // 获取数据源
        DataSource sourceDataSource = dataSourceRepository.findById(task.getSourceDataSourceId())
            .orElseThrow(() -> new IllegalArgumentException("Source data source not found"));

        DataSource targetDataSource = dataSourceRepository.findById(task.getTargetDataSourceId())
            .orElseThrow(() -> new IllegalArgumentException("Target data source not found"));

        // 生成DataX配置
        String dataXConfig = dataXDomainService.generateDataXConfig(task, sourceDataSource, targetDataSource);

        // 执行DataX作业
        String executionId = dataXDomainService.executeDataXJob(dataXConfig);

        // 更新任务状态
        task.start(executionId);
        taskRepository.save(task);

        return new TaskExecutionDTO(
            executionId,
            task.getId().getValue(),
            "RUNNING",
            LocalDateTime.now(),
            null,
            null,
            null,
            null,
            null
        );
    }

    /**
     * 停止归集任务
     */
    public void stopTask(String id) {
        CollectionTaskId taskId = CollectionTaskId.of(id);
        CollectionTask task = taskRepository.findById(taskId)
            .orElseThrow(() -> new IllegalArgumentException("Task not found: " + id));

        if (task.getLastExecutionId() != null) {
            boolean stopped = dataXDomainService.stopDataXJob(task.getLastExecutionId());
            if (stopped) {
                task.stop();
                taskRepository.save(task);
            }
        }
    }

    /**
     * 获取任务执行状态
     */
    @Transactional(readOnly = true)
    public TaskExecutionStatusDTO getTaskExecutionStatus(String id) {
        CollectionTaskId taskId = CollectionTaskId.of(id);
        CollectionTask task = taskRepository.findById(taskId)
            .orElseThrow(() -> new IllegalArgumentException("Task not found: " + id));

        if (task.getLastExecutionId() == null) {
            return new TaskExecutionStatusDTO(
                task.getId().getValue(),
                task.getStatus().name(),
                null,
                0.0,
                0L,
                0L,
                null
            );
        }

        DataXJobStatus jobStatus = dataXDomainService.getJobStatus(task.getLastExecutionId());

        return new TaskExecutionStatusDTO(
            task.getId().getValue(),
            jobStatus.getState().name(),
            jobStatus.getErrorMessage(),
            jobStatus.getProgress(),
            jobStatus.getRecordsProcessed(),
            jobStatus.getRecordsTotal(),
            jobStatus.getState().name()
        );
    }

    /**
     * 获取任务执行日志
     */
    @Transactional(readOnly = true)
    public TaskExecutionLogsDTO getTaskExecutionLogs(String id, int lines) {
        CollectionTaskId taskId = CollectionTaskId.of(id);
        CollectionTask task = taskRepository.findById(taskId)
            .orElseThrow(() -> new IllegalArgumentException("Task not found: " + id));

        if (task.getLastExecutionId() == null) {
            return new TaskExecutionLogsDTO(task.getId().getValue(), new ArrayList<>(), 0, 1, lines);
        }

        String logs = dataXDomainService.getJobLogs(task.getLastExecutionId(), lines);
        String[] logLines = logs.split("\n");

        List<TaskExecutionLogsDTO.LogEntry> logEntries = new ArrayList<>();
        for (String line : logLines) {
            logEntries.add(new TaskExecutionLogsDTO.LogEntry(
                LocalDateTime.now().toString(),
                "INFO",
                line
            ));
        }

        return new TaskExecutionLogsDTO(task.getLastExecutionId(), logEntries, logLines.length, 1, lines);
    }

    /**
     * 删除归集任务
     */
    public void deleteTask(String id) {
        CollectionTaskId taskId = CollectionTaskId.of(id);
        CollectionTask task = taskRepository.findById(taskId)
            .orElseThrow(() -> new IllegalArgumentException("Task not found: " + id));

        // 如果任务正在运行，先停止
        if (task.getStatus() == TaskStatus.RUNNING && task.getLastExecutionId() != null) {
            dataXDomainService.stopDataXJob(task.getLastExecutionId());
        }

        taskRepository.delete(task);
    }

    /**
     * 定时检查任务执行状态
     */
//    jar包启动时报错 先注释掉
//    @Scheduled(fixedDelay = 30000) // 每30秒检查一次
    public void checkRunningTasks() {
        var runningTasks = taskRepository.findRunningTasks();

        for (CollectionTask task : runningTasks) {
            if (task.getLastExecutionId() != null) {
                DataXJobStatus jobStatus = dataXDomainService.getJobStatus(task.getLastExecutionId());

                // 更新任务状态
                if (jobStatus.isCompleted()) {
                    task.complete();
                    taskRepository.save(task);
                } else if (jobStatus.isFailed()) {
                    task.fail();
                    taskRepository.save(task);
                }
            }
        }
    }

    /**
     * 转换为DTO
     */
    private CollectionTaskDTO convertToDTO(CollectionTask task, DataSource sourceDataSource, DataSource targetDataSource) {
        return new CollectionTaskDTO(
            task.getId().getValue(),
            task.getName(),
            task.getDescription(),
            task.getSourceDataSourceId().getValue(),
            sourceDataSource != null ? sourceDataSource.getName() : null,
            task.getTargetDataSourceId().getValue(),
            targetDataSource != null ? targetDataSource.getName() : null,
            task.getConfig(),
            task.getStatus(),
            task.getScheduleExpression(),
            task.getCreatedAt(),
            task.getUpdatedAt()
        );
    }
}
