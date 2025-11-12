package com.datamate.common.setting.infrastructure.client;

import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.setting.domain.entity.ModelConfig;
import com.datamate.common.setting.infrastructure.exception.ModelsErrorCode;
import dev.langchain4j.model.chat.ChatModel;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.model.openai.OpenAiChatModel;
import dev.langchain4j.model.openai.OpenAiEmbeddingModel;
import lombok.extern.slf4j.Slf4j;

/**
 * 模型客户端接口
 *
 * @author dallas
 * @since 2025-10-27
 */
@Slf4j
public class ModelClient {
    public static <T> T invokeModel(ModelConfig modelConfig, Class<T> modelInterface) {
        return switch (modelConfig.getType()) {
            case CHAT -> modelInterface.cast(invokeChatModel(modelConfig));
            case EMBEDDING -> modelInterface.cast(invokeEmbeddingModel(modelConfig));
        };
    }

    public static EmbeddingModel invokeEmbeddingModel(ModelConfig modelConfig) {
        return OpenAiEmbeddingModel.builder()
                .baseUrl(modelConfig.getBaseUrl())
                .apiKey(modelConfig.getApiKey())
                .modelName(modelConfig.getModelName())
                .build();
    }

    public static ChatModel invokeChatModel(ModelConfig modelConfig) {
        return OpenAiChatModel.builder()
                .baseUrl(modelConfig.getBaseUrl())
                .apiKey(modelConfig.getApiKey())
                .modelName(modelConfig.getModelName())
                .build();
    }

    public static void checkHealth(ModelConfig modelConfig) {
        try {
            switch (modelConfig.getType()) {
                case CHAT -> checkChatModelHealth(modelConfig);
                case EMBEDDING -> checkEmbeddingModelHealth(modelConfig);
            }
        } catch (Exception e) {
            log.error("Model health check failed for modelConfig: {}", modelConfig, e);
            throw BusinessException.of(ModelsErrorCode.MODEL_HEALTH_CHECK_FAILED);
        }
    }

    private static void checkEmbeddingModelHealth(ModelConfig modelConfig) {
        EmbeddingModel embeddingModel = invokeEmbeddingModel(modelConfig);
        embeddingModel.embed("text");
    }

    private static void checkChatModelHealth(ModelConfig modelConfig) {
        ChatModel chatModel = invokeChatModel(modelConfig);
        chatModel.chat("hello");
    }
}
