package com.dataengine.cleaning.infrastructure.persistence.mapper;

import com.dataengine.cleaning.interfaces.dto.CleaningTemplate;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface CleaningTemplateMapper {

    List<CleaningTemplate> findAllTemplates();

    CleaningTemplate findTemplateById(@Param("templateId") String templateId);

    void insertTemplate(CleaningTemplate template);

    void updateTemplate(CleaningTemplate template);

    void deleteTemplate(@Param("templateId") String templateId);
}
