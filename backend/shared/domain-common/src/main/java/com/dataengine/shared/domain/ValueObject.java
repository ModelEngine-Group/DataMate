package com.dataengine.shared.domain;

/**
 * 值对象基类
 */
public abstract class ValueObject {
    
    @Override
    public abstract boolean equals(Object o);
    
    @Override
    public abstract int hashCode();
}
