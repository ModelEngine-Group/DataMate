package com.datamate.datamanagement.infrastructure.persistence.repository.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.repository.CrudRepository;
import com.datamate.datamanagement.domain.model.dataset.Dataset;
import com.datamate.datamanagement.infrastructure.persistence.mapper.DatasetMapper;
import com.datamate.datamanagement.infrastructure.persistence.repository.DatasetRepository;
import com.datamate.datamanagement.interfaces.dto.AllDatasetStatisticsResponse;
import com.datamate.datamanagement.interfaces.dto.DatasetPagingQuery;
import lombok.RequiredArgsConstructor;
import org.apache.commons.lang3.StringUtils;
import org.apache.ibatis.session.RowBounds;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 数据集仓储层实现类
 *
 * @author dallas
 * @since 2025-10-15
 */
@Repository
@RequiredArgsConstructor
public class DatasetRepositoryImpl extends CrudRepository<DatasetMapper, Dataset> implements DatasetRepository {
    private final DatasetMapper datasetMapper;

    @Override
    public Dataset findByName(String name) {
        return datasetMapper.selectOne(new LambdaQueryWrapper<Dataset>().eq(Dataset::getName, name));
    }

    @Override
    public List<Dataset> findByCriteria(String type, String status, String keyword, List<String> tagList,
                                        RowBounds bounds) {
        return datasetMapper.findByCriteria(type, status, keyword, tagList, bounds);
    }

    @Override
    public long countByCriteria(String type, String status, String keyword, List<String> tagList) {
        return datasetMapper.countByCriteria(type, status, keyword, tagList);
    }

    @Override
    public AllDatasetStatisticsResponse getAllDatasetStatistics() {
        return datasetMapper.getAllDatasetStatistics();
    }


    @Override
    public IPage<Dataset> findByCriteria(IPage<Dataset> page, DatasetPagingQuery query) {
        LambdaQueryWrapper<Dataset> wrapper = new LambdaQueryWrapper<Dataset>()
                .eq(query.getType() != null, Dataset::getDatasetType, query.getType())
                .eq(query.getStatus() != null, Dataset::getStatus, query.getStatus());

        if (StringUtils.isNotBlank(query.getKeyword())) {
            wrapper.and(w ->
                    w.like(Dataset::getName, query.getKeyword()).or()
                            .like(Dataset::getDescription, query.getKeyword()));
        }

        /*
          标签过滤 {@link Tag}
          */
        for (String tagName : query.getTags()) {
            wrapper.and(w ->
                w.apply("tags IS NOT NULL " +
                    "AND JSON_VALID(tags) = 1 " +
                    "AND JSON_LENGTH(tags) > 0 " +
                    "AND JSON_SEARCH(tags, 'one', {0}, NULL, '$[*].name') IS NOT NULL", tagName)
            );
        }
        wrapper.orderByDesc(Dataset::getCreatedAt);
        return datasetMapper.selectPage(page, wrapper);
    }
}
