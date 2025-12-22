package com.datamate.operator.application;

import com.datamate.common.domain.model.ChunkUploadPreRequest;
import com.datamate.common.domain.service.FileService;
import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import com.datamate.operator.domain.contants.OperatorConstant;
import com.datamate.operator.infrastructure.converter.OperatorConverter;
import com.datamate.operator.domain.model.OperatorView;
import com.datamate.operator.domain.repository.CategoryRelationRepository;
import com.datamate.operator.domain.repository.OperatorRepository;
import com.datamate.operator.domain.repository.OperatorViewRepository;
import com.datamate.operator.infrastructure.exception.OperatorErrorCode;
import com.datamate.operator.infrastructure.parser.ParserHolder;
import com.datamate.operator.interfaces.dto.OperatorDto;
import com.datamate.operator.interfaces.dto.UploadOperatorRequest;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.collections4.CollectionUtils;
import org.apache.commons.collections4.MapUtils;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.File;
import java.net.MalformedURLException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Service
@Slf4j
@RequiredArgsConstructor
public class OperatorService {
    private final OperatorRepository operatorRepo;

    private final OperatorViewRepository operatorViewRepo;

    private final CategoryRelationRepository relationRepo;

    private final ParserHolder parserHolder;

    private final FileService fileService;

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${operator.base.path:/operators}")
    private String operatorBasePath;

    public List<OperatorDto> getOperators(Integer page, Integer size, List<String> categories,
                                          String keyword, Boolean isStar) {
        return operatorViewRepo.findOperatorsByCriteria(page, size, keyword, categories, isStar);
    }

    public int getOperatorsCount(List<String> categories, String keyword, Boolean isStar) {
        return operatorViewRepo.countOperatorsByCriteria(keyword, categories, isStar);
    }

    public OperatorDto getOperatorById(String id) {
        OperatorView operator = operatorViewRepo.findOperatorById(id);
        return OperatorConverter.INSTANCE.fromEntityToDto(operator);
    }

    @Transactional
    public OperatorDto createOperator(OperatorDto req) {
        overrideSettings(req);
        operatorRepo.insertOperator(req);
        relationRepo.batchInsert(req.getId(), req.getCategories());
        parserHolder.extractTo(getFileType(req.getFileName()), getUploadPath(req.getFileName()),
                getExtractPath(getFileNameWithoutExtension(req.getFileName())));
        return getOperatorById(req.getId());
    }

    @Transactional
    public OperatorDto updateOperator(String id, OperatorDto req) {
        overrideSettings(req);
        operatorRepo.updateOperator(req);
        if (CollectionUtils.isNotEmpty(req.getCategories())) {
            relationRepo.batchUpdate(id, req.getCategories());
        }
        if (StringUtils.isNotBlank(req.getFileName())) {
            parserHolder.extractTo(getFileType(req.getFileName()), getUploadPath(req.getFileName()),
                    getExtractPath(getFileNameWithoutExtension(req.getFileName())));
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
        operatorRepo.deleteOperator(id);
        relationRepo.deleteByOperatorId(id);
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

    private String getFileNameWithoutExtension(String fileName) {
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
}
