package com.datamate.cleaning.domain.repository;


import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.datamate.cleaning.domain.model.entity.CleaningResult;
import com.datamate.cleaning.interfaces.dto.CleaningResultDto;

import java.util.List;

public interface CleaningResultRepository extends IRepository<CleaningResult> {
    void deleteByInstanceId(String instanceId);

    int[] countByInstanceId(String instanceId);

    List<CleaningResultDto> findByInstanceId(String instanceId);
}
