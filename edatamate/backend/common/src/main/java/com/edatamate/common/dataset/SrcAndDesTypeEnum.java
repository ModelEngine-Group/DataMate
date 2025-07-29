package com.edatamate.common.dataset;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * 数据源和目标类型枚举
 */
@RequiredArgsConstructor
@Getter
public enum SrcAndDesTypeEnum {
    LOCAL("local", "local"),  // 本地导入
    DATABASE("database", "database"),   // 数据库导入
    NFS("nfs", "nfs"),    // NAS导入
    S3("s3", "obs"), // OBS导入
    LOCAL_COLLECTION("local_collection", "local_collection"); // 本地采集

    private final String name;

    private final String type;

    /**
     * 获取名称
     */
    public static Set<String> getRemoteSource() {
        return new HashSet<>(List.of(NFS.getName(), S3.getName(), DATABASE.getName()));
    }

    /**
     * 获取名称
     */
    public static boolean isLegalSrcAndDesType(String name) {
        return Arrays.stream(SrcAndDesTypeEnum.values()).anyMatch(v -> v.name.equals(name));
    }
}
