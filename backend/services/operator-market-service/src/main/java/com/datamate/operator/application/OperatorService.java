package com.datamate.operator.application;

import com.datamate.common.domain.model.ChunkUploadPreRequest;
import com.datamate.common.domain.model.FileUploadResult;
import com.datamate.common.domain.service.FileService;
import com.datamate.operator.domain.contants.OperatorConstant;
import com.datamate.operator.infrastructure.converter.OperatorConverter;
import com.datamate.operator.domain.model.OperatorView;
import com.datamate.operator.domain.repository.CategoryRelationRepository;
import com.datamate.operator.domain.repository.OperatorRepository;
import com.datamate.operator.domain.repository.OperatorViewRepository;
import com.datamate.operator.infrastructure.parser.ParserHolder;
import com.datamate.operator.interfaces.dto.OperatorDto;
import com.datamate.operator.interfaces.dto.UploadOperatorRequest;
import lombok.RequiredArgsConstructor;
import org.apache.commons.io.FileUtils;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.util.List;

@Service
@RequiredArgsConstructor
public class OperatorService {
    private final OperatorRepository operatorRepo;

    private final OperatorViewRepository operatorViewRepo;

    private final CategoryRelationRepository relationRepo;

    private final ParserHolder parserHolder;

    private final FileService fileService;

    @Value("${operator.base.path:/operator}")
    private String operatorBasePath;

    private final String uploadPath = operatorBasePath + File.separator + "upload";

    private final String extractPath = operatorBasePath + File.separator + "extract";

    public List<OperatorDto> getOperators(Integer page, Integer size, List<Integer> categories,
                                          String operatorName, Boolean isStar) {
        List<OperatorView> filteredOperators = operatorViewRepo.findOperatorsByCriteria(page, size, operatorName,
                categories, isStar);
        return filteredOperators.stream().map(OperatorConverter.INSTANCE::fromEntityToDto).toList();
    }

    public int getOperatorsCount(List<Integer> categories, String operatorName, Boolean isStar) {
        return operatorViewRepo.countOperatorsByCriteria(operatorName, categories, isStar);
    }

    public OperatorDto getOperatorById(String id) {
        OperatorView operator = operatorViewRepo.findOperatorById(id);
        return OperatorConverter.INSTANCE.fromEntityToDto(operator);
    }

    public OperatorDto createOperator(OperatorDto req) {
        operatorRepo.insertOperator(req);
        relationRepo.batchInsert(req.getId(), req.getCategories());
        parserHolder.extractTo(getFileType(req.getFileName()), uploadPath + File.separator + req.getFileName(),
            extractPath + File.separator + getFileNameWithoutExtension(req.getFileName()));
        return getOperatorById(req.getId());
    }

    public OperatorDto updateOperator(String id, OperatorDto req) {
        operatorRepo.updateOperator(req);
        relationRepo.batchInsert(id, req.getCategories());
        parserHolder.extractTo(getFileType(req.getFileName()), uploadPath + File.separator + req.getFileName(),
            extractPath + File.separator + getFileNameWithoutExtension(req.getFileName()));
        return getOperatorById(id);
    }

    public OperatorDto uploadOperator(MultipartFile multipartFile) {
        // TODO: 文件上传与解析
        try {
            File file = new File(multipartFile.getName());
            // 从MultipartFile获取输入流并复制到目标文件
            FileUtils.copyInputStreamToFile(multipartFile.getInputStream(), file);
            OperatorDto operatorDto = parserHolder.parseYamlFromArchive(getFileType(file.getName()), file,
                OperatorConstant.YAML_PATH, OperatorDto.class);
        } catch (IOException e) {
            e.printStackTrace();
        }
        return new OperatorDto();
    }

    public String preUpload() {
        ChunkUploadPreRequest request = ChunkUploadPreRequest.builder().build();
        request.setUploadPath(operatorBasePath + File.separator + "upload");
        request.setTotalFileNum(1);
        request.setServiceId(OperatorConstant.SERVICE_ID);
        return fileService.preUpload(request);
    }

    public void chunkUpload(UploadOperatorRequest request) {
        FileUploadResult uploadResult = fileService.chunkUpload(OperatorConverter.INSTANCE.toChunkRequest(request));
        if (uploadResult.isAllFilesUploaded()) {
            // TODO: 文件上传与解析
            OperatorDto operatorDto = parserHolder.parseYamlFromArchive(getFileType(uploadResult.getFileName()), uploadResult.getSavedFile(),
                OperatorConstant.YAML_PATH, OperatorDto.class);
        }
    }

    private String getFileType(String fileName) {
        return fileName.substring(fileName.lastIndexOf('.') + 1);
    }

    private String getFileNameWithoutExtension(String fileName) {
        return fileName.substring(0, fileName.lastIndexOf('.'));
    }
}
