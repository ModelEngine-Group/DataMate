package com.edatamate.application.datax;

public class DataXConstant {
    public static final String URL;

    public static final String NAS_READER = "nasreader";

    public static final String NAS_WRITER = "naswriter";

    static {
        String dataxUrl = System.getenv("DATAX_URL");
        if (dataxUrl == null) {
            dataxUrl = "http://datax:8000/process"; // 设置默认值
        }
        URL = dataxUrl;
    }
}
