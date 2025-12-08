package com.datamate.common.domain.utils;

import com.datamate.common.domain.model.FileUploadResult;
import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import lombok.extern.slf4j.Slf4j;

import org.apache.commons.compress.archivers.ArchiveEntry;
import org.apache.commons.compress.archivers.ArchiveInputStream;
import org.apache.commons.compress.archivers.tar.TarArchiveEntry;
import org.apache.commons.compress.archivers.tar.TarArchiveInputStream;
import org.apache.commons.compress.archivers.zip.ZipArchiveEntry;
import org.apache.commons.compress.archivers.zip.ZipArchiveInputStream;
import org.apache.commons.compress.compressors.gzip.GzipCompressorInputStream;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;

/**
 * Responsible for validating and unpacking archive files.
 *
 * @since 2023-11-17
 */
@Slf4j
public class ArchiveAnalyzer {
    private static final int DEFAULT_BUFFER_SIZE = 4096;

    /**
     * Process list.
     *
     * @param fileDto The uploaded file DTO
     * @return the list
     */
    public static List<FileUploadResult> process(FileUploadResult fileDto) {
        log.info("Start unpacking [{}]", fileDto.getFileName());
        File file = fileDto.getSavedFile();
        Path archivePath;
        try {
            archivePath = Paths.get(file.getCanonicalPath());
        } catch (IOException e) {
            log.error("Failed to get the archive file path.");
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR, "Failed to get the archive file path.");
        }

        List<FileUploadResult> unpacked;
        String extension = AnalyzerUtils.getExtension(fileDto.getFileName());
        if (AnalyzerUtils.TYPE_ZIP.equalsIgnoreCase(extension)) {
            log.info("ZIP unpacking [{}]", fileDto.getFileName());
            unpacked = processZip(archivePath);
            log.info("ZIP unpacking FINISHED [{}]", fileDto.getFileName());
        } else if (AnalyzerUtils.TYPE_TAR_GZ.equalsIgnoreCase(extension)) {
            unpacked = processTarGz(archivePath);
        } else {
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR, "Unrecognized archive format.");
        }

        if (!archivePath.toFile().delete()) {
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR, "Unable to delete the archive file " + archivePath.toAbsolutePath());
        }

        log.info("Finished unpacking [{}]", fileDto.getFileName());
        return unpacked;
    }

    private static List<FileUploadResult> processZip(Path archivePath) {
        try (ArchiveInputStream<ZipArchiveEntry> inputStream = new ZipArchiveInputStream(
            new BufferedInputStream(Files.newInputStream(archivePath)))) {
            return unpackArchive(inputStream, archivePath);
        } catch (IOException e) {
            log.error("Failed to unpack zip archive:", e);
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR, "Failed to unpack zip archive.");
        }
    }

    private static List<FileUploadResult> processTarGz(Path archivePath) {
        try (ArchiveInputStream<TarArchiveEntry> inputStream = new TarArchiveInputStream(
            new GzipCompressorInputStream(new BufferedInputStream(Files.newInputStream(archivePath))),
            StandardCharsets.UTF_8.toString())) {
            return unpackArchive(inputStream, archivePath);
        } catch (IOException e) {
            log.error("Failed to unpack tar.gz archive:", e);
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR, "Failed to unpack tar.gz archive.");
        }
    }

    private static List<FileUploadResult> unpackArchive(ArchiveInputStream<?> archiveInputStream, Path archivePath) throws IOException {
        List<FileUploadResult> unpacked = new ArrayList<>();
        long unpackedSize = 0L;
        try {
            ArchiveEntry archiveEntry;
            int entryCount = 0;
            while ((archiveEntry = archiveInputStream.getNextEntry()) != null) {
                if (isSymlink(archiveEntry)) {
                    // 解压时跳过symlink文件
                    continue;
                }
                entryCount++;
                if (checkUnpackSizeAndFileSize(entryCount, unpacked) || checkVersionSize(unpackedSize, archiveEntry.getSize())) {
                    break;
                }
                if (!archiveEntry.isDirectory()) {
                    unpackedSize = addFileAndCountFileSize(archiveInputStream, archiveEntry, unpacked,
                        unpackedSize, archivePath);
                }
            }
        } catch (IOException e) {
            unpacked.forEach(v -> deleteFile(v.getSavedFile()));
            throw e;
        }

        return unpacked;
    }

    private static boolean checkVersionSize(long unpackedSize, long currFileSize) {
        return false;
    }

    private static long addFileAndCountFileSize(ArchiveInputStream<?> archiveInputStream, ArchiveEntry archiveEntry,
                                         List<FileUploadResult> unpacked, long unpackedSize, Path archivePath) throws IOException {
        Optional<FileUploadResult> uploadFileDto = extractEntity(archiveInputStream, archiveEntry, archivePath);
        long newSize = unpackedSize;
        if (uploadFileDto.isPresent()) {
            FileUploadResult dto = uploadFileDto.get();
            unpacked.add(dto);
            newSize += dto.getSavedFile().length();
        }
        return newSize;
    }

    private static boolean checkUnpackSizeAndFileSize(int entryCount, List<FileUploadResult> unpacked) {
        return false;
    }

    private static Optional<FileUploadResult> extractEntity(ArchiveInputStream<?> archiveInputStream, ArchiveEntry archiveEntry, Path archivePath)
        throws IOException {
        byte[] buffer = new byte[DEFAULT_BUFFER_SIZE];
        Path path = Paths.get(archivePath.getParent().toString(), archiveEntry.getName());
        File file = path.toFile();
        long fileSize = 0L;
        String extension = AnalyzerUtils.getExtension(archiveEntry.getName());

        long supportFileSize = 1024*1024*1024; // 上传大小暂定为1个G
        try (OutputStream outputStream = new BufferedOutputStream(Files.newOutputStream(file.toPath()))) {
            int byteRead;
            while ((byteRead = archiveInputStream.read(buffer)) != -1) {
                outputStream.write(buffer, 0, byteRead);
                fileSize += byteRead;
                if (fileSize > supportFileSize) {
                    break;
                }
            }
        } catch (IOException e) {
            log.error("error happened while write entry to file system");
            file.delete();
            throw e;
        }

        if (fileSize > supportFileSize) {
            // 文件大小超过限制，删除
            log.info("file {} size exceeds limit", archiveEntry.getName());
            file.delete();
            return Optional.empty();
        }
        return Optional.of(FileUploadResult.builder().savedFile(file).fileName(CommonUtils.trimFilePath(archiveEntry.getName())).build());
    }

    private static void deleteFile(File file) {
        Path fileToDeletePath = Paths.get(file.getPath());
        if (Files.exists(fileToDeletePath)) {
            try {
                Files.delete(fileToDeletePath);
            } catch (IOException e1) {
                log.error("Failed to delete file.", e1);
            }
        }
    }

    private static boolean isSymlink(ArchiveEntry archiveEntry) {
        if (archiveEntry instanceof TarArchiveEntry) {
            return ((TarArchiveEntry) archiveEntry).isSymbolicLink();
        }
        return false;
    }
}
