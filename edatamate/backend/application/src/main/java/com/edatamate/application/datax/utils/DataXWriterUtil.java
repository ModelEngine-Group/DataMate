package com.edatamate.application.datax.utils;

import com.edatamate.application.datax.DataXConstant;
import com.edatamate.application.datax.dto.NasParameter;
import com.edatamate.application.datax.dto.Writer;

public class DataXWriterUtil {
    public static Writer generateNasWriter(String ip, String path, String prefix) {
        return Writer.builder()
                .name(DataXConstant.NAS_WRITER)
                .parameter(NasParameter.builder().ip(ip).path(path).prefix(prefix).build())
                .build();
    }
}
