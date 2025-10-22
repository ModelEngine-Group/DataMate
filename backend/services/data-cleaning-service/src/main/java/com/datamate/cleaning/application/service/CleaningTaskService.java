package com.datamate.cleaning.application.service;


import com.datamate.cleaning.application.httpclient.DatasetClient;
import com.datamate.cleaning.application.scheduler.CleaningTaskScheduler;
import com.datamate.cleaning.domain.converter.OperatorInstanceConverter;
import com.datamate.cleaning.domain.model.DatasetResponse;
import com.datamate.cleaning.domain.model.ExecutorType;
import com.datamate.cleaning.domain.model.OperatorInstancePo;
import com.datamate.cleaning.domain.model.PagedDatasetFileResponse;
import com.datamate.cleaning.domain.model.TaskProcess;
import com.datamate.cleaning.infrastructure.persistence.mapper.CleaningResultMapper;
import com.datamate.cleaning.infrastructure.persistence.mapper.CleaningTaskMapper;
import com.datamate.cleaning.infrastructure.persistence.mapper.OperatorInstanceMapper;
import com.datamate.cleaning.interfaces.dto.CleaningProcess;
import com.datamate.cleaning.interfaces.dto.CleaningTask;
import com.datamate.cleaning.interfaces.dto.CreateCleaningTaskRequest;
import com.datamate.cleaning.interfaces.dto.OperatorInstance;
import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.yaml.snakeyaml.DumperOptions;
import org.yaml.snakeyaml.Yaml;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class CleaningTaskService {
    private final CleaningTaskMapper cleaningTaskMapper;

    private final OperatorInstanceMapper operatorInstanceMapper;

    private final CleaningResultMapper cleaningResultMapper;

    private final CleaningTaskScheduler taskScheduler;

    private final String DATASET_PATH = "/dataset";

    private final String FLOW_PATH = "/flow";

    public List<CleaningTask> getTasks(String status, String keywords, Integer page, Integer size) {
        Integer offset = page * size;
        List<CleaningTask> tasks = cleaningTaskMapper.findTasks(status, keywords, size, offset);
        tasks.forEach(this::setProcess);
        return tasks;
    }

    private void setProcess(CleaningTask task) {
        int count = cleaningResultMapper.countByInstanceId(task.getId());
        task.setProgress(CleaningProcess.of(task.getFileCount(), count));
    }

    public int countTasks(String status, String keywords) {
        return cleaningTaskMapper.findTasks(status, keywords, null, null).size();
    }

    @Transactional
    public CleaningTask createTask(CreateCleaningTaskRequest request) {
        DatasetResponse destDataset = DatasetClient.createDataset(request.getDestDatasetName(),
                request.getDestDatasetType());

        DatasetResponse srcDataset = DatasetClient.getDataset(request.getSrcDatasetId());

        CleaningTask task = new CleaningTask();
        task.setName(request.getName());
        task.setDescription(request.getDescription());
        task.setStatus(CleaningTask.StatusEnum.PENDING);
        String taskId = UUID.randomUUID().toString();
        task.setId(taskId);
        task.setSrcDatasetId(request.getSrcDatasetId());
        task.setSrcDatasetName(request.getSrcDatasetName());
        task.setDestDatasetId(destDataset.getId());
        task.setDestDatasetName(destDataset.getName());
        task.setBeforeSize(srcDataset.getTotalSize());
        task.setFileCount(srcDataset.getFileCount());
        cleaningTaskMapper.insertTask(task);

        List<OperatorInstancePo> instancePos = request.getInstance().stream()
                .map(OperatorInstanceConverter.INSTANCE::operatorToDo).toList();
        operatorInstanceMapper.insertInstance(taskId, instancePos);

        prepareTask(task, request.getInstance());
        scanDataset(taskId, request.getSrcDatasetId());
        executeTask(taskId);
        return task;
    }

    public CleaningTask getTask(String taskId) {
        CleaningTask task = cleaningTaskMapper.findTaskById(taskId);
        setProcess(task);
        return task;
    }

    @Transactional
    public void deleteTask(String taskId) {
        cleaningTaskMapper.deleteTask(taskId);
        operatorInstanceMapper.deleteByInstanceId(taskId);
        cleaningResultMapper.deleteByInstanceId(taskId);
    }

    public void executeTask(String taskId) {
        taskScheduler.executeTask(taskId);
    }

    private void prepareTask(CleaningTask task, List<OperatorInstance> instances) {
        TaskProcess process = new TaskProcess();
        process.setInstanceId(task.getId());
        process.setDatasetId(task.getDestDatasetId());
        process.setDatasetPath(FLOW_PATH + "/" + task.getId() + "/dataset.jsonl");
        process.setExportPath(DATASET_PATH + "/" + task.getDestDatasetId());
        process.setExecutorType(ExecutorType.DATAMATE.getValue());
        process.setProcess(instances.stream()
                .map(instance -> Map.of(instance.getId(), instance.getOverrides()))
                .toList());

        ObjectMapper jsonMapper = new ObjectMapper(new YAMLFactory());
        jsonMapper.setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE);
        JsonNode jsonNode = jsonMapper.valueToTree(process);

        DumperOptions options = new DumperOptions();
        options.setIndent(2);
        options.setDefaultFlowStyle(DumperOptions.FlowStyle.BLOCK);
        Yaml yaml = new Yaml(options);

        File file = new File(FLOW_PATH + "/" + process.getInstanceId() + "/process.yaml");
        file.getParentFile().mkdirs();

        try (FileWriter writer = new FileWriter(file)) {
            yaml.dump(jsonMapper.treeToValue(jsonNode, Map.class), writer);
        } catch (IOException e) {
            log.error("Failed to prepare process.yaml.", e);
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR);
        }
    }

    private void scanDataset(String taskId, String srcDatasetId) {
        int pageNumber = 0;
        int pageSize = 500;
        PageRequest pageRequest = PageRequest.of(pageNumber, pageSize);
        PagedDatasetFileResponse datasetFile;
        do {
            datasetFile = DatasetClient.getDatasetFile(srcDatasetId, pageRequest);
            if (datasetFile.getContent() != null && datasetFile.getContent().isEmpty()) {
                break;
            }
            List<Map<String, Object>> files = datasetFile.getContent().stream()
                    .map(content -> Map.of("fileName", (Object) content.getFileName(),
                            "fileSize", content.getFileSize(),
                            "filePath", content.getFilePath(),
                            "fileType", content.getFileType(),
                            "fileId", content.getId()))
                    .toList();
            writeListMapToJsonlFile(files, FLOW_PATH + "/" + taskId + "/dataset.jsonl");
            pageNumber += 1;
        } while (pageNumber < datasetFile.getTotalPages());
    }

    private void writeListMapToJsonlFile(List<Map<String, Object>> mapList, String fileName) {
        ObjectMapper objectMapper = new ObjectMapper();

        try (BufferedWriter writer = new BufferedWriter(new FileWriter(fileName))) {
            if (!mapList.isEmpty()) { // 检查列表是否为空，避免异常
                String jsonString = objectMapper.writeValueAsString(mapList.get(0));
                writer.write(jsonString);

                for (int i = 1; i < mapList.size(); i++) {
                    writer.newLine();
                    jsonString = objectMapper.writeValueAsString(mapList.get(i));
                    writer.write(jsonString);
                }
            }
        } catch (IOException e) {
            log.error("Failed to prepare dataset.jsonl.", e);
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR);
        }
    }

    public void stopTask(String taskId) {
        taskScheduler.stopTask(taskId);
    }
}
