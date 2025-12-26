package com.datamate.operator.domain.contants;

import java.util.HashMap;
import java.util.Map;

public class OperatorConstant {
    public static String SERVICE_ID = "operator";

    public static String YAML_PATH = "metadata.yml";

    public static String CATEGORY_PYTHON = "python";

    public static String CATEGORY_PYTHON_ID = "9eda9d5d-072b-499b-916c-797a0a8750e1";

    public static String CATEGORY_JAVA = "java";

    public static String CATEGORY_JAVA_ID = "b5bfc548-8ef6-417c-b8a6-a4197c078249";

    public static String CATEGORY_CUSTOMIZED_ID = "ec2cdd17-8b93-4a81-88c4-ac9e98d10757";

    public static String CATEGORY_TEXT_ID = "d8a5df7a-52a9-42c2-83c4-01062e60f597";

    public static String CATEGORY_IMAGE_ID = "de36b61c-9e8a-4422-8c31-d30585c7100f";

    public static String CATEGORY_AUDIO_ID = "42dd9392-73e4-458c-81ff-41751ada47b5";

    public static String CATEGORY_VIDEO_ID = "a233d584-73c8-4188-ad5d-8f7c8dda9c27";

    public static String CATEGORY_ALL_ID = "4d7dbd77-0a92-44f3-9056-2cd62d4a71e4";

    public static String CATEGORY_STAR_ID = "51847c24-bba9-11f0-888b-5b143cb738aa";

    public static String CATEGORY_PREDEFINED_ID = "96a3b07a-3439-4557-a835-525faad60ca3";

    public static Map<String, String> CATEGORY_MAP = new HashMap<>();

    static {
        CATEGORY_MAP.put(CATEGORY_PYTHON, CATEGORY_PYTHON_ID);
        CATEGORY_MAP.put(CATEGORY_JAVA, CATEGORY_JAVA_ID);
        CATEGORY_MAP.put("text", CATEGORY_TEXT_ID);
        CATEGORY_MAP.put("image", CATEGORY_IMAGE_ID);
        CATEGORY_MAP.put("audio", CATEGORY_AUDIO_ID);
        CATEGORY_MAP.put("video", CATEGORY_VIDEO_ID);
        CATEGORY_MAP.put("all", CATEGORY_ALL_ID);
    }
}
