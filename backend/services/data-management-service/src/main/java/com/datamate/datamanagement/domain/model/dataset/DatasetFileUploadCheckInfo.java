package com.datamate.datamanagement.domain.model.dataset;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 数据集文件上传检查信息
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class DatasetFileUploadCheckInfo {
    /** 数据集id */
    private String datasetId;

    /** 是否为压缩包上传 */
    private boolean hasArchive;

    /** 目标子目录前缀，例如 "images/"，为空表示数据集根目录 */
    private String prefix;
}
