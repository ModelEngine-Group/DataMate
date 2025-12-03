package com.datamate.cleaning.application;


import com.datamate.cleaning.application.scheduler.CleaningTaskScheduler;
import com.datamate.cleaning.common.enums.CleaningTaskStatusEnum;
import com.datamate.cleaning.common.enums.ExecutorType;
import com.datamate.cleaning.domain.model.TaskProcess;
import com.datamate.cleaning.domain.repository.CleaningResultRepository;
import com.datamate.cleaning.domain.repository.CleaningTaskRepository;
import com.datamate.cleaning.domain.repository.OperatorInstanceRepository;
import com.datamate.cleaning.infrastructure.validator.CleanTaskValidator;
import com.datamate.cleaning.interfaces.dto.*;
import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import com.datamate.common.interfaces.PagedResponse;
import com.datamate.common.interfaces.PagingQuery;
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
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.yaml.snakeyaml.DumperOptions;
import org.yaml.snakeyaml.Yaml;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.*;
import java.util.concurrent.atomic.AtomicReference;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import java.util.stream.Stream;

@Slf4j
@Service
@RequiredArgsConstructor
public class CleaningTaskService {
    private final CleaningTaskRepository cleaningTaskRepo;

    private final OperatorInstanceRepository operatorInstanceRepo;

    private final CleaningResultRepository cleaningResultRepo;

    private final CleaningTaskScheduler taskScheduler;

    private final DatasetApplicationService datasetService;

    private final DatasetFileApplicationService datasetFileService;

    private final CleanTaskValidator cleanTaskValidator;

    private final String DATASET_PATH = "/dataset";

    private final String FLOW_PATH = "/flow";

    private final Pattern LEVEL_PATTERN = Pattern.compile(
            "\\b(TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL)\\b",
            Pattern.CASE_INSENSITIVE
    );

    public List<CleaningTaskDto> getTasks(String status, String keywords, Integer page, Integer size) {
        List<CleaningTaskDto> tasks = cleaningTaskRepo.findTasks(status, keywords, page, size);
        tasks.forEach(this::setProcess);
        return tasks;
    }

    private void setProcess(CleaningTaskDto task) {
        int[] count = cleaningResultRepo.countByInstanceId(task.getId());
        task.setProgress(CleaningProcess.of(task.getFileCount(), count[0], count[1]));
    }

    public int countTasks(String status, String keywords) {
        return cleaningTaskRepo.findTasks(status, keywords, null, null).size();
    }

    @Transactional
    public CleaningTaskDto createTask(CreateCleaningTaskRequest request) {
        cleanTaskValidator.checkNameDuplication(request.getName());
        cleanTaskValidator.checkInputAndOutput(request.getInstance());

        CreateDatasetRequest createDatasetRequest = new CreateDatasetRequest();
        createDatasetRequest.setName(request.getDestDatasetName());
        createDatasetRequest.setDatasetType(DatasetType.valueOf(request.getDestDatasetType()));
        createDatasetRequest.setStatus("ACTIVE");
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
        cleaningTaskRepo.insertTask(task);

        operatorInstanceRepo.insertInstance(taskId, request.getInstance());

        prepareTask(task, request.getInstance());
        scanDataset(taskId, request.getSrcDatasetId());
        taskScheduler.executeTask(taskId);
        return task;
    }

    public CleaningTaskDto getTask(String taskId) {
        CleaningTaskDto task = cleaningTaskRepo.findTaskById(taskId);
        setProcess(task);
        task.setInstance(operatorInstanceRepo.findOperatorByInstanceId(taskId));
        return task;
    }

    public List<CleaningResultDto> getTaskResults(String taskId) {
        return cleaningResultRepo.findByInstanceId(taskId);
    }

    public List<CleaningTaskLog> getTaskLog(String taskId) {
        String logPath = FLOW_PATH + "/" + taskId + "/output.log";
        try (Stream<String> lines = Files.lines(Paths.get(logPath))) {
            List<CleaningTaskLog> logs = new ArrayList<>();
            AtomicReference<String> lastLevel = new AtomicReference<>("INFO");
            lines.forEach(line -> {
                lastLevel.set(getLogLevel(line, lastLevel.get()));
                CleaningTaskLog log = new CleaningTaskLog();
                log.setLevel(lastLevel.get());
                log.setMessage(line);
                logs.add(log);
            });
            return logs;
        } catch (IOException e) {
            log.error("Fail to read log file {}", logPath, e);
            return Collections.emptyList();
        }
    }

    private String getLogLevel(String logLine, String defaultLevel) {
        if (logLine == null || logLine.trim().isEmpty()) {
            return defaultLevel;
        }

        Matcher matcher = LEVEL_PATTERN.matcher(logLine);
        if (matcher.find()) {
            return matcher.group(1).toUpperCase();
        }
        return defaultLevel;
    }

    @Transactional
    public void deleteTask(String taskId) {
        cleaningTaskRepo.deleteTaskById(taskId);
        operatorInstanceRepo.deleteByInstanceId(taskId);
        cleaningResultRepo.deleteByInstanceId(taskId);
    }

    public void executeTask(String taskId) {
        List<CleaningResultDto> succeed = cleaningResultRepo.findByInstanceId(taskId, "COMPLETED");
        Set<String> succeedSet = succeed.stream().map(CleaningResultDto::getSrcFileId).collect(Collectors.toSet());
        CleaningTaskDto task = cleaningTaskRepo.findTaskById(taskId);
        scanDataset(taskId, task.getSrcDatasetId(), succeedSet);
        cleaningResultRepo.deleteByInstanceId(taskId, "FAILED");
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
        PagingQuery pageRequest = new PagingQuery(pageNumber, pageSize);
        PagedResponse<DatasetFile> datasetFiles;
        do {
            datasetFiles = datasetFileService.getDatasetFiles(srcDatasetId, null, null,null, pageRequest);
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

    private void scanDataset(String taskId, String srcDatasetId, Set<String> succeedFiles) {
        int pageNumber = 0;
        int pageSize = 500;
        PagingQuery pageRequest = new PagingQuery(pageNumber, pageSize);
        PagedResponse<DatasetFile> datasetFiles;
        do {
            datasetFiles = datasetFileService.getDatasetFiles(srcDatasetId, null, null,null, pageRequest);
            if (datasetFiles.getContent().isEmpty()) {
                break;
            }
            List<Map<String, Object>> files = datasetFiles.getContent().stream()
                    .filter(content -> !succeedFiles.contains(content.getId()))
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
                String jsonString = objectMapper.writeValueAsString(mapList.getFirst());
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

    public List<OperatorInstanceDto> getInstanceByTemplateId(String templateId) {
        return operatorInstanceRepo.findInstanceByInstanceId(templateId);
    }
}
