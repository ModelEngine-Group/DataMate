package com.dataengine.datamanagement.interfaces.rest;

import com.dataengine.datamanagement.application.service.DatasetFileApplicationService;
import com.dataengine.datamanagement.domain.model.dataset.DatasetFile;
import com.dataengine.datamanagement.interfaces.api.DatasetFileApi;
import com.dataengine.datamanagement.interfaces.dto.DatasetFileResponse;
import com.dataengine.datamanagement.interfaces.dto.PagedDatasetFileResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.Resource;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import java.time.ZoneOffset;
import java.util.stream.Collectors;

/**
 * 数据集文件 REST 控制器（UUID 模式）
 */
@RestController
public class DatasetFileController implements DatasetFileApi {

    private final DatasetFileApplicationService datasetFileApplicationService;

    @Autowired
    public DatasetFileController(DatasetFileApplicationService datasetFileApplicationService) {
        this.datasetFileApplicationService = datasetFileApplicationService;
    }

    @Override
    public ResponseEntity<PagedDatasetFileResponse> datasetsDatasetIdFilesGet(String datasetId, Integer page, Integer size,
                                                                  String fileType, String status) {
        Pageable pageable = PageRequest.of(page != null ? page : 0, size != null ? size : 20);

        Page<DatasetFile> filesPage = datasetFileApplicationService.getDatasetFiles(
            datasetId, fileType, status, pageable);

        PagedDatasetFileResponse response = new PagedDatasetFileResponse();
        response.setContent(filesPage.getContent().stream()
            .map(this::convertToResponse)
            .collect(Collectors.toList()));
        response.setPage(filesPage.getNumber());
        response.setSize(filesPage.getSize());
        response.setTotalElements((int) filesPage.getTotalElements());
        response.setTotalPages(filesPage.getTotalPages());
        response.setFirst(filesPage.isFirst());
        response.setLast(filesPage.isLast());

        return ResponseEntity.ok(response);
    }

    @Override
    public ResponseEntity<DatasetFileResponse> datasetsDatasetIdFilesPost(String datasetId, MultipartFile file, String description) {
        try {
            DatasetFile datasetFile = datasetFileApplicationService.uploadFile(
                datasetId, file, description, "system");

            return ResponseEntity.status(HttpStatus.CREATED).body(convertToResponse(datasetFile));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().build();
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @Override
    public ResponseEntity<DatasetFileResponse> datasetsDatasetIdFilesFileIdGet(String datasetId, String fileId) {
        try {
            DatasetFile datasetFile = datasetFileApplicationService.getDatasetFile(datasetId, fileId);
            return ResponseEntity.ok(convertToResponse(datasetFile));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        }
    }

    @Override
    public ResponseEntity<Void> datasetsDatasetIdFilesFileIdDelete(String datasetId, String fileId) {
        try {
            datasetFileApplicationService.deleteDatasetFile(datasetId, fileId);
            return ResponseEntity.noContent().build();
        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        }
    }

    @Override
    public ResponseEntity<Resource> datasetsDatasetIdFilesFileIdDownloadGet(String datasetId, String fileId) {
        try {
            DatasetFile datasetFile = datasetFileApplicationService.getDatasetFile(datasetId, fileId);
            Resource resource = datasetFileApplicationService.downloadFile(datasetId, fileId);

            return ResponseEntity.ok()
                .contentType(MediaType.APPLICATION_OCTET_STREAM)
                .header(HttpHeaders.CONTENT_DISPOSITION,
                    "attachment; filename=\"" + datasetFile.getFileName() + "\"")
                .body(resource);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.notFound().build();
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    private DatasetFileResponse convertToResponse(DatasetFile datasetFile) {
        DatasetFileResponse response = new DatasetFileResponse();
        response.setId(datasetFile.getId());
        response.setFileName(datasetFile.getFileName());
        response.setOriginalName(null);
        response.setFileType(datasetFile.getFileType());
        response.setSize(datasetFile.getFileSize());
        try { response.setStatus(DatasetFileResponse.StatusEnum.fromValue(datasetFile.getStatus())); } catch (Exception ignore) {}
        response.setDescription(null);
        response.setFilePath(datasetFile.getFilePath());
        if (datasetFile.getUploadTime() != null) response.setUploadedAt(datasetFile.getUploadTime().atOffset(ZoneOffset.UTC));
        response.setUploadedBy(null);
        return response;
    }
}
