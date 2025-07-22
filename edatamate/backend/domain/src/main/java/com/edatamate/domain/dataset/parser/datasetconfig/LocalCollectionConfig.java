package com.edatamate.domain.dataset.parser.datasetconfig;

import lombok.Getter;
import lombok.Setter;
import lombok.ToString;

/**
 * 本地归集配置类
 */
@Getter
@Setter
@ToString
public class LocalCollectionConfig extends CommonConfig{
    /**
     * 本地归集绝对路径
     */
    private String path;
}
