package com.datamate.common.models.application;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.datamate.common.infrastructure.exception.BusinessAssert;
import com.datamate.common.interfaces.PagedResponse;
import com.datamate.common.models.domain.entity.ModelConfig;
import com.datamate.common.models.domain.repository.ModelConfigRepository;
import com.datamate.common.models.infrastructure.client.ModelClient;
import com.datamate.common.models.infrastructure.exception.ModelsErrorCode;
import com.datamate.common.models.interfaces.rest.dto.CreateModelRequest;
import com.datamate.common.models.interfaces.rest.dto.QueryModelRequest;
import dev.langchain4j.model.chat.ChatModel;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

/**
 * 模型配置应用服务类
 *
 * @author dallas
 * @since 2025-10-27
 */
@Service
@RequiredArgsConstructor
public class ModelConfigApplicationService {
    private final ModelConfigRepository modelConfigRepository;

    public List<ModelConfig> getProviders() {
        List<ModelConfig> providers = new ArrayList<>();
        providers.add(ModelConfig.builder().provider("ModelEngine").baseUrl("http://localhost:9981").build());
        providers.add(ModelConfig.builder().provider("Ollama").baseUrl("http://localhost:11434").build());
        providers.add(ModelConfig.builder().provider("OpenAI").baseUrl("https://api.openai.com/v1").build());
        providers.add(ModelConfig.builder().provider("DeepSeek").baseUrl("https://api.deepseek.cn/v1").build());
        providers.add(ModelConfig.builder().provider("火山方舟").baseUrl("https://ark.cn-beijing.volces.com/api/v3").build());
        providers.add(ModelConfig.builder().provider("阿里云百炼").baseUrl("https://dashscope.aliyuncs.com/compatible-mode/v1").build());
        providers.add(ModelConfig.builder().provider("硅基流动").baseUrl("https://api.siliconflow.cn/v1").build());
        providers.add(ModelConfig.builder().provider("智谱AI").baseUrl("https://open.bigmodel.cn/api/paas/v4").build());
        return providers;
    }

    public PagedResponse<ModelConfig> getModels(QueryModelRequest queryModelRequest) {
        // 从数据库查询模型配置
        IPage<ModelConfig> page = modelConfigRepository.page(queryModelRequest);
        return PagedResponse.of(page.getRecords(), page.getCurrent(), page.getTotal(), page.getPages());
    }

    public ModelConfig getModelDetail(String modelId) {
        return modelConfigRepository.getById(modelId);
    }

    public ModelConfig createModel(CreateModelRequest modelConfig) {
        ModelConfig newConfig = ModelConfig.builder()
                .provider(modelConfig.getProvider())
                .modelName(modelConfig.getModelName())
                .type(modelConfig.getType())
                .baseUrl(modelConfig.getBaseUrl())
                .apiKey(modelConfig.getApiKey())
                .isEnabled(true)
                .build();
        ModelClient.checkHealth(newConfig);
        modelConfigRepository.save(newConfig);
        return newConfig;
    }

    public ModelConfig updateModel(String modelId, @Valid CreateModelRequest updateModelRequest) {
        ModelConfig modelConfig = modelConfigRepository.getById(modelId);
        BusinessAssert.notNull(modelConfig, ModelsErrorCode.MODEL_CONFIG_NOT_FOUND);
        modelConfig.setProvider(updateModelRequest.getProvider());
        modelConfig.setModelName(updateModelRequest.getModelName());
        modelConfig.setType(updateModelRequest.getType());
        modelConfig.setBaseUrl(updateModelRequest.getBaseUrl());
        modelConfig.setApiKey(updateModelRequest.getApiKey());
        modelConfig.setIsEnabled(true);
        ModelClient.checkHealth(modelConfig);
        modelConfigRepository.updateById(modelConfig);
        return modelConfig;
    }

    public void deleteModel(String modelId) {
        modelConfigRepository.removeById(modelId);
    }
}
