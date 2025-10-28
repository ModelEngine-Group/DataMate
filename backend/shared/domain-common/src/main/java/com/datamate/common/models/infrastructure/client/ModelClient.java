package com.datamate.common.models.infrastructure.client;

import com.datamate.common.models.domain.entity.ModelConfig;
import com.datamate.common.models.domain.entity.ModelType;
import dev.langchain4j.model.chat.ChatModel;
import dev.langchain4j.model.embedding.EmbeddingModel;
import dev.langchain4j.model.openai.OpenAiChatModel;
import dev.langchain4j.model.openai.OpenAiEmbeddingModel;

import java.util.function.Consumer;

/**
 * 模型客户端接口
 *
 * @author dallas
 * @since 2025-10-27
 */
public class ModelClient {
    public static <T> T invokeModel(ModelConfig modelConfig, Class<T> modelInterface) {
        return switch (modelConfig.getType()) {
            case CHAT -> modelInterface.cast(invokeChatModel(modelConfig));
            case EMBEDDING -> modelInterface.cast(invokeEmbeddingModel(modelConfig));
        };
    }

    private static EmbeddingModel invokeEmbeddingModel(ModelConfig modelConfig) {
        return OpenAiEmbeddingModel.builder()
                .baseUrl(modelConfig.getBaseUrl())
                .apiKey(modelConfig.getApiKey())
                .modelName(modelConfig.getModelName())
                .build();
    }

    private static ChatModel invokeChatModel(ModelConfig modelConfig) {
        return OpenAiChatModel.builder()
                .baseUrl(modelConfig.getBaseUrl())
                .apiKey(modelConfig.getApiKey())
                .modelName(modelConfig.getModelName())
                .build();
    }

    public static void checkHealth(ModelConfig modelConfig) {
    }
}
