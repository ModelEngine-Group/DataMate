package com.datamate.collection.interfaces.converter;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.datamate.collection.domain.model.entity.CollectionTask;
import com.datamate.collection.interfaces.dto.*;
import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import com.datamate.common.interfaces.PagedResponse;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.Named;
import org.mapstruct.factory.Mappers;

import java.util.List;
import java.util.Map;

@Mapper
public interface CollectionTaskConverter {
    CollectionTaskConverter INSTANCE = Mappers.getMapper(CollectionTaskConverter.class);

    @Mapping(source = "config", target = "config", qualifiedByName = "parseJsonToMap")
    CollectionTaskResponse toResponse(CollectionTask task);

    List<CollectionTaskResponse> toResponse(List<CollectionTask> tasks);

    @Mapping(source = "config", target = "config", qualifiedByName = "mapToJsonString")
    CollectionTask toCollectionTask(CreateCollectionTaskRequest request);

    @Mapping(source = "config", target = "config", qualifiedByName = "mapToJsonString")
    CollectionTask toCollectionTask(UpdateCollectionTaskRequest request);

    @Mapping(source = "current", target = "page")
    @Mapping(source = "size", target = "size")
    @Mapping(source = "total", target = "totalElements")
    @Mapping(source = "pages", target = "totalPages")
    @Mapping(source = "records", target = "content")
    PagedResponse<CollectionTaskResponse> toResponse(IPage<CollectionTask> tasks);

    @Named("parseJsonToMap")
    default Map<String, Object> parseJsonToMap(String json) {
        try {
            ObjectMapper objectMapper = new ObjectMapper();
            return
                objectMapper.readValue(json, Map.class);
        } catch (Exception e) {
            throw BusinessException.of(SystemErrorCode.INVALID_PARAMETER);
        }
    }

    @Named("mapToJsonString")
    default String mapToJsonString(Map<String, Object> map) {
        try {
            ObjectMapper objectMapper = new ObjectMapper();
            return objectMapper.writeValueAsString(map != null ? map : Map.of());
        } catch (Exception e) {
            throw BusinessException.of(SystemErrorCode.INVALID_PARAMETER);
        }
    }
}
