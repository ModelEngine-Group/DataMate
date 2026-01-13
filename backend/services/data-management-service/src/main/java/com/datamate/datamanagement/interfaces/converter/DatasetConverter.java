package com.datamate.datamanagement.interfaces.converter;

import com.datamate.common.domain.model.ChunkUploadRequest;
import com.datamate.datamanagement.domain.model.dataset.Dataset;
import com.datamate.datamanagement.domain.model.dataset.DatasetFile;
import com.datamate.datamanagement.domain.model.dataset.FileTag;
import com.datamate.datamanagement.domain.model.dataset.Tag;
import com.datamate.datamanagement.interfaces.dto.*;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.apache.commons.collections4.CollectionUtils;
import org.apache.commons.lang3.StringUtils;
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
    @Mapping(source = "tags", target = "tags", qualifiedByName = "getDatasetTags")
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

    /**
     * 获取数据集标签
     *
     * @param datasetTag 数据集标签
     * @return 标签
     */
    @Named("getDatasetTags")
    default List<TagResponse> getDatasetTags(String datasetTag) {
        List<TagResponse> tagResponses = new ArrayList<>();
        if (StringUtils.isBlank(datasetTag)) {
            return tagResponses;
        }
        ObjectMapper mapper = new ObjectMapper();
        try {
            mapper.registerModule(new JavaTimeModule());
            // 可选：配置日期时间格式
            mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
            return mapper.readValue(datasetTag, new TypeReference<List<Tag>>() {
            }).stream().map(TagConverter.INSTANCE::convertToResponse).toList();
        } catch (Exception e) {
            return Collections.emptyList();
        }
    }
}
