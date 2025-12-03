package com.datamate.operator.infrastructure.persistence.Impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.core.toolkit.Wrappers;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.datamate.operator.domain.model.OperatorView;
import com.datamate.operator.domain.repository.OperatorViewRepository;
import com.datamate.operator.infrastructure.converter.OperatorConverter;
import com.datamate.operator.infrastructure.persistence.mapper.OperatorViewMapper;
import com.datamate.operator.interfaces.dto.OperatorDto;
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
    public List<OperatorDto> findOperatorsByCriteria(Integer page, Integer size, String keyword,
                                                     List<String> categories, Boolean isStar) {
        QueryWrapper<OperatorView> queryWrapper = Wrappers.query();
        queryWrapper.in(CollectionUtils.isNotEmpty(categories), "category_id", categories)
            .eq(isStar != null, "is_star", isStar);
        if (StringUtils.isNotEmpty(keyword)) {
            queryWrapper.and(w ->
                    w.like("operator_name", keyword)
                    .or()
                    .like("description", keyword));
        }
        queryWrapper.groupBy("operator_id")
            .orderByDesc("created_at");
        Page<OperatorView> queryPage;
        if (size != null && page != null) {
            queryPage = new Page<>(page + 1, size);
        } else {
            queryPage = new Page<>(1, -1);
        }
        IPage<OperatorView> operators = mapper.findOperatorsByCriteria(queryPage, queryWrapper);

        return OperatorConverter.INSTANCE.fromEntityViewToDto(operators.getRecords());
    }

    @Override
    public Integer countOperatorsByCriteria(String keyword, List<String> categories, Boolean isStar) {
        QueryWrapper<OperatorView> queryWrapper = Wrappers.query();
        queryWrapper.in(CollectionUtils.isNotEmpty(categories),"category_id", categories)
            .eq(isStar != null, "is_star", isStar);
        if (StringUtils.isNotEmpty(keyword)) {
            queryWrapper.and(w ->
                    w.like("operator_name", keyword)
                    .or()
                    .like("description", keyword));
        }
        return mapper.countOperatorsByCriteria(queryWrapper);
    }

    @Override
    public OperatorView findOperatorById(String id) {
        return mapper.findOperatorById(id);
    }
}
