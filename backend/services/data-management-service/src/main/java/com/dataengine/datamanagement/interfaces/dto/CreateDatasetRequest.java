package com.dataengine.datamanagement.interfaces.dto;

import lombok.Getter;
import lombok.Setter;

import java.util.List;

/**
 * 创建数据集请求DTO
 */
@Getter
@Setter
public class CreateDatasetRequest {
    /** 数据集名称 */
    private String name;
    /** 数据集描述 */
    private String description;
    /** 数据集类型 */
    private String type;
    /** 标签列表 */
    private List<String> tags;
    /** 数据源 */
    private String dataSource;
    /** 目标位置 */
    private String targetLocation;
}
