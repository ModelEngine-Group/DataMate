package com.dataengine.datamanagement.interfaces.converter;

import com.dataengine.datamanagement.domain.model.dataset.Tag;
import com.dataengine.datamanagement.interfaces.dto.TagResponse;
import com.dataengine.datamanagement.interfaces.dto.UpdateTagRequest;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

/**
 * 标签转换器
 */
@Mapper
public interface TagConverter {
    /** 单例实例 */
    TagConverter INSTANCE = Mappers.getMapper(TagConverter.class);

    /**
     * 将 UpdateTagRequest 转换为 Tag 实体
     * @param request 更新标签请求DTO
     * @return 标签实体
     */
    Tag updateRequestToTag(UpdateTagRequest request);

    /**
     * 将 Tag 实体转换为 TagResponse DTO
     * @param tag 标签实体
     * @return 标签响应DTO
     */
    TagResponse convertToResponse(Tag tag);
}
