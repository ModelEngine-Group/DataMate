package com.dataengine.datamanagement.interfaces.dto;

import lombok.Getter;
import lombok.Setter;

/**
 * 创建标签请求DTO
 */
@Getter
@Setter
public class CreateTagRequest {
    /** 标签名称 */
    private String name;
    /** 标签颜色 */
    private String color;
    /** 标签描述 */
    private String description;
}
