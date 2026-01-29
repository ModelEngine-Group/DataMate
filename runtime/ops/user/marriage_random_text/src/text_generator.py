# -*- coding: utf-8 -*-
"""结婚证随机文本生成逻辑，从 MarriageCertificate/random_text 抽取。"""
import json
import os
import random
import copy
import uuid
from typing import List, Dict, Any, Optional

# 随机数据源
SURNAMES = ['王', '李', '张', '刘', '陈', '杨', '赵', '黄', '周', '吴', '徐', '孙', '胡', '朱', '高',
            '林', '何', '郭', '马', '罗', '梁', '宋', '郑', '谢', '韩', '唐', '冯', '于', '董', '萧']

GIVEN_NAMES = ['伟', '芳', '娜', '秀英', '敏', '静', '丽', '强', '磊', '军', '洋', '勇', '艳', '杰', '娟',
               '涛', '明', '超', '秀兰', '霞', '平', '刚', '桂英', '丹', '玲', '华', '文', '博', '雪', '婷',
               '子轩', '梓涵', '浩然', '雨萱', '欣怡', '思远', '嘉琪', '子豪', '美玲', '建华', '志强', '俊杰']

NATIONALITIES = ['中国', '中华人民共和国']

PROVINCES = ['北京', '上海', '天津', '重庆', '河北', '山西', '辽宁', '吉林', '黑龙江', '江苏',
             '浙江', '安徽', '福建', '江西', '山东', '河南', '湖北', '湖南', '广东', '四川']

DISTRICT_NAMES = ['东城', '西城', '朝阳', '海淀', '丰台', '石景山', '通州', '顺义', '房山', '大兴',
                  '昌平', '怀柔', '平谷', '密云', '延庆', '南山', '福田', '罗湖', '宝安', '龙岗']


def _generate_random_name():
    surname = random.choice(SURNAMES)
    given_name = random.choice(GIVEN_NAMES)
    return surname + given_name


def _generate_random_date(start_year=1950, end_year=2005):
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{year}年{month:02d}月{day:02d}日"


def _generate_random_id_number(birth_date_str):
    try:
        year = birth_date_str[:4]
        month = birth_date_str[5:7]
        day = birth_date_str[8:10]
    except Exception:
        year = str(random.randint(1970, 2000))
        month = f"{random.randint(1, 12):02d}"
        day = f"{random.randint(1, 28):02d}"
    area_code = str(random.randint(110000, 659999))
    birth_code = f"{year}{month}{day}"
    seq_code = f"{random.randint(0, 999):03d}"
    check_codes = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'X']
    check_code = random.choice(check_codes)
    return f"{area_code}{birth_code}{seq_code}{check_code}"


def _generate_marriage_cert_number(register_date_str):
    try:
        year = register_date_str[:4]
    except Exception:
        year = str(random.randint(1990, 2024))
    prefix = f"J{random.randint(100000, 999999)}"
    seq = f"{random.randint(1, 99999):05d}"
    return f"{prefix}-{year}-{seq}"


def _generate_random_registration_office():
    province = random.choice(PROVINCES)
    district = random.choice(DISTRICT_NAMES)
    return f"{province}市民政局{district}区"


def _generate_random_text_by_label(label_name: str, original_text: str, context: Optional[Dict] = None) -> str:
    if context is None:
        context = {}
    if label_name == '持证人':
        return _generate_random_name()
    elif label_name == '登记日期':
        date = _generate_random_date(1980, 2024)
        context['登记日期'] = date
        return date
    elif label_name == '结婚证字号':
        register_date = context.get('登记日期', '2020年01月01日')
        return _generate_marriage_cert_number(register_date)
    elif label_name in ['男方姓名', '女方姓名']:
        name = _generate_random_name()
        context[label_name] = name
        return name
    elif label_name in ['男方国籍', '女方国籍']:
        return random.choice(NATIONALITIES)
    elif label_name == '男方出生日期':
        date = _generate_random_date(1950, 2000)
        context['男方出生日期'] = date
        return date
    elif label_name == '女方出生日期':
        date = _generate_random_date(1950, 2000)
        context['女方出生日期'] = date
        return date
    elif label_name == '男方身份证件号':
        birth_date = context.get('男方出生日期', '1980年01月01日')
        return _generate_random_id_number(birth_date)
    elif label_name == '女方身份证件号':
        birth_date = context.get('女方出生日期', '1980年01月01日')
        return _generate_random_id_number(birth_date)
    elif label_name == '登记机关':
        return _generate_random_registration_office()
    elif label_name == '婚姻登记':
        return '结婚登记专用章'
    elif label_name == '备注':
        return ''
    else:
        return original_text if original_text else ''


