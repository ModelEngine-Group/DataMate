package com.dataengine.datamanagement.domain.repository;

import com.dataengine.datamanagement.domain.model.dataset.Dataset;
import com.dataengine.datamanagement.domain.model.dataset.DatasetStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * 数据集仓储接口
 */
@Repository
public interface DatasetRepository extends JpaRepository<Dataset, String> {

    /**
     * 根据名称查找数据集
     */
    Optional<Dataset> findByName(String name);

    /**
     * 根据状态查找数据集
     */
    List<Dataset> findByStatus(DatasetStatus status);

    /**
     * 根据创建者查找数据集
     */
    Page<Dataset> findByCreatedBy(String createdBy, Pageable pageable);

    /**
     * 根据类型代码查找数据集
     */
    @Query("SELECT d FROM Dataset d WHERE d.type.code = :typeCode")
    Page<Dataset> findByTypeCode(@Param("typeCode") String typeCode, Pageable pageable);

    /**
     * 根据标签查找数据集
     */
    @Query("SELECT DISTINCT d FROM Dataset d JOIN d.tags t WHERE t.name IN :tagNames")
    Page<Dataset> findByTagNames(@Param("tagNames") List<String> tagNames, Pageable pageable);

    /**
     * 根据关键词搜索数据集（名称或描述）
     */
    @Query("SELECT d FROM Dataset d WHERE d.name LIKE %:keyword% OR d.description LIKE %:keyword%")
    Page<Dataset> findByKeyword(@Param("keyword") String keyword, Pageable pageable);

    /**
     * 复合条件查询数据集
     */
    @Query("SELECT DISTINCT d FROM Dataset d LEFT JOIN d.tags t WHERE " +
           "(:typeCode IS NULL OR d.type.code = :typeCode) AND " +
           "(:status IS NULL OR d.status = :status) AND " +
           "(:keyword IS NULL OR d.name LIKE %:keyword% OR d.description LIKE %:keyword%) AND " +
           "(:tagNames IS NULL OR t.name IN :tagNames)")
    Page<Dataset> findByCriteria(@Param("typeCode") String typeCode,
                                @Param("status") DatasetStatus status,
                                @Param("keyword") String keyword,
                                @Param("tagNames") List<String> tagNames,
                                Pageable pageable);
}
