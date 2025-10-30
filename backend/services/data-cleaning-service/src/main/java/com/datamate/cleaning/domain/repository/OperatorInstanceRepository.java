package com.datamate.cleaning.domain.repository;

import com.baomidou.mybatisplus.extension.repository.IRepository;
import com.datamate.cleaning.interfaces.dto.OperatorInstanceDto;
import com.datamate.cleaning.domain.model.entity.OperatorInstance;

import java.util.List;

public interface OperatorInstanceRepository extends IRepository<OperatorInstance> {
    void insertInstance(String instanceId, List<OperatorInstanceDto> instances);

    void deleteByInstanceId(String instanceId);
}
