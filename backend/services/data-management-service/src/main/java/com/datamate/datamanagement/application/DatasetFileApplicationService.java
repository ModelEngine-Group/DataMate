package com.datamate.datamanagement.application;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.datamate.common.domain.model.ChunkUploadPreRequest;
import com.datamate.common.domain.model.FileUploadResult;
import com.datamate.common.domain.service.FileService;
import com.datamate.common.domain.utils.AnalyzerUtils;
import com.datamate.common.domain.utils.ArchiveAnalyzer;
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
import com.datamate.datamanagement.interfaces.dto.CopyFilesRequest;
import com.datamate.datamanagement.interfaces.dto.CreateDirectoryRequest;
import com.datamate.datamanagement.interfaces.dto.UploadFileRequest;
import com.datamate.datamanagement.interfaces.dto.UploadFilesPreRequest;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.compress.archivers.zip.ZipArchiveEntry;
import org.apache.commons.compress.archivers.zip.ZipArchiveOutputStream;
import org.apache.commons.io.IOUtils;
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
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.attribute.BasicFileAttributes;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.CompletableFuture;
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
        List<DatasetFile> datasetFiles = datasetFileRepository.findAllByDatasetId(datasetId);
        Map<String, DatasetFile> datasetFilesMap = datasetFiles
            .stream()
            .collect(Collectors.toMap(DatasetFile::getFilePath, Function.identity()));
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
            List<DatasetFile> datasetFilesPage = pageData.stream()
                .map(path -> getDatasetFile(path, datasetFilesMap, datasetFiles))
                .toList();

            return new PagedResponse<>(page, size, total, totalPages, datasetFilesPage);
        } catch (IOException e) {
            log.error("list dataset path error", e);
            return PagedResponse.of(new Page<>(page, size));
        }
    }

    private DatasetFile getDatasetFile(Path path, Map<String, DatasetFile> datasetFilesMap, List<DatasetFile> allDatasetFiles) {
        DatasetFile datasetFile = new DatasetFile();
        LocalDateTime localDateTime = LocalDateTime.now();
        try {
            localDateTime = Files.getLastModifiedTime(path).toInstant().atZone(ZoneId.systemDefault()).toLocalDateTime();
        } catch (IOException e) {
            log.error("get last modified time error", e);
        }
        datasetFile.setFileName(path.getFileName().toString());
        datasetFile.setUploadTime(localDateTime);
        datasetFile.setFilePath(path.toString());
        if (Files.isDirectory(path)) {
            datasetFile.setId(encodeDirectoryId(path));
            datasetFile.setDirectory(true);
            datasetFile.setFileType("DIRECTORY");
            // Prefer filesystem walk to ensure we show real counts/sizes even if DB is missing entries
            try (Stream<Path> walk = Files.walk(path)) {
                long fileCount = walk.filter(Files::isRegularFile).count();
                datasetFile.setFileCount(fileCount);
            } catch (IOException e) {
                log.warn("Failed to count files under directory {}", path, e);
            }
            try (Stream<Path> walk = Files.walk(path)) {
                long fileSize = walk.filter(Files::isRegularFile)
                    .mapToLong(p -> {
                        try {
                            return Files.size(p);
                        } catch (IOException e) {
                            log.warn("Failed to read size for {}", p, e);
                            return 0L;
                        }
                    })
                    .sum();
                datasetFile.setFileSize(fileSize);
            } catch (IOException e) {
                log.warn("Failed to sum sizes under directory {}", path, e);
            }
        } else if (Objects.isNull(datasetFilesMap.get(path.toString()))) {
            datasetFile.setId("file-" + datasetFile.getFileName());
            datasetFile.setFileSize(path.toFile().length());
            datasetFile.setDirectory(false);
        } else {
            datasetFile = datasetFilesMap.get(path.toString());
            datasetFile.setDirectory(false);
        }
        return datasetFile;
    }

    /**
     * 获取文件详情
     */
    @Transactional(readOnly = true)
    public DatasetFile getDatasetFile(String datasetId, String fileId) {
        DatasetFile file = datasetFileRepository.getById(fileId);
        if (file == null) {
            throw new IllegalArgumentException("File not found: " + fileId);
        }
        if (!file.getDatasetId().equals(datasetId)) {
            throw new IllegalArgumentException("File does not belong to the specified dataset");
        }
        return file;
    }

    /**
     * 删除文件
     */
    @Transactional
    public void deleteDatasetFile(String datasetId, String fileId) {
        if (isDirectoryId(fileId)) {
            deleteDirectory(datasetId, fileId);
            return;
        }
        DatasetFile file = getDatasetFile(datasetId, fileId);
        Dataset dataset = datasetRepository.getById(datasetId);
        dataset.setFiles(new ArrayList<>(Collections.singleton(file)));
        datasetFileRepository.removeById(fileId);
        dataset.removeFile(file);
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
    public Resource downloadFile(String datasetId, String fileId) {
        DatasetFile file = getDatasetFile(datasetId, fileId);
        try {
            Path filePath = Paths.get(file.getFilePath()).normalize();
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
     * 下载目录为 zip
     */
    @Transactional(readOnly = true)
    public void downloadDirectoryAsZip(String datasetId, String directoryId, HttpServletResponse response) {
        Dataset dataset = datasetRepository.getById(datasetId);
        if (Objects.isNull(dataset)) {
            throw BusinessException.of(DataManagementErrorCode.DATASET_NOT_FOUND);
        }
        Path directoryPath = decodeDirectoryId(directoryId);
        if (Objects.isNull(directoryPath)) {
            throw BusinessException.of(SystemErrorCode.RESOURCE_NOT_FOUND);
        }
        if (!directoryPath.toString().startsWith(dataset.getPath())) {
            throw BusinessException.of(SystemErrorCode.RESOURCE_NOT_FOUND);
        }
        List<DatasetFile> allByDatasetId = datasetFileRepository.findAllByDatasetId(datasetId);
        response.setContentType("application/zip");
        String zipName = String.format("%s_%s.zip", directoryPath.getFileName().toString(),
                LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss")));
        response.setHeader(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=" + zipName);
        try (ZipArchiveOutputStream zos = new ZipArchiveOutputStream(response.getOutputStream())) {
            try (Stream<Path> pathStream = Files.walk(directoryPath)) {
                List<Path> allPaths = pathStream.toList();
                for (Path path : allPaths) {
                    addToZipFile(path, directoryPath, zos);
                }
            }
        } catch (IOException e) {
            log.error("Failed to download directory as zip.", e);
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR);
        }
    }

    /**
     * 下载文件
     */
    @Transactional(readOnly = true)
    public void downloadDatasetFileAsZip(String datasetId, HttpServletResponse response) {
        Dataset dataset = datasetRepository.getById(datasetId);
        if (Objects.isNull(dataset)) {
            throw BusinessException.of(DataManagementErrorCode.DATASET_NOT_FOUND);
        }
        List<DatasetFile> allByDatasetId = datasetFileRepository.findAllByDatasetId(datasetId);
        Set<String> filePaths = allByDatasetId.stream().map(DatasetFile::getFilePath).collect(Collectors.toSet());
        String datasetPath = dataset.getPath();
        Path downloadPath = Path.of(datasetPath);
        response.setContentType("application/zip");
        String zipName = String.format("dataset_%s.zip",
                LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss")));
        response.setHeader(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=" + zipName);
        try (ZipArchiveOutputStream zos = new ZipArchiveOutputStream(response.getOutputStream())) {
            try (Stream<Path> pathStream = Files.walk(downloadPath)) {
                List<Path> allPaths = pathStream.filter(path -> path.toString().startsWith(datasetPath))
                    .filter(path -> filePaths.stream().anyMatch(filePath -> filePath.startsWith(path.toString())))
                    .toList();
                for (Path path : allPaths) {
                    addToZipFile(path, downloadPath, zos);
                }
            }
        } catch (IOException e) {
            log.error("Failed to download files in batches.", e);
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

    private void deleteDirectory(String datasetId, String directoryId) {
        Dataset dataset = datasetRepository.getById(datasetId);
        if (Objects.isNull(dataset)) {
            throw BusinessException.of(DataManagementErrorCode.DATASET_NOT_FOUND);
        }
        Path directoryPath = decodeDirectoryId(directoryId);
        if (Objects.isNull(directoryPath) || !directoryPath.toString().startsWith(dataset.getPath())) {
            throw BusinessException.of(SystemErrorCode.RESOURCE_NOT_FOUND);
        }
        List<DatasetFile> allByDatasetId = datasetFileRepository.findAllByDatasetId(datasetId);
        List<DatasetFile> filesToDelete = allByDatasetId.stream()
            .filter(file -> Objects.nonNull(file.getFilePath()) && file.getFilePath().startsWith(directoryPath.toString()))
            .toList();
        dataset.setFiles(new ArrayList<>(filesToDelete));
        for (DatasetFile file : filesToDelete) {
            datasetFileRepository.removeById(file.getId());
            dataset.removeFile(file);
        }
        datasetRepository.updateById(dataset);

        // 删除文件系统中的目录及内容（仅删除归属于数据集目录的文件）
        if (directoryPath.toString().startsWith(dataset.getPath())) {
            try (Stream<Path> walk = Files.walk(directoryPath)) {
                walk.sorted(Comparator.reverseOrder()).forEach(path -> {
                    try {
                        Files.deleteIfExists(path);
                    } catch (IOException e) {
                        log.warn("Failed to delete path {}", path, e);
                    }
                });
            } catch (IOException e) {
                throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR);
            }
        }
    }

    public boolean isDirectoryId(String fileId) {
        return Objects.nonNull(fileId) && fileId.startsWith("directory-");
    }

    private String encodeDirectoryId(Path path) {
        return "directory-" + Base64.getUrlEncoder().encodeToString(path.toString().getBytes(StandardCharsets.UTF_8));
    }

    private Path decodeDirectoryId(String directoryId) {
        if (!isDirectoryId(directoryId)) {
            return null;
        }
        String encoded = directoryId.substring("directory-".length());
        try {
            String decodedPath = new String(Base64.getUrlDecoder().decode(encoded), StandardCharsets.UTF_8);
            return Paths.get(decodedPath);
        } catch (IllegalArgumentException e) {
            log.warn("Failed to decode directory id {}", directoryId, e);
            return null;
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
        ChunkUploadPreRequest request = ChunkUploadPreRequest.builder().build();
        String basePath = datasetBasePath + File.separator + datasetId;
        String prefix = Optional.ofNullable(chunkUploadRequest.getPrefix()).orElse("").trim();
        if (!prefix.isEmpty()) {
            // 统一使用正斜杠作为前端传入的分隔符，后端根据系统转换
            prefix = prefix.replace("\\", "/");
            // 去掉开头的斜杠，避免越出数据集目录
            while (prefix.startsWith("/")) {
                prefix = prefix.substring(1);
            }
            if (!prefix.isEmpty()) {
                basePath = basePath + File.separator + prefix;
            }
        }
        request.setUploadPath(basePath);
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
            DatasetFile datasetFile = DatasetFile.builder()
                .id(UUID.randomUUID().toString())
                .datasetId(datasetId)
                .fileSize(savedFile.length())
                .uploadTime(currentTime)
                .lastAccessTime(currentTime)
                .fileName(file.getFileName())
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
     * 复制文件到数据集目录
     *
     * @param datasetId 数据集id
     * @param req       复制文件请求
     * @return 复制的文件列表
     */
    @Transactional
    public List<DatasetFile> copyFilesToDatasetDir(String datasetId, CopyFilesRequest req) {
        Dataset dataset = datasetRepository.getById(datasetId);
        BusinessAssert.notNull(dataset, SystemErrorCode.RESOURCE_NOT_FOUND);
        List<DatasetFile> copiedFiles = new ArrayList<>();
        List<DatasetFile> existDatasetFiles = datasetFileRepository.findAllByDatasetId(datasetId);
        dataset.setFiles(existDatasetFiles);
        for (String sourceFilePath : req.sourcePaths()) {
            Path sourcePath = Paths.get(sourceFilePath);
            if (!Files.exists(sourcePath) || !Files.isRegularFile(sourcePath)) {
                log.warn("Source file does not exist or is not a regular file: {}", sourceFilePath);
                continue;
            }
            String fileName = sourcePath.getFileName().toString();
            File sourceFile = sourcePath.toFile();
            LocalDateTime currentTime = LocalDateTime.now();
            DatasetFile datasetFile = DatasetFile.builder()
                    .id(UUID.randomUUID().toString())
                    .datasetId(datasetId)
                    .fileName(fileName)
                    .fileType(AnalyzerUtils.getExtension(fileName))
                    .fileSize(sourceFile.length())
                    .filePath(Paths.get(dataset.getPath(), fileName).toString())
                    .uploadTime(currentTime)
                    .lastAccessTime(currentTime)
                    .build();
            setDatasetFileId(datasetFile, dataset);
            dataset.addFile(datasetFile);
            copiedFiles.add(datasetFile);
        }
        datasetFileRepository.saveOrUpdateBatch(copiedFiles, 100);
        dataset.active();
        datasetRepository.updateById(dataset);
        CompletableFuture.runAsync(() -> copyFilesToDatasetDir(req.sourcePaths(), dataset));
        return copiedFiles;
    }

    private void copyFilesToDatasetDir(List<String> sourcePaths, Dataset dataset) {
        for (String sourcePath : sourcePaths) {
            Path sourceFilePath = Paths.get(sourcePath);
            Path targetFilePath = Paths.get(dataset.getPath(), sourceFilePath.getFileName().toString());
            try {
                Files.createDirectories(Path.of(dataset.getPath()));
                Files.copy(sourceFilePath, targetFilePath);
            } catch (IOException e) {
                log.error("Failed to copy file from {} to {}", sourcePath, targetFilePath, e);
            }
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
        Dataset dataset = datasetRepository.getById(datasetId);
        BusinessAssert.notNull(dataset, SystemErrorCode.RESOURCE_NOT_FOUND);
        List<DatasetFile> addedFiles = new ArrayList<>();
        List<DatasetFile> existDatasetFiles = datasetFileRepository.findAllByDatasetId(datasetId);
        dataset.setFiles(existDatasetFiles);

        boolean softAdd = req.softAdd();
        String metadata;
        try {
            Map<String, Boolean> metadataMap = Map.of("softAdd", softAdd);
            ObjectMapper objectMapper = new ObjectMapper();
            metadata = objectMapper.writeValueAsString(metadataMap);
        } catch (JsonProcessingException e) {
            log.error("Failed to serialize metadataMap", e);
            throw BusinessException.of(SystemErrorCode.UNKNOWN_ERROR);
        }

        for (String sourceFilePath : req.sourcePaths()) {
            Path sourcePath = Paths.get(sourceFilePath);
            String fileName = sourcePath.getFileName().toString();
            File sourceFile = sourcePath.toFile();
            LocalDateTime currentTime = LocalDateTime.now();

            DatasetFile datasetFile = DatasetFile.builder()
                .id(UUID.randomUUID().toString())
                .datasetId(datasetId)
                .fileName(fileName)
                .fileType(AnalyzerUtils.getExtension(fileName))
                .fileSize(sourceFile.length())
                .filePath(sourceFilePath)
                .uploadTime(currentTime)
                .lastAccessTime(currentTime)
                .metadata(metadata)
                .build();
            setDatasetFileId(datasetFile, dataset);
            dataset.addFile(datasetFile);
            addedFiles.add(datasetFile);
        }
        datasetFileRepository.saveOrUpdateBatch(addedFiles, 100);
        dataset.active();
        datasetRepository.updateById(dataset);
        // Note: addFilesToDataset only creates DB records, no file system operations
        // If file copy is needed, use copyFilesToDatasetDir endpoint instead
        return addedFiles;
    }
}
