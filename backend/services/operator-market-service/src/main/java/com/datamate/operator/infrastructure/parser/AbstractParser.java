package com.datamate.operator.infrastructure.parser;

import org.yaml.snakeyaml.Yaml;

import java.io.File;
import java.nio.file.Path;

public abstract class AbstractParser {
    // 使用 SnakeYAML 的 Yaml 实例，子类直接使用
    protected final Yaml yaml = new Yaml();

    /**
     * 从压缩包内读取指定路径的 yaml 文件并解析为指定类型
     * @param archive 压缩包路径（zip 或 tar）
     * @param entryPath 压缩包内部的文件路径，例如 "config/app.yaml" 或 "./config/app.yaml"
     * @param clazz 目标类型
     * @param <T> 类型参数
     * @return 解析后的对象
     */
    public abstract <T> T parseYamlFromArchive(File archive, String entryPath, Class<T> clazz);

    /**
     * 将压缩包解压到目标目录（保持相对路径）
     * @param archive 压缩包路径
     * @param targetDir 目标目录
     */
    public abstract void extractTo(File archive, String targetDir);
}
