package com.edatamate.infrastructure.datax;


import com.edatamate.common.datax.dto.JobEnum;
import com.edatamate.common.datax.dto.Reader;
import com.edatamate.common.datax.dto.Writer;
import com.edatamate.common.k8s.JobConfig;
import com.edatamate.common.k8s.JobResult;
import com.edatamate.infrastructure.utils.DataXUtil;
import com.edatamate.infrastructure.utils.FileUtil;
import com.edatamate.infrastructure.utils.K8sJobExecutor;

import io.fabric8.kubernetes.api.model.VolumeBuilder;
import io.fabric8.kubernetes.api.model.VolumeMountBuilder;
import lombok.RequiredArgsConstructor;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.UUID;


@Service
@RequiredArgsConstructor
public class DataXHandler {
    @Value("${namespace:default}")
    private String namespace;

    public boolean createJob(String srcConf, String destConf, String srcType, String destType) {
        JobEnum readerType = JobEnum.of(srcType);
        JobEnum writerType = JobEnum.of(destType);
        Reader reader = DataXUtil.generateReader(srcConf, readerType);
        Writer writer = DataXUtil.generateWriter(destConf, writerType);
        Map<String, Object> config = generateConfig(reader, writer);
        String filepath = "/dataset/flow/" + UUID.randomUUID() + ".json";
        FileUtil.writePrettyJson(config, filepath);
        K8sJobExecutor executor = new K8sJobExecutor(namespace);
        JobConfig jobConfig = JobConfig.builder()
                .command(List.of("python3", "/opt/datax/bin/datax.py", filepath))
                .image("datax:latest")
                .jobNamePrefix("datax")
                .volumes(List.of(new VolumeBuilder()
                        .withName("dataset")
                        .withNewHostPath("/tmp/data-platform", "DirectoryOrCreate").build()))
                .volumeMounts(List.of(new VolumeMountBuilder()
                        .withName("dataset")
                        .withMountPath("/dataset")
                        .withSubPath("dataset").build()))
                .build();
        JobResult jobResult = executor.executeJob(jobConfig);
        FileUtil.deleteFile(filepath);
        return jobResult.success();
    }


    /**
     * 根据传入的参数生成DataX JSON配置文件
     *
     * @param reader reader部分的配置
     * @param writer writer部分的配置
     */
    public Map<String, Object> generateConfig(Reader reader, Writer writer) {
        // 固定的settings部分
        Map<String, Object> settings = Map.of(
                "speed", Map.of("channel", 3),
                "errorLimit", Map.of("record", 0)
        );

        // 使用FastJSON将Map转换为JSON并写入文件
        return Map.of(
                "job", Map.of(
                        "setting", settings,
                        "content", new Map[]{
                                Map.of(
                                        "reader", reader,
                                        "writer", writer
                                )
                        }
                )
        );
    }
}
