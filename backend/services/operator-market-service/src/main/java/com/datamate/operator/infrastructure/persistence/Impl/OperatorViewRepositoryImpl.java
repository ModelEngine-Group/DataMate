package com.datamate.operator.infrastructure.persistence.Impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.datamate.operator.domain.model.OperatorView;
import com.datamate.operator.domain.repository.OperatorViewRepository;
import com.datamate.operator.infrastructure.persistence.mapper.OperatorViewMapper;
import io.micrometer.common.util.StringUtils;
import lombok.RequiredArgsConstructor;
import org.apache.commons.collections4.CollectionUtils;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
@RequiredArgsConstructor
public class OperatorViewRepositoryImpl extends CrudRepository<OperatorViewMapper, OperatorView> implements OperatorViewRepository {
    private final OperatorViewMapper mapper;

    @Override
    public List<OperatorView> findOperatorsByCriteria(Integer page, Integer size, String operatorName,
                                                      List<String> categories, Boolean isStar) {
        QueryWrapper<OperatorView> queryWrapper = Wrappers.query();
        queryWrapper.in(CollectionUtils.isNotEmpty(categories), "category_id", categories)
            .like(StringUtils.isNotBlank(operatorName), "operator_name", operatorName)
            .eq(isStar != null, "is_star", isStar)
            .groupBy("operator_id")
            .orderByDesc("created_at");
        Page<OperatorView> queryPage = null;
        if (size != null && page != null) {
            queryPage = new Page<>(page + 1, size);
        }
        IPage<OperatorView> operators = mapper.findOperatorsByCriteria(queryPage, queryWrapper);
        return operators.getRecords();
    }

    @Override
    public Integer countOperatorsByCriteria(String operatorName, List<String> categories, Boolean isStar) {
        QueryWrapper<OperatorView> queryWrapper = Wrappers.query();
        queryWrapper.in(CollectionUtils.isNotEmpty(categories),"category_id", categories)
            .like(StringUtils.isNotBlank(operatorName), "operator_name", operatorName)
            .eq(isStar != null, "is_star", isStar);
        return mapper.countOperatorsByCriteria(queryWrapper);
    }

    @Override
    public OperatorView findOperatorById(String id) {
        return mapper.findOperatorById(id);
    }
}
