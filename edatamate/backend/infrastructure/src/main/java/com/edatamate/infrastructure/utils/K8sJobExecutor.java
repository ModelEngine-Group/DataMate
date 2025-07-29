package com.edatamate.infrastructure.utils;


import com.edatamate.common.k8s.JobConfig;
import com.edatamate.common.k8s.JobResult;
import io.fabric8.kubernetes.api.model.Container;
import io.fabric8.kubernetes.api.model.ContainerBuilder;
import io.fabric8.kubernetes.api.model.EnvVar;
import io.fabric8.kubernetes.api.model.EnvVarBuilder;
import io.fabric8.kubernetes.api.model.PodList;
import io.fabric8.kubernetes.api.model.PodTemplateSpec;
import io.fabric8.kubernetes.api.model.PodTemplateSpecBuilder;
import io.fabric8.kubernetes.api.model.batch.v1.Job;
import io.fabric8.kubernetes.api.model.batch.v1.JobBuilder;
import io.fabric8.kubernetes.api.model.batch.v1.JobSpec;
import io.fabric8.kubernetes.api.model.batch.v1.JobSpecBuilder;
import io.fabric8.kubernetes.api.model.batch.v1.JobStatus;
import io.fabric8.kubernetes.client.KubernetesClient;
import io.fabric8.kubernetes.client.KubernetesClientBuilder;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;

/**
 * 调度k8s job
 */
public class K8sJobExecutor {
    private static final Logger logger = LoggerFactory.getLogger(K8sJobExecutor.class);

    private final KubernetesClient kubernetesClient;

    private final String namespace;

    public K8sJobExecutor(String namespace) {
        this.kubernetesClient = new KubernetesClientBuilder().build();
        this.namespace = namespace;
    }

    /**
     * 创建并执行 Job
     */
    public JobResult executeJob(JobConfig config) {
        String jobId = generateJobId(config.getJobNamePrefix());
        Instant startTime = Instant.now();

        try {
            logger.info("开始创建 Job: {}, 镜像: {}", jobId, config.getImage());

            // 创建 Job
            Job job = createJob(jobId, config);
            kubernetesClient.batch().v1().jobs().resource(job).create();

            logger.info("Job 创建成功: {}", jobId);

            // 监控 Job 状态
            boolean success = waitForJobCompletion(jobId, config.getTimeoutSeconds());

            // 获取 Job 日志
            String logs = getJobLogs(jobId);

            // 清理 Job（可选）
            // cleanupJob(jobId);

            long executionTime = Duration.between(startTime, Instant.now()).toMillis();

            if (success) {
                logger.info("Job 执行成功: {}, 执行时间: {}ms", jobId, executionTime);
                return new JobResult(true, jobId, logs, executionTime, null);
            } else {
                String errorMsg = "Job 执行失败: " + jobId;
                logger.error(errorMsg);
                return new JobResult(false, jobId, logs, executionTime, errorMsg);
            }

        } catch (Exception e) {
            long executionTime = Duration.between(startTime, Instant.now()).toMillis();
            String errorMsg = "Job 执行异常: " + e.getMessage();
            logger.error("Job 执行异常: {}", jobId, e);
            return new JobResult(false, jobId, "", executionTime, errorMsg);
        }
    }

    /**
     * 异步执行 Job
     */
    public CompletableFuture<JobResult> executeJobAsync(JobConfig config) {
        return CompletableFuture.supplyAsync(() -> executeJob(config));
    }

