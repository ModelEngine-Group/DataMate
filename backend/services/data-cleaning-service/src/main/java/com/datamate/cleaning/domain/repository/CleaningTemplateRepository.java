package com.datamate.cleaning.domain.repository;

import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.datamate.cleaning.domain.model.entity.TemplateWithInstance;
import com.datamate.cleaning.domain.model.entity.CleaningTemplate;
import com.datamate.cleaning.interfaces.dto.CleaningTemplateDto;

import java.util.List;

public interface CleaningTemplateRepository extends IRepository<CleaningTemplate> {
    List<TemplateWithInstance> findAllTemplates(String keywords);

    CleaningTemplateDto findTemplateById(String templateId);

    void insertTemplate(CleaningTemplateDto template);

    void updateTemplate(CleaningTemplateDto template);

    void deleteTemplate(String templateId);
}
