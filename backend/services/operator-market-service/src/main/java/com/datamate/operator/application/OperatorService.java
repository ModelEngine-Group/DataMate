package com.datamate.operator.application;

import com.datamate.common.domain.model.ChunkUploadPreRequest;
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
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.File;
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

    public List<OperatorDto> getOperators(Integer page, Integer size, List<String> categories,
                                          String operatorName, Boolean isStar) {
        List<OperatorView> filteredOperators = operatorViewRepo.findOperatorsByCriteria(page, size, operatorName,
                categories, isStar);
        return filteredOperators.stream().map(OperatorConverter.INSTANCE::fromEntityToDto).toList();
    }

    public int getOperatorsCount(List<String> categories, String operatorName, Boolean isStar) {
        return operatorViewRepo.countOperatorsByCriteria(operatorName, categories, isStar);
    }

    public OperatorDto getOperatorById(String id) {
        OperatorView operator = operatorViewRepo.findOperatorById(id);
        return OperatorConverter.INSTANCE.fromEntityToDto(operator);
    }

    @Transactional
    public OperatorDto createOperator(OperatorDto req) {
        operatorRepo.insertOperator(req);
        relationRepo.batchInsert(req.getId(), req.getCategories());
        parserHolder.extractTo(getFileType(req.getFileName()), getUploadPath(req.getFileName()),
            getExtractPath(getFileNameWithoutExtension(req.getFileName())));
        return getOperatorById(req.getId());
    }

    @Transactional
    public OperatorDto updateOperator(String id, OperatorDto req) {
        operatorRepo.updateOperator(req);
        relationRepo.batchInsert(id, req.getCategories());
        parserHolder.extractTo(getFileType(req.getFileName()), getUploadPath(req.getFileName()),
            getExtractPath(getFileNameWithoutExtension(req.getFileName())));
        return getOperatorById(id);
    }

    @Transactional
    public void deleteOperator(String id) {
        operatorRepo.deleteOperator(id);
        relationRepo.deleteByOperatorId(id);
    }

    public OperatorDto uploadOperator(String fileName) {
        return parserHolder.parseYamlFromArchive(getFileType(fileName), new File(getUploadPath(fileName)),
            OperatorConstant.YAML_PATH);
    }

    public String preUpload() {
        ChunkUploadPreRequest request = ChunkUploadPreRequest.builder().build();
        request.setUploadPath(operatorBasePath + File.separator + "upload");
        request.setTotalFileNum(1);
        request.setServiceId(OperatorConstant.SERVICE_ID);
        return fileService.preUpload(request);
    }

    public void chunkUpload(UploadOperatorRequest request) {
        fileService.chunkUpload(OperatorConverter.INSTANCE.toChunkRequest(request));
    }

    private String getFileType(String fileName) {
        return fileName.substring(fileName.lastIndexOf('.') + 1);
    }

    private String getFileNameWithoutExtension(String fileName) {
        return fileName.substring(0, fileName.lastIndexOf('.'));
    }

    private String getUploadPath(String fileName) {
        return operatorBasePath + File.separator + "upload" + File.separator + fileName;
    }

    private String getExtractPath(String fileName) {
        return operatorBasePath + File.separator + "extract" + File.separator + fileName;
    }
}
