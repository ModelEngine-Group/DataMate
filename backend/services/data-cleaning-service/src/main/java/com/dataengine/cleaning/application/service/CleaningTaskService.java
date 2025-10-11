package com.dataengine.cleaning.application.service;


import com.dataengine.cleaning.application.httpclient.DatasetClient;
import com.dataengine.cleaning.application.httpclient.RuntimeClient;
import com.dataengine.cleaning.domain.converter.OperatorInstanceConverter;
import com.dataengine.cleaning.domain.model.Dataset;
import com.dataengine.cleaning.domain.model.ExecutorType;
import com.dataengine.cleaning.domain.model.OperatorInstancePo;
import com.dataengine.cleaning.domain.model.PagedDatasetFile;
import com.dataengine.cleaning.domain.model.TaskProcess;
import com.dataengine.cleaning.infrastructure.persistence.mapper.CleaningTaskMapper;
import com.dataengine.cleaning.infrastructure.persistence.mapper.OperatorInstanceMapper;
import com.dataengine.cleaning.interfaces.dto.CleaningTask;
import com.dataengine.cleaning.interfaces.dto.CreateCleaningTaskRequest;
import com.dataengine.cleaning.interfaces.dto.OperatorInstance;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import lombok.RequiredArgsConstructor;
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
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@Service
@RequiredArgsConstructor
public class CleaningTaskService {
    private final CleaningTaskMapper cleaningTaskMapper;

    private final OperatorInstanceMapper operatorInstanceMapper;

    private final ExecutorService taskExecutor = Executors.newFixedThreadPool(5);

    public List<CleaningTask> getTasks(String status) {
        return cleaningTaskMapper.findTasksByStatus(status);
    }

    @Transactional
    public CleaningTask createTask(CreateCleaningTaskRequest request) {
        Dataset dataset = DatasetClient.createDataset(request.getDestDatasetName(), request.getDestDatasetType());

        CleaningTask task = new CleaningTask();
        task.setName(request.getName());
        task.setDescription(request.getDescription());
        task.setStatus(CleaningTask.StatusEnum.PENDING);
        String taskId = UUID.randomUUID().toString();
        task.setId(taskId);
        task.setSrcDatasetId(request.getSrcDatasetId());
        task.setDestDatasetId(dataset.getId());
        task.setDestDatasetName(dataset.getName());
        cleaningTaskMapper.insertTask(task);

        List<OperatorInstancePo> instancePos = request.getInstance().stream()
                .map(OperatorInstanceConverter.INSTANCE::operatorToDo).toList();
        operatorInstanceMapper.insertInstance(taskId, instancePos);

        taskExecutor.submit(() -> executeTask(task, request, dataset.getId()));
        return task;
    }

    public CleaningTask getTask(String taskId) {
        return cleaningTaskMapper.findTaskById(taskId);
    }

    @Transactional
    public void deleteTask(String taskId) {
        cleaningTaskMapper.deleteTask(taskId);
    }

    private void executeTask(CleaningTask task, CreateCleaningTaskRequest request, String destDatasetId) {
        task.setStatus(CleaningTask.StatusEnum.RUNNING);
        cleaningTaskMapper.updateTaskStatus(task);
        prepareTask(task, request.getInstance());
        scanDataset(task.getId(), request.getSrcDatasetId());
        submitTask(task);
    }

    private void prepareTask(CleaningTask task, List<OperatorInstance> instances) {
        TaskProcess process = new TaskProcess();
        process.setInstanceId(task.getId());
        process.setDatasetPath("/opt/runtime/" + task.getSrcDatasetId() + "/");
        process.setExportPath("/opt/runtime/" + task.getDestDatasetId() + "/");
        process.setExecutorType(ExecutorType.DATA_PLATFORM.getValue());
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

        File file = new File("/opt/runtime/flow/" + process.getInstanceId() + "/process.yaml");
        file.getParentFile().mkdirs();

        try (FileWriter writer = new FileWriter(file)) {
            yaml.dump(jsonNode, writer);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    private void scanDataset(String taskId, String srcDatasetId) {
        int pageNumber = 0;
        int pageSize = 500;
        PageRequest pageRequest = PageRequest.of(pageNumber, pageSize);
        PagedDatasetFile datasetFile;
        do {
            datasetFile = DatasetClient.getDatasetFile(srcDatasetId, pageRequest);
            List<Map<String, Object>> files = datasetFile.getContent().stream()
                    .map(content -> Map.of("file_name", (Object) content.getFileName(),
                            "file_size", content.getFileSize()))
                    .toList();
            writeListMapToJsonlFile(files, "/opt/runtime/flow/" + taskId + "/dataset.jsonl");
            pageNumber += 1;
        } while (pageNumber < datasetFile.getTotalPages());
    }

    private void submitTask(CleaningTask task) {
        RuntimeClient.submitTask(task.getId());
    }

    private void writeListMapToJsonlFile(List<Map<String, Object>> mapList, String fileName) {
        ObjectMapper objectMapper = new ObjectMapper();

        try (BufferedWriter writer = new BufferedWriter(new FileWriter(fileName))) {
            for (Map<String, Object> map : mapList) {
                    String jsonString = objectMapper.writeValueAsString(map);
                    writer.write(jsonString);
                    writer.newLine();
            }
        } catch (IOException e) {
            System.err.println("Error serializing map to JSON: " + e.getMessage());
        }
    }
}
