package com.dataengine.cleaning.application.service;


import com.dataengine.cleaning.domain.model.TemplateWithInstance;
import com.dataengine.cleaning.infrastructure.persistence.mapper.CleaningTemplateMapper;
import com.dataengine.cleaning.interfaces.dto.CleaningTemplate;
import com.dataengine.cleaning.interfaces.dto.CreateCleaningTemplateRequest;
import com.dataengine.cleaning.interfaces.dto.OperatorResponse;
import com.dataengine.cleaning.interfaces.dto.UpdateCleaningTemplateRequest;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

@Service
public class CleaningTemplateService {

    @Autowired
    private CleaningTemplateMapper cleaningTemplateMapper;

    public List<CleaningTemplate> getTemplates() {
        List<OperatorResponse> allOperators = cleaningTemplateMapper.findAllOperators();
        Map<String, OperatorResponse> operatorsMap = allOperators.stream()
                .collect(Collectors.toMap(OperatorResponse::getId, Function.identity()));

        List<TemplateWithInstance> allTemplates = cleaningTemplateMapper.findAllTemplates();
        Map<String, List<TemplateWithInstance>> templatesMap = allTemplates.stream()
                .collect(Collectors.groupingBy(TemplateWithInstance::getId));
        return templatesMap.entrySet().stream().map(twi -> {
            List<TemplateWithInstance> value = twi.getValue();
            CleaningTemplate template = new CleaningTemplate();
            template.setId(twi.getKey());
            template.setName(value.get(0).getName());
            template.setDescription(value.get(0).getDescription());
            template.setInstance(value.stream().filter(v -> StringUtils.isNotBlank(v.getOperatorId()))
                    .sorted(Comparator.comparingInt(TemplateWithInstance::getOpIndex))
                    .map(v -> {
                        OperatorResponse operator = operatorsMap.get(v.getOperatorId());
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
    public CleaningTemplate createTemplate(CreateCleaningTemplateRequest request) {
        CleaningTemplate template = new CleaningTemplate();
        template.setName(request.getName());
        template.setDescription(request.getDescription());
        cleaningTemplateMapper.insertTemplate(template);
        return template;
    }

    public CleaningTemplate getTemplate(String templateId) {
        return cleaningTemplateMapper.findTemplateById(templateId);
    }

    @Transactional
    public CleaningTemplate updateTemplate(String templateId, UpdateCleaningTemplateRequest request) {
        CleaningTemplate template = cleaningTemplateMapper.findTemplateById(templateId);
        if (template != null) {
            template.setName(request.getName());
            template.setDescription(request.getDescription());
            cleaningTemplateMapper.updateTemplate(template);
        }
        return template;
    }

    @Transactional
    public void deleteTemplate(String templateId) {
        cleaningTemplateMapper.deleteTemplate(templateId);
    }
}
