package com.dataengine.collection.domain.repository;

import com.dataengine.collection.domain.model.DataSource;
import com.dataengine.collection.domain.model.DataSourceId;
import com.dataengine.collection.domain.model.DataSourceType;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.util.List;
import java.util.Optional;

/**
 * 数据源仓储接口
 */
public interface DataSourceRepository {

    /**
     * 保存数据源
     */
    DataSource save(DataSource dataSource);

    /**
     * 根据ID查找数据源
     */
    Optional<DataSource> findById(DataSourceId id);

    /**
     * 分页查询数据源
     */
    Page<DataSource> findAll(Pageable pageable);

    /**
     * 根据类型查询数据源
     */
    Page<DataSource> findByType(DataSourceType type, Pageable pageable);

    /**
     * 根据名称查询数据源
     */
    Optional<DataSource> findByName(String name);

    /**
     * 查询所有激活的数据源
     */
    List<DataSource> findAllActive();

    /**
     * 删除数据源
     */
    void delete(DataSource dataSource);

    /**
     * 根据ID删除数据源
     */
    void deleteById(DataSourceId id);

    /**
     * 检查数据源是否存在
     */
    boolean existsById(DataSourceId id);
}
