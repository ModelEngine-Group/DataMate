package com.dataengine.shared.domain;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * 聚合根基类
 */
public abstract class AggregateRoot<ID> extends Entity<ID> {
    
    private List<DomainEvent> domainEvents = new ArrayList<>();
    
    protected AggregateRoot() {
        super();
    }
    
    protected AggregateRoot(ID id) {
        super(id);
    }
    
    protected void addDomainEvent(DomainEvent event) {
        this.domainEvents.add(event);
    }
    
    public List<DomainEvent> getDomainEvents() {
        return Collections.unmodifiableList(domainEvents);
    }
    
    public void clearDomainEvents() {
        this.domainEvents.clear();
    }
}