    /**
     * 创建 Job 对象
     */
    private Job createJob(String jobId, JobConfig config) {
        // 构建容器环境变量
        List<EnvVar> envVars = new ArrayList<>();
        if (config.getEnvVars() != null) {
            config.getEnvVars().forEach((key, value) ->
                    envVars.add(new EnvVarBuilder().withName(key).withValue(value).build()));
        }

        // 构建容器
        Container container = new ContainerBuilder()
                .withName("job-container")
                .withImage(config.getImage())
                .withImagePullPolicy(config.getImagePullPolicy())
                .withCommand(config.getCommand())
                .withEnv(envVars)
                .withVolumeMounts(config.getVolumeMounts())
                .build();

        // 构建 Pod 模板
        PodTemplateSpec podTemplate = new PodTemplateSpecBuilder()
                .withNewSpec()
                .withContainers(container)
                .withRestartPolicy("Never")
                .withServiceAccountName(config.getServiceAccountName())
                .withVolumes(config.getVolumes())
                .endSpec()
                .build();

        // 构建 Job 规范
        JobSpec jobSpec = new JobSpecBuilder()
                .withBackoffLimit(config.getBackoffLimit())
                .withTtlSecondsAfterFinished(config.getTtlSecondsAfterFinished())
                .withTemplate(podTemplate)
                .build();

        // 构建 Job 对象
        return new JobBuilder()
                .withNewMetadata()
                .withName(jobId)
                .withLabels(config.getLabels())
                .withAnnotations(config.getAnnotations())
                .endMetadata()
                .withSpec(jobSpec)
                .build();
    }

    /**
     * 等待 Job 完成
     */
    private boolean waitForJobCompletion(String jobId, long timeoutSeconds) throws InterruptedException {
        logger.info("开始监控 Job 状态: {}, 超时时间: {}秒", jobId, timeoutSeconds);

        long startTime = System.currentTimeMillis();
        long timeoutMillis = timeoutSeconds * 1000;

        while (System.currentTimeMillis() - startTime < timeoutMillis) {
            try {
                Job job = kubernetesClient.batch().v1().jobs().inNamespace(namespace).withName(jobId).get();

                if (job == null) {
                    logger.warn("Job 不存在: {}", jobId);
                    return false;
                }

                JobStatus status = job.getStatus();
                if (status != null) {
                    Integer succeeded = status.getSucceeded();
                    Integer failed = status.getFailed();

                    if (succeeded != null && succeeded > 0) {
                        logger.info("Job 执行成功: {}", jobId);
                        return true;
                    }

                    if (failed != null && failed > 0) {
                        logger.error("Job 执行失败: {}", jobId);
                        return false;
                    }
                }

                // 等待一段时间后重试
                Thread.sleep(2000);

            } catch (Exception e) {
                logger.error("监控 Job 状态时发生异常: {}", jobId, e);
                return false;
            }
        }

        logger.error("Job 执行超时: {}", jobId);
        return false;
    }

    /**
     * 获取 Job 日志
     */
    private String getJobLogs(String jobId) {
        try {
            // 获取 Job 对应的 Pod
            PodList podList = kubernetesClient.pods()
                    .inNamespace(namespace)
                    .withLabel("job-name", jobId)
                    .list();

            if (podList.getItems().isEmpty()) {
                logger.warn("未找到 Job 对应的 Pod: {}", jobId);
                return "";
            }

            String podName = podList.getItems().get(0).getMetadata().getName();
            logger.info("获取 Pod 日志: {}", podName);

            // 获取日志
            return kubernetesClient.pods()
                    .inNamespace(namespace)
                    .withName(podName)
                    .getLog();

        } catch (Exception e) {
            logger.error("获取 Job 日志失败: {}", jobId, e);
            return "获取日志失败: " + e.getMessage();
        }
    }

    /**
     * 清理 Job
     */
    private void cleanupJob(String jobId) {
        try {
            kubernetesClient.batch().v1().jobs()
                    .inNamespace(namespace)
                    .withName(jobId)
                    .delete();
            logger.info("Job 清理完成: {}", jobId);
        } catch (Exception e) {
            logger.warn("Job 清理失败: {}", jobId, e);
        }
    }

    /**
     * 生成唯一的 Job ID
     */
    private String generateJobId(String prefix) {
        return prefix + "-" + UUID.randomUUID().toString().substring(0, 8);
    }

    /**
     * 关闭客户端
     */
    public void close() {
        if (kubernetesClient != null) {
            kubernetesClient.close();
        }
    }
}