package com.dataengine.common.domain.service;

import com.dataengine.common.domain.model.ChunkUploadPreRequest;
import com.dataengine.common.domain.model.ChunkUploadRequest;
import com.dataengine.common.domain.model.FileUploadResult;
import com.dataengine.common.domain.utils.ChunksSaver;
import com.dataengine.common.infrastructure.mapper.ChunkUploadRequestMapper;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.io.File;
import java.time.LocalDateTime;
import java.util.Objects;
import java.util.Optional;
import java.util.UUID;

/**
 * 文件服务
 */
@Component
public class FileService {
    private static final int DEFAULT_TIMEOUT = 120;

    private final ChunkUploadRequestMapper chunkUploadRequestMapper;

    public FileService(ChunkUploadRequestMapper chunkUploadRequestMapper) {
        this.chunkUploadRequestMapper = chunkUploadRequestMapper;
    }

    /**
     * 预上传
     */
    @Transactional
    public String preUpload(ChunkUploadPreRequest chunkUploadPreRequest) {
        chunkUploadPreRequest.setId(UUID.randomUUID().toString());
        chunkUploadPreRequest.setTimeout(LocalDateTime.now().plusSeconds(DEFAULT_TIMEOUT));
        chunkUploadRequestMapper.insert(chunkUploadPreRequest);
        return chunkUploadPreRequest.getId();
    }

    /**
     * 切片上传
     */
    @Transactional
    public FileUploadResult chunkUpload(ChunkUploadRequest uploadFileRequest) {
        uploadFileRequest.setFileSize(uploadFileRequest.getFile().getSize());
        ChunkUploadPreRequest preRequest = chunkUploadRequestMapper.findById(uploadFileRequest.getReqId());
        if (preRequest == null || preRequest.isUploadComplete() || preRequest.isRequestTimeout()) {
            throw new IllegalArgumentException("预上传请求不存在");
        }
        File savedFile;
        if (uploadFileRequest.getTotalChunkNum() > 1) {
            savedFile = uploadChunk(uploadFileRequest, preRequest);
        } else {
            savedFile = uploadFile(uploadFileRequest, preRequest);
        }
        if (chunkUploadRequestMapper.update(preRequest) == 0) {
            throw new IllegalArgumentException("预上传请求不存在");
        }
        boolean isFinish = Objects.equals(preRequest.getUploadedFileNum(), preRequest.getTotalFileNum());
        if (isFinish) {
            // 删除存分片的临时路径
            ChunksSaver.deleteFiles(new File(preRequest.getUploadPath(),
                String.format(ChunksSaver.TEMP_DIR_NAME_FORMAT, preRequest.getId())).getPath());
            chunkUploadRequestMapper.deleteById(preRequest.getId());
        }
        return FileUploadResult.builder()
            .isAllFilesUploaded(isFinish)
            .checkInfo(preRequest.getCheckInfo())
            .savedFile(savedFile)
            .fileName(uploadFileRequest.getFileName())
            .build();
    }

    private File uploadFile(ChunkUploadRequest fileUploadRequest, ChunkUploadPreRequest preRequest) {
        File savedFile = ChunksSaver.saveFile(fileUploadRequest, preRequest);
        preRequest.setTimeout(LocalDateTime.now().plusSeconds(DEFAULT_TIMEOUT));
        preRequest.incrementUploadedFileNum();
        return savedFile;
    }

    private File uploadChunk(ChunkUploadRequest fileUploadRequest, ChunkUploadPreRequest preRequest) {
        Optional<File> savedFile = ChunksSaver.save(fileUploadRequest, preRequest);
        if (savedFile.isPresent()) {
            preRequest.incrementUploadedFileNum();
            return savedFile.get();
        }
        preRequest.setTimeout(LocalDateTime.now().plusSeconds(DEFAULT_TIMEOUT));
        return null;
    }
}
