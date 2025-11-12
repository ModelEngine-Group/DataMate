package com.datamate.operator.infrastructure.persistence.Impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.datamate.operator.infrastructure.converter.OperatorConverter;
import com.datamate.operator.domain.model.Operator;
import com.datamate.operator.domain.repository.OperatorRepository;
import com.datamate.operator.infrastructure.persistence.mapper.OperatorMapper;
import com.datamate.operator.interfaces.dto.OperatorDto;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

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
}
