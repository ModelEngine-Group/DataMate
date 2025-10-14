package com.dataengine.common.infrastructure.mapper;

import com.dataengine.common.domain.model.ChunkUploadPreRequest;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 文件切片上传请求Mapper
 */
@Mapper
public interface ChunkUploadRequestMapper {

    /**
     * 根据ID查询
     */
    ChunkUploadPreRequest findById(@Param("id") String id);

    /**
     * 根据服务ID查询
     */
    List<ChunkUploadPreRequest> findByServiceId(@Param("serviceId") String serviceId);

    /**
     * 查询所有
     */
    List<ChunkUploadPreRequest> findAll();

    /**
     * 插入
     */
    int insert(ChunkUploadPreRequest request);

    /**
     * 更新
     */
    int update(ChunkUploadPreRequest request);

    /**
     * 根据ID删除
     */
    int deleteById(@Param("id") String id);

    /**
     * 根据服务ID删除
     */
    int deleteByServiceId(@Param("serviceId") String serviceId);
}
