package com.datamate.datamanagement.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.datamate.common.infrastructure.config.IgnoreDataScopeAnnotation;
import com.datamate.datamanagement.domain.model.dataset.DatasetFile;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.session.RowBounds;

import java.util.List;

@Mapper
@IgnoreDataScopeAnnotation
public interface DatasetFileMapper extends BaseMapper<DatasetFile> {
    DatasetFile findById(@Param("id") String id);
    List<DatasetFile> findByDatasetId(@Param("datasetId") String datasetId, RowBounds rowBounds);
    List<DatasetFile> findByDatasetIdAndStatus(@Param("datasetId") String datasetId, @Param("status") String status, RowBounds rowBounds);
    List<DatasetFile> findByDatasetIdAndFileType(@Param("datasetId") String datasetId, @Param("fileType") String fileType, RowBounds rowBounds);
    Long countByDatasetId(@Param("datasetId") String datasetId);
    Long countCompletedByDatasetId(@Param("datasetId") String datasetId);
    Long sumSizeByDatasetId(@Param("datasetId") String datasetId);
    DatasetFile findByDatasetIdAndFileName(@Param("datasetId") String datasetId, @Param("fileName") String fileName);
    List<DatasetFile> findAllByDatasetId(@Param("datasetId") String datasetId);
    List<DatasetFile> findByCriteria(@Param("datasetId") String datasetId,
                                     @Param("fileType") String fileType,
                                     @Param("status") String status,
                                     RowBounds rowBounds);

    int update(DatasetFile file);
    int deleteById(@Param("id") String id);
}
