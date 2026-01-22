package com.datamate.operator.infrastructure.persistence.Impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.datamate.operator.infrastructure.converter.OperatorConverter;
import com.datamate.operator.domain.model.Operator;
import com.datamate.operator.domain.repository.OperatorRepository;
import com.datamate.operator.infrastructure.persistence.mapper.OperatorMapper;
import com.datamate.operator.interfaces.dto.OperatorDto;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.Collections;
import java.util.List;

@Repository
@RequiredArgsConstructor
public class OperatorRepositoryImpl extends CrudRepository<OperatorMapper, Operator> implements OperatorRepository {
    private final OperatorMapper mapper;

    @Override
    public List<OperatorDto> findAllOperators() {
        return OperatorConverter.INSTANCE.fromEntityToDto(mapper.selectList(null));
    }

    @Override
    public void updateOperator(OperatorDto operator) {
        mapper.updateById(OperatorConverter.INSTANCE.fromDtoToEntity(operator));
    }

    @Override
    public void insertOperator(OperatorDto operator) {
        mapper.insert(OperatorConverter.INSTANCE.fromDtoToEntity(operator));
    }

    @Override
    public void deleteOperator(String id) {
        mapper.deleteById(id);
    }

    @Override
    public int countOperatorByStar(boolean isStar) {
        LambdaQueryWrapper<Operator> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(Operator::getIsStar, isStar);
        return Math.toIntExact(mapper.selectCount(queryWrapper));
    }

    @Override
    public boolean operatorInTemplateOrRunning(String operatorId) {
        return mapper.operatorInTemplate(operatorId) > 0 && mapper.operatorInUnstopTask(operatorId) > 0;
    }

    @Override
    public void incrementUsageCount(List<String> operatorIds) {
        if (operatorIds == null || operatorIds.isEmpty()) {
            return;
        }
        Collections.sort(operatorIds);
        LambdaUpdateWrapper<Operator> updateWrapper = new LambdaUpdateWrapper<>();
        updateWrapper.in(Operator::getId, operatorIds)
                .setSql("usage_count = usage_count + 1");
        this.update(updateWrapper);
    }
}
