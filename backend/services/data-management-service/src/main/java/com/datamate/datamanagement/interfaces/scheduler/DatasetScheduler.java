package com.datamate.datamanagement.interfaces.scheduler;

import com.datamate.common.interfaces.PagedResponse;
import com.datamate.datamanagement.application.DatasetApplicationService;
import com.datamate.datamanagement.interfaces.dto.DatasetPagingQuery;
import com.datamate.datamanagement.interfaces.dto.DatasetResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.collections4.CollectionUtils;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

/**
 * 数据集定时任务触发
 *
 * @since 2025/10/24
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class DatasetScheduler {
    private final DatasetApplicationService datasetApplicationService;

    /**
     * 每天凌晨 00:00 扫描并删除超出保留期的数据集
     */
    @Scheduled(cron = "0 0 0 * * ?")
    public void cleanupExpiredDatasets() {
        int pageNo = 1;
        int pageSize = 500;

        while (true) {
            DatasetPagingQuery datasetPagingQuery = new DatasetPagingQuery();
            datasetPagingQuery.setPage(pageNo);
            datasetPagingQuery.setSize(pageSize);
            PagedResponse<DatasetResponse> datasets = datasetApplicationService.getDatasets(datasetPagingQuery);
            if (CollectionUtils.isEmpty(datasets.getContent())) {
                break;
            }

            datasets.getContent().forEach(dataset -> {
                Integer retentionDays = dataset.getRetentionDays();
                LocalDateTime createdAt = dataset.getCreatedAt();
                if (retentionDays != null && retentionDays > 0 && createdAt != null) {
                    LocalDateTime expireAt = createdAt.plusDays(retentionDays);
                    if (expireAt.isBefore(LocalDateTime.now())) {
                        try {
                            log.info("Deleting dataset {}, expired at {} (retentionDays={})", dataset.getId(), expireAt, retentionDays);
                            datasetApplicationService.deleteDataset(dataset.getId());
                        } catch (Exception e) {
                            log.warn("Failed to delete expired dataset {}: {}", dataset.getId(), e.getMessage());
                        }
                    }
                }
            });

            if (datasets.getPage() >= datasets.getTotalPages()) {
                break;
            }
            pageNo++;
        }
    }
}
