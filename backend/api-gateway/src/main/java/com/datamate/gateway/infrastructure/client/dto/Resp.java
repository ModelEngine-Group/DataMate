/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2026-2026. All rights reserved.
 */

package com.datamate.gateway.infrastructure.client.dto;

import lombok.Getter;

/**
 * oms-extension统一返回包装类
 *
 * @param code 状态码
 * @param msg 消息
 * @param data 数据
 * @param <T> 数据类
 */
public record Resp<T>(String code, String msg, T data) {
    public static final String SUCCESS = "0";

    /**
     * 成功
     * @param data 数据
     * @return 响应体
     * @param <T> 数据类型
     */
    public static <T> Resp<T> ok(T data) {
        return new Resp<>(SUCCESS, "success", data);
    }

    /**
     * 成功
     *
     * @return 响应体
     * @param <T> 数据类型
     */
    public static <T> Resp<T> ok() {
        return Resp.ok(null);
    }

    /**
     * 失败返回
     *
     * @param code 状态码
     * @param message 错误信息
     * @return 响应体
     * @param <T> 数据类型
     */
    public static <T> Resp<T> error(String code, String message) {
        return new Resp<>(code, message, null);
    }
}
