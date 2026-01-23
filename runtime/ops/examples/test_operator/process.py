
from typing import Dict, Any

from datamate.core.base_op import Mapper


class TestMapper(Mapper):
    """
    算子类名建议使用驼峰命名法定义，例如 TestMapper
    """

    def __init__(self, *args, **kwargs):
        """
        初始化参数
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.slider_param = float(kwargs.get("sliderParam", 0.5))
        self.switch_param = kwargs.get('switchParam', False)
        self.select_param = kwargs.get('selectParam', '')
        self.radio_param = kwargs.get('radioParam', '')
        self.range_param = kwargs.get('rangeParam', [0, 0])
        self.checkbox_param = kwargs.get('checkboxParam', [])
        self.input_param = kwargs.get('inputParam', '').strip()

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心处理逻辑
        :param sample: 输入的数据样本，通常包含 text_key 等字段
        :return: 处理后的数据样本
        """
        # 示例：获取文本并进行修改
        # input_text = sample['text']
        # processed_text = do_something(input_text)
        # sample['text'] = processed_text

        return sample