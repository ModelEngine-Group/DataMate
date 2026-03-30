# -*- coding: utf-8 -*-

import sys
from pathlib import Path
from datamate.common.utils.custom_importer import CustomImporter


def _configure_importer():
    base_path = Path(__file__).resolve().parent
    sys.meta_path.append(CustomImporter(base_path))


_configure_importer()


def _import_operators():
    from . import content_cleaner
    from . import credit_card_number_cleaner
    from . import email_cleaner
    from . import emoji_cleaner
    from . import extra_space_cleaner
    from . import full_width_characters_cleaner
    from . import garble_characters_cleaner
    from . import html_tag_cleaner
    from . import id_number_cleaner
    from . import invisible_characters_cleaner
    from . import ip_address_cleaner
    from . import legend_cleaner
    from . import phone_number_cleaner
    from . import political_word_cleaner
    from . import sexual_and_violent_word_cleaner
    from . import text_to_word
    from . import traditional_chinese
    from . import unicode_space_cleaner
    from . import url_cleaner
    from . import xml_tag_cleaner
    from . import img_enhanced_brightness
    from . import img_enhanced_contrast
    from . import img_enhanced_saturation
    from . import img_enhanced_sharpness
    from . import img_perspective_transformation
    from . import img_direction_correct
    from . import img_denoise
    from . import img_shadow_remove
    from . import img_type_unify
    from . import img_resize
    from . import remove_duplicate_sentences
    from . import knowledge_relation_slice
    from . import pii_ner_detection
    from . import audio_format_convert
    from . import audio_anomaly_filter
    from . import audio_dc_offset_removal
    from . import audio_pre_emphasis
    from . import audio_simple_agc
    from . import audio_noise_gate
    from . import audio_soft_peak_limiter
    from . import audio_trim_silence_edges
    from . import audio_rms_loudness_normalize
    from . import audio_hum_notch
    from . import audio_telephony_bandpass


_import_operators()
