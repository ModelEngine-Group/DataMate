import presidio_analyzer as analyzer
import presidio_anonymizer as anonymizer
import spacy

from datamate.core.base_op import Mapper

from .custom_entities import id_recognizer, phone_recognizer, zipcode_recognizer, url_recognizer


class PiiDetector(Mapper):
    custom_ops = True

    def __init__(self, *args, **kwargs):
        super(PiiDetector, self).__init__(*args, **kwargs)
        self.support_language = kwargs.get("support_language", "zh")

        self.nlp_engine = None
        self.text_analyzer = None
        self.anom = None

        self.init_model(*args, **kwargs)

    def init_model(self, *args, **kwargs):
        spacy.load("zh_core_web_sm")
        provider = analyzer.nlp_engine.NlpEngineProvider(
            nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [
                    {"lang_code": "zh", "model_name": "zh_core_web_sm"}
                ]
            }
        )

        # 创建NLP Engine
        self.nlp_engine = provider.create_engine()

        #  初始化AnalyzerEngine
        self.text_analyzer = analyzer.AnalyzerEngine(nlp_engine=self.nlp_engine, supported_languages=["zh"])
        self.text_analyzer.registry.load_predefined_recognizers()
        for recognizer in [id_recognizer, phone_recognizer, zipcode_recognizer, url_recognizer]:
            self.text_analyzer.registry.add_recognizer(recognizer)

        # 初始化AnonymizerEngine
        self.anom = anonymizer.AnonymizerEngine()

    def execute(self, sample):
        self.read_file_first(sample)
        text = sample.get('text')
        analyzer_results = self.text_analyzer.analyze(text=text, language=self.support_language)
        res = self.anom.anonymize(text=text, analyzer_results=analyzer_results)
        sample['text'] = res.text
        return sample
