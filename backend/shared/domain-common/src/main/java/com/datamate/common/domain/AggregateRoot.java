package com.datamate.common.domain;

import com.datamate.common.domain.model.base.BaseEntity;

/**
 * DDD聚合根基类
 */
public abstract class AggregateRoot<ID> extends BaseEntity<ID> {

    protected AggregateRoot() {
        super();
    }

    protected AggregateRoot(ID id) {
        super(id);
    }

    /**
     * 获取聚合版本号（用于乐观锁）
     */
    public abstract Long getVersion();

    /**
     * 设置聚合版本号
     */
    public abstract void setVersion(Long version);
}
