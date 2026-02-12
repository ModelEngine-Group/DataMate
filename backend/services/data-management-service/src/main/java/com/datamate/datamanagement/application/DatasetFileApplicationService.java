package com.datamate.datamanagement.application;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.datamate.common.domain.model.ChunkUploadPreRequest;
import com.datamate.common.domain.model.FileUploadResult;
import com.datamate.common.domain.service.FileService;
import com.datamate.common.domain.utils.AnalyzerUtils;
import com.datamate.common.domain.utils.ArchiveAnalyzer;
import com.datamate.common.domain.utils.CommonUtils;
import com.datamate.common.infrastructure.exception.BusinessAssert;
import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.infrastructure.exception.CommonErrorCode;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import com.datamate.common.interfaces.PagedResponse;
import com.datamate.common.interfaces.PagingQuery;
import com.datamate.datamanagement.common.enums.DuplicateMethod;
import com.datamate.datamanagement.domain.contants.DatasetConstant;
import com.datamate.datamanagement.domain.model.dataset.Dataset;
import com.datamate.datamanagement.domain.model.dataset.DatasetFile;
import com.datamate.datamanagement.domain.model.dataset.DatasetFileUploadCheckInfo;
import com.datamate.datamanagement.infrastructure.exception.DataManagementErrorCode;
import com.datamate.datamanagement.infrastructure.persistence.repository.DatasetFileRepository;
import com.datamate.datamanagement.infrastructure.persistence.repository.DatasetRepository;
import com.datamate.datamanagement.interfaces.converter.DatasetConverter;
import com.datamate.datamanagement.interfaces.dto.AddFilesRequest;
import com.datamate.datamanagement.interfaces.dto.CreateDirectoryRequest;
import com.datamate.datamanagement.interfaces.dto.UploadFileRequest;
import com.datamate.datamanagement.interfaces.dto.UploadFilesPreRequest;
import com.datamate.datamanagement.interfaces.dto.RenameFileRequest;
import com.datamate.datamanagement.interfaces.dto.RenameDirectoryRequest;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.compress.archivers.zip.ZipArchiveEntry;
import org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream;
import org.apache.commons.io.IOUtils;
import org.apache.commons.lang3.StringUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.net.MalformedURLException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.attribute.BasicFileAttributes;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * 数据集文件应用服务
 */
@Slf4j
@Service
@Transactional
public class DatasetFileApplicationService {

    private final DatasetFileRepository datasetFileRepository;
    private final DatasetRepository datasetRepository;
    private final FileService fileService;

    @Value("${datamate.data-management.base-path:/dataset}")
    private String datasetBasePath;

    @Value("${datamate.data-management.file.duplicate:COVER}")
    private DuplicateMethod duplicateMethod;

    @Autowired
    public DatasetFileApplicationService(DatasetFileRepository datasetFileRepository,
                                         DatasetRepository datasetRepository, FileService fileService) {
        this.datasetFileRepository = datasetFileRepository;
        this.datasetRepository = datasetRepository;
        this.fileService = fileService;
    }

    /**
     * 获取数据集文件列表
     */
    @Transactional(readOnly = true)
    public PagedResponse<DatasetFile> getDatasetFiles(String datasetId, String fileType, String status, String name, PagingQuery pagingQuery) {
        IPage<DatasetFile> page = new Page<>(pagingQuery.getPage(), pagingQuery.getSize());
        IPage<DatasetFile> files = datasetFileRepository.findByCriteria(datasetId, fileType, status, name, page);
        return PagedResponse.of(files);
    }

