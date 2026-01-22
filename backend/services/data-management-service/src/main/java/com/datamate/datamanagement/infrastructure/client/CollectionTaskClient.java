package com.datamate.datamanagement.infrastructure.client;

import com.datamate.common.infrastructure.common.Response;
import com.datamate.datamanagement.infrastructure.client.dto.CollectionTaskDetailResponse;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestHeader;

/**
 * 数据归集服务 Feign Client
 */
@FeignClient(name = "collection-service", url = "${collection.service.url:http://datamate-backend-python:18000}")
public interface CollectionTaskClient {

    /**
     * 获取归集任务详情
     * @param taskId 任务ID
     * @return 任务详情
     */
    @GetMapping("/api/data-collection/tasks/{id}")
    Response<CollectionTaskDetailResponse> getTaskDetail(@PathVariable("id") String taskId, @RequestHeader("User") String authorization);
}
