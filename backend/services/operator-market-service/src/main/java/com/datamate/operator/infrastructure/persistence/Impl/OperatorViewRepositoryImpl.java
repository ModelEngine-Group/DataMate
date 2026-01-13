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
import java.util.stream.Collectors;

@Repository
@RequiredArgsConstructor
public class OperatorViewRepositoryImpl extends CrudRepository<OperatorViewMapper, OperatorView> implements OperatorViewRepository {
    private final OperatorViewMapper mapper;

    @Override
    public List<OperatorDto> findOperatorsByCriteria(Integer page, Integer size, String keyword,
                                                     List<List<String>> categories, Boolean isStar) {
        QueryWrapper<OperatorView> queryWrapper = getQueryWrapper(keyword, categories, isStar);

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
    public int countOperatorsByCriteria(String keyword, List<List<String>> categories, Boolean isStar) {
        QueryWrapper<OperatorView> queryWrapper = getQueryWrapper(keyword, categories, isStar);
        Integer count = mapper.countOperatorsByCriteria(queryWrapper);
        return count != null ? count : 0;
    }

    @Override
    public OperatorView findOperatorById(String id) {
        return mapper.findOperatorById(id);
    }

    private QueryWrapper<OperatorView> getQueryWrapper(String keyword, List<List<String>> categories, Boolean isStar) {
        QueryWrapper<OperatorView> queryWrapper = Wrappers.query();
        queryWrapper.eq(isStar != null, "is_star", isStar);
        if (StringUtils.isNotEmpty(keyword)) {
            queryWrapper.and(w ->
                    w.like("operator_name", keyword)
                            .or()
                            .like("description", keyword));
        }
        StringBuilder havingSql = new StringBuilder();
        if (CollectionUtils.isNotEmpty(categories)) {
            queryWrapper.in("category_id", categories.stream().flatMap(List::stream).toList());
            int index = 0;
            for (List<String> category : categories) {
                if (index > 0) {
                    havingSql.append(" AND ");
                }
                havingSql.append("SUM(CASE WHEN CAST(category_id AS TEXT) IN (");
                havingSql.append(category.stream()
                        .map(id -> "'" + id + "'")
                        .collect(Collectors.joining(",")));
                havingSql.append(") THEN 1 ELSE 0 END) > 0");
                index++;
            }
        }

        queryWrapper.groupBy("operator_id", "operator_name", "description", "version", "inputs", "outputs",
                        "runtime", "settings", "is_star", "created_at", "updated_at")
                .having(!havingSql.isEmpty(), havingSql.toString())
                .orderByDesc("created_at");
        return queryWrapper;
    }
}
