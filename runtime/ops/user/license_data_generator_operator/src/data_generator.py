"""
数据生成器模块
提供营业执照随机数据生成功能
"""
import json
import os
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

# ============================================================================
# 数据集
# ============================================================================

# small data sets for generation
SURNAMES = ['王','李','张','刘','陈','杨','黄','赵','吴','周','徐','孙','马','朱','胡','林','何','高','郭','马']
GIVEN_CHARS = list('伟芳娜秀敏静丽强磊洋艳军杰涛超明秀红晨洁')

# Company name prefixes and suffixes
COMPANY_PREFIXES = ['星','诚','联','鸿','嘉','华','泰','瑞','安','鑫','盛','通','达','顺','康','福','德','信','和','兴']
COMPANY_SUFFIXES = ['科技','智能','信息','供应链','创新','发展','实业','建设','投资','控股','集团','贸易','制造','服务','咨询']
COMPANY_TYPES = ['有限公司','股份有限公司','个人独资企业','有限责任公司','国有独资公司','合伙企业','外商投资企业']

# Address components
PROVINCES = ['北京','上海','天津','重庆','河北','山西','辽宁','吉林','黑龙江','江苏','浙江','安徽','福建','江西','山东','河南','湖北','湖南','广东','海南','四川','贵州','云南','陕西','甘肃','青海','台湾','内蒙古','广西','西藏','宁夏','新疆','香港','澳门']
CITIES = ['市','区','县']
DISTRICTS = ['新华区','东山区','嘉禾区','江南区','银泰区','香樟区','和平区','建设区','中心区','发展区','科技区','商务区','工业区']
COMMUNITIES = ['江南小区','银泰花园','香樟里','嘉禾花园','新华花园','东湖花园','和平小区','建设小区','中心小区','科技小区','商务小区','工业小区']
BUILDING_TYPES = ['栋','号楼','座','大厦','中心','广场','大厦']

# Business scope keywords
BUSINESS_TYPES = ['教育','金融','电子商务','制造','服务','咨询','贸易','投资','建设','科技','信息','物流','医疗','文化','体育']
BUSINESS_ACTIVITIES = ['技术研发','产品销售','服务提供','咨询服务','贸易代理','投资管理','建设施工','科技推广','信息处理','物流配送','医疗服务','文化传播','体育赛事']

# Registration authorities
REG_AUTHORITIES = ['市场监督管理局','工商行政管理局','行政审批局','商务局','发展和改革委员会']


# ============================================================================
# 数据生成函数
# ============================================================================

def parse_coords(path: str) -> List[Dict[str, Any]]:
    """Load and do light validation of coords JSON.
    Returns parsed JSON (expects a list of annotation items as used by existing compositor).
    Raises FileNotFoundError / json.JSONDecodeError / ValueError on invalid structure.
    """
    data = load_json(path)
    if not isinstance(data, list):
        raise ValueError("coords JSON must be a list of annotation items")
    return data

