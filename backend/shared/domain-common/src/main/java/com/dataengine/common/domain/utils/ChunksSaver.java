package com.dataengine.common.domain.utils;

import com.dataengine.common.domain.model.ChunkUploadPreRequest;
import com.dataengine.common.domain.model.ChunkUploadRequest;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.io.FileUtils;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;
import java.util.Locale;
import java.util.Optional;

@Slf4j
public class ChunksSaver {
    /**
     * 分片保存的临时目录
     */
    public static final String TEMP_DIR_NAME_FORMAT = "req_%s_chunks";

    /**
     * 保存分片
     *
     * @param fileUploadRequest 上传分片的请求
     * @param preUploadReq 上传文件的请求
     * @return 保存后完整的文件
     */
    public static Optional<File> save(ChunkUploadRequest fileUploadRequest, ChunkUploadPreRequest preUploadReq) {
        Path uploadPath = Paths.get(preUploadReq.getUploadPath(),
            String.format(TEMP_DIR_NAME_FORMAT, preUploadReq.getId()));
        LocalDateTime startTime = LocalDateTime.now();
        // 临时文件名为文件序号
        File targetFile = new File(uploadPath.toString(), String.valueOf(fileUploadRequest.getFileNo()));

        // 追加分片到目标文件末尾
        appendToTargetFile(targetFile, getFileInputStream(fileUploadRequest.getFile()));

        // 判断是否分片已经全部上传，全部上传后将重组文件移动到指定路径，否则返回空
        if (fileUploadRequest.getTotalChunkNum() != fileUploadRequest.getChunkNo()) {
            log.debug("save chunk {} cost {}", fileUploadRequest.getChunkNo(),
                ChronoUnit.MILLIS.between(startTime, LocalDateTime.now()));
            return Optional.empty();
        }

        File finalFile = new File(preUploadReq.getUploadPath(), fileUploadRequest.getFileName());
        if (!targetFile.renameTo(finalFile)) {
            log.error("failed to mv file:{}, req Id:{}", targetFile.getName(), fileUploadRequest.getReqId());
            throw new IllegalArgumentException("failed to move file to target dir");
        }
        log.debug("save chunk {} cost {}", fileUploadRequest.getChunkNo(),
            ChronoUnit.MILLIS.between(startTime, LocalDateTime.now()));
        return Optional.of(finalFile);
    }

    private static InputStream getFileInputStream(MultipartFile file) {
        try {
            return file.getInputStream();
        } catch (IOException e) {
            log.error("get uploaded file input stream failed", e);
            throw new IllegalArgumentException();
        }
    }

    /**
     * 保存文件
     *
     * @param fileUploadRequest 上传分片的请求
     * @param preUploadReq      上传文件的请求
     */
    public static File saveFile(ChunkUploadRequest fileUploadRequest, ChunkUploadPreRequest preUploadReq) {
        // 保存文件
        File targetFile = new File(preUploadReq.getUploadPath(), fileUploadRequest.getFileName());
        try {
            log.info("file path {}, file size {}", targetFile.toPath(), targetFile.getTotalSpace());
            FileUtils.copyInputStreamToFile(getFileInputStream(fileUploadRequest.getFile()), targetFile);
        } catch (IOException e) {
            throw new IllegalArgumentException();
        }
        return targetFile;
    }

    /**
     * 追加分片到文件末尾
     *
     * @param targetFile 目标文件
     * @param inputStream file stream
     */
    public static void appendToTargetFile(File targetFile, InputStream inputStream) {
        try {
            byte[] buffer = new byte[1024 * 1024];
            int byteRead;
            while ((byteRead = inputStream.read(buffer)) != -1) {
                FileUtils.writeByteArrayToFile(targetFile, buffer, 0, byteRead, true);
            }
        } catch (IOException e) {
            throw new IllegalArgumentException();
        }
    }

    /**
     * 删除指定路径下的所有文件
     *
     * @param uploadPath 文件路径
     */
    public static void deleteFiles(String uploadPath) {
        File dic = new File(uploadPath);
        if (!dic.exists()) {
            return;
        }
        File[] files = dic.listFiles();
        if (files == null || files.length == 0) {
            dic.delete();
            return;
        }
        try {
            for (File file : files) {
                if (file.isDirectory()) {
                    deleteFiles(file.getPath());
                } else {
                    file.delete();
                }
            }
            if (dic.exists()) {
                dic.delete();
            }
        } catch (SecurityException e) {
            log.warn("Fail to delete file", e);
        }
    }
}
