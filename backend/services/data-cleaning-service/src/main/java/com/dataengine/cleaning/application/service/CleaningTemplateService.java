package com.dataengine.cleaning.application.service;


import com.dataengine.cleaning.infrastructure.persistence.mapper.CleaningTemplateMapper;
import com.dataengine.cleaning.interfaces.dto.CleaningTemplate;
import com.dataengine.cleaning.interfaces.dto.CreateCleaningTemplateRequest;
import com.dataengine.cleaning.interfaces.dto.UpdateCleaningTemplateRequest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.List;

@Service
public class CleaningTemplateService {

    @Autowired
    private CleaningTemplateMapper cleaningTemplateMapper;

    public List<CleaningTemplate> getTemplates() {
        return cleaningTemplateMapper.findAllTemplates();
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
