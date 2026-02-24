package com.datamate.datamanagement.interfaces.dto;

import com.datamate.datamanagement.interfaces.validation.ValidHexColor;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.Setter;

/**
 * 创建标签请求DTO
 */
@Getter
@Setter
public class CreateTagRequest {
    /** 标签名称 */
    @NotBlank(message = "标签名称不能为空")
    @Size(min = 1, max = 100, message = "标签名称长度不能超过100个字符")
    private String name;
    /** 标签颜色 */
    @ValidHexColor
    private String color;
    /** 标签描述 */
    @Size(max = 500, message = "标签描述长度不能超过500个字符")
    private String description;
    /** 标签分类 */
    @Size(max = 50, message = "标签分类长度不能超过50个字符")
    private String category;
}
