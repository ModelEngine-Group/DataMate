package com.datamate.operator.infrastructure.parser;

import com.datamate.common.infrastructure.exception.BusinessException;
import com.datamate.common.infrastructure.exception.SystemErrorCode;
import com.datamate.operator.domain.contants.OperatorConstant;
import com.datamate.operator.infrastructure.exception.OperatorErrorCode;
import com.datamate.operator.interfaces.dto.OperatorDto;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.yaml.snakeyaml.LoaderOptions;
import org.yaml.snakeyaml.Yaml;
import org.yaml.snakeyaml.constructor.SafeConstructor;

import java.io.File;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;

public abstract class AbstractParser {
    protected ObjectMapper objectMapper = new ObjectMapper();

    protected OperatorDto parseYaml(InputStream yamlContent) {
        Yaml yaml = new Yaml(new SafeConstructor(new LoaderOptions()));
        Map<String, Object> content = yaml.load(yamlContent);
        OperatorDto operator = new OperatorDto();
        operator.setId(toStringIfNotNull(content.get("raw_id")));
        operator.setName(toStringIfNotNull(content.get("name")));
        operator.setDescription(toStringIfNotNull(content.get("description")));
        operator.setVersion(toStringIfNotNull(content.get("version")));
        operator.setInputs(toStringIfNotNull(content.get("inputs")));
        operator.setOutputs(toStringIfNotNull(content.get("outputs")));
        operator.setRuntime(toJsonIfNotNull(content.get("runtime")));
        operator.setSettings(toJsonIfNotNull(content.get("settings")));
        List<String> categories = new ArrayList<>();
        categories.add(OperatorConstant.CATEGORY_MAP.get(toLowerCaseIfNotNull(content.get("language"))));
        categories.add(OperatorConstant.CATEGORY_MAP.get(toLowerCaseIfNotNull(content.get("modal"))));
        categories.add(OperatorConstant.CATEGORY_MAP.getOrDefault(toLowerCaseIfNotNull(content.get("vendor")),
                OperatorConstant.CATEGORY_OTHER_VENDOR_ID));
        categories.add(OperatorConstant.CATEGORY_CUSTOMIZED_ID);
        operator.setCategories(categories);
        return operator;
    }

    /**
     * 从压缩包内读取指定路径的 yaml 文件并解析为指定类型
     * @param archive 压缩包路径（zip 或 tar）
     * @param entryPath 压缩包内部的文件路径，例如 "config/app.yaml" 或 "./config/app.yaml"
     * @return 解析后的对象
     */
    public abstract OperatorDto parseYamlFromArchive(File archive, String entryPath);

    /**
     * 将压缩包解压到目标目录（保持相对路径）
     * @param archive 压缩包路径
     * @param targetDir 目标目录
     */
    public abstract void extractTo(File archive, String targetDir);

    private String toStringIfNotNull(Object obj) {
        if (obj == null) {
            throw BusinessException.of(OperatorErrorCode.FIELD_NOT_FOUND);
        }
        return obj.toString();
    }

    private String toLowerCaseIfNotNull(Object obj) {
        if (obj == null) {
            throw BusinessException.of(OperatorErrorCode.FIELD_NOT_FOUND);
        }
        return obj.toString().toLowerCase(Locale.ROOT);
    }

    private String toJsonIfNotNull(Object obj) {
        try {
            return obj == null ? null : objectMapper.writeValueAsString(obj);
        } catch (JsonProcessingException e) {
            throw BusinessException.of(SystemErrorCode.UNKNOWN_ERROR, e.getMessage());
        }
    }
}
