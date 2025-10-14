package com.dataengine.datamanagement.infrastructure.client;

import com.dataengine.datamanagement.infrastructure.client.dto.CollectionTaskDetailResponse;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

/**
 * 数据归集服务 Feign Client
 */
@FeignClient(name = "collection-service", url = "${collection.service.url:http://localhost:8080}")
public interface CollectionTaskClient {

    /**
     * 获取归集任务详情
     * @param taskId 任务ID
     * @return 任务详情
     */
    @GetMapping("/api/data-collection/tasks/{id}")
    CollectionTaskDetailResponse getTaskDetail(@PathVariable("id") String taskId);
}
