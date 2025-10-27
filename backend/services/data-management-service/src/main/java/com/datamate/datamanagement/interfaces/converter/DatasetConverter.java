package com.datamate.datamanagement.interfaces.converter;

import com.datamate.datamanagement.interfaces.dto.CreateDatasetRequest;
import com.datamate.datamanagement.interfaces.dto.DatasetFileResponse;
import com.datamate.datamanagement.interfaces.dto.DatasetResponse;
import com.datamate.datamanagement.interfaces.dto.UploadFileRequest;
import com.datamate.common.domain.model.ChunkUploadRequest;
import com.datamate.datamanagement.domain.model.dataset.Dataset;
import com.datamate.datamanagement.domain.model.dataset.DatasetFile;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.factory.Mappers;

import java.util.List;

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
     * 将上传文件请求转换为分片上传请求
     */
    ChunkUploadRequest toChunkUploadRequest(UploadFileRequest uploadFileRequest);

    /**
     * 将数据集转换为响应
     */
    List<DatasetResponse> convertToResponse(List<Dataset> datasets);

    /**
     *
     * 将数据集文件转换为响应
     */
    DatasetFileResponse convertToResponse(DatasetFile datasetFile);
}
