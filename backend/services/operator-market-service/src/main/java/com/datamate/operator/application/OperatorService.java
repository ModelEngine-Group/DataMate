package com.datamate.operator.application;

import com.datamate.common.domain.model.ChunkUploadPreRequest;
import com.datamate.common.domain.service.FileService;
import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import com.datamate.operator.domain.contants.OperatorConstant;
import com.datamate.operator.domain.repository.OperatorReleaseRepository;
import com.datamate.operator.infrastructure.converter.OperatorConverter;
import com.datamate.operator.domain.model.OperatorView;
import com.datamate.operator.domain.repository.CategoryRelationRepository;
import com.datamate.operator.domain.repository.OperatorRepository;
import com.datamate.operator.domain.repository.OperatorViewRepository;
import com.datamate.operator.infrastructure.exception.OperatorErrorCode;
import com.datamate.operator.infrastructure.parser.ParserHolder;
import com.datamate.operator.interfaces.dto.OperatorDto;
import com.datamate.operator.interfaces.dto.OperatorReleaseDto;
import com.datamate.operator.interfaces.dto.UploadOperatorRequest;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.collections4.CollectionUtils;
import org.apache.commons.collections4.MapUtils;
import org.apache.commons.io.FileUtils;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;
import java.util.stream.Stream;

@Service
@Slf4j
@RequiredArgsConstructor
public class OperatorService {
    private final OperatorRepository operatorRepo;

    private final OperatorViewRepository operatorViewRepo;

    private final CategoryRelationRepository relationRepo;

    private final OperatorReleaseRepository operatorReleaseRepo;

    private final ParserHolder parserHolder;

    private final FileService fileService;

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${operator.base.path:/operators}")
    private String operatorBasePath;

    public List<OperatorDto> getOperators(Integer page, Integer size, List<List<String>> categories,
                                          String keyword, Boolean isStar) {
        return operatorViewRepo.findOperatorsByCriteria(page, size, keyword, categories, isStar);
    }

    public int getOperatorsCount(List<List<String>> categories, String keyword, Boolean isStar) {
        return operatorViewRepo.countOperatorsByCriteria(keyword, categories, isStar);
    }

    public OperatorDto getOperatorById(String id) {
        OperatorView operator = operatorViewRepo.findOperatorById(id);
        OperatorDto operatorDto = OperatorConverter.INSTANCE.fromEntityToDto(operator);
        if (StringUtils.isNotBlank(operatorDto.getFileName())) {
            String filePath = getExtractPath(getStem(operatorDto.getFileName()));
            String requirements = filePath + "/requirements.txt";
            operatorDto.setRequirements(readRequirements(requirements));
            operatorDto.setReadme(getReadmeContent(filePath));
        }
        operatorDto.setFileName(null);
        operatorDto.setReleases(operatorReleaseRepo.findAllByOperatorId(id));
        return operatorDto;
    }

    @Transactional
    public OperatorDto createOperator(OperatorDto req) {
        overrideSettings(req);
        operatorRepo.insertOperator(req);
        relationRepo.batchInsert(req.getId(), req.getCategories());
        if (CollectionUtils.isNotEmpty(req.getReleases())) {
            OperatorReleaseDto release = req.getReleases().getFirst();
            release.setId(req.getId());
            release.setVersion(req.getVersion());
            release.setReleaseDate(LocalDateTime.now());
            operatorReleaseRepo.insertOperatorRelease(release);
        }
        parserHolder.extractTo(getFileType(req.getFileName()), getUploadPath(req.getFileName()),
                getExtractPath(getStem(req.getFileName())));
        return getOperatorById(req.getId());
    }

    @Transactional
    public OperatorDto updateOperator(String id, OperatorDto req) {
        OperatorDto operator = getOperatorById(id);
        overrideSettings(req);
        operatorRepo.updateOperator(req);
        if (StringUtils.isNotBlank(req.getFileName()) && CollectionUtils.isNotEmpty(req.getCategories())) {
            relationRepo.batchUpdate(id, req.getCategories());
        }
        if (CollectionUtils.isNotEmpty(req.getReleases())) {
            OperatorReleaseDto release = req.getReleases().getFirst();
            release.setId(req.getId());
            release.setVersion(req.getVersion());
            release.setReleaseDate(LocalDateTime.now());
            if (StringUtils.equals(operator.getVersion(), req.getVersion())) {
                operatorReleaseRepo.updateOperatorRelease(release);
            } else {
                operatorReleaseRepo.insertOperatorRelease(release);
            }
        }
        if (StringUtils.isNotBlank(req.getFileName())) {
            parserHolder.extractTo(getFileType(req.getFileName()), getUploadPath(req.getFileName()),
                    getExtractPath(getStem(req.getFileName())));
        }
        return getOperatorById(id);
    }

    @Transactional
    public void deleteOperator(String id) {
        if (operatorRepo.operatorInTemplateOrRunning(id)) {
            throw BusinessException.of(OperatorErrorCode.OPERATOR_IN_INSTANCE);
        }
        if (relationRepo.operatorIsPredefined(id)) {
            throw BusinessException.of(OperatorErrorCode.CANT_DELETE_PREDEFINED_OPERATOR);
        }
        OperatorView operator = operatorViewRepo.findOperatorById(id);
        operatorRepo.deleteOperator(id);
        relationRepo.deleteByOperatorId(id);
        operatorReleaseRepo.deleteOperatorRelease(id);
        FileUtils.deleteQuietly(new File(getExtractPath(getStem(operator.getFileName()))));
    }

