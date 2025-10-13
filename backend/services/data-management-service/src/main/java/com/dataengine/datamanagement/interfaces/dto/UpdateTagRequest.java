package com.dataengine.datamanagement.interfaces.dto;

import lombok.Getter;
import lombok.Setter;

/**
 * 更新标签请求DTO
 */
@Getter
@Setter
public class UpdateTagRequest {
    /** 标签 ID */
    private String id;
    /** 标签名称 */
    private String name;
    /** 标签颜色 */
    private String color;
    /** 标签描述 */
    private String description;
}
