package com.dataengine.datamanagement.interfaces.rest;

import com.dataengine.datamanagement.application.service.DatasetFileApplicationService;
import com.dataengine.datamanagement.domain.model.dataset.DatasetFile;
import com.dataengine.datamanagement.interfaces.dto.DatasetFileResponse;
import com.dataengine.datamanagement.interfaces.dto.PagedDatasetFileResponse;
import com.dataengine.common.interfaces.Response;
import com.dataengine.datamanagement.interfaces.dto.UploadFileRequest;
import com.dataengine.datamanagement.interfaces.dto.UploadFilesPreRequest;
import jakarta.validation.Valid;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.Resource;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.time.ZoneOffset;
import java.util.stream.Collectors;

/**
 * 数据集文件 REST 控制器（UUID 模式）
 */
@Slf4j
@RestController
@RequestMapping("/data-management/datasets/{datasetId}/files")
public class DatasetFileController {

    private final DatasetFileApplicationService datasetFileApplicationService;

    @Autowired
    public DatasetFileController(DatasetFileApplicationService datasetFileApplicationService) {
        this.datasetFileApplicationService = datasetFileApplicationService;
    }

    @GetMapping
    public ResponseEntity<Response<PagedDatasetFileResponse>> getDatasetFiles(
        @PathVariable("datasetId") String datasetId,
        @RequestParam(value = "page", required = false, defaultValue = "0") Integer page,
        @RequestParam(value = "size", required = false, defaultValue = "20") Integer size,
        @RequestParam(value = "fileType", required = false) String fileType,
        @RequestParam(value = "status", required = false) String status) {
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

        return ResponseEntity.ok(Response.ok(response));
    }

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<Response<DatasetFileResponse>> uploadDatasetFile(
        @PathVariable("datasetId") String datasetId,
        @RequestPart(value = "file", required = false) MultipartFile file,
        @RequestParam(value = "description", required = false) String description) {
        try {
            DatasetFile datasetFile = datasetFileApplicationService.uploadFile(
                datasetId, file, description, "system");

            return ResponseEntity.status(HttpStatus.CREATED).body(Response.ok(convertToResponse(datasetFile)));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Response.error("参数错误", null));
        } catch (Exception e) {
            log.error("upload fail", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Response.error("服务器错误", null));
        }
    }

    @GetMapping("/{fileId}")
    public ResponseEntity<Response<DatasetFileResponse>> getDatasetFileById(
        @PathVariable("datasetId") String datasetId,
        @PathVariable("fileId") String fileId) {
        try {
            DatasetFile datasetFile = datasetFileApplicationService.getDatasetFile(datasetId, fileId);
            return ResponseEntity.ok(Response.ok(convertToResponse(datasetFile)));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Response.error("未找到文件", null));
        }
    }

    @DeleteMapping("/{fileId}")
    public ResponseEntity<Response<Void>> deleteDatasetFile(
        @PathVariable("datasetId") String datasetId,
        @PathVariable("fileId") String fileId) {
        try {
            datasetFileApplicationService.deleteDatasetFile(datasetId, fileId);
            return ResponseEntity.noContent().build();
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Response.error("未找到文件", null));
        }
    }

    @GetMapping(value = "/{fileId}/download", produces = MediaType.APPLICATION_OCTET_STREAM_VALUE)
    public ResponseEntity<Resource> downloadDatasetFile(
        @PathVariable("datasetId") String datasetId,
        @PathVariable("fileId") String fileId) {
        try {
            DatasetFile datasetFile = datasetFileApplicationService.getDatasetFile(datasetId, fileId);
            Resource resource = datasetFileApplicationService.downloadFile(datasetId, fileId);

            return ResponseEntity.ok()
                .contentType(MediaType.APPLICATION_OCTET_STREAM)
                .header(HttpHeaders.CONTENT_DISPOSITION,
                    "attachment; filename=\"" + datasetFile.getFileName() + "\"")
                .body(resource);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).build();
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
        response.setStatus(datasetFile.getStatus());
        response.setDescription(null);
        response.setFilePath(datasetFile.getFilePath());
        if (datasetFile.getUploadTime() != null) {
            response.setUploadedAt(datasetFile.getUploadTime().atOffset(ZoneOffset.UTC).toLocalDateTime());
        }
        response.setLastAccessTime(datasetFile.getLastAccessTime());
        response.setUploadedBy(null);
        return response;
    }

    /**
     * 文件上传请求
     *
     * @param request 批量文件上传请求
     * @return 批量上传请求id
     */
    @PostMapping("/upload/pre-upload")
    public ResponseEntity<Response<String>> preUpload(@PathVariable("datasetId") String datasetId, @RequestBody @Valid UploadFilesPreRequest request) {
        return ResponseEntity.ok(Response.ok(datasetFileApplicationService.preUpload(request, datasetId)));
    }

    /**
     * 分块上传
     *
     * @param uploadFileRequest 上传文件请求
     */
    @PostMapping("/upload/chunk")
    public ResponseEntity<Void> chunkUpload(@PathVariable("datasetId") String datasetId, UploadFileRequest uploadFileRequest) {
        log.info("file upload reqId:{}, fileNo:{}, total chunk num:{}, current chunkNo:{}",
            uploadFileRequest.getReqId(), uploadFileRequest.getFileNo(), uploadFileRequest.getTotalChunkNum(),
            uploadFileRequest.getChunkNo());
        datasetFileApplicationService.chunkUpload(datasetId, uploadFileRequest);
        return ResponseEntity.ok().build();
    }
}
