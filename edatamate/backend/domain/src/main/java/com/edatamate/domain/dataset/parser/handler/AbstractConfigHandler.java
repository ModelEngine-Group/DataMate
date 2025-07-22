package com.edatamate.domain.dataset.parser.handler;

import com.edatamate.domain.dataset.parser.datasetconfig.CommonConfig;

public abstract class AbstractConfigHandler implements ConfigHandler {
    @Override
    public CommonConfig parse(String config) {
        return getConfig(config);
    }

    /**
     * 从String中解析不同的配置类型
     * @param config 用户前端输入的信息
     * @return {@link CommonConfig}
     */
    protected abstract CommonConfig getConfig(String config);
}
