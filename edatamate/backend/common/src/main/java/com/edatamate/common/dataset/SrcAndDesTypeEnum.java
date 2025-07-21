package com.edatamate.common.dataset;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

import java.util.Arrays;
import java.util.List;

/**
 * 数据源和目标类型枚举
 */
@RequiredArgsConstructor
@Getter
public enum SrcAndDesTypeEnum {
    LOCAL("local", "local"),  // 本地导入
    DATABASE("database", "database"),   // 数据库导入
    NFS("nfs", "nas"),    // NAS导入
    S3("s3", "obs"), // OBS导入
    LOCAL_COLLECTION("local_collection", "local_collection"); // 本地采集

    private final String name;

    private final String type;

    /**
     * 获取名称
     */
    public static List<String> getRemoteSource() {
        return Arrays.asList(NFS.getName(), S3.getName(), DATABASE.getName(), LOCAL_COLLECTION.getName());
    }

    /**
     * 获取名称
     */
    public static boolean isLegalSrcAndDesType(String name) {
        return Arrays.stream(SrcAndDesTypeEnum.values()).anyMatch(v -> v.name.equals(name));
    }
}
