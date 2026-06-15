from pycorrector import ProperCorrector
import json
import os


class MedicalCorrector:
    def __init__(self, use_proper_corrector=False, segment_length=100, max_text_length=200):
        """
        初始化医疗纠错器

        Args:
            use_proper_corrector: 是否使用 ProperCorrector 进行拼音和错别字纠正
                                 False: 仅使用混淆集（速度快，<1ms）
                                 True: 使用混淆集 + ProperCorrector（速度慢，~600ms）
            segment_length: 分段长度，当文本长度超过此值时进行分段处理以加速（默认100字符）
            max_text_length: 当文本长度超过此值时，自动禁用 ProperCorrector 以提升速度（默认200字符）
        """
        # 初始化自定义医疗混淆集（用于快速替换常见医疗术语错误）
        # 格式：错误词 -> 正确词
        # 按长度从长到短排序，优先匹配长词（避免短词覆盖长词）
        self.use_proper_corrector = use_proper_corrector
        self.segment_length = segment_length
        self.max_text_length = max_text_length
        
        # 从 JSON 文件加载纠错字典
        script_dir = os.path.dirname(os.path.abspath(__file__))
        confusion_dict_path = os.path.join(script_dir, "confusion_dict.json")
        with open(confusion_dict_path, 'r', encoding='utf-8') as f:
            self.confusion_dict = json.load(f)
        # 按长度从长到短排序，优先匹配长词
        self.sorted_keys = sorted(
            self.confusion_dict.keys(), key=len, reverse=True)

        # 可选：使用 ProperCorrector 进行拼音和错别字纠正（CPU版本）
        # ProperCorrector 使用混淆集 + 字频统计，不加载BERT，但速度较慢（~600ms）
        if self.use_proper_corrector:
            self.proper_corrector = ProperCorrector()
            print(
                f">>> [Corrector] 医疗混淆集和拼音纠错器加载完成")
        else:
            self.proper_corrector = None
            print(">>> [Corrector] 医疗混淆集加载完成（快速模式，仅使用混淆集）")

    def correct(self, text):
        """
        执行纠错：先使用混淆集快速替换，再使用ProperCorrector处理拼音和错别字
        """
        # 第一步：使用混淆集快速替换常见医疗术语错误
        corrected_text = text
        confusion_errors = []
        for wrong_word in self.sorted_keys:
            if wrong_word in corrected_text:
                corrected_text = corrected_text.replace(
                    wrong_word, self.confusion_dict[wrong_word])
                confusion_errors.append(
                    (wrong_word, self.confusion_dict[wrong_word]))

        # 第二步：可选使用 ProperCorrector 处理拼音错误和未预定义的错别字
        if self.use_proper_corrector and self.proper_corrector:
            # 智能策略：如果文本太长，自动跳过 ProperCorrector 以提升速度
            # ProperCorrector 对短文本效果好且快，对长文本慢且效果有限
            if len(corrected_text) > self.max_text_length:
                # 文本太长，仅使用混淆集
                final_text = corrected_text
                proper_errors = []
            elif len(corrected_text) > self.segment_length:
                # 中等长度文本，分段处理
                final_text, proper_errors = self._correct_with_segmentation(
                    corrected_text)
            else:
                # 短文本，直接处理（最快）
                proper_result = self.proper_corrector.correct(corrected_text)
                final_text = proper_result.get('target', corrected_text)
                proper_errors = proper_result.get('errors', [])
        else:
            # 仅使用混淆集，速度更快
            final_text = corrected_text
            proper_errors = []

        # 合并错误信息
        all_errors = confusion_errors + proper_errors

        return final_text, {
            'errors': all_errors,
            'source': text,
            'target': final_text,
            'confusion_errors': confusion_errors,
            'proper_errors': proper_errors
        }

    def _correct_with_segmentation(self, text):
        """
        分段处理长文本，提升 ProperCorrector 的处理速度
        """
        import re

        # 按句号、换行符等自然分隔符分段
        segments = re.split(r'([。\n])', text)
        # 重新组合，保留分隔符
        segments_with_sep = []
        for i in range(0, len(segments), 2):
            if i < len(segments):
                segment = segments[i]
                sep = segments[i+1] if i+1 < len(segments) else ''
                if segment.strip():
                    segments_with_sep.append((segment, sep))

        # 如果分段后仍然很长，按固定长度切分
        final_segments = []
        for segment, sep in segments_with_sep:
            if len(segment) <= self.segment_length:
                final_segments.append((segment, sep))
            else:
                # 按固定长度切分
                for i in range(0, len(segment), self.segment_length):
                    sub_segment = segment[i:i+self.segment_length]
                    final_segments.append(
                        (sub_segment, '' if i+self.segment_length < len(segment) else sep))

        # 分段处理
        corrected_parts = []
        all_proper_errors = []

        for segment, sep in final_segments:
            if segment.strip():
                proper_result = self.proper_corrector.correct(segment)
                corrected_parts.append(proper_result.get('target', segment))
                all_proper_errors.extend(proper_result.get('errors', []))
            corrected_parts.append(sep)

        final_text = ''.join(corrected_parts)
        return final_text, all_proper_errors


# --- 单元测试 ---
if __name__ == "__main__":
    corrector = MedicalCorrector()
    text = "患者尤下腹痛，既往有澜尾炎病史。"
    res, det = corrector.correct(text)
    print(f"原句: {text}")
    print(f"纠正: {res}")
    print(f"明细: {det}")
