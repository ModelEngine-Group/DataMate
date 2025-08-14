package com.dataengine.datamanagement.domain.repository;

import com.dataengine.datamanagement.domain.model.dataset.Tag;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * 标签仓储接口
 */
@Repository
public interface TagRepository extends JpaRepository<Tag, String> {

    /**
     * 根据名称查找标签
     */
    Optional<Tag> findByName(String name);

    /**
     * 根据名称列表查找标签
     */
    List<Tag> findByNameIn(List<String> names);

    /**
     * 根据关键词搜索标签
     */
    @Query("SELECT t FROM Tag t WHERE t.name LIKE %:keyword%")
    List<Tag> findByKeyword(@Param("keyword") String keyword);

    /**
     * 查找使用次数大于0的标签
     */
    List<Tag> findByUsageCountGreaterThan(Integer count);

    /**
     * 按使用次数降序排列
     */
    List<Tag> findAllByOrderByUsageCountDesc();
}
