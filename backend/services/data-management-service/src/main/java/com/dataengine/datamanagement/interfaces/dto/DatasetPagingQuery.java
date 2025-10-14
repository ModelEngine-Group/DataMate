package com.dataengine.datamanagement.interfaces.dto;

import com.dataengine.common.interfaces.PagingQuery;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.Arrays;
import java.util.List;

/**
 * 数据集分页查询请求
 *
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class DatasetPagingQuery extends PagingQuery {
    /**
     * 数据集类型过滤
     */
    private String type;

    /**
     * 标签过滤，多个标签用逗号分隔
     */
    private String tags;

    /**
     * 关键词搜索（名称或描述）
     */
    private String keyword;

    /**
     * 状态过滤
     */
    private String status;

    /**
     * 将逗号分隔的标签字符串转换为标签列表
     *
     * @return 标签列表，如果tags为空则返回null
     */
    public List<String> getTagList() {
        if (tags != null && !tags.trim().isEmpty()) {
            return Arrays.asList(tags.split(","));
        }
        return null;
    }
}
