package com.dataengine.cleaning.domain.model;

import lombok.Getter;
import lombok.Setter;
import java.util.List;

/**
 * 数据集类型响应DTO
 */
@Getter
@Setter
public class DatasetTypeResponse {
    /** 类型编码 */
    private String code;
    /** 类型名称 */
    private String name;
    /** 类型描述 */
    private String description;
    /** 支持的文件格式 */
    private List<String> supportedFormats;
    /** 图标 */
    private String icon;
}