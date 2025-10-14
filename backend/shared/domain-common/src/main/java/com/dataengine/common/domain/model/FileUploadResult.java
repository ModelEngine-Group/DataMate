package com.dataengine.common.domain.model;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

import java.io.File;

@Getter
@Setter
@Builder
public class FileUploadResult {
    /** 切片是否已经全部上传 */
    boolean isAllFilesUploaded;

    /** 业务上传信息 */
    String checkInfo;

    /** 保存的文件 */
    File savedFile;

    /** 真实文件名 */
    String fileName;
}