    /**
     * 获取数据集文件列表
     */
    @Transactional(readOnly = true)
    public PagedResponse<DatasetFile> getDatasetFilesWithDirectory(String datasetId, String prefix, PagingQuery pagingQuery) {
        Dataset dataset = datasetRepository.getById(datasetId);
        int page = Math.max(pagingQuery.getPage(), 1);
        int size = pagingQuery.getSize() == null || pagingQuery.getSize() < 0 ? 20 : pagingQuery.getSize();
        if (dataset == null) {
            return PagedResponse.of(new Page<>(page, size));
        }
        String datasetPath = dataset.getPath();
        Path queryPath = Path.of(dataset.getPath() + File.separator + prefix);
        Map<String, DatasetFile> datasetFilesMap = datasetFileRepository.findAllByDatasetId(datasetId)
            .stream().collect(Collectors.toMap(DatasetFile::getFilePath, Function.identity()));
        try (Stream<Path> pathStream = Files.list(queryPath)) {
            List<Path> allFiles = pathStream
                .filter(path -> path.toString().startsWith(datasetPath))
                .sorted(Comparator
                    .comparing((Path path) -> !Files.isDirectory(path))
                    .thenComparing(path -> path.getFileName().toString()))
                .collect(Collectors.toList());

            // 计算分页
            int total = allFiles.size();
            int totalPages = (int) Math.ceil((double) total / size);

            // 获取当前页数据
            int fromIndex = (page - 1) * size;
            fromIndex = Math.max(fromIndex, 0);
            int toIndex = Math.min(fromIndex + size, total);

            List<Path> pageData = new ArrayList<>();
            if (fromIndex < total) {
                pageData = allFiles.subList(fromIndex, toIndex);
            }
            List<DatasetFile> datasetFiles = pageData.stream().map(path -> getDatasetFile(path, datasetFilesMap)).toList();

            return new PagedResponse<>(page, size, total, totalPages, datasetFiles);
        } catch (IOException e) {
            log.warn("list dataset path error");
            return PagedResponse.of(new Page<>(page, size));
        }
    }

    private DatasetFile getDatasetFile(Path path, Map<String, DatasetFile> datasetFilesMap) {
        DatasetFile datasetFile = new DatasetFile();
        LocalDateTime localDateTime = LocalDateTime.now();
        try {
            localDateTime = Files.getLastModifiedTime(path).toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime();
        } catch (IOException e) {
            log.error("get last modified time error", e);
        }
        datasetFile.setFileName(path.getFileName().toString());
        datasetFile.setUploadTime(localDateTime);

        // 目录与普通文件区分处理
        if (Files.isDirectory(path)) {
            datasetFile.setId("directory-" + datasetFile.getFileName());
            datasetFile.setDirectory(true);

            // 统计目录下文件数量和总大小
            try {
                long fileCount;
                long totalSize;

                try (Stream<Path> walk = Files.walk(path)) {
                    fileCount = walk.filter(Files::isRegularFile).count();
                }

                try (Stream<Path> walk = Files.walk(path)) {
                    totalSize = walk
                        .filter(Files::isRegularFile)
                        .mapToLong(p -> {
                            try {
                                return Files.size(p);
                            } catch (IOException e) {
                                log.error("get file size error", e);
                                return 0L;
                            }
                        })
                        .sum();
                }

                datasetFile.setFileCount(fileCount);
                datasetFile.setFileSize(totalSize);
            } catch (IOException e) {
                log.error("stat directory info error", e);
            }
        } else {
            DatasetFile exist = datasetFilesMap.get(path.toString());
            if (exist == null) {
                datasetFile.setId(datasetFile.getFileName());
                datasetFile.setFileSize(path.toFile().length());
            } else {
                datasetFile = exist;
            }
        }
        return datasetFile;
    }

    /**
     * 获取文件详情
     */
    @Transactional(readOnly = true)
    public DatasetFile getDatasetFile(Dataset dataset, String fileId, String prefix) {
        prefix = StringUtils.isBlank(prefix) ? "" : prefix;
        if (dataset != null && !CommonUtils.isUUID(fileId) && !fileId.startsWith(".") && !prefix.startsWith(".")) {
            DatasetFile file = new DatasetFile();
            file.setId(fileId);
            file.setFileName(fileId);
            file.setDatasetId(dataset.getId());
            file.setFileSize(0L);
            file.setFilePath(dataset.getPath() + File.separator + prefix + fileId);
            return file;
        }
        DatasetFile file = datasetFileRepository.getById(fileId);
        if (file == null || dataset == null) {
            throw new IllegalArgumentException("File not found: " + fileId);
        }
        if (!file.getDatasetId().equals(dataset.getId())) {
            throw new IllegalArgumentException("File does not belong to the specified dataset");
        }
        return file;
    }

