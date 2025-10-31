package com.datamate.cleaning.application;


import com.datamate.cleaning.domain.repository.CleaningTemplateRepository;
import com.datamate.cleaning.domain.repository.OperatorInstanceRepository;
import com.datamate.cleaning.interfaces.dto.*;
import com.datamate.cleaning.domain.model.entity.TemplateWithInstance;
import com.datamate.operator.domain.repository.OperatorRepository;
import com.datamate.operator.interfaces.dto.OperatorDto;
import lombok.RequiredArgsConstructor;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class CleaningTemplateService {
    private final CleaningTemplateRepository cleaningTemplateRepo;

    private final OperatorInstanceRepository operatorInstanceRepo;

    private final OperatorRepository operatorRepo;

    public List<CleaningTemplateDto> getTemplates(String keywords) {
        List<OperatorDto> allOperators = operatorRepo.findAllOperators();
        Map<String, OperatorDto> operatorsMap = allOperators.stream()
                .collect(Collectors.toMap(OperatorDto::getId, Function.identity()));
        List<TemplateWithInstance> allTemplates = cleaningTemplateRepo.findAllTemplates(keywords);
        Map<String, List<TemplateWithInstance>> templatesMap = allTemplates.stream()
                .collect(Collectors.groupingBy(TemplateWithInstance::getId));
        return templatesMap.entrySet().stream().map(twi -> {
            List<TemplateWithInstance> value = twi.getValue();
            CleaningTemplateDto template = new CleaningTemplateDto();
            template.setId(twi.getKey());
            template.setName(value.get(0).getName());
            template.setDescription(value.get(0).getDescription());
            template.setInstance(value.stream().filter(v -> StringUtils.isNotBlank(v.getOperatorId()))
                    .sorted(Comparator.comparingInt(TemplateWithInstance::getOpIndex))
                    .map(v -> {
                        OperatorDto operator = operatorsMap.get(v.getOperatorId());
                        if (StringUtils.isNotBlank(v.getSettingsOverride())) {
                            operator.setSettings(v.getSettingsOverride());
                        }
                        return operator;
                    }).toList());
            template.setCreatedAt(value.get(0).getCreatedAt());
            template.setUpdatedAt(value.get(0).getUpdatedAt());
            return template;
        }).toList();
    }

    @Transactional
    public CleaningTemplateDto createTemplate(CreateCleaningTemplateRequest request) {
        CleaningTemplateDto template = new CleaningTemplateDto();
        String templateId = UUID.randomUUID().toString();
        template.setId(templateId);
        template.setName(request.getName());
        template.setDescription(request.getDescription());
        cleaningTemplateRepo.insertTemplate(template);

        operatorInstanceRepo.insertInstance(templateId, request.getInstance());
        return template;
    }

    public CleaningTemplateDto getTemplate(String templateId) {
        return cleaningTemplateRepo.findTemplateById(templateId);
    }

    @Transactional
    public CleaningTemplateDto updateTemplate(String templateId, UpdateCleaningTemplateRequest request) {
        CleaningTemplateDto template = cleaningTemplateRepo.findTemplateById(templateId);
        if (template != null) {
            template.setName(request.getName());
            template.setDescription(request.getDescription());
            cleaningTemplateRepo.updateTemplate(template);
        }
        return template;
    }

    @Transactional
    public void deleteTemplate(String templateId) {
        cleaningTemplateRepo.deleteTemplate(templateId);
        operatorInstanceRepo.deleteByInstanceId(templateId);
    }
}
