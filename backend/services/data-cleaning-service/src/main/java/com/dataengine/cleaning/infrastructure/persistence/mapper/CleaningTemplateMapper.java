package com.dataengine.cleaning.infrastructure.persistence.mapper;

import com.dataengine.cleaning.domain.model.TemplateWithInstance;
import com.dataengine.cleaning.interfaces.dto.CleaningTemplate;
import com.dataengine.cleaning.interfaces.dto.OperatorResponse;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface CleaningTemplateMapper {

    List<TemplateWithInstance> findAllTemplates();

    List<OperatorResponse> findAllOperators();

    CleaningTemplate findTemplateById(@Param("templateId") String templateId);

    void insertTemplate(CleaningTemplate template);

    void updateTemplate(CleaningTemplate template);

    void deleteTemplate(@Param("templateId") String templateId);
}
