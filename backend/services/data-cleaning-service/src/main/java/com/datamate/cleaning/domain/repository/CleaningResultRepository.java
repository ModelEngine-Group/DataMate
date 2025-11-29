package com.datamate.cleaning.domain.repository;


import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.datamate.cleaning.domain.model.entity.CleaningResult;
import com.datamate.cleaning.interfaces.dto.CleaningResultDto;

import java.util.List;

public interface CleaningResultRepository extends IRepository<CleaningResult> {
    void deleteByInstanceId(String instanceId);

    void deleteByInstanceId(String instanceId, String status);

    int[] countByInstanceId(String instanceId);

    List<CleaningResultDto> findByInstanceId(String instanceId);

    List<CleaningResultDto> findByInstanceId(String instanceId, String status);
}