    public OperatorDto uploadOperator(String fileName) {
        return parserHolder.parseYamlFromArchive(getFileType(fileName), new File(getUploadPath(fileName)),
                OperatorConstant.YAML_PATH);
    }

    public String preUpload() {
        ChunkUploadPreRequest request = ChunkUploadPreRequest.builder().build();
        request.setUploadPath(operatorBasePath + File.separator + "upload");
        request.setTotalFileNum(1);
        request.setServiceId(OperatorConstant.SERVICE_ID);
        return fileService.preUpload(request);
    }

    public void chunkUpload(UploadOperatorRequest request) {
        fileService.chunkUpload(OperatorConverter.INSTANCE.toChunkRequest(request));
    }

    private String getFileType(String fileName) {
        return fileName.substring(fileName.lastIndexOf('.') + 1);
    }

    private String getStem(String fileName) {
        return fileName.substring(0, fileName.lastIndexOf('.'));
    }

    private String getUploadPath(String fileName) {
        return operatorBasePath + File.separator + "upload" + File.separator + fileName;
    }

    private String getExtractPath(String fileName) {
        return operatorBasePath + File.separator + "extract" + File.separator + fileName;
    }

    public void overrideSettings(OperatorDto operatorDto) {
        if (StringUtils.isBlank(operatorDto.getSettings()) || MapUtils.isEmpty(operatorDto.getOverrides())) {
            return;
        }
        try {
            Map<String, Map<String, Object>> settings = objectMapper.readValue(operatorDto.getSettings(), Map.class);
            for (Map.Entry<String, Object> entry : operatorDto.getOverrides().entrySet()) {
                String key = entry.getKey();
                if (!settings.containsKey(key)) {
                    continue;
                }
                Object value = entry.getValue();
                Map<String, Object> setting = settings.get(key);
                String type = setting.get("type").toString();
                switch (type) {
                    case "slider":
                    case "switch":
                    case "select":
                    case "input":
                    case "radio":
                        setting.put("defaultVal", value);
                        break;
                    case "checkbox":
                        setting.put("defaultVal", convertObjectToListString(value));
                        break;
                    case "range":
                        updateProperties(setting, value);
                    default:
                }
                settings.put(key, setting);
            }
            operatorDto.setSettings(objectMapper.writeValueAsString(settings));
        } catch (JsonProcessingException e) {
            throw BusinessException.of(OperatorErrorCode.SETTINGS_PARSE_FAILED, e.getMessage());
        }
    }

    public Resource downloadExampleOperator(File file) {
        try {
            Resource resource = new UrlResource(file.toURI());
            if (resource.exists()) {
                return resource;
            } else {
                throw BusinessException.of(SystemErrorCode.RESOURCE_NOT_FOUND);
            }
        } catch (MalformedURLException ex) {
            log.error("File not found: {}", file.getName(), ex);
            throw BusinessException.of(SystemErrorCode.RESOURCE_NOT_FOUND);
        }
    }

    private String convertObjectToListString(Object object) {
        if (object == null) {
            return null;
        } else if (object instanceof List<?> list) {
            List<String> result = new ArrayList<>();
            for (Object item : list) {
                result.add(String.valueOf(item));
            }
            return String.join(",", result);
        } else {
            return object.toString();
        }
    }

    private void updateProperties(Map<String, Object> setting, Object value) {
        List<Object> defaultValue = new ArrayList<>();
        if (value instanceof List) {
            defaultValue.addAll((List<?>) value);
        }

        Object properties = setting.get("properties");
        if (properties instanceof List<?> list) {
            if (defaultValue.size() != list.size()) {
                return;
            }
            List<Map<String, Object>> result = new ArrayList<>();
            for (int i = 0; i < list.size(); i++) {
                Map<String, Object> map = objectMapper.convertValue(list.get(i), Map.class);
                map.put("defaultVal", defaultValue.get(i));
                result.add(map);
            }
            setting.put("properties", result);
        }
    }

    private List<String> readRequirements(String filePath) {
        Path path = Paths.get(filePath);
        if (!Files.exists(path) || !Files.isRegularFile(path)) {
            log.warn("requirements文件不存在或路径错误: {}", filePath);
            return Collections.emptyList();
        }

        List<String> requirements = new ArrayList<>();
        try (Stream<String> lines = Files.lines(path)) {
            requirements = lines.map(String::trim)
                    .filter(line -> !line.isEmpty())
                    .filter(line -> !line.startsWith("#"))
                    .collect(Collectors.toList());
        } catch (IOException e) {
            log.warn("读取requirements文件异常: {}", e.getMessage());
        }
        return requirements;
    }

    private String getReadmeContent(String directoryPath) {
        Path dir = Paths.get(directoryPath);
        if (!Files.exists(dir) || !Files.isDirectory(dir)) {
            System.err.println("目录不存在: " + directoryPath);
            return null;
        }
        List<String> candidateNames = Arrays.asList("README.md", "readme.md", "Readme.md");
        for (String fileName : candidateNames) {
            Path filePath = dir.resolve(fileName);
            if (Files.exists(filePath) && Files.isRegularFile(filePath)) {
                try {
                    byte[] bytes = Files.readAllBytes(filePath);
                    return new String(bytes, StandardCharsets.UTF_8);
                } catch (IOException e) {
                    log.warn("找到文件但读取失败: {}, 错误: {}", filePath, e.getMessage());
                }
            }
        }
        return "";
    }
}
