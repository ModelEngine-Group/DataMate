package com.dataengine.common.domain;

/**
 * DDD值对象基类
 */
public abstract class ValueObject {
    
    @Override
    public abstract boolean equals(Object obj);
    
    @Override
    public abstract int hashCode();
    
    @Override
    public abstract String toString();
}
