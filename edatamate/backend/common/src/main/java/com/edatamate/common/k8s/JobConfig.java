package com.edatamate.common.k8s;

import io.fabric8.kubernetes.api.model.Volume;
import io.fabric8.kubernetes.api.model.VolumeMount;
import lombok.Builder;
import lombok.Getter;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 执行 Job 的参数配置
 */
@Getter
@Builder
public class JobConfig {
    private final String image;

    @Builder.Default
    private final String imagePullPolicy = "IfNotPresent";

    @Builder.Default
    private final List<String> command = new ArrayList<>();

    @Builder.Default
    private final Map<String, String> envVars = new HashMap<>();

    @Builder.Default
    private final String jobNamePrefix = "job-executor";

    @Builder.Default
    private final int backoffLimit = 0;

    @Builder.Default
    private final int ttlSecondsAfterFinished = 3600;

    @Builder.Default
    private final long timeoutSeconds = 86400;

    @Builder.Default
    private final Map<String, String> labels = new HashMap<>();

    @Builder.Default
    private final Map<String, String> annotations = new HashMap<>();

    private final String serviceAccountName;

    @Builder.Default
    private final List<Volume> volumes = new ArrayList<>();

    @Builder.Default
    private final List<VolumeMount> volumeMounts = new ArrayList<>();
}
