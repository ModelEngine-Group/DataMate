package com.datamate.cleaning.domain.model;

import lombok.Getter;
import lombok.Setter;

import java.util.List;
import java.util.Map;


@Getter
@Setter
public class TaskProcess {
    private String instanceId;

    private String datasetId;

    private String datasetPath;

    private String exportPath;

    private String executorType;

    private List<Map<String, Map<String, Object>>> process;
}
