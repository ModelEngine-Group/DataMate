package com.datamate.cleaning.domain.repository;


import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.datamate.cleaning.domain.model.entity.CleaningResult;

public interface CleaningResultRepository extends IRepository<CleaningResult> {
    void deleteByInstanceId(String instanceId);

    int countByInstanceId(String instanceId);
}
