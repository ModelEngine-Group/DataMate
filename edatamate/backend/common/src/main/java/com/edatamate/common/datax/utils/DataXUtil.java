package com.edatamate.common.datax.utils;


import com.edatamate.common.datax.dto.Parameter;
import com.edatamate.common.datax.dto.Reader;
import com.edatamate.common.datax.dto.Writer;

public class DataXUtil {
    private final static String READER = "reader";

    private final static String WRITER = "writer";

    public static Reader generateReader(Parameter parameter, String type) {
        return Reader.builder()
                .name(type + READER)
                .parameter(parameter)
                .build();
    }

    public static Writer generateWriter(Parameter parameter, String type) {
        return Writer.builder()
                .name(type + WRITER)
                .parameter(parameter)
                .build();
    }
}
