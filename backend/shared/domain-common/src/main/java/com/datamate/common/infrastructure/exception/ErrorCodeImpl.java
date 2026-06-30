package com.datamate.common.infrastructure.exception;

import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class ErrorCodeImpl implements ErrorCode {
    private final String code;
    private final String message;

    public static ErrorCodeImpl of(String code, String message) {
        return new ErrorCodeImpl(code, message);
    }
}
