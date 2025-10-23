package com.datamate.collection.interfaces.dto;

import com.datamate.collection.common.enums.TaskStatus;
import com.datamate.common.interfaces.PagingQuery;
import lombok.Getter;
import lombok.Setter;

/**
 * 归集任务分页查询参数
 *
 * @since 2025/10/23
 */
@Getter
@Setter
public class CollectionTaskPagingQuery extends PagingQuery {
    /**
     * 任务状态
     */
    private TaskStatus status;

    /**
     * 任务名称
     */
    private String name;
}
