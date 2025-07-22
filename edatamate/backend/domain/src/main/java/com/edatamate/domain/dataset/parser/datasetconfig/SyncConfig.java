package com.edatamate.domain.dataset.parser.datasetconfig;

import lombok.Getter;
import lombok.Setter;

@Setter
@Getter
public class SyncConfig extends CommonConfig {
    private String syncType;

    private String cron;

    private int maxExecuteTimes;
}
