package com.edatamate.application.dataset;

import com.edatamate.common.dataset.DatasetFile;
import com.edatamate.domain.repository.DatasetFileRepository;
import com.edatamate.domain.service.FileService;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class DatasetFileService {
    @Value("${dataset.file.base-dir:/dataset}")
    private String targetDirectory;

    private final DatasetFileRepository datasetFileRepository;

    private final FileService fileService;

    /**
     * 根据ID查询数据集文件
     *
     * @param id 数据集文件ID
     * @return 数据集文件
     */
    public DatasetFile getDatasetFileById(Long id) {
        return datasetFileRepository.getById(id);
    }

    /**
     * 新增数据集文件
     *
     * @param datasetFile 数据集文件
     * @return 数据集文件
     */
    public DatasetFile createDatasetFile(DatasetFile datasetFile) {
        datasetFileRepository.save(datasetFile);
        return datasetFile;
    }

    /**
     * 更新数据集文件
     *
     * @param datasetFile 数据集文件
     * @return 更新后的数据集文件
     */
    public DatasetFile updateDatasetFile(DatasetFile datasetFile) {
        datasetFileRepository.updateById(datasetFile);
        return datasetFile;
    }

    /**
     * 删除数据集文件
     *
     * @param id 数据集文件ID
     */
    public void deleteDatasetFile(Long id) {
        datasetFileRepository.removeById(id);
    }

    /**
     * 新增多个数据集文件
     *
     * @param files 上传的文件列表
     * @param datasetId 数据集ID
     * @return 数据集文件列表
     */
    public List<DatasetFile> createDatasetFiles(List<MultipartFile> files, Long datasetId) {
        String baseDir = fileService.initDatasetDirectory(datasetId);
        List<DatasetFile> datasetFiles = files.stream().map(file -> {
            String filePath = fileService.uploadFileToDataset(file, baseDir);
            DatasetFile datasetFile = new DatasetFile(file, datasetId, filePath);
            datasetFile.setHash(fileService.calculateFileHash(file));
            return datasetFile;
        }).collect(Collectors.toList());
        datasetFileRepository.saveBatch(datasetFiles, 1000);
        return datasetFiles;
    }

    public void deleteDatasetFiles(Long datasetId) {
        fileService.deleteFilesByDatasetId(datasetId);
        datasetFileRepository.removeByDatasetId(datasetId);
    }
}
