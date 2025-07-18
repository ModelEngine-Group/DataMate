package com.edatamate.application.datax;


import com.alibaba.fastjson2.JSON;
import com.edatamate.application.datax.dto.Reader;
import com.edatamate.application.datax.dto.Writer;
import com.edatamate.application.datax.utils.DataXReaderUtil;
import com.edatamate.application.datax.utils.DataXWriterUtil;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.Map;


@Service
@RequiredArgsConstructor
public class DataXHandler {
    private final DataXClient dataXClient;

    public Map<String, Object> createNasJob(String ip, String path, String prefix, String destPath) {
        Reader reader = DataXReaderUtil.generateNasReader(ip, path, prefix);
        Writer writer = DataXWriterUtil.generateNasWriter(ip, path, prefix, destPath);
        return invokeDataX(generateConfig(reader, writer));
    }


    /**
     * 根据传入的参数生成DataX JSON配置文件
     *
     * @param reader reader部分的配置
     * @param writer writer部分的配置
     */
    public String generateConfig(Reader reader, Writer writer) {
        // 固定的settings部分
        Map<String, Object> settings = Map.of(
                "speed", Map.of("channel", 3),
                "errorLimit", Map.of("record", 0)
        );

        // 构建完整的JSON结构
        Map<String, Object> dataXConfig = Map.of(
                "job", Map.of(
                        "setting", settings,
                        "content", new Map[]{
                                Map.of(
                                        "reader", reader,
                                        "writer", writer
                                )
                        }
                )
        );

        // 使用FastJSON将Map转换为JSON并写入文件
        return JSON.toJSONString(dataXConfig);
    }

    /**
     * 调用DataX接口
     *
     * @param dataXConfig JSON配置字符串
     * @return 接口响应
     */
    public Map<String, Object> invokeDataX(String dataXConfig) {
        return dataXClient.process(Map.of("content", dataXConfig));
    }
}
