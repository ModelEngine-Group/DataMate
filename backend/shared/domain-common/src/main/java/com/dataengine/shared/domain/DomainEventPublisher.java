package com.dataengine.shared.domain;

import java.util.ArrayList;
import java.util.List;

/**
 * 领域事件发布器
 */
public class DomainEventPublisher {
    
    private static final ThreadLocal<List<DomainEvent>> events = new ThreadLocal<>();
    
    public static void publish(DomainEvent event) {
        if (events.get() == null) {
            events.set(new ArrayList<>());
        }
        events.get().add(event);
    }
    
    public static List<DomainEvent> getEvents() {
        return events.get() != null ? new ArrayList<>(events.get()) : new ArrayList<>();
    }
    
    public static void clear() {
        if (events.get() != null) {
            events.get().clear();
        }
    }
    
    public static void remove() {
        events.remove();
    }
}
