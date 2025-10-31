package com.datamate.cleaning.domain.repository;

import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.datamate.cleaning.domain.model.entity.CleaningTask;
import com.datamate.cleaning.interfaces.dto.CleaningTaskDto;

import java.util.List;

public interface CleaningTaskRepository extends IRepository<CleaningTask> {
    List<CleaningTaskDto> findTasks(String status, String keywords, Integer page, Integer size);

    CleaningTaskDto findTaskById(String taskId);

    void insertTask(CleaningTaskDto task);

    void updateTask(CleaningTaskDto task);

    void deleteTaskById(String taskId);

    boolean isNameExist(String name);
}
