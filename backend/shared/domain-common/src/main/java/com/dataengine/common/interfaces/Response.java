package com.dataengine.common.interfaces;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Setter;

/**
 * 通用返回体
 */
@Getter
@Setter
@AllArgsConstructor
public class Response<T> {
    /** 成功状态码 */
    private static Integer SUCCESS_CODE = 0;

    /** 错误状态码 */
    private static Integer ERROR_CODE = 1;

    /** 状态码 */
    private Integer code;

    /** 消息 */
    private String message;

    /** 数据 */
    private T data;

    /**
     * 构造成功时的返回体
     *
     * @param data 返回数据
     * @return 返回体内容
     * @param <T> 返回数据类型
     */
    public static <T> Response<T> ok(T data) {
        return new Response<>(SUCCESS_CODE, "Success", data);
    }

    /**
     * 构造错误时的返回体
     *
     * @param message 失败信息
     * @param data 返回数据
     * @return 返回体内容
     * @param <T> 返回数据类型
     */
    public static <T> Response<T> error(String message, T data) {
        return new Response<>(ERROR_CODE, message, data);
    }
}
