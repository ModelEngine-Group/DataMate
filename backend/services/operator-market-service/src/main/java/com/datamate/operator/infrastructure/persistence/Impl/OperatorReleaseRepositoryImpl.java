package com.datamate.operator.infrastructure.persistence.Impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.datamate.operator.domain.model.OperatorRelease;
import com.datamate.operator.domain.repository.OperatorReleaseRepository;
import com.datamate.operator.infrastructure.converter.OperatorReleaseConverter;

import com.datamate.operator.infrastructure.persistence.mapper.OperatorReleaseMapper;
import com.datamate.operator.interfaces.dto.OperatorReleaseDto;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
@RequiredArgsConstructor
public class OperatorReleaseRepositoryImpl extends CrudRepository<OperatorReleaseMapper, OperatorRelease> implements OperatorReleaseRepository {
    private final OperatorReleaseMapper mapper;

    public List<OperatorReleaseDto> findAllByOperatorId(String operatorId) {
        QueryWrapper<OperatorRelease> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("id", operatorId)
                .orderByDesc("release_date");
        return OperatorReleaseConverter.INSTANCE.fromEntityToDto(mapper.selectList(queryWrapper));
    }

    @Override
    public void insertOperatorRelease(OperatorReleaseDto operatorReleaseDto) {
        mapper.insert(OperatorReleaseConverter.INSTANCE.fromDtoToEntity(operatorReleaseDto));
    }

    @Override
    public void updateOperatorRelease(OperatorReleaseDto operatorReleaseDto) {
        QueryWrapper<OperatorRelease> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("id", operatorReleaseDto.getId())
                .eq("version", operatorReleaseDto.getVersion());
        mapper.update(OperatorReleaseConverter.INSTANCE.fromDtoToEntity(operatorReleaseDto), queryWrapper);
    }

    @Override
    public void deleteOperatorRelease(String operatorId) {
        mapper.delete(new QueryWrapper<OperatorRelease>().eq("id", operatorId));
    }

}
