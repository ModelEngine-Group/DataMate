package com.dataengine.datamanagement.interfaces.converter;

import com.dataengine.common.domain.model.ChunkUploadRequest;
import com.dataengine.common.interfaces.PagedResponse;
import com.dataengine.datamanagement.domain.model.dataset.Dataset;
import com.dataengine.datamanagement.domain.model.dataset.Tag;
import com.dataengine.datamanagement.interfaces.dto.CreateDatasetRequest;
import com.dataengine.datamanagement.interfaces.dto.DatasetResponse;
import com.dataengine.datamanagement.interfaces.dto.TagResponse;
import com.dataengine.datamanagement.interfaces.dto.UploadFileRequest;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.factory.Mappers;
import org.springframework.data.domain.Page;

/**
 * 数据集文件转换器
 */
@Mapper
public interface DatasetConverter {
    /** 单例实例 */
    DatasetConverter INSTANCE = Mappers.getMapper(DatasetConverter.class);

    /**
     * 将数据集转换为响应
     */
    @Mapping(source = "sizeBytes", target = "totalSize")
    @Mapping(source = "path", target = "targetLocation")
    DatasetResponse convertToResponse(Dataset dataset);

    /**
     * 将数据集转换为响应
     */
    @Mapping(target = "tags", ignore = true)
    Dataset convertToDataset(CreateDatasetRequest createDatasetRequest);

    /**
     * 将数据集转换为响应
     */
    @Mapping(source = "number", target = "page")
    PagedResponse<DatasetResponse> convertToPagedResponse(Page<Dataset> dataset);

    /**
     * 将上传文件请求转换为分片上传请求
     */
    ChunkUploadRequest toChunkUploadRequest(UploadFileRequest uploadFileRequest);

    /**
     * 将数据集转换为响应
     */
    TagResponse convertToResponse(Tag dataset);
}
