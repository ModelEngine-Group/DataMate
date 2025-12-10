package com.datamate.datamanagement.application;

import com.baomidou.mybatisplus.core.metadata.IPage;
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
import com.datamate.datamanagement.interfaces.dto.UploadFileRequest;
import com.datamate.datamanagement.interfaces.dto.UploadFilesPreRequest;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.BufferedInputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.net.MalformedURLException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.function.Function;
import java.util.stream.Collectors;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

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
        IPage<DatasetFile> page = new com.baomidou.mybatisplus.extension.plugins.pagination.Page<>(pagingQuery.getPage(), pagingQuery.getSize());
        IPage<DatasetFile> files = datasetFileRepository.findByCriteria(datasetId, fileType, status, name, page);
        return PagedResponse.of(files);
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
     * 下载文件
     */
    @Transactional(readOnly = true)
    public void downloadDatasetFileAsZip(String datasetId, HttpServletResponse response) {
        List<DatasetFile> allByDatasetId = datasetFileRepository.findAllByDatasetId(datasetId);
        fileRename(allByDatasetId);
        response.setContentType("application/zip");
        String zipName = String.format("dataset_%s.zip",
                LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss")));
        response.setHeader(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=" + zipName);
        try (ZipOutputStream zos = new ZipOutputStream(response.getOutputStream())) {
            for (DatasetFile file : allByDatasetId) {
                addToZipFile(file, zos);
            }
        } catch (IOException e) {
            log.error("Failed to download files in batches.", e);
            throw BusinessException.of(SystemErrorCode.FILE_SYSTEM_ERROR);
        }
    }

    private void fileRename(List<DatasetFile> files) {
        Set<String> uniqueFilenames = new HashSet<>();
        for (DatasetFile file : files) {
            String originalFilename = file.getFileName();
            if (!uniqueFilenames.add(originalFilename)) {
                String newFilename;
                int counter = 1;
                do {
                    newFilename = generateNewFilename(originalFilename, counter);
                    counter++;
                } while (!uniqueFilenames.add(newFilename));
                file.setFileName(newFilename);
            }
        }
    }

    private String generateNewFilename(String oldFilename, int counter) {
        int dotIndex = oldFilename.lastIndexOf(".");
        return oldFilename.substring(0, dotIndex) + "-(" + counter + ")" + oldFilename.substring(dotIndex);
    }

    private void addToZipFile(DatasetFile file, ZipOutputStream zos) throws IOException {
        if (file.getFilePath() == null || !Files.exists(Paths.get(file.getFilePath()))) {
            log.warn("The file hasn't been found on filesystem, id: {}", file.getId());
            return;
        }
        try (InputStream fis = Files.newInputStream(Paths.get(file.getFilePath()));
             BufferedInputStream bis = new BufferedInputStream(fis)) {
            ZipEntry zipEntry = new ZipEntry(file.getFileName());
            zos.putNextEntry(zipEntry);
            byte[] buffer = new byte[8192];
            int length;
            while ((length = bis.read(buffer)) >= 0) {
                zos.write(buffer, 0, length);
            }
            zos.closeEntry();
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
        request.setUploadPath(datasetBasePath + File.separator + datasetId);
        request.setTotalFileNum(chunkUploadRequest.getTotalFileNum());
        request.setServiceId(DatasetConstant.SERVICE_ID);
        DatasetFileUploadCheckInfo checkInfo = new DatasetFileUploadCheckInfo();
        checkInfo.setDatasetId(datasetId);
        checkInfo.setHasArchive(chunkUploadRequest.isHasArchive());
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
