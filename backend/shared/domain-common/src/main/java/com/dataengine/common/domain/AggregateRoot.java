package com.dataengine.common.domain;

import java.time.LocalDateTime;
import java.util.Objects;

/**
 * DDD聚合根基类
 */
public abstract class AggregateRoot<ID> extends Entity<ID> {
    
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
