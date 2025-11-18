package com.datamate.cleaning.infrastructure.persistence.Impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.datamate.cleaning.common.enums.CleaningTaskStatusEnum;
import com.datamate.cleaning.domain.model.entity.CleaningResult;
import com.datamate.cleaning.domain.repository.CleaningResultRepository;
import com.datamate.cleaning.infrastructure.converter.CleaningResultConverter;
import com.datamate.cleaning.infrastructure.persistence.mapper.CleaningResultMapper;
import com.datamate.cleaning.interfaces.dto.CleaningResultDto;
import lombok.RequiredArgsConstructor;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Repository;

import java.util.List;

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
    public int[] countByInstanceId(String instanceId) {
        LambdaQueryWrapper<CleaningResult> lambdaWrapper = new LambdaQueryWrapper<>();
        lambdaWrapper.eq(CleaningResult::getInstanceId, instanceId);
        List<CleaningResult> cleaningResults = mapper.selectList(lambdaWrapper);
        int succeed = Math.toIntExact(cleaningResults.stream()
                .filter(result ->
                        StringUtils.equals(result.getStatus(), CleaningTaskStatusEnum.COMPLETED.getValue()))
                .count());
        return new int[] {succeed, cleaningResults.size() - succeed};
    }

    public List<CleaningResultDto> findByInstanceId(String instanceId) {
        LambdaQueryWrapper<CleaningResult> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(CleaningResult::getInstanceId, instanceId);
        return CleaningResultConverter.INSTANCE.convertEntityToDto(mapper.selectList(queryWrapper));
    }
}
