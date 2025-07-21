package com.edatamate.domain.parser.handler;

import com.edatamate.domain.parser.datasetconfig.CommonConfig;

public interface ConfigHandler {
    /**
     * 处理数据集配置
     *
     * @param config 用户前端输入的信息
     * @return 配置信息
     */
    CommonConfig parse(String config);
}
