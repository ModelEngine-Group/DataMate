package com.datamate.cleaning.infrastructure.persistence.Impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.datamate.cleaning.domain.model.entity.CleaningTask;
import com.datamate.cleaning.domain.repository.CleaningTaskRepository;
import com.datamate.cleaning.infrastructure.converter.CleaningTaskConverter;
import com.datamate.cleaning.infrastructure.persistence.mapper.CleaningTaskMapper;
import com.datamate.cleaning.interfaces.dto.CleaningTaskDto;
import lombok.RequiredArgsConstructor;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Repository;

import java.util.List;


@Repository
@RequiredArgsConstructor
public class CleaningTaskRepositoryImpl extends CrudRepository<CleaningTaskMapper, CleaningTask>
    implements CleaningTaskRepository {
    private final CleaningTaskMapper mapper;

    public List<CleaningTaskDto> findTasks(String status, String keywords, Integer page, Integer size) {
        LambdaQueryWrapper<CleaningTask> lambdaWrapper = new LambdaQueryWrapper<>();
        lambdaWrapper.eq(StringUtils.isNotBlank(status), CleaningTask::getStatus, status)
            .like(StringUtils.isNotBlank(keywords), CleaningTask::getName, keywords)
            .orderByDesc(CleaningTask::getCreatedAt);
        if (size != null && page != null) {
            Page<CleaningTask> queryPage = new Page<>(page + 1, size);
            IPage<CleaningTask> resultPage = mapper.selectPage(queryPage, lambdaWrapper);
            return CleaningTaskConverter.INSTANCE.fromEntityToDto(resultPage.getRecords());
        } else {
            return CleaningTaskConverter.INSTANCE.fromEntityToDto(mapper.selectList(lambdaWrapper));
        }
    }

    public CleaningTaskDto findTaskById(String taskId) {
        return CleaningTaskConverter.INSTANCE.fromEntityToDto(mapper.selectById(taskId));
    }

    public void insertTask(CleaningTaskDto task) {
        mapper.insert(CleaningTaskConverter.INSTANCE.fromDtoToEntity(task));
    }

    public void updateTask(CleaningTaskDto task) {
        mapper.updateById(CleaningTaskConverter.INSTANCE.fromDtoToEntity(task));
    }

    public void deleteTaskById(String taskId) {
        mapper.deleteById(taskId);
    }
}
