package com.datamate.cleaning.domain.model;

import lombok.Getter;
import lombok.Setter;


@Getter
@Setter
public class DataMateTaskProcess extends TaskProcess {
    private String instanceId;

    private String datasetId;
}
