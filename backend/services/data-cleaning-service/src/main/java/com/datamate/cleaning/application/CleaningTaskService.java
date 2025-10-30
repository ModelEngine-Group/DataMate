package com.datamate.cleaning.application;


import com.datamate.cleaning.application.scheduler.CleaningTaskScheduler;
import com.datamate.cleaning.common.enums.CleaningTaskStatusEnum;
import com.datamate.cleaning.common.enums.ExecutorType;

import com.datamate.cleaning.domain.model.TaskProcess;
import com.datamate.cleaning.domain.repository.CleaningResultRepository;
import com.datamate.cleaning.domain.repository.CleaningTaskRepository;
import com.datamate.cleaning.domain.repository.OperatorInstanceRepository;

import com.datamate.cleaning.infrastructure.validator.CleanTaskValidator;
import com.datamate.cleaning.interfaces.dto.CleaningProcess;
import com.datamate.cleaning.interfaces.dto.CleaningTaskDto;
import com.datamate.cleaning.interfaces.dto.CreateCleaningTaskRequest;
import com.datamate.cleaning.interfaces.dto.OperatorInstanceDto;
import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import com.datamate.datamanagement.application.DatasetApplicationService;
import com.datamate.datamanagement.application.DatasetFileApplicationService;
import com.datamate.datamanagement.common.enums.DatasetType;
import com.datamate.datamanagement.domain.model.dataset.Dataset;
import com.datamate.datamanagement.domain.model.dataset.DatasetFile;
import com.datamate.datamanagement.interfaces.dto.CreateDatasetRequest;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
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
    private final CleaningTaskRepository CleaningTaskRepo;

    private final OperatorInstanceRepository operatorInstanceRepo;

    private final CleaningResultRepository cleaningResultRepo;

    private final CleaningTaskScheduler taskScheduler;

    private final DatasetApplicationService datasetService;

    private final DatasetFileApplicationService datasetFileService;

    private final CleanTaskValidator cleanTaskValidator;

    private final String DATASET_PATH = "/dataset";

    private final String FLOW_PATH = "/flow";

    public List<CleaningTaskDto> getTasks(String status, String keywords, Integer page, Integer size) {
        List<CleaningTaskDto> tasks = CleaningTaskRepo.findTasks(status, keywords, page, size);
        tasks.forEach(this::setProcess);
        return tasks;
    }

    private void setProcess(CleaningTaskDto task) {
        int count = cleaningResultRepo.countByInstanceId(task.getId());
        task.setProgress(CleaningProcess.of(task.getFileCount(), count));
    }

    public int countTasks(String status, String keywords) {
        return CleaningTaskRepo.findTasks(status, keywords, null, null).size();
    }

    @Transactional
    public CleaningTaskDto createTask(CreateCleaningTaskRequest request) {
        cleanTaskValidator.checkNameDuplication(request.getName());
        cleanTaskValidator.checkInputAndOutput(request.getInstance());

        CreateDatasetRequest createDatasetRequest = new CreateDatasetRequest();
        createDatasetRequest.setName(request.getDestDatasetName());
        createDatasetRequest.setDatasetType(DatasetType.valueOf(request.getDestDatasetType()));
        Dataset destDataset = datasetService.createDataset(createDatasetRequest);

        Dataset srcDataset = datasetService.getDataset(request.getSrcDatasetId());

        CleaningTaskDto task = new CleaningTaskDto();
        task.setName(request.getName());
        task.setDescription(request.getDescription());
        task.setStatus(CleaningTaskStatusEnum.PENDING);
        String taskId = UUID.randomUUID().toString();
        task.setId(taskId);
        task.setSrcDatasetId(request.getSrcDatasetId());
        task.setSrcDatasetName(request.getSrcDatasetName());
        task.setDestDatasetId(destDataset.getId());
        task.setDestDatasetName(destDataset.getName());
        task.setBeforeSize(srcDataset.getSizeBytes());
        task.setFileCount(srcDataset.getFileCount().intValue());
        CleaningTaskRepo.insertTask(task);

        operatorInstanceRepo.insertInstance(taskId, request.getInstance());

        prepareTask(task, request.getInstance());
        scanDataset(taskId, request.getSrcDatasetId());
        executeTask(taskId);
        return task;
    }

    public CleaningTaskDto getTask(String taskId) {
        CleaningTaskDto task = CleaningTaskRepo.findTaskById(taskId);
        setProcess(task);
        return task;
    }

    @Transactional
    public void deleteTask(String taskId) {
        CleaningTaskRepo.deleteTaskById(taskId);
        operatorInstanceRepo.deleteByInstanceId(taskId);
        cleaningResultRepo.deleteByInstanceId(taskId);
    }

    public void executeTask(String taskId) {
        taskScheduler.executeTask(taskId);
    }

    private void prepareTask(CleaningTaskDto task, List<OperatorInstanceDto> instances) {
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
        Page<DatasetFile> datasetFiles;
        do {
            datasetFiles = datasetFileService.getDatasetFiles(srcDatasetId, null, null, pageRequest);
            if (datasetFiles.getContent().isEmpty()) {
                break;
            }
            List<Map<String, Object>> files = datasetFiles.getContent().stream()
                    .map(content -> Map.of("fileName", (Object) content.getFileName(),
                            "fileSize", content.getFileSize(),
                            "filePath", content.getFilePath(),
                            "fileType", content.getFileType(),
                            "fileId", content.getId()))
                    .toList();
            writeListMapToJsonlFile(files, FLOW_PATH + "/" + taskId + "/dataset.jsonl");
            pageNumber += 1;
        } while (pageNumber < datasetFiles.getTotalPages());
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
