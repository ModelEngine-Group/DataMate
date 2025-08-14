package com.dataengine.datamanagement.domain.repository;

import com.dataengine.datamanagement.domain.model.dataset.DatasetFile;
import com.dataengine.datamanagement.domain.model.dataset.DatasetFileStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * 数据集文件仓储接口
 */
@Repository
public interface DatasetFileRepository extends JpaRepository<DatasetFile, String> {

    /**
     * 根据数据集ID查找文件
     */
    Page<DatasetFile> findByDatasetId(String datasetId, Pageable pageable);

    /**
     * 根据数据集ID和状态查找文件
     */
    Page<DatasetFile> findByDatasetIdAndStatus(String datasetId, DatasetFileStatus status, Pageable pageable);

    /**
     * 根据数据集ID和文件类型查找文件
     */
    Page<DatasetFile> findByDatasetIdAndFileType(String datasetId, String fileType, Pageable pageable);

    /**
     * 根据数据集ID统计文件数量
     */
    @Query("SELECT COUNT(f) FROM DatasetFile f WHERE f.dataset.id = :datasetId")
    Long countByDatasetId(@Param("datasetId") String datasetId);

    /**
     * 根据数据集ID统计完成的文件数量
     */
    @Query("SELECT COUNT(f) FROM DatasetFile f WHERE f.dataset.id = :datasetId AND f.status = 'COMPLETED'")
    Long countCompletedByDatasetId(@Param("datasetId") String datasetId);

    /**
     * 根据数据集ID计算总大小
     */
    @Query("SELECT COALESCE(SUM(f.size), 0) FROM DatasetFile f WHERE f.dataset.id = :datasetId")
    Long sumSizeByDatasetId(@Param("datasetId") String datasetId);

    /**
     * 根据数据集ID和文件名查找文件
     */
    Optional<DatasetFile> findByDatasetIdAndFileName(String datasetId, String fileName);

    /**
     * 根据数据集ID查找所有文件
     */
    List<DatasetFile> findAllByDatasetId(String datasetId);

    /**
     * 复合条件查询文件
     */
    @Query("SELECT f FROM DatasetFile f WHERE f.dataset.id = :datasetId AND " +
           "(:fileType IS NULL OR f.fileType = :fileType) AND " +
           "(:status IS NULL OR f.status = :status)")
    Page<DatasetFile> findByCriteria(@Param("datasetId") String datasetId,
                                    @Param("fileType") String fileType,
                                    @Param("status") DatasetFileStatus status,
                                    Pageable pageable);
}
