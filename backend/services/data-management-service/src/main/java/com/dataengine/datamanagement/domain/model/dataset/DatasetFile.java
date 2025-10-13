package com.dataengine.datamanagement.domain.model.dataset;

import lombok.*;

import java.time.LocalDateTime;

/**
 * 数据集文件实体（与数据库表 t_dm_dataset_files 对齐）
 */
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DatasetFile {

    private String id; // UUID
    private String datasetId; // UUID
    private String fileName;
    private String filePath;
    private String fileType; // IMAGE/TEXT/VIDEO/AUDIO
    private Long fileSize; // bytes
    private String fileFormat;
    private LocalDateTime uploadTime;
    private LocalDateTime lastAccessTime;
    private String status; // UPLOADED, PROCESSING, COMPLETED, ERROR
}
