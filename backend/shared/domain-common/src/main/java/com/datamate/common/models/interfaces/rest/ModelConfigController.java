package com.datamate.common.models.interfaces.rest;


import com.datamate.common.interfaces.PagedResponse;
import com.datamate.common.models.application.ModelConfigApplicationService;
import com.datamate.common.models.domain.entity.ModelConfig;
import com.datamate.common.models.interfaces.rest.dto.CreateModelRequest;
import com.datamate.common.models.interfaces.rest.dto.QueryModelRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 模型配置控制器类
 *
 * @author dallas
 * @since 2025-10-27
 */
@RestController
@RequestMapping("/api/models")
@RequiredArgsConstructor
public class ModelConfigController {
    private final ModelConfigApplicationService modelConfigApplicationService;

    /**
     * 获取厂商列表
     *
     * @return 厂商列表
     */
    @GetMapping("/providers")
    public List<ModelConfig> getProviders() {
        return modelConfigApplicationService.getProviders();
    }

    /**
     * 获取模型列表
     *
     * @return 模型列表
     */
    @GetMapping("/list")
    public PagedResponse<ModelConfig> getModels(@RequestParam QueryModelRequest queryModelRequest) {
        return modelConfigApplicationService.getModels(queryModelRequest);
    }

    /**
     * 获取模型详情
     *
     * @param modelId 模型 ID
     * @return 模型详情
     */
    @GetMapping("/{modelId}")
    public ModelConfig getModelDetail(@PathVariable String modelId) {
        return modelConfigApplicationService.getModelDetail(modelId);
    }

    /**
     * 创建模型配置
     *
     * @param createModelRequest 创建模型配置请求
     * @return 创建的模型配置
     */
    @PostMapping("/create")
    public ModelConfig createModel(@RequestBody @Valid CreateModelRequest createModelRequest) {
        return modelConfigApplicationService.createModel(createModelRequest);
    }

    /**
     * 更新模型配置
     *
     * @param modelId            模型 ID
     * @param updateModelRequest 更新模型配置请求
     * @return 更新后的模型配置
     */
    @PutMapping("/{modelId}")
    public ModelConfig updateModel(@PathVariable String modelId, @RequestBody @Valid CreateModelRequest updateModelRequest) {
        return modelConfigApplicationService.updateModel(modelId, updateModelRequest);
    }

    /**
     * 删除模型配置
     *
     * @param modelId 模型 ID
     */
    @DeleteMapping("/{modelId}")
    public void deleteModel(@PathVariable String modelId) {
        modelConfigApplicationService.deleteModel(modelId);
    }
}
