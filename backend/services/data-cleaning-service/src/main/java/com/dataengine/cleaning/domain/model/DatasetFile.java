package com.dataengine.cleaning.domain.model;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;


@Getter
@Setter
@NoArgsConstructor
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
    private String status;
}
