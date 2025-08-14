package com.dataengine.collection.infrastructure.persistence;

import com.dataengine.collection.domain.model.DataSource;
import com.dataengine.collection.domain.model.DataSourceType;
import com.dataengine.collection.domain.repository.DataSourceRepository;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * 数据源JPA仓储实现
 */
@Repository
public interface DataSourceJpaRepository extends JpaRepository<DataSource, String>, DataSourceRepository {

    /**
     * 根据类型查找数据源
     */
    @Query("SELECT ds FROM DataSource ds WHERE ds.type = :type")
    List<DataSource> findByType(@Param("type") DataSourceType type);

    /**
     * 根据名称查找数据源
     */
    @Query("SELECT ds FROM DataSource ds WHERE ds.name = :name")
    Optional<DataSource> findByName(@Param("name") String name);

    /**
     * 查找所有活跃的数据源
     */
    @Query("SELECT ds FROM DataSource ds WHERE ds.status = 'ACTIVE'")
    List<DataSource> findAllActive();

    /**
     * 根据类型查找活跃的数据源
     */
    @Query("SELECT ds FROM DataSource ds WHERE ds.type = :type AND ds.status = 'ACTIVE'")
    List<DataSource> findActiveByType(@Param("type") DataSourceType type);
}
