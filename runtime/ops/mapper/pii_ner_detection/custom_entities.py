import presidio_analyzer as analyzer

# 中国身份证号识别器
id_recognizer = analyzer.PatternRecognizer(
    supported_entity="ID_CHINA",
    supported_language="zh",
    patterns=[
        analyzer.Pattern(
            name="china_id_pattern",
            regex=r"\b[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b|\b[1-9]\d{7}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}\b",
            score=0.9
        )
    ],
    context=["身份证", "身份证明", "身份证号", "证件号码"]
)

# 中国电话号码识别器
phone_recognizer = analyzer.PatternRecognizer(
    supported_entity="Phone_CHINA",
    supported_language="zh",
    patterns=[
        analyzer.Pattern(
            name="china_mobile_pattern",
            regex=r"\b(1[3-9]\d{9})\b",
            score=0.85
        ),
        analyzer.Pattern(
            name="china_landline_pattern",
            regex=r"\b(0\d{2,3}-?\d{7,8})\b",
            score=0.8
        )
    ],
    context=["电话", "手机", "联系方式", "联系电话"]
)

# 中国邮编识别器
zipcode_recognizer = analyzer.PatternRecognizer(
    supported_entity="ZIPCODE_CHINA",
    supported_language="zh",
    patterns=[
        analyzer.Pattern(
            name="china_zipcode_pattern",
            regex=r"\b[1-9]\d{5}\b",
            score=0.7
        )
    ],
    context=["邮编", "邮政编码", "邮编号码"]
)

# 兼容中文域名的URL识别器
url_recognizer = analyzer.PatternRecognizer(
    supported_entity="URL",
    supported_language="zh",
    patterns=[
        analyzer.Pattern(
            name="url_pattern",
            regex=r"\b((?:https?://|www\.)[\w-]+\.[\w-]+\S*|(?:https?://|www\.)[\u4e00-\u9fa5]+\.[\u4e00-\u9fa5]+\S*)\b",
            score=0.9
        )
    ],
    context=["网址", "链接", "网站", "网页"]
)