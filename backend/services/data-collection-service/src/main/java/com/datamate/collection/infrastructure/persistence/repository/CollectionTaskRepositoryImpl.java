package com.datamate.collection.infrastructure.persistence.repository;

import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.datamate.collection.domain.model.entity.CollectionTask;
import com.datamate.collection.domain.repository.CollectionTaskRepository;
import com.datamate.collection.infrastructure.persistence.mapper.CollectionTaskMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * CollectionTaskRepositoryImpl
 *
 * @since 2025/10/23
 */
@Repository
@RequiredArgsConstructor
public class CollectionTaskRepositoryImpl extends CrudRepository<CollectionTaskMapper, CollectionTask> implements CollectionTaskRepository {
    private final CollectionTaskMapper collectionTaskMapper;

    @Override
    public List<CollectionTask> selectActiveTasks() {
        return collectionTaskMapper.selectActiveTasks();
    }

    @Override
    public void updateStatus(String id, String status) {
        collectionTaskMapper.updateStatus(id, status);
    }

    @Override
    public void updateLastExecution(String id, String lastExecutionId) {
        collectionTaskMapper.updateLastExecution(id, lastExecutionId);
    }
}
