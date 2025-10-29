package com.datamate.cleaning.infrastructure.persistence.Impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.datamate.cleaning.domain.model.entity.CleaningResult;
import com.datamate.cleaning.domain.repository.CleaningResultRepository;
import com.datamate.cleaning.infrastructure.persistence.mapper.CleaningResultMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class CleaningResultRepositoryImpl extends CrudRepository<CleaningResultMapper, CleaningResult>
    implements CleaningResultRepository {
    private final CleaningResultMapper mapper;

    @Override
    public void deleteByInstanceId(String instanceId) {
        LambdaQueryWrapper<CleaningResult> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(CleaningResult::getInstanceId, instanceId);
        mapper.delete(queryWrapper);
    }

    @Override
    public int countByInstanceId(String instanceId) {
        LambdaQueryWrapper<CleaningResult> lambdaWrapper = new LambdaQueryWrapper<>();
        lambdaWrapper.eq(CleaningResult::getInstanceId, instanceId);
        return mapper.selectCount(lambdaWrapper).intValue();
    }
}
