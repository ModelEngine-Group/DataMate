package com.datamate.datamanagement.interfaces.rest;

import com.datamate.common.infrastructure.common.IgnoreResponseWrap;
import com.datamate.common.infrastructure.common.Response;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import com.datamate.common.interfaces.PagedResponse;
import com.datamate.common.interfaces.PagingQuery;
import com.datamate.datamanagement.application.DatasetFileApplicationService;
import com.datamate.datamanagement.domain.model.dataset.DatasetFile;
import com.datamate.datamanagement.interfaces.converter.DatasetConverter;
import com.datamate.datamanagement.interfaces.dto.CopyFilesRequest;
import com.datamate.datamanagement.interfaces.dto.DatasetFileResponse;
import com.datamate.datamanagement.interfaces.dto.UploadFileRequest;
import com.datamate.datamanagement.interfaces.dto.UploadFilesPreRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

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
    public Response<PagedResponse<DatasetFile>> getDatasetFiles(
            @PathVariable("datasetId") String datasetId,
            @RequestParam(value = "page", required = false, defaultValue = "0") Integer page,
            @RequestParam(value = "size", required = false, defaultValue = "20") Integer size,
            @RequestParam(value = "fileType", required = false) String fileType,
            @RequestParam(value = "status", required = false) String status,
            @RequestParam(value = "name", required = false) String name) {
        PagingQuery pagingQuery = new PagingQuery(page, size);
        PagedResponse<DatasetFile> filesPage = datasetFileApplicationService.getDatasetFiles(
                datasetId, fileType, status, name, pagingQuery);
        return Response.ok(filesPage);
    }

    @GetMapping("/{fileId}")
    public ResponseEntity<Response<DatasetFileResponse>> getDatasetFileById(
            @PathVariable("datasetId") String datasetId,
            @PathVariable("fileId") String fileId) {
        try {
            DatasetFile datasetFile = datasetFileApplicationService.getDatasetFile(datasetId, fileId);
            return ResponseEntity.ok(Response.ok(DatasetConverter.INSTANCE.convertToResponse(datasetFile)));
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Response.error(SystemErrorCode.UNKNOWN_ERROR, null));
        }
    }

    @DeleteMapping("/{fileId}")
    public ResponseEntity<Response<Void>> deleteDatasetFile(
            @PathVariable("datasetId") String datasetId,
            @PathVariable("fileId") String fileId) {
        try {
            datasetFileApplicationService.deleteDatasetFile(datasetId, fileId);
            return ResponseEntity.ok().build();
        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Response.error(SystemErrorCode.UNKNOWN_ERROR, null));
        }
    }

    @IgnoreResponseWrap
    @GetMapping(value = "/{fileId}/download", produces = MediaType.APPLICATION_OCTET_STREAM_VALUE + ";charset=UTF-8")
    public ResponseEntity<Resource> downloadDatasetFileById(@PathVariable("datasetId") String datasetId,
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

    @IgnoreResponseWrap
    @GetMapping(value = "/download", produces = MediaType.APPLICATION_OCTET_STREAM_VALUE)
    public void downloadDatasetFileAsZip(@PathVariable("datasetId") String datasetId, HttpServletResponse response) {
        datasetFileApplicationService.downloadDatasetFileAsZip(datasetId, response);
    }

    /**
     * 文件上传请求
     *
     * @param request 批量文件上传请求
     * @return 批量上传请求id
     */
    @PostMapping("/upload/pre-upload")
    public ResponseEntity<Response<String>> preUpload(@PathVariable("datasetId") String datasetId,
                                                      @RequestBody @Valid UploadFilesPreRequest request) {
        return ResponseEntity.ok(Response.ok(datasetFileApplicationService.preUpload(request, datasetId)));
    }

    /**
     * 分块上传
     *
     * @param uploadFileRequest 上传文件请求
     */
    @PostMapping("/upload/chunk")
    public ResponseEntity<Void> chunkUpload(@PathVariable("datasetId") String datasetId,
                                            @Valid UploadFileRequest uploadFileRequest) {
        log.info("file upload reqId:{}, fileNo:{}, total chunk num:{}, current chunkNo:{}",
                uploadFileRequest.getReqId(), uploadFileRequest.getFileNo(), uploadFileRequest.getTotalChunkNum(),
                uploadFileRequest.getChunkNo());
        datasetFileApplicationService.chunkUpload(datasetId, uploadFileRequest);
        return ResponseEntity.ok().build();
    }

    /**
     * 将指定路径中的文件拷贝到数据集目录下
     *
     * @param datasetId 数据集ID
     * @param req       源文件路径列表
     * @return 数据集文件响应DTO列表
     */
    @PostMapping("/upload/copy")
    public List<DatasetFileResponse> copyFilesToDatasetDir(@PathVariable("datasetId") String datasetId,
                                                      @RequestBody @Valid CopyFilesRequest req) {
        List<DatasetFile> datasetFiles = datasetFileApplicationService.copyFilesToDatasetDir(datasetId, req);
        return DatasetConverter.INSTANCE.convertToResponseList(datasetFiles);
    }
}
