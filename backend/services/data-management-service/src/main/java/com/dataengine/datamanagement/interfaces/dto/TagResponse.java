package com.dataengine.datamanagement.interfaces.dto;

import lombok.Getter;
import lombok.Setter;

/**
 * 标签响应DTO
 */
@Getter
@Setter
public class TagResponse {
    /** 标签ID */
    private String id;
    /** 标签名称 */
    private String name;
    /** 标签颜色 */
    private String color;
    /** 标签描述 */
    private String description;
    /** 使用次数 */
    private Integer usageCount;
}