def parse_labelstudio_like(data: Any) -> List[Dict]:
    """解析 Label Studio 风格的 coordinate_info.json，返回 original_values 列表。"""
    original_values = []
    if not isinstance(data, list) or len(data) == 0:
        return original_values
    first = data[0]
    annotations = first.get('annotations') or []
    if len(annotations) == 0:
        return original_values
    results = annotations[-1].get('result', [])
    for r in results:
        value = r.get('value', {})
        labels = value.get('rectanglelabels') or []
        if not labels:
            continue
        label_name = labels[0]
        bbox = {
            'x': value.get('x'),
            'y': value.get('y'),
            'width': value.get('width'),
            'height': value.get('height')
        }
        entry = {
            'label_name': label_name,
            'text': '',
            'bbox': bbox,
            'original_width': r.get('original_width'),
            'original_height': r.get('original_height'),
            'image_rotation': r.get('image_rotation')
        }
        original_values.append(entry)
    return original_values


def generate_one_group(original_values: List[Dict]) -> List[Dict]:
    """生成一组 values 数据。"""
    new_values = copy.deepcopy(original_values)
    context = {}
    for value in new_values:
        label_name = value.get('label_name', '')
        original_text = value.get('text', '')
        if label_name in ['登记日期', '男方出生日期', '女方出生日期']:
            value['text'] = _generate_random_text_by_label(label_name, original_text, context)
    for value in new_values:
        label_name = value.get('label_name', '')
        original_text = value.get('text', '')
        if label_name not in ['登记日期', '男方出生日期', '女方出生日期']:
            value['text'] = _generate_random_text_by_label(label_name, original_text, context)
    male_name = None
    female_name = None
    for v in new_values:
        ln = v.get('label_name')
        if ln == '男方姓名' and v.get('text'):
            male_name = v.get('text')
        elif ln == '女方姓名' and v.get('text'):
            female_name = v.get('text')
    if not male_name and not female_name:
        male_name = _generate_random_name()
        female_name = _generate_random_name()
        for v in new_values:
            if v.get('label_name') == '男方姓名':
                v['text'] = male_name
            elif v.get('label_name') == '女方姓名':
                v['text'] = female_name
    else:
        for v in new_values:
            if v.get('label_name') == '男方姓名' and not v.get('text') and male_name:
                v['text'] = male_name
            if v.get('label_name') == '女方姓名' and not v.get('text') and female_name:
                v['text'] = female_name
    for v in new_values:
        if v.get('label_name') == '持证人':
            cur = v.get('text')
            if cur and (cur == male_name or cur == female_name):
                continue
            choices = [n for n in (male_name, female_name) if n]
            if choices:
                v['text'] = random.choice(choices)
            else:
                v['text'] = _generate_random_name()
    return new_values


def build_content_only_data(num_generate: int, all_generated_data: List[Dict]) -> Dict[str, Any]:
    """从完整组数据构建仅含 label/text 的 content_only 结构。"""
    content_only_groups = []
    for group in all_generated_data:
        contents = []
        for v in group.get('values', []):
            label = v.get('label_name')
            text = v.get('text')
            if label is not None:
                contents.append({'label': label, 'text': text})
        content_only_groups.append({'group_id': group.get('group_id'), 'contents': contents})
    return {
        'num_generated': num_generate,
        'generated_groups': content_only_groups
    }


def process_coordinate_and_generate(
    input_path: str,
    output_dir: str,
    num_generate: int,
) -> Optional[Dict[str, Any]]:
    """
    读取坐标 JSON，生成 num_generate 组数据，并返回 content_only 结构（不写文件）。
    若无法提取模板则返回 None。
    """
    if not os.path.exists(input_path):
        return None
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    original_values = []
    if isinstance(data, dict) and 'parsed_json' in data and 'values' in data['parsed_json']:
        original_values = data['parsed_json']['values']
    else:
        original_values = parse_labelstudio_like(data)
    if not original_values:
        return None
    all_generated_data = []
    for _ in range(num_generate):
        new_values = generate_one_group(original_values)
        all_generated_data.append({
            'group_id': str(uuid.uuid4()),
            'values': new_values,
            'key_value_pairs': [{'label': v['label_name'], 'value': v['text']} for v in new_values if 'label_name' in v]
        })
    return build_content_only_data(num_generate, all_generated_data)
