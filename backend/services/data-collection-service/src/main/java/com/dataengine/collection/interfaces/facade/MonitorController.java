package com.dataengine.collection.interfaces.facade;

import com.dataengine.collection.interfaces.api.MonitorApi;
import com.dataengine.collection.interfaces.dto.CollectionStatistics;
import com.dataengine.collection.interfaces.dto.TaskExecutionLogs;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class MonitorController implements MonitorApi {
    @Override
    public ResponseEntity<TaskExecutionLogs> executionsExecutionIdLogsGet(String executionId, Integer lines, String level) {
        return ResponseEntity.ok(new TaskExecutionLogs());
    }

    @Override
    public ResponseEntity<CollectionStatistics> monitorStatisticsGet(String period) {
        return ResponseEntity.ok(new CollectionStatistics());
    }
}
