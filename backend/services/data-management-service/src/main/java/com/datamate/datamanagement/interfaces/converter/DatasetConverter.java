package com.datamate.datamanagement.interfaces.converter;

import com.datamate.common.domain.model.ChunkUploadRequest;
import com.datamate.datamanagement.domain.model.dataset.Dataset;
import com.datamate.datamanagement.domain.model.dataset.DatasetFile;
import com.datamate.datamanagement.domain.model.dataset.FileTag;
import com.datamate.datamanagement.interfaces.dto.*;
import org.apache.commons.collections4.CollectionUtils;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.Named;
import org.mapstruct.factory.Mappers;

import java.util.*;

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
    @Mapping(source = "files", target = "distribution", qualifiedByName = "getDistribution")
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


     /**
     * 将数据集文件列表转换为响应
     */
    List<DatasetFileResponse> convertToResponseList(List<DatasetFile> datasetFiles);


    /**
     * 获取数据文件的标签分布
     *
     * @param datasetFiles 数据集文件
     * @return 标签分布
     */
    @Named("getDistribution")
    default Map<String, Map<String, Long>> getDistribution(List<DatasetFile> datasetFiles) {
        Map<String, Map<String, Long>> distribution = new HashMap<>();
        if (CollectionUtils.isEmpty(datasetFiles)) {
            return distribution;
        }
        for (DatasetFile datasetFile : datasetFiles) {
            List<FileTag> tags = datasetFile.analyzeTag();
            if (CollectionUtils.isEmpty(tags)) {
                continue;
            }
            for (FileTag tag : tags) {
                Map<String, Long> tagValueMap = distribution.getOrDefault(tag.getFromName(), new HashMap<>());
                tag.getTagValues().forEach(tagValue -> tagValueMap.put(tagValue, tagValueMap.getOrDefault(tagValue, 0L) + 1));
                distribution.put(tag.getFromName(), tagValueMap);
            }
        }
        return distribution;
    }
}
