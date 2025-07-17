package com.edatamate.common.dataset;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDateTime;

@Getter
@Setter
@TableName("t_dataset_file")
public class DatasetFile {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long datasetId;

    private String name;

    private String path;

    private Long size;

    private String type;

    private String status;

    private Long parentId;

    private String hash;

    private String sourceFile;

    private LocalDateTime createdTime;

    private LocalDateTime updatedTime;
}
