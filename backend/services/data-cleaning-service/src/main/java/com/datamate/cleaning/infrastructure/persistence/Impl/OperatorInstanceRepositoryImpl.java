package com.datamate.cleaning.infrastructure.persistence.Impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.datamate.cleaning.infrastructure.converter.OperatorInstanceConverter;
import com.datamate.cleaning.interfaces.dto.OperatorInstanceDto;
import com.datamate.cleaning.domain.model.entity.OperatorInstance;
import com.datamate.cleaning.domain.repository.OperatorInstanceRepository;
import com.datamate.cleaning.infrastructure.persistence.mapper.OperatorInstanceMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.List;

@Repository
@RequiredArgsConstructor
public class OperatorInstanceRepositoryImpl extends CrudRepository<OperatorInstanceMapper, OperatorInstance>
    implements OperatorInstanceRepository {
    private final OperatorInstanceMapper mapper;

    @Override
    public void insertInstance(String instanceId, List<OperatorInstanceDto> instances) {
        List<OperatorInstance> operatorInstances = new ArrayList<>();
        for (int i = 0; i < instances.size(); i++) {
            OperatorInstance operatorInstance = OperatorInstanceConverter.INSTANCE.fromDtoToEntity(instances.get(i));
            operatorInstance.setInstanceId(instanceId);
            operatorInstance.setOpIndex(i + 1);
            operatorInstances.add(operatorInstance);
        }
        mapper.insert(operatorInstances);
    }

    @Override
    public void deleteByInstanceId(String instanceId) {
        LambdaQueryWrapper<OperatorInstance> lambdaWrapper = new LambdaQueryWrapper<>();
        lambdaWrapper.eq(OperatorInstance::getInstanceId, instanceId);
        mapper.delete(lambdaWrapper);
    }
}
