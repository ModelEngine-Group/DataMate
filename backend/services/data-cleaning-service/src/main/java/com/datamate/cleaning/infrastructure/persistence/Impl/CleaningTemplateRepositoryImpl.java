package com.datamate.cleaning.infrastructure.persistence.Impl;


import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.datamate.cleaning.domain.model.entity.TemplateWithInstance;
import com.datamate.cleaning.domain.model.entity.CleaningTemplate;
import com.datamate.cleaning.domain.repository.CleaningTemplateRepository;
import com.datamate.cleaning.infrastructure.converter.CleaningTemplateConverter;
import com.datamate.cleaning.infrastructure.persistence.mapper.CleaningTemplateMapper;
import com.datamate.cleaning.interfaces.dto.CleaningTemplateDto;
import lombok.RequiredArgsConstructor;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Repository;

import java.util.List;


@Repository
@RequiredArgsConstructor
public class CleaningTemplateRepositoryImpl extends CrudRepository<CleaningTemplateMapper, CleaningTemplate>
    implements CleaningTemplateRepository {
    private final CleaningTemplateMapper mapper;

    @Override
    public List<TemplateWithInstance> findAllTemplates(String keywords) {
        QueryWrapper<TemplateWithInstance> queryWrapper = new QueryWrapper<>();
        if (StringUtils.isNotBlank(keywords)) {
            queryWrapper.like("name", keywords)
                    .or()
                    .like("description", keywords);
        }
        queryWrapper.orderByDesc("created_at");
        return mapper.findAllTemplates(queryWrapper);
    }

    @Override
    public CleaningTemplateDto findTemplateById(String templateId) {
        return CleaningTemplateConverter.INSTANCE.fromEntityToDto(mapper.selectById(templateId));
    }

    @Override
    public void insertTemplate(CleaningTemplateDto template) {
        mapper.insert(CleaningTemplateConverter.INSTANCE.fromDtoToEntity(template));
    }

    @Override
    public void updateTemplate(CleaningTemplateDto template) {
        mapper.updateById(CleaningTemplateConverter.INSTANCE.fromDtoToEntity(template));
    }

    @Override
    public void deleteTemplate(String templateId) {
        mapper.deleteById(templateId);
    }
}
