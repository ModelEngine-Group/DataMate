"""
数据生成模块 - 生成符合常识的随机可变信息数据
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from faker import Faker

# 中文数字映射
DIGITS = ["零", "壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌", "玖"]
UNITS = ["", "拾", "佰", "仟"]
BIG_UNITS = ["", "万", "亿"]

# 姓氏和名字用字
SURNAMES = ["张", "王", "李", "刘", "陈", "杨", "赵", "黄", "周", "吴", "徐", "孙", "胡", "朱", "高", "林", "何", "郭",
            "马", "罗"]
GIVEN_NAMES = [
    "伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "军", "洋", "勇", "艳", "杰", "娟", "涛", "明", "超", "秀英", "霞",
    "平", "刚", "桂英", "玉兰", "建国", "国庆", "小红", "雪梅", "文静", "志伟", "建华", "婷婷", "佳琪", "子轩", "浩然", "欣怡"
]


def number_to_chinese(num_str):
    """
    将整数金额字符串转为中文大写金额
    :param num_str: 金额字符串 (如 '18900')
    :return: 中文大写金额 (如 '壹万捌仟玖佰元整')
    """
    try:
        num = int(float(num_str))
    except ValueError:
        return "零元整"

    if num == 0:
        return "零元整"

    def convert_section(n):
        """转换四位数以内的数字"""
        s = ""
        str_n = str(n).zfill(4)
        for i, digit in enumerate(str_n):
            d = int(digit)
            if d != 0:
                s += DIGITS[d] + UNITS[3 - i]
            else:
                if s and not s.endswith("零"):
                    s += "零"
        return s.rstrip("零")

    # 按照万、亿进行分段处理
    sections = []
    temp = num
    while temp > 0:
        sections.append(temp % 10000)
        temp //= 10000

    result = ""
    for i, sec in enumerate(reversed(sections)):
        if sec != 0:
            part = convert_section(sec)
            part += BIG_UNITS[len(sections) - 1 - i]
            result += part
        else:
            if result and not result.endswith("零") and i < len(sections) - 1:
                result += "零"

    result = result.rstrip("零")
    return (result or "零") + "元整"


class DataGenerator:
    """数据生成器 - 生成个人所得税完税证明的可变信息"""

    def __init__(self, seed: Optional[int] = None):
        """
        初始化数据生成器

        Args:
            seed: 随机种子，用于可复现的生成
        """
        self.faker = Faker('zh_CN')
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)

    def generate_name(self) -> str:
        """生成中文姓名"""
        return random.choice(SURNAMES) + random.choice(GIVEN_NAMES)

    def generate_id_number_masked(self) -> str:
        """
        生成脱敏的身份证号
        格式：11010119******1234
        """
        year = random.randint(1950, 2005)
        month = random.randint(1, 12)
        day = random.randint(1, 28)  # 简化处理，避免闰年问题
        suffix = f"{random.randint(1000, 9999):04d}"
        full_id = f"110101{year:04d}{month:02d}{day:02d}{suffix}"
        # 脱敏：隐藏出生日期部分 (索引8到13)
        return full_id[:8] + "******" + full_id[14:]

    def random_date_in_range(self, start, end) -> datetime:
        """在指定范围内随机生成日期"""
        delta = end - start
        random_days = random.randint(0, delta.days)
        return start + timedelta(days=random_days)

    def random_month_before(self, fill_date: datetime) -> str:
        """
        生成填发日期之前的某个月份字符串
        格式：xxxx年xx月
        """
        min_date = datetime(2020, 1, 1)
        max_date = fill_date - timedelta(days=1)
        if max_date < min_date:
            max_date = min_date
        random_dt = self.random_date_in_range(min_date, max_date)
        return f"{random_dt.year}年{random_dt.month:02d}月"

    def random_amount(self) -> str:
        """
        生成指定范围内的随机金额
        格式：xxxxx.00
        """
        amount = random.randint(1000, 100000)
        return f"{amount}.00"

    def generate_tax_record(self, fill_date: datetime) -> Dict[str, Any]:
        """
        生成单个纳税记录数据
        """
        # 生成随机金额
        salary_amt = self.random_amount()
        labor_amt = self.random_amount()
        royalty_amt = self.random_amount()

        # 计算总和
        total_int = int(float(salary_amt)) + int(float(labor_amt)) + int(float(royalty_amt))
        total_small = f"{total_int}.00"
        total_large = number_to_chinese(str(total_int))

        # 构建纳税项目列表
        tax_items = [
            {"item": "工资、薪金所得小计", "period": self.random_month_before(fill_date), "amount": salary_amt},
            {"item": "劳务报酬所得", "period": self.random_month_before(fill_date), "amount": labor_amt},
            {"item": "稿酬所得", "period": self.random_month_before(fill_date), "amount": royalty_amt}
        ]
        tax_name = self.generate_name()

        # 构建最终数据字典
        return {
            "文件属性": "附件2：年终为纳税人开具全年纳税情况的完税证明",
            "文件名称": "个人所得税完税证明",
            "文件名": f"{tax_name}_个人所得税完税证明",
            "纳税人姓名": tax_name,
            "纳税人身份证照类型": "居民身份证",
            "纳税人身份号码": self.generate_id_number_masked(),
            "凭证编码": f"({fill_date.year})市区个证{random.randint(1, 999):03d}号",
            "填发日期": f"填发日期：{fill_date.year}年{fill_date.month:02d}月{fill_date.day:02d}日",
            "纳税项目": tax_items,
            "工资、薪金所得小计": salary_amt,
            "劳务报酬所得": labor_amt,
            "稿酬所得": royalty_amt,
            "税款金额合计（小写）": total_small,
            "税款金额合计（大写）": total_large
        }

    def generate_batch(self, count: int, start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None, seed: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        批量生成记录

        Args:
            count: 生成数量
            start_date: 起始日期
            end_date: 结束日期
            seed: 随机种子（可选）

        Returns:
            记录列表
        """
        if seed is not None:
            random.seed(seed)
            Faker.seed(seed)

        if start_date is None:
            start_date = datetime(2024, 1, 1)
        if end_date is None:
            end_date = datetime(2025, 12, 30)

        records = []
        for _ in range(count):
            fill_date = self.random_date_in_range(start_date, end_date)
            records.append(self.generate_tax_record(fill_date))
        return records


if __name__ == "__main__":
    # 测试代码
    generator = DataGenerator(seed=42)

    print("=" * 60)
    print("生成一条测试记录")
    print("=" * 60)

    record = generator.generate_tax_record(datetime.now())
    for key, value in record.items():
        print(f"{key}: {value}")

    print("\n" + "=" * 60)
    print("批量生成5条记录")
    print("=" * 60)

    batch = generator.generate_batch(5)
    for i, record in enumerate(batch):
        print(f"\n--- 记录 {i+1} ---")
        print(f"纳税人: {record['纳税人姓名']}")
        print(f"凭证编码: {record['凭证编码']}")
        print(f"税款合计: {record['税款金额合计（小写）']}")