def load_json(path):
    """Load JSON file. `path` may be relative to project root or absolute.
    Returns parsed JSON object.
    """
    if not os.path.isabs(path):
        # treat as relative to repo root
        # Get to project root (2 levels up from shared/utils/)
        current_dir = os.path.abspath(os.path.dirname(__file__))
        repo_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
        abs_path = os.path.join(repo_root, path)
    else:
        abs_path = path
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"JSON file not found: {abs_path}")
    with open(abs_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def gen_chinese_name():
    """Generate a random Chinese person name."""
    surname = random.choice(SURNAMES)
    # given name 1-2 chars
    g = ''.join(random.choice(GIVEN_CHARS) for _ in range(random.choice([1,2])))
    return surname + g


def gen_company_name():
    """Generate a random company name."""
    prefix = random.choice(COMPANY_PREFIXES)
    middle = random.choice(COMPANY_SUFFIXES)
    suffix = random.choice(COMPANY_TYPES)
    # Sometimes add extra characters
    if random.random() > 0.5:
        extra = random.choice(['股份','控股','集团','国际','中国'])
        return f"{prefix}{extra}{middle}{suffix}"
    return f"{prefix}{middle}{suffix}"


def gen_address():
    """Generate a random Chinese address."""
    province = random.choice(PROVINCES)
    city = random.choice(['市']) + random.choice(['东','西','南','北','中','新','古','金','银','玉','云','海','星','河','长'])
    district = random.choice(DISTRICTS)
    community = random.choice(COMMUNITIES)
    building_num = random.randint(1, 50)
    building_type = random.choice(BUILDING_TYPES)
    unit = random.randint(1, 10)
    room = random.randint(100, 9999)
    return f"{province}{city}{district}{community}{building_num}{building_type}{unit}单元{room}室"


def gen_company_type():
    """Generate a random company type."""
    return random.choice(COMPANY_TYPES)


def gen_business_scope():
    """Generate a random business scope description (max 18 Chinese characters)."""
    business_type = random.choice(BUSINESS_TYPES)
    # Select 1-2 activities to keep within 18 characters
    activities = random.sample(BUSINESS_ACTIVITIES, random.randint(1, 2))
    scope = f"从事{business_type}相关业务，包括{'、'.join(activities)}等"
    # Ensure max 18 characters
    if len(scope) > 18:
        # Fallback to shorter format
        scope = f"{business_type}相关业务"
        if len(scope) > 18:
            scope = business_type
    return scope


def gen_random_date(start_year=1980, end_year=2026):
    """Generate a random date in Chinese format."""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    d = start + timedelta(days=random.randint(0, delta.days))
    return d.strftime('%Y年%m月%d日')


def gen_registration_date():
    """Generate a reasonable registration date between 1990 and now."""
    return gen_random_date(1990, datetime.now().year)


def gen_issue_date(registration_date_str=None):
    """Generate an issue date (usually after registration date)."""
    if registration_date_str:
        try:
            reg_date = datetime.strptime(registration_date_str, '%Y年%m月%d日')
            min_year = reg_date.year
            max_year = min(reg_date.year + 5, datetime.now().year)
            return gen_random_date(min_year, max_year)
        except Exception:
            pass
    return gen_random_date(1990, datetime.now().year)


def gen_capital():
    """Generate a random capital amount (in 万元)."""
    amount = random.randint(100, 10000)
    return f"{amount}万元"


def gen_registration_number():
    """Generate a random business registration number.
    Format: 13 digits, with positions 7-8 as fixed letters 'BL', others are random digits.
    Example: 123456BL78901
    """
    # First 6 digits
    part1 = random.randint(100000, 999999)
    # Fixed letters 'BL' at positions 7-8
    fixed_letters = 'BL'
    # Last 5 digits
    part2 = random.randint(10000, 99999)
    return f"{part1}{fixed_letters}{part2}"


def gen_business_period(registration_date_str=None):
    """Generate a business period (营业期限)."""
    if registration_date_str:
        try:
            reg_date = datetime.strptime(registration_date_str, '%Y年%m月%d日')
            start_date = reg_date.strftime('%Y年%m月%d日')
        except Exception:
            start_date = gen_registration_date()
    else:
        start_date = gen_registration_date()
    # Most companies have "至长期" (to long-term/permanent)
    return f"{start_date} 至 长期"


def gen_issue_year(registration_date_str=None):
    """Generate issue year (after registration date by 1 or 2 years)."""
    if registration_date_str:
        try:
            reg_date = datetime.strptime(registration_date_str, '%Y年%m月%d日')
            # Issue year is 1 or 2 years after registration year
            years_after = random.choice([1, 2])
            issue_year = reg_date.year + years_after
            # Ensure issue year is not in the future
            issue_year = min(issue_year, datetime.now().year)
            return str(issue_year)
        except Exception:
            pass
    return str(datetime.now().year)


def gen_issue_month(registration_date_str=None):
    """Generate issue month (01-12)."""
    return f"{random.randint(1, 12):02d}"


def gen_issue_day(registration_date_str=None):
    """Generate issue day (01-31)."""
    return f"{random.randint(1, 31):02d}"


def gen_paid_in_capital(registered_capital_str: str = None) -> str:
    """Generate paid-in capital that is 90%-100% of registered capital."""
    if registered_capital_str:
        try:
            # Extract numeric value from registered capital string (e.g., "4250万元" -> 4250)
            amount = int(registered_capital_str.replace('万元', ''))
            # Calculate paid-in capital as 90%-100% of registered capital
            ratio = random.uniform(0.9, 1.0)
            paid_in = int(amount * ratio)
            return f"{paid_in}万元"
        except Exception:
            pass
    # Fallback: generate a random capital amount
    return gen_capital()


def generate_for_label(label: str, registered_capital=None) -> str:
    """Generate appropriate content for a given label."""
    l = label or ''
    # Match by keywords
    if '名称' in l and '公司' not in l:  # 公司名称
        return gen_company_name()
    if '住所' in l or '地址' in l:
        return gen_address()
    if '法定代表人' in l or '代表人' in l:
        return gen_chinese_name()
    if '公司类型' in l or '类型' in l:
        return gen_company_type()
    if '经营范围' in l:
        return gen_business_scope()
    if '成立日期' in l or '注册日期' in l:
        return gen_registration_date()
    if '营业期限' in l:
        return gen_business_period()
    if '注册资本' in l:
        return gen_capital()
    if '实收资本' in l:
        return gen_paid_in_capital(registered_capital)
    if '注册号' in l or '统一社会信用代码' in l:
        return gen_registration_number()
    # Note: "发证日期-年/月/日" are handled separately in generate_groups
    # Fallback
    return gen_company_name()


def extract_labels_from_coords(coords_path: str) -> list:
    """Extract labels from coords JSON in order of appearance and normalize known variants.
    Returns a list of labels (strings) in order they are first seen.
    """
    coords = parse_coords(coords_path)
    seen = []
    for item in coords:
        annotations = item.get('annotations', [])
        for ann in annotations:
            for res in ann.get('result', []):
                val = res.get('value', {})
                rect_labels = val.get('rectanglelabels') or val.get('labels') or []
                if isinstance(rect_labels, list):
                    for l in rect_labels:
                        if l not in seen:
                            seen.append(l)
                elif rect_labels:
                    if rect_labels not in seen:
                        seen.append(rect_labels)
    return seen


def generate_groups(coords_path: str, num_groups: int = 5):
    """Generate random text groups based on labels from coords JSON.

    Args:
        coords_path: Path to coords JSON file
        num_groups: Number of groups to generate

    Returns:
        List of group dictionaries with 'group_id' and 'contents'
    """
    # extract_labels_from_coords returns an ordered list; preserve that order
    labels = extract_labels_from_coords(coords_path)
    groups = []
    for i in range(1, num_groups + 1):
        contents = []
        # Track registration date and registered capital for consistency
        reg_date = None
        registered_capital = None
        # Track issue date components for consistency
        issue_year = None
        issue_month = None
        issue_day = None
        for label in labels:
            # First pass: generate registration date if needed
            if '成立日期' in label:
                reg_date = gen_registration_date()
                contents.append({'label': label, 'text': reg_date})
            elif '营业期限' in label:
                text = gen_business_period(reg_date) if reg_date else gen_business_period()
                contents.append({'label': label, 'text': text})
            elif '发证日期-年' in label:
                issue_year = gen_issue_year(reg_date)
                contents.append({'label': label, 'text': issue_year})
            elif '发证日期-月' in label:
                issue_month = gen_issue_month(reg_date)
                contents.append({'label': label, 'text': issue_month})
            elif '发证日期-日' in label:
                issue_day = gen_issue_day(reg_date)
                contents.append({'label': label, 'text': issue_day})
            elif '注册资本' in label:
                registered_capital = gen_capital()
                contents.append({'label': label, 'text': registered_capital})
            elif '实收资本' in label:
                text = gen_paid_in_capital(registered_capital)
                contents.append({'label': label, 'text': text})
            else:
                contents.append({'label': label, 'text': generate_for_label(label)})
        groups.append({'group_id': str(i), 'contents': contents})
    return groups
