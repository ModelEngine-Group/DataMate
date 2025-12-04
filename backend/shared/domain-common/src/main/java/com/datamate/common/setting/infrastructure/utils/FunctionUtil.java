package com.datamate.common.setting.infrastructure.utils;

import lombok.extern.slf4j.Slf4j;

import java.util.function.BiConsumer;
import java.util.function.Consumer;
import java.util.function.Function;

@Slf4j
public class FunctionUtil {
    public static <T, R> R getWithoutThrow(Function<T, R> action, T key) {
        try {
            return action.apply(key);
        } catch (Exception e) {
            log.warn(e.getMessage());
            return null;
        }
    }

    public static <T> void doWithoutThrow(Consumer<T> action, T key) {
        try {
            action.accept(key);
        } catch (Exception e) {
            log.warn(e.getMessage());
        }
    }

    public static <T, R> void doWithoutThrow(BiConsumer<T, R> action, T t, R r) {
        try {
            action.accept(t, r);
        } catch (Exception e) {
            log.warn(e.getMessage());
        }
    }
}
