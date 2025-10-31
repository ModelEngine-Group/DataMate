package com.datamate.datamanagement.domain.model.dataset;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.*;
import org.apache.commons.lang3.StringUtils;

import java.time.LocalDateTime;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/**
 * 数据集文件实体（与数据库表 t_dm_dataset_files 对齐）
 */
@Getter
@Setter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@TableName("t_dm_dataset_files")
public class DatasetFile {
    @TableId
    private String id; // UUID
    private String datasetId; // UUID
    private String fileName;
    private String filePath;
    private String fileType; // JPG/PNG/DCM/TXT
    private Long fileSize; // bytes
    private String checkSum;
    private String tags;
    private String metadata;
    private String status; // UPLOADED, PROCESSING, COMPLETED, ERROR
    private LocalDateTime uploadTime;
    private LocalDateTime lastAccessTime;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    /**
     * 解析标签
     *
     * @return 标签列表
     */
    public List<String> analyzeTag() {
        try {
            ObjectMapper mapper = new ObjectMapper();
            return mapper.readValue(tags, List.class);
        } catch (Exception e) {
            return Collections.emptyList();
        }
    }
}
