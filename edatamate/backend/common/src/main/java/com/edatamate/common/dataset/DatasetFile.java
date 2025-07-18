package com.edatamate.common.dataset;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Getter;
import lombok.Setter;
import org.springframework.web.multipart.MultipartFile;

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

    public DatasetFile(MultipartFile file,Long datasetId,String filePath) {
        this.datasetId = datasetId;
        this.name = file.getOriginalFilename();
        this.path = filePath;
        this.size = file.getSize();
        this.type = file.getContentType();
        this.status = "active"; // 默认状态为 active
        this.parentId = 0L; // 默认父级ID为0
        this.sourceFile = file.getOriginalFilename();
    }
}