    /**
     * 删除文件
     */
    @Transactional
    public void deleteDatasetFile(String datasetId, String fileId, String prefix) {
        Dataset dataset = datasetRepository.getById(datasetId);
        DatasetFile file = getDatasetFile(dataset, fileId, prefix);
        dataset.setFiles(new ArrayList<>(Collections.singleton(file)));
        datasetFileRepository.removeById(fileId);
        if (CommonUtils.isUUID(fileId)) {
            dataset.removeFile(file);
        }
        datasetRepository.updateById(dataset);
        // 删除文件时，上传到数据集中的文件会同时删除数据库中的记录和文件系统中的文件，归集过来的文件仅删除数据库中的记录
        if (file.getFilePath().startsWith(dataset.getPath())) {
            try {
                Path filePath = Paths.get(file.getFilePath());
                Files.deleteIfExists(filePath);
            } catch (IOException ex) {
                throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR);
            }
        }
    }

    /**
     * 下载文件
     */
    @Transactional(readOnly = true)
    public Resource downloadFile(DatasetFile file) {
        try {
            Path filePath = Paths.get(file.getFilePath()).normalize();
            log.info("start download file {}", file.getFilePath());
            Resource resource = new UrlResource(filePath.toUri());
            if (resource.exists()) {
                return resource;
            } else {
                throw new RuntimeException("File not found: " + file.getFileName());
            }
        } catch (MalformedURLException ex) {
            throw new RuntimeException("File not found: " + file.getFileName(), ex);
        }
    }

    /**
     * 下载数据集所有文件为 ZIP
     */
    @Transactional(readOnly = true)
    public void downloadDatasetFileAsZip(String datasetId, HttpServletResponse response) {
        Dataset dataset = datasetRepository.getById(datasetId);
        if (Objects.isNull(dataset)) {
            throw BusinessException.of(DataManagementErrorCode.DATASET_NOT_FOUND);
        }
        String datasetPath = dataset.getPath();
        Path downloadPath = Paths.get(datasetPath).normalize();
        
        // 检查路径是否存在
        if (!Files.exists(downloadPath) || !Files.isDirectory(downloadPath)) {
            throw BusinessException.of(DataManagementErrorCode.DATASET_NOT_FOUND);
        }
        
        response.setContentType("application/zip");
        String zipName = String.format("dataset_%s_%s.zip",
                dataset.getName() != null ? dataset.getName().replaceAll("[^a-zA-Z0-9_-]", "_") : "dataset",
                LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss")));
        response.setHeader(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + zipName + "\"");
        
        try (ZipArchiveOutputStream zos = new ZipArchiveOutputStream(response.getOutputStream())) {
            try (Stream<Path> pathStream = Files.walk(downloadPath)) {
                pathStream
                    .filter(path -> {
                        // 确保路径在数据集目录内，防止路径遍历攻击
                        Path normalized = path.normalize();
                        return normalized.startsWith(downloadPath);
                    })
                    .forEach(path -> {
                        try {
                            addToZipFile(path, downloadPath, zos);
                        } catch (IOException e) {
                            log.error("Failed to add file to zip: {}", path, e);
                        }
                    });
            }
            zos.finish();
        } catch (IOException e) {
            log.error("Failed to download dataset files as zip for dataset {}", datasetId, e);
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR);
        }
    }

    private void addToZipFile(Path path, Path basePath, ZipArchiveOutputStream zos) throws IOException {
        String entryName = basePath.relativize(path)
            .toString()
            .replace(File.separator, "/");

        // 处理目录
        if (Files.isDirectory(path)) {
            if (!entryName.isEmpty()) {
                entryName += "/";
                ZipArchiveEntry dirEntry = new ZipArchiveEntry(entryName);
                zos.putArchiveEntry(dirEntry);
                zos.closeArchiveEntry();
            }
        } else {
            // 处理文件
            ZipArchiveEntry fileEntry = new ZipArchiveEntry(path.toFile(), entryName);

            // 设置更多属性
            BasicFileAttributes attrs = Files.readAttributes(path, BasicFileAttributes.class);
            fileEntry.setSize(attrs.size());
            fileEntry.setLastModifiedTime(attrs.lastModifiedTime());

            zos.putArchiveEntry(fileEntry);

            try (InputStream is = Files.newInputStream(path)) {
                IOUtils.copy(is, zos);
            }
            zos.closeArchiveEntry();
        }
    }

    /**
     * 预上传
     *
     * @param chunkUploadRequest 上传请求
     * @param datasetId          数据集id
     * @return 请求id
     */
    @Transactional
    public String preUpload(UploadFilesPreRequest chunkUploadRequest, String datasetId) {
        if (Objects.isNull(datasetRepository.getById(datasetId))) {
            throw BusinessException.of(DataManagementErrorCode.DATASET_NOT_FOUND);
        }
        
        // 构建上传路径，如果有 prefix 则追加到路径中
        String prefix = Optional.ofNullable(chunkUploadRequest.getPrefix()).orElse("").trim();
        prefix = prefix.replace("\\", "/");
        while (prefix.startsWith("/")) {
            prefix = prefix.substring(1);
        }
        
        String uploadPath = datasetBasePath + File.separator + datasetId;
        if (!prefix.isEmpty()) {
            uploadPath = uploadPath + File.separator + prefix.replace("/", File.separator);
        }
        
        ChunkUploadPreRequest request = ChunkUploadPreRequest.builder().build();
        request.setUploadPath(uploadPath);
        request.setTotalFileNum(chunkUploadRequest.getTotalFileNum());
        request.setServiceId(DatasetConstant.SERVICE_ID);
        DatasetFileUploadCheckInfo checkInfo = new DatasetFileUploadCheckInfo();
        checkInfo.setDatasetId(datasetId);
        checkInfo.setHasArchive(chunkUploadRequest.isHasArchive());
        checkInfo.setPrefix(prefix);
        try {
            ObjectMapper objectMapper = new ObjectMapper();
            String checkInfoJson = objectMapper.writeValueAsString(checkInfo);
            request.setCheckInfo(checkInfoJson);
        } catch (JsonProcessingException e) {
            log.warn("Failed to serialize checkInfo to JSON", e);
        }
        return fileService.preUpload(request);
    }

    /**
     * 切片上传
     *
     * @param uploadFileRequest 上传请求
     */
    @Transactional
    public void chunkUpload(String datasetId, UploadFileRequest uploadFileRequest) {
        FileUploadResult uploadResult = fileService.chunkUpload(DatasetConverter.INSTANCE.toChunkUploadRequest(uploadFileRequest));
        saveFileInfoToDb(uploadResult, datasetId);
    }

    private void saveFileInfoToDb(FileUploadResult fileUploadResult, String datasetId) {
        if (Objects.isNull(fileUploadResult.getSavedFile())) {
            // 文件切片上传没有完成
            return;
        }
        DatasetFileUploadCheckInfo checkInfo;
        try {
            ObjectMapper objectMapper = new ObjectMapper();
            checkInfo = objectMapper.readValue(fileUploadResult.getCheckInfo(), DatasetFileUploadCheckInfo.class);
            if (!Objects.equals(checkInfo.getDatasetId(), datasetId)) {
                throw BusinessException.of(DataManagementErrorCode.DATASET_NOT_FOUND);
            }
        } catch (IllegalArgumentException | JsonProcessingException e) {
            log.warn("Failed to convert checkInfo to DatasetFileUploadCheckInfo", e);
            throw BusinessException.of(CommonErrorCode.PRE_UPLOAD_REQUEST_NOT_EXIST);
        }
        List<FileUploadResult> files;
        if (checkInfo.isHasArchive() && AnalyzerUtils.isPackage(fileUploadResult.getSavedFile().getPath())) {
            files = ArchiveAnalyzer.process(fileUploadResult);
        } else {
            files = Collections.singletonList(fileUploadResult);
        }
        addFileToDataset(datasetId, files);
    }

    private void addFileToDataset(String datasetId, List<FileUploadResult> unpacked) {
        Dataset dataset = datasetRepository.getById(datasetId);
        dataset.setFiles(datasetFileRepository.findAllByDatasetId(datasetId));
        for (FileUploadResult file : unpacked) {
            File savedFile = file.getSavedFile();
            LocalDateTime currentTime = LocalDateTime.now();
            // 统一 fileName：无论是否通过文件夹/压缩包上传，都只保留纯文件名
            String originalFileName = file.getFileName();
            String baseFileName = originalFileName;
            if (originalFileName != null) {
                String normalized = originalFileName.replace("\\", "/");
                int lastSlash = normalized.lastIndexOf('/');
                if (lastSlash >= 0 && lastSlash + 1 < normalized.length()) {
                    baseFileName = normalized.substring(lastSlash + 1);
                }
            }
            DatasetFile datasetFile = DatasetFile.builder()
                .id(UUID.randomUUID().toString())
                .datasetId(datasetId)
                .fileSize(savedFile.length())
                .uploadTime(currentTime)
                .lastAccessTime(currentTime)
                .fileName(baseFileName)
                .filePath(savedFile.getPath())
                .fileType(AnalyzerUtils.getExtension(file.getFileName()))
                .build();
            setDatasetFileId(datasetFile, dataset);
            datasetFileRepository.saveOrUpdate(datasetFile);
            dataset.addFile(datasetFile);
        }
        dataset.active();
        datasetRepository.updateById(dataset);
    }

    /**
     * 在数据集下创建子目录
     */
    @Transactional
    public void createDirectory(String datasetId, CreateDirectoryRequest req) {
        Dataset dataset = datasetRepository.getById(datasetId);
        if (dataset == null) {
            throw BusinessException.of(DataManagementErrorCode.DATASET_NOT_FOUND);
        }
        String datasetPath = dataset.getPath();
        String parentPrefix = Optional.ofNullable(req.getParentPrefix()).orElse("").trim();
        parentPrefix = parentPrefix.replace("\\", "/");
        while (parentPrefix.startsWith("/")) {
            parentPrefix = parentPrefix.substring(1);
        }

        String directoryName = Optional.ofNullable(req.getDirectoryName()).orElse("").trim();
        if (directoryName.isEmpty()) {
            throw BusinessException.of(CommonErrorCode.PARAM_ERROR);
        }
        if (directoryName.contains("..") || directoryName.contains("/") || directoryName.contains("\\")) {
            throw BusinessException.of(CommonErrorCode.PARAM_ERROR);
        }

        Path basePath = Paths.get(datasetPath);
        Path targetPath = parentPrefix.isEmpty()
            ? basePath.resolve(directoryName)
            : basePath.resolve(parentPrefix).resolve(directoryName);

        Path normalized = targetPath.normalize();
        if (!normalized.startsWith(basePath)) {
            throw BusinessException.of(CommonErrorCode.PARAM_ERROR);
        }

        try {
            Files.createDirectories(normalized);
        } catch (IOException e) {
            log.error("Failed to create directory {} for dataset {}", normalized, datasetId, e);
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR);
        }
    }

    /**
     * 下载目录为 ZIP 文件
     */
    @Transactional(readOnly = true)
    public void downloadDirectory(String datasetId, String prefix, HttpServletResponse response) {
        Dataset dataset = datasetRepository.getById(datasetId);
        if (dataset == null) {
            throw BusinessException.of(DataManagementErrorCode.DATASET_NOT_FOUND);
        }

        String datasetPath = dataset.getPath();
        prefix = Optional.ofNullable(prefix).orElse("").trim();
        prefix = prefix.replace("\\", "/");
        while (prefix.startsWith("/")) {
            prefix = prefix.substring(1);
        }
        while (prefix.endsWith("/")) {
            prefix = prefix.substring(0, prefix.length() - 1);
        }

        Path basePath = Paths.get(datasetPath);
        Path targetPath = prefix.isEmpty() ? basePath : basePath.resolve(prefix);
        Path normalized = targetPath.normalize();

        if (!normalized.startsWith(basePath)) {
            throw BusinessException.of(CommonErrorCode.PARAM_ERROR);
        }

        if (!Files.exists(normalized) || !Files.isDirectory(normalized)) {
            throw BusinessException.of(DataManagementErrorCode.DIRECTORY_NOT_FOUND);
        }

        String zipFileName = prefix.isEmpty() ? dataset.getName() : prefix.replace("/", "_");
        zipFileName = zipFileName + "_" + LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss")) + ".zip";

        try {
            response.setContentType("application/zip");
            response.setHeader(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + zipFileName + "\"");
            
            try (ZipArchiveOutputStream zipOut = new ZipArchiveOutputStream(response.getOutputStream())) {
                zipDirectory(normalized, normalized, zipOut);
                zipOut.finish();
            }
        } catch (IOException e) {
            log.error("Failed to download directory {} for dataset {}", normalized, datasetId, e);
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR);
        }
    }

    /**
     * 递归压缩目录
     */
    private void zipDirectory(Path sourceDir, Path basePath, ZipArchiveOutputStream zipOut) throws IOException {
        try (Stream<Path> paths = Files.walk(sourceDir)) {
            paths.filter(path -> !Files.isDirectory(path))
                .forEach(path -> {
                    try {
                        Path relativePath = basePath.relativize(path);
                        ZipArchiveEntry zipEntry = new ZipArchiveEntry(relativePath.toString());
                        zipOut.putArchiveEntry(zipEntry);
                        try (InputStream fis = Files.newInputStream(path)) {
                            IOUtils.copy(fis, zipOut);
                        }
                        zipOut.closeArchiveEntry();
                    } catch (IOException e) {
                        log.error("Failed to add file to zip: {}", path, e);
                    }
                });
        }
    }

    /**
     * 删除目录及其所有内容
     */
    @Transactional
    public void deleteDirectory(String datasetId, String prefix) {
        Dataset dataset = datasetRepository.getById(datasetId);
        if (dataset == null) {
            throw BusinessException.of(DataManagementErrorCode.DATASET_NOT_FOUND);
        }

        prefix = Optional.ofNullable(prefix).orElse("").trim();
        prefix = prefix.replace("\\", "/");
        while (prefix.startsWith("/")) {
            prefix = prefix.substring(1);
        }
        while (prefix.endsWith("/")) {
            prefix = prefix.substring(0, prefix.length() - 1);
        }

        if (prefix.isEmpty()) {
            throw BusinessException.of(CommonErrorCode.PARAM_ERROR);
        }

        String datasetPath = dataset.getPath();
        Path basePath = Paths.get(datasetPath);
        Path targetPath = basePath.resolve(prefix);
        Path normalized = targetPath.normalize();

        if (!normalized.startsWith(basePath)) {
            throw BusinessException.of(CommonErrorCode.PARAM_ERROR);
        }

        if (!Files.exists(normalized) || !Files.isDirectory(normalized)) {
            throw BusinessException.of(DataManagementErrorCode.DIRECTORY_NOT_FOUND);
        }

        // 删除数据库中该目录下的所有文件记录（基于数据集内相对路径判断）
        String datasetPathNorm = datasetPath.replace("\\", "/");
        String logicalPrefix = prefix; // 已经去掉首尾斜杠
        List<DatasetFile> filesToDelete = datasetFileRepository.findAllByDatasetId(datasetId).stream()
            .filter(file -> {
                if (file.getFilePath() == null) {
                    return false;
                }
                String filePath = file.getFilePath().replace("\\", "/");
                if (!filePath.startsWith(datasetPathNorm)) {
                    return false;
                }
                String relative = filePath.substring(datasetPathNorm.length());
                while (relative.startsWith("/")) {
                    relative = relative.substring(1);
                }
                return relative.equals(logicalPrefix) || relative.startsWith(logicalPrefix + "/");
            })
            .collect(Collectors.toList());

        for (DatasetFile file : filesToDelete) {
            datasetFileRepository.removeById(file.getId());
        }

        // 删除文件系统中的目录
        try {
            deleteDirectoryRecursively(normalized);
        } catch (IOException e) {
            log.error("Failed to delete directory {} for dataset {}", normalized, datasetId, e);
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR);
        }

        // 更新数据集
        dataset.setFiles(filesToDelete);
        for (DatasetFile file : filesToDelete) {
            dataset.removeFile(file);
        }
        datasetRepository.updateById(dataset);
    }

    /**
     * 重命名数据集文件（仅允许修改主名称，文件后缀保持不变）
     */
    @Transactional
    public void renameFile(String datasetId, String fileId, RenameFileRequest request) {
        Dataset dataset = datasetRepository.getById(datasetId);
        if (dataset == null) {
            throw BusinessException.of(DataManagementErrorCode.DATASET_NOT_FOUND);
        }

        DatasetFile file = getDatasetFile(dataset, fileId, null);
        String newName = Optional.ofNullable(request.getNewName()).orElse("").trim();
        if (newName.isEmpty()) {
            throw BusinessException.of(CommonErrorCode.PARAM_ERROR);
        }

        String originalFileName = file.getFileName();
        String extension = "";
        int dotIndex = originalFileName.lastIndexOf('.');
        if (dotIndex > 0 && dotIndex < originalFileName.length() - 1) {
            extension = originalFileName.substring(dotIndex); // 包含点号，如 .jpg
        }

        // 只接收主名称，后缀始终使用原始后缀
        String finalFileName = newName + extension;

        Path oldPath = Paths.get(file.getFilePath()).normalize();
        Path basePath = Paths.get(dataset.getPath()).normalize();

        // 仅允许重命名数据集自身目录下的文件
        if (!oldPath.startsWith(basePath)) {
            throw BusinessException.of(CommonErrorCode.PARAM_ERROR);
        }

        Path parentDir = oldPath.getParent();
        if (parentDir == null) {
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR);
        }
        Path newPath = parentDir.resolve(finalFileName).normalize();

        if (!newPath.startsWith(basePath)) {
            throw BusinessException.of(CommonErrorCode.PARAM_ERROR);
        }

        if (Files.exists(newPath)) {
            throw BusinessException.of(DataManagementErrorCode.DATASET_FILE_ALREADY_EXISTS);
        }

        try {
            Files.move(oldPath, newPath);
        } catch (IOException e) {
            log.error("Failed to rename file from {} to {}", oldPath, newPath, e);
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR);
        }

        file.setFileName(finalFileName);
        file.setFilePath(newPath.toString());
        file.setFileType(AnalyzerUtils.getExtension(finalFileName));
        file.setLastAccessTime(LocalDateTime.now());
        datasetFileRepository.updateById(file);
    }

    /**
     * 重命名目录
     */
    @Transactional
    public void renameDirectory(String datasetId, RenameDirectoryRequest request) {
        Dataset dataset = datasetRepository.getById(datasetId);
        if (dataset == null) {
            throw BusinessException.of(DataManagementErrorCode.DATASET_NOT_FOUND);
        }

        String prefix = Optional.ofNullable(request.getPrefix()).orElse("").trim();
        prefix = prefix.replace("\\", "/");
        while (prefix.startsWith("/")) {
            prefix = prefix.substring(1);
        }
        while (prefix.endsWith("/")) {
            prefix = prefix.substring(0, prefix.length() - 1);
        }

        if (prefix.isEmpty()) {
            throw BusinessException.of(CommonErrorCode.PARAM_ERROR);
        }

        String newName = Optional.ofNullable(request.getNewName()).orElse("").trim();
        if (newName.isEmpty() || newName.contains("..") || newName.contains("/") || newName.contains("\\")) {
            throw BusinessException.of(CommonErrorCode.PARAM_ERROR);
        }

        String datasetPath = dataset.getPath();
        Path basePath = Paths.get(datasetPath).normalize();
        Path oldDir = basePath.resolve(prefix).normalize();

        if (!oldDir.startsWith(basePath)) {
            throw BusinessException.of(CommonErrorCode.PARAM_ERROR);
        }

        if (!Files.exists(oldDir) || !Files.isDirectory(oldDir)) {
            throw BusinessException.of(DataManagementErrorCode.DIRECTORY_NOT_FOUND);
        }

        Path parentDir = oldDir.getParent();
        if (parentDir == null) {
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR);
        }
        Path newDir = parentDir.resolve(newName).normalize();

        if (!newDir.startsWith(basePath)) {
            throw BusinessException.of(CommonErrorCode.PARAM_ERROR);
        }

        if (Files.exists(newDir)) {
            throw BusinessException.of(DataManagementErrorCode.DIRECTORY_NOT_FOUND);
        }

        try {
            Files.move(oldDir, newDir);
        } catch (IOException e) {
            log.error("Failed to rename directory from {} to {}", oldDir, newDir, e);
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR);
        }

        // 同步更新数据库中该目录下所有文件的 filePath
        String oldDirPath = oldDir.toString().replace("\\", "/");
        String newDirPath = newDir.toString().replace("\\", "/");

        List<DatasetFile> allFiles = datasetFileRepository.findAllByDatasetId(datasetId);
        for (DatasetFile file : allFiles) {
            String filePath = Optional.ofNullable(file.getFilePath()).orElse("").replace("\\", "/");
            if (filePath.startsWith(oldDirPath + "/")) {
                String relative = filePath.substring(oldDirPath.length() + 1);
                Path updatedPath = Paths.get(newDirPath).resolve(relative);
                file.setFilePath(updatedPath.toString());
                file.setLastAccessTime(LocalDateTime.now());
                datasetFileRepository.updateById(file);
            }
        }
    }

    /**
     * 递归删除目录
     */
    private void deleteDirectoryRecursively(Path directory) throws IOException {
        try (Stream<Path> paths = Files.walk(directory)) {
            paths.sorted(Comparator.reverseOrder())
                .forEach(path -> {
                    try {
                        Files.delete(path);
                    } catch (IOException e) {
                        log.error("Failed to delete: {}", path, e);
                    }
                });
        }
    }

    /**
     * 为数据集文件设置文件id
     *
     * @param datasetFile 要设置id的文件
     * @param dataset 数据集（包含文件列表）
     */
    private void setDatasetFileId(DatasetFile datasetFile, Dataset dataset) {
        Map<String, DatasetFile> existDatasetFilMap = dataset.getFiles().stream().collect(Collectors.toMap(DatasetFile::getFilePath, Function.identity()));
        DatasetFile existDatasetFile = existDatasetFilMap.get(datasetFile.getFilePath());
        if (Objects.isNull(existDatasetFile)) {
            return;
        }
        if (duplicateMethod == DuplicateMethod.ERROR) {
            log.error("file {} already exists in dataset {}", datasetFile.getFileName(), datasetFile.getDatasetId());
            throw BusinessException.of(DataManagementErrorCode.DATASET_FILE_ALREADY_EXISTS);
        }
        if (duplicateMethod == DuplicateMethod.COVER) {
            dataset.removeFile(existDatasetFile);
            datasetFile.setId(existDatasetFile.getId());
        }
    }

    /**
     * 添加文件到数据集（仅创建数据库记录，不执行文件系统操作）
     *
     * @param datasetId 数据集id
     * @param req       添加文件请求
     * @return 添加的文件列表
     */
    @Transactional
    public List<DatasetFile> addFilesToDataset(String datasetId, AddFilesRequest req) {
        if (!req.isValidPrefix()) {
            throw BusinessException.of(DataManagementErrorCode.DIRECTORY_NOT_FOUND);
        }
        Dataset dataset = datasetRepository.getById(datasetId);
        BusinessAssert.notNull(dataset, SystemErrorCode.RESOURCE_NOT_FOUND);
        List<DatasetFile> addedFiles = new ArrayList<>();
        List<DatasetFile> existDatasetFiles = datasetFileRepository.findAllByDatasetId(datasetId);
        dataset.setFiles(existDatasetFiles);
        try {
            ObjectMapper objectMapper = new ObjectMapper();

            for (AddFilesRequest.FileRequest file : req.getFiles()) {
                DatasetFile datasetFile = getDatasetFileForAdd(req, file, dataset, objectMapper);
                setDatasetFileId(datasetFile, dataset);
                dataset.addFile(datasetFile);
                addedFiles.add(datasetFile);
                addFile(file.getFilePath(), datasetFile.getFilePath(), req.isSoftAdd());
            }
        } catch (BusinessException e) {
            throw e;
        } catch (Exception e) {
            log.error("Failed to add file to dataset {}", dataset.getName(), e);
            throw BusinessException.of(SystemErrorCode.UNKNOWN_ERROR);
        }

        datasetFileRepository.saveOrUpdateBatch(addedFiles, 100);
        dataset.active();
        datasetRepository.updateById(dataset);
        return addedFiles;
    }

    private void addFile(String sourPath, String targetPath, boolean softAdd) {
        if (StringUtils.isBlank(sourPath) || StringUtils.isBlank(targetPath)) {
            return;
        }
        Path source = Paths.get(sourPath).normalize();
        Path target = Paths.get(targetPath).normalize();

        // 检查源文件是否存在且为普通文件
        if (!Files.exists(source) || !Files.isRegularFile(source)) {
            log.warn("Source file does not exist or is not a regular file: {}", sourPath);
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR);
        }

        try {
            Path parent = target.getParent();
            // 创建目标目录（如果需要）
            if (parent != null) {
                Files.createDirectories(parent);
            }
            Files.deleteIfExists(target);
            if (softAdd) {
                // 优先尝试创建硬链接，失败后尝试创建符号链接；若均失败抛出异常
                try {
                    Files.createLink(target, source);
                    return;
                } catch (Throwable hardEx) {
                    log.warn("create hard link failed from {} to {}: {}", source, target, hardEx.getMessage());
                }
                Files.createSymbolicLink(target, source);
            } else {
                // 覆盖已存在的目标文件，保持与其他地方行为一致
                Files.copy(source, target);
            }
        } catch (IOException e) {
            log.error("Failed to add file from {} to {}", source, target, e);
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR);
        }
    }

    private static DatasetFile getDatasetFileForAdd(AddFilesRequest req, AddFilesRequest.FileRequest file,
                                                    Dataset dataset, ObjectMapper objectMapper) throws JsonProcessingException {
        Path sourcePath = Paths.get(file.getFilePath());
        File sourceFile = sourcePath.toFile();
        file.getMetadata().put("softAdd", req.isSoftAdd());
        LocalDateTime currentTime = LocalDateTime.now();
        String fileName = sourcePath.getFileName().toString();

        return DatasetFile.builder()
                .id(UUID.randomUUID().toString())
                .datasetId(dataset.getId())
                .fileName(fileName)
                .fileType(AnalyzerUtils.getExtension(fileName))
                .fileSize(sourceFile.length())
                .filePath(Paths.get(dataset.getPath(), req.getPrefix(), fileName).toString())
                .uploadTime(currentTime)
                .lastAccessTime(currentTime)
                .metadata(objectMapper.writeValueAsString(file.getMetadata()))
                .build();
    }
}
