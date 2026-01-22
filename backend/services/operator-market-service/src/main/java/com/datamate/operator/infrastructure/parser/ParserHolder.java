package com.datamate.operator.infrastructure.parser;

import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import com.datamate.operator.infrastructure.exception.OperatorErrorCode;
import com.datamate.operator.interfaces.dto.OperatorDto;
import jakarta.annotation.PostConstruct;
import org.apache.commons.io.FileUtils;
import org.springframework.stereotype.Component;

import java.io.File;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class ParserHolder {
    // 存放 parser：key 为 parser 类型标识（例如 "zip" 或 "tar"），value 为 parser 实例
    private final Map<String, AbstractParser> parserMap = new ConcurrentHashMap<>();

    // 注册 parser（可在启动时调用）
    public void registerParser(String type, AbstractParser parser) {
        if (type == null || parser == null) {
            throw BusinessException.of(SystemErrorCode.UNKNOWN_ERROR);
        }
        parserMap.put(type, parser);
    }

    // 根据类型获取 parser（可能为 null）
    public AbstractParser getParser(String type) {
        return parserMap.get(type);
    }

    // 便捷代理：从指定类型的压缩包中读取 entry 并解析为 clazz
    public OperatorDto parseYamlFromArchive(String type, File archive, String entryPath) {
        AbstractParser parser = getParser(type);
        if (parser == null) {
            throw BusinessException.of(OperatorErrorCode.UNSUPPORTED_FILE_TYPE,
                "No parser registered for type: " + type);
        }
        return parser.parseYamlFromArchive(archive, entryPath);
    }

    // 便捷代理：将指定类型的压缩包解压到目标目录
    public void extractTo(String type, File archive, String targetDir) {
        AbstractParser parser = getParser(type);
        if (parser == null) {
            throw BusinessException.of(OperatorErrorCode.UNSUPPORTED_FILE_TYPE,
                "No parser registered for type: " + type);
        }
        parser.extractTo(archive, targetDir);
        FileUtils.deleteQuietly(archive);
    }

    public void extractTo(String type, String sourceDir, String targetDir) {
        extractTo(type, new File(sourceDir), targetDir);
    }

    @PostConstruct
    public void init() {
        // 注册 zip 和 tar parser，key 可根据需要调整（例如 "zip"/"tar"）
        registerParser("zip", new ZipParser());
        registerParser("tar", new TarParser());
    }
}
