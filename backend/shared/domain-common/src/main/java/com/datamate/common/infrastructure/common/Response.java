package com.datamate.common.infrastructure.common;

import com.datamate.common.infrastructure.exception.ErrorCode;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.io.Serial;
import java.io.Serializable;

/**
 * 通用返回体
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class Response<T> implements Serializable {
    @Serial
    private static final long serialVersionUID = 1L;
    /**
     * 状态码
     */
    private String code;

    /**
     * 消息
     */
    private String message;

    /**
     * 数据
     */
    private T data;

    /**
     * 构造成功时的返回体
     *
     * @param data 返回数据
     * @param <T>  返回数据类型
     * @return 返回体内容
     */
    public static <T> Response<T> ok(T data) {
        return new Response<>("0", "success", data);
    }

    /**
     * 构造错误时的返回体
     *
     * @param errorCode 错误码
     * @param data      返回数据
     * @param <T>       返回数据类型
     * @return 返回体内容
     */
    public static <T> Response<T> error(ErrorCode errorCode, T data) {
        return new Response<>(errorCode.getCode(), errorCode.getMessage(), data);
    }

    public static <T> Response<T> error(ErrorCode errorCode) {
        return new Response<>(errorCode.getCode(), errorCode.getMessage(), null);
    }
}
