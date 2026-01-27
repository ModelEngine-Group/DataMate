"""
数据生成模块
负责生成符合常识的随机可变信息数据
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from faker import Faker
import re


class DataGenerator:
    """数据生成器 - 生成贷款结清证明的可变信息"""

    # 银行列表
    BANKS = [
        "中国工商银行", "中国建设银行", "中国农业银行", "中国银行",
        "交通银行", "招商银行", "中信银行", "浦发银行",
        "兴业银行", "民生银行", "光大银行", "平安银行", "华夏银行"
    ]

    # 征信专线名称
    CREDIT_LINES = ["个人征信查询专线", "征信服务热线", "客户服务专线"]

    # 地址模板
    ADDRESSES = [
        "北京市朝阳区建国路88号",
        "上海市浦东新区陆家嘴环路1000号",
        "广州市天河区天河路123号",
        "深圳市福田区深南大道5000号",
        "杭州市西湖区文三路398号",
        "南京市鼓楼区汉中路168号",
        "成都市武侯区天府大道北段",
        "武汉市江汉区新华路218号",
        "西安市雁塔区高新路25号",
        "重庆市渝中区解放碑步行街"
    ]

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

    def generate_customer_name(self) -> str:
        """生成客户姓名"""
        return self.faker.name()

    def generate_id_card(self) -> str:
        """
        生成符合格式的身份证号码

        Returns:
            18位身份证号码
        """
        # 生成地区码（前6位）- 使用常见地区
        area_codes = [
            "110101",  # 北京市东城区
            "310101",  # 上海市黄浦区
            "440303",  # 深圳市罗湖区
            "440106",  # 广州市天河区
            "320106",  # 南京市鼓楼区
            "330106",  # 杭州市西湖区
            "510107",  # 成都市武侯区
        ]
        area_code = random.choice(area_codes)

        # 生成出生日期（8位）- 1970-2000年出生
        start_date = datetime(1970, 1, 1)
        end_date = datetime(2000, 12, 31)
        birth_date = self.faker.date_between(start_date, end_date)
        birth_str = birth_date.strftime("%Y%m%d")

        # 生成顺序码（3位）
        sequence_code = f"{random.randint(1, 999):03d}"

        # 计算校验码（1位）
        id_17 = area_code + birth_str + sequence_code
        check_code = self._calculate_id_check_code(id_17)

        return id_17 + check_code

    def _calculate_id_check_code(self, id_17: str) -> str:
        """计算身份证校验码"""
        weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_codes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']

        total = sum(int(id_17[i]) * weights[i] for i in range(17))
        return check_codes[total % 11]

    def generate_credit_line(self) -> str:
        """生成征信专线名称"""
        return random.choice(self.CREDIT_LINES)

    def generate_bank(self) -> str:
        """生成贷款银行"""
        return random.choice(self.BANKS)

    def generate_loan_account(self) -> str:
        """
        生成贷款账号

        Returns:
            格式如: 2024011500001234567
        """
        year = random.randint(2020, 2024)
        month = f"{random.randint(1, 12):02d}"
        day = f"{random.randint(1, 28):02d}"
        random_num = f"{random.randint(0, 9999999):07d}"
        return f"{year}{month}{day}{random_num}"

    def generate_date_range(self, start_date: str, end_date: str) -> datetime:
        """
        在指定范围内生成日期

        Args:
            start_date: 起始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            datetime对象
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        return self.faker.date_between(start, end)

    def generate_loan_open_date(self) -> datetime:
        """生成贷款开立日期 (2020-2023)"""
        start = datetime(2020, 1, 1)
        end = datetime(2023, 12, 31)
        return self.faker.date_between(start, end)

    def generate_loan_due_date(self, open_date: datetime) -> datetime:
        """
        根据开立日期生成到期日期 (1-5年后)

        Args:
            open_date: 贷款开立日期

        Returns:
            到期日期
        """
        months = random.choice([12, 24, 36, 48, 60])
        year = open_date.year + months // 12
        month = open_date.month + months % 12
        if month > 12:
            year += 1
            month -= 12
        # 确保日期有效
        day = min(open_date.day, 28)
        return datetime(year, month, day)

    def calculate_loan_term(self, open_date: datetime, due_date: datetime) -> str:
        """
        计算贷款期限

        Args:
            open_date: 开立日期
            due_date: 到期日期

        Returns:
            期限字符串，如 "36个月"
        """
        months = (due_date.year - open_date.year) * 12 + (due_date.month - open_date.month)
        return f"{months}个月"

    def generate_credit_limit(self) -> str:
        """
        生成授信额度

        Returns:
            如 "150000元" (5万-50万之间)
        """
        amount = random.randint(50000, 500000)
        # 取整到千位
        amount = round(amount / 1000) * 1000
        return f"{amount}元"

    def parse_money_amount(self, money_str: str) -> int:
        """从金额字符串中提取数值"""
        return int(money_str.replace("元", "").replace(",", "").replace(".", ""))

    def format_money(self, amount: int) -> str:
        """格式化金额"""
        return f"{amount}元"

    def generate_repayment_amount(self, credit_limit_str: str) -> str:
        """
        生成应还款金额（本金+利息）

        Args:
            credit_limit_str: 授信额度字符串

        Returns:
            应还款金额字符串
        """
        principal = self.parse_money_amount(credit_limit_str)
        # 利息比例 0%-15%
        interest_rate = random.uniform(0, 0.15)
        total = int(principal * (1 + interest_rate))
        return self.format_money(total)

    def generate_actual_repayment(self, repayment_str: str) -> str:
        """
        生成实还款金额（通常等于应还款）

        Args:
            repayment_str: 应还款金额字符串

        Returns:
            实还款金额字符串
        """
        return repayment_str

    def generate_interest_status(self) -> str:
        """生成利息结清状态"""
        return "已结清"

    def generate_clear_date(self, due_date: datetime) -> datetime:
        """
        生成贷款结清日期（到期前后30天内）

        Args:
            due_date: 到期日期

        Returns:
            结清日期
        """
        days_offset = random.randint(-30, 60)
        return due_date + timedelta(days=days_offset)

    def generate_certificate_date(self, clear_date: datetime) -> datetime:
        """
        生成证明开具日期（结清后0-7天内）

        Args:
            clear_date: 结清日期

        Returns:
            证明开具日期
        """
        days_offset = random.randint(0, 7)
        return clear_date + timedelta(days=days_offset)

    def format_date(self, date: datetime) -> str:
        """格式化日期为中文格式"""
        return date.strftime("%Y年%m月%d日")

    def generate_issuer(self, bank: str) -> str:
        """
        根据银行生成证明出具单位

        Args:
            bank: 贷款银行名称

        Returns:
            证明出具单位全称
        """
        return f"{bank}股份有限公司"

    def generate_contact_name(self) -> str:
        """生成联系人姓名"""
        return self.faker.name()

    def generate_contact_phone(self) -> str:
        """生成联系电话（固定电话格式）"""
        # 区号 + 号码
        area_codes = ["010", "021", "020", "0755", "028", "025", "0571"]
        area = random.choice(area_codes)
        number = f"{random.randint(10000000, 99999999)}"
        return f"{area}-{number}"

    def generate_address(self) -> str:
        """生成银行地址"""
        return random.choice(self.ADDRESSES)

    def generate_single_record(self) -> Dict[str, Any]:
        """
        生成一条完整的贷款结清证明记录

        Returns:
            包含所有可变字段的字典
        """
        # 生成基础数据
        customer_name = self.generate_customer_name()
        id_card = self.generate_id_card()
        credit_line = self.generate_credit_line()
        bank = self.generate_bank()
        loan_account = self.generate_loan_account()

        # 生成日期相关数据（有依赖关系）
        open_date = self.generate_loan_open_date()
        due_date = self.generate_loan_due_date(open_date)
        loan_term = self.calculate_loan_term(open_date, due_date)

        credit_limit = self.generate_credit_limit()
        repayment_amount = self.generate_repayment_amount(credit_limit)
        actual_repayment = self.generate_actual_repayment(repayment_amount)

        interest_status = self.generate_interest_status()
        clear_date = self.generate_clear_date(due_date)
        certificate_date = self.generate_certificate_date(clear_date)

        issuer = self.generate_issuer(bank)
        contact_name = self.generate_contact_name()
        contact_phone = self.generate_contact_phone()
        address = self.generate_address()

        return {
            "客户姓名": customer_name,
            "身份证号码": id_card,
            "征信专线名称": credit_line,
            "贷款银行": bank,
            "贷款账户标识": loan_account,
            "贷款开立日期": self.format_date(open_date),
            "贷款到期日期": self.format_date(due_date),
            "贷款期限": loan_term,
            "授信额度": credit_limit,
            "应还款金额": repayment_amount,
            "实还款金额": actual_repayment,
            "利息结清状态": interest_status,
            "贷款结清日期": self.format_date(clear_date),
            "证明开具日期": self.format_date(certificate_date),
            "落款日期": self.format_date(certificate_date),  # 与证明开具日期相同
            "证明出具单位": issuer,
            "联系人姓名": contact_name,
            "联系电话": contact_phone,
            "地址": address
        }

    def generate_batch(self, count: int, seed: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        批量生成记录

        Args:
            count: 生成数量
            seed: 随机种子（可选）

        Returns:
            记录列表
        """
        if seed is not None:
            random.seed(seed)
            Faker.seed(seed)

        records = []
        for _ in range(count):
            records.append(self.generate_single_record())
        return records


if __name__ == "__main__":
    # 测试代码
    generator = DataGenerator(seed=42)

    print("=" * 60)
    print("生成一条测试记录")
    print("=" * 60)

    record = generator.generate_single_record()
    for key, value in record.items():
        print(f"{key}: {value}")

    print("\n" + "=" * 60)
    print("批量生成5条记录")
    print("=" * 60)

    batch = generator.generate_batch(5)
    for i, record in enumerate(batch):
        print(f"\n--- 记录 {i+1} ---")
        print(f"客户: {record['客户姓名']}")
        print(f"银行: {record['贷款银行']}")
        print(f"金额: {record['授信额度']}")
