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
import com.datamate.operator.domain.repository.OperatorRepository;
import com.datamate.operator.infrastructure.exception.OperatorErrorCode;
import com.datamate.operator.interfaces.dto.OperatorDto;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.collections4.CollectionUtils;
import org.apache.commons.io.FileUtils;
import org.apache.commons.lang3.StringUtils;
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
import java.util.function.Function;
import java.util.function.Predicate;
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

    private final OperatorRepository operatorRepo;

    private final CleaningResultRepository cleaningResultRepo;

    private final CleaningTaskScheduler taskScheduler;

    private final DatasetApplicationService datasetService;

    private final DatasetFileApplicationService datasetFileService;

    private final CleanTaskValidator cleanTaskValidator;

    private final String DATASET_PATH = "/dataset";

    private final String FLOW_PATH = "/flow";

    private static final Pattern STANDARD_LEVEL_PATTERN = Pattern.compile(
            "\\b(DEBUG|Debug|INFO|Info|WARN|Warn|WARNING|Warning|ERROR|Error|FATAL|Fatal)\\b"
    );

    private static final Pattern EXCEPTION_SUFFIX_PATTERN = Pattern.compile(
            "\\b\\w+(Warning|Error|Exception)\\b"
    );

    private final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

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

        ExecutorType executorType = cleanTaskValidator.checkAndGetExecutorType(request.getInstance());

        Dataset destDataset;
        if (StringUtils.isNotBlank(request.getDestDatasetId())) {
            destDataset = datasetService.getDataset(request.getDestDatasetId());
        } else {
            CreateDatasetRequest createDatasetRequest = new CreateDatasetRequest();
            createDatasetRequest.setName(request.getDestDatasetName());
            createDatasetRequest.setDatasetType(DatasetType.valueOf(request.getDestDatasetType()));
            createDatasetRequest.setStatus("ACTIVE");
            destDataset = datasetService.createDataset(createDatasetRequest);
        }
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

        prepareTask(task, request.getInstance(), executorType);
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
        cleanTaskValidator.checkTaskId(taskId);
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

        Matcher stdMatcher = STANDARD_LEVEL_PATTERN.matcher(logLine);
        if (stdMatcher.find()) {
            return stdMatcher.group(1).toUpperCase();
        }

        Matcher exMatcher = EXCEPTION_SUFFIX_PATTERN.matcher(logLine);
        if (exMatcher.find()) {
            String match = exMatcher.group(1).toUpperCase();
            if ("WARNING".equals(match)) return "WARN";
            if ("ERROR".equals(match) || "EXCEPTION".equals(match)) return "ERROR";
        }
        return defaultLevel;
    }

    @Transactional
    public void deleteTask(String taskId) {
        cleanTaskValidator.checkTaskId(taskId);
        cleaningTaskRepo.deleteTaskById(taskId);
        operatorInstanceRepo.deleteByInstanceId(taskId);
        cleaningResultRepo.deleteByInstanceId(taskId);
        try {
            FileUtils.deleteDirectory(new File(FLOW_PATH + "/" + taskId));
        } catch (IOException e) {
            log.warn("Can't delete flow path with task id: {}.", taskId, e);
        }
    }

    public void executeTask(String taskId) {
        List<CleaningResultDto> succeed = cleaningResultRepo.findByInstanceId(taskId, "COMPLETED");
        Set<String> succeedSet = succeed.stream().map(CleaningResultDto::getSrcFileId).collect(Collectors.toSet());
        CleaningTaskDto task = cleaningTaskRepo.findTaskById(taskId);
        scanDataset(taskId, task.getSrcDatasetId(), succeedSet);
        cleaningResultRepo.deleteByInstanceId(taskId, "FAILED");
        taskScheduler.executeTask(taskId);
    }

    private void prepareTask(CleaningTaskDto task, List<OperatorInstanceDto> instances, ExecutorType executorType) {
        List<OperatorDto> allOperators = operatorRepo.findAllOperators();
        Map<String, OperatorDto> operatorDtoMap = allOperators.stream()
                .collect(Collectors.toMap(OperatorDto::getId, Function.identity()));

        TaskProcess process = new TaskProcess();
        process.setInstanceId(task.getId());
        process.setDatasetId(task.getDestDatasetId());
        process.setExecutorType(executorType.getValue());
        process.setDatasetPath(FLOW_PATH + "/" + task.getId() + "/dataset.jsonl");
        process.setExportPath(DATASET_PATH + "/" + task.getDestDatasetId());
        process.setProcess(instances.stream()
                .map(instance -> {
                    OperatorDto operatorDto = operatorDtoMap.get(instance.getId());
                    Map<String, Object> stringObjectMap = getDefaultValue(operatorDto);
                    stringObjectMap.putAll(instance.getOverrides());
                    Map<String, Object> runtime = getRuntime(operatorDto);
                    stringObjectMap.putAll(runtime);
                    return Map.of(instance.getId(), stringObjectMap);
                })
                .toList());

        ObjectMapper jsonMapper = new ObjectMapper(new YAMLFactory());
        jsonMapper.setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE);
        JsonNode jsonNode = jsonMapper.valueToTree(process);

        DumperOptions options = new DumperOptions();
        options.setIndent(2);
        options.setDefaultFlowStyle(DumperOptions.FlowStyle.BLOCK);
        Yaml yaml = new Yaml(options);

        File file = new File(FLOW_PATH + "/" + task.getId() + "/process.yaml");
        file.getParentFile().mkdirs();

        try (FileWriter writer = new FileWriter(file)) {
            yaml.dump(jsonMapper.treeToValue(jsonNode, Map.class), writer);
        } catch (IOException e) {
            log.error("Failed to prepare process.yaml.", e);
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR);
        }
    }

    private Map<String, Object> getDefaultValue(OperatorDto operatorDto) {
        if (StringUtils.isBlank(operatorDto.getSettings())) {
            return new HashMap<>();
        }

        Map<String, Object> defaultSettings = new HashMap<>();
        try {
            Map<String, Map<String, Object>> settings = OBJECT_MAPPER.readValue(operatorDto.getSettings(), Map.class);
            for  (Map.Entry<String, Map<String, Object>> entry : settings.entrySet()) {
                String key = entry.getKey();
                Map<String, Object> setting = entry.getValue();
                String type = setting.get("type").toString();
                switch (type) {
                    case "slider":
                    case "switch":
                    case "select":
                    case "input":
                    case "radio":
                    case "checkbox":
                        if (setting.containsKey("defaultVal")) {
                            defaultSettings.put(key, setting.get("defaultVal"));
                        }
                        break;
                    case "range":
                        List<Object> rangeDefault = getRangeDefault(setting);
                        if (CollectionUtils.isNotEmpty(rangeDefault)) {
                            defaultSettings.put(key, rangeDefault);
                        }
                        break;
                    default:
                }
            }
            return defaultSettings;
        } catch (JsonProcessingException e) {
            throw BusinessException.of(OperatorErrorCode.SETTINGS_PARSE_FAILED, e.getMessage());
        }
    }

    private List<Object> getRangeDefault(Map<String, Object> setting) {
        List<Object> defaultValue = new ArrayList<>();
        Object properties = setting.get("properties");
        if (properties instanceof List<?> list) {
            for (Object o : list) {
                Map<String, Object> map = OBJECT_MAPPER.convertValue(o, Map.class);
                if (map.containsKey("defaultVal")) {
                    defaultValue.add(map.get("defaultVal"));
                }
            }
        }
        return defaultValue;
    }

    private Map<String, Object> getRuntime(OperatorDto operatorDto) {
        if (StringUtils.isBlank(operatorDto.getRuntime())) {
            return new HashMap<>();
        }
        try {
            return OBJECT_MAPPER.readValue(operatorDto.getRuntime(), Map.class);
        } catch (JsonProcessingException e) {
            throw BusinessException.of(OperatorErrorCode.SETTINGS_PARSE_FAILED, e.getMessage());
        }
    }

    private void scanDataset(String taskId, String srcDatasetId) {
        doScan(taskId, srcDatasetId, file -> true);
    }

    private void scanDataset(String taskId, String srcDatasetId, Set<String> succeedFiles) {
        doScan(taskId, srcDatasetId, file -> !succeedFiles.contains(file.getId()));
    }

    private void doScan(String taskId, String srcDatasetId, Predicate<DatasetFile> filterCondition) {
        cleanTaskValidator.checkTaskId(taskId);
        String targetFilePath = FLOW_PATH + "/" + taskId + "/dataset.jsonl";
        File targetFile = new File(targetFilePath);
        if (targetFile.getParentFile() != null && !targetFile.getParentFile().exists()) {
            targetFile.getParentFile().mkdirs();
        }

        int pageNumber = 0;
        int pageSize = 500;
        try (BufferedWriter writer = new BufferedWriter(new FileWriter(targetFile))) {
            PagedResponse<DatasetFile> datasetFiles;
            do {
                PagingQuery pageRequest = new PagingQuery(pageNumber, pageSize);
                datasetFiles = datasetFileService.getDatasetFiles(srcDatasetId, null, null, null, pageRequest);
                if (datasetFiles.getContent().isEmpty()) {
                    break;
                }
                for (DatasetFile content : datasetFiles.getContent()) {
                    if (!filterCondition.test(content)) {
                        continue;
                    }
                    Map<String, Object> fileMap = Map.of(
                            "fileName", content.getFileName(),
                            "fileSize", content.getFileSize(),
                            "filePath", content.getFilePath(),
                            "fileType", content.getFileType(),
                            "fileId", content.getId()
                    );
                    writer.write(OBJECT_MAPPER.writeValueAsString(fileMap));
                    writer.newLine();
                }
                pageNumber++;
            } while (pageNumber < datasetFiles.getTotalPages());
        } catch (IOException e) {
            log.error("Failed to write dataset.jsonl for taskId: {}", taskId, e);
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
