# -*- coding: utf-8 -*-

"""
Description:
    贷款数据生成器 - 生成虚拟贷款调查报告的随机数据
Create: 2025/01/28
"""

import json
import random
import os
import re
from datetime import datetime, timedelta
from typing import Dict, Any

from loguru import logger

from datamate.core.base_op import Mapper


class LoanReportDataGenerator(Mapper):
    """贷款数据生成器"""

    def __init__(self, *args, **kwargs):
        super(LoanReportDataGenerator, self).__init__(*args, **kwargs)
        self._data_dir = None
        self._sequence_file = None
        self._output_dir = None
        self._batch_count = int(kwargs.get("batchCount", 10))
        self._start_sequence = int(kwargs.get("startSequence", 0))

    def _generate_id_number(self) -> str:
        """生成虚拟身份证号码"""
        area_code = "110101"
        birth_year = random.randint(1985, 1990)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        birth_date = f"{birth_year:04d}{birth_month:02d}{birth_day:02d}"
        sequence = random.randint(100, 999)
        check_code = random.randint(0, 9)
        return f"{area_code}{birth_date}{sequence}{check_code}"

    def _generate_phone_number(self) -> str:
        """生成虚拟手机号码"""
        prefixes = ["138", "139", "150", "151", "152", "158", "159", "186", "187", "188"]
        prefix = random.choice(prefixes)
        suffix = "".join([str(random.randint(0, 9)) for _ in range(8)])
        return prefix + suffix

    def _format_currency(self, amount: int) -> str:
        """格式化货币为千分位分隔"""
        return f"{amount:,}"

    def _calculate_monthly_payment(self, principal: float, annual_rate: float, months: int) -> float:
        """计算等额本息月供"""
        monthly_rate = annual_rate / 12 / 100
        if monthly_rate == 0:
            return principal / months
        return principal * monthly_rate * (1 + monthly_rate) ** months / ((1 + monthly_rate) ** months - 1)

    def _generate_loan_data(self) -> Dict[str, Any]:
        """生成完整的贷款调查报告数据"""
        # 随机生成虚拟人物基本信息
        first_names = ["张", "李", "王", "刘", "陈", "杨", "赵", "黄", "周", "吴"]
        male_names = ["伟强", "志强", "明辉", "建国", "建华", "文斌", "海涛", "建军", "德华", "志华",
                      "俊凯", "俊杰", "宇轩", "浩然", "子轩", "文轩", "铭轩", "雨轩", "思涵", "思彤"]
        female_names = ["秀英", "桂英", "丽华", "玉兰", "凤英", "素芬", "秀兰", "玉梅", "海燕", "春梅",
                        "雨桐", "思彤", "诗涵", "雨涵", "思琪", "雨琪", "芯怡", "诗怡", "雨萱", "思颖"]

        # 生成借款人姓名（80%概率为3个字）
        if random.random() < 0.8:
            borrower_name = random.choice(first_names) + random.choice(male_names)
        else:
            single_names = ["伟", "强", "磊", "洋", "勇", "军", "杰", "涛", "超", "明", "丽", "静", "敏", "芳", "娜"]
            borrower_name = random.choice(first_names) + random.choice(single_names)

        borrower_age = random.randint(25, 55)
        borrower_id = self._generate_id_number()
        marital_status = random.choice(["已婚", "未婚", "离异"])

        # 配偶信息
        if marital_status == "已婚":
            spouse_name = random.choice(first_names) + random.choice(female_names)
            spouse_age = random.randint(23, 53)
            spouse_id = self._generate_id_number()
            spouse_monthly_income = random.randint(8000, 35000)
            has_spouse = True
        else:
            spouse_name = ""
            spouse_age = ""
            spouse_id = ""
            spouse_monthly_income = 0
            has_spouse = False

        # 贷款基本信息
        loan_amount = random.choice([500000, 800000, 1000000, 1500000, 2000000, 3000000])
        loan_term = random.choice([60, 120, 180, 240, 300, 360])
        interest_rate = random.choice([3.8, 4.0, 4.2, 4.3, 4.5, 4.8])
        monthly_payment = self._calculate_monthly_payment(loan_amount, interest_rate, loan_term)

        # 收入信息
        borrower_monthly_income = random.randint(15000, 50000)
        family_monthly_income = borrower_monthly_income + spouse_monthly_income
        other_monthly_debt = random.randint(0, 8000)
        property_fee = random.randint(200, 1500)

        # DTI计算
        loan_dti = (monthly_payment / family_monthly_income) * 100
        total_monthly_debt = monthly_payment + other_monthly_debt
        total_dti = (total_monthly_debt / family_monthly_income) * 100

        # 抵押物信息
        property_value = loan_amount * random.randint(2, 4)
        property_area = random.uniform(60, 200)
        property_age = random.randint(0, 20)
        transaction_price = property_value * random.uniform(1.0, 1.2)
        ltv = (loan_amount / property_value) * 100

        # 其他信息
        branches = ["北京分行营业部", "上海分行营业部", "广州分行营业部", "深圳分行营业部", "天津分行营业部"]
        managers = ["王经理", "李经理", "张经理", "陈经理", "刘经理", "赵经理"]
        occupations = ["企业职工", "公务员", "教师", "医生", "工程师", "销售经理"]
        credit_record = ["无", "无", "无", "无", "有轻微逾期记录"]
        companies = [
            "北京科技创新有限公司", "上海金融科技集团", "广州互联网科技公司",
            "深圳软件开发公司", "天津制造业集团"
        ]
        positions = ["项目经理", "技术总监", "财务经理", "运营主管", "市场总监"]
        districts = ["海淀区", "朝阳区", "西城区", "东城区", "丰台区"]
        streets = ["中关村大街", "金融街", "王府井大街", "建国路", "长安街"]
        communities = ["科技园小区", "金融城小区", "商务中心小区", "文化小区", "国际花园"]

        property_address = f"北京市{random.choice(districts)}{random.choice(streets)}{random.randint(100, 999)}号{random.choice(communities)}A座{random.randint(1, 30)}单元{random.randint(101, 3001)}室"

        # 生成完整数据结构
        loan_data = {
            "基本信息": {
                "经办机构": random.choice(branches),
                "填表日期": datetime.now().strftime("%Y年%m月%d日"),
                "经办客户经理": random.choice(managers),
                "电话": self._generate_phone_number()
            },
            "贷款申请信息": {
                "借款人姓名": borrower_name,
                "借款人身份证号码": borrower_id,
                "借款人配偶姓名": spouse_name,
                "借款人配偶身份证号码": spouse_id,
                "单笔金额(元)": self._format_currency(loan_amount),
                "单笔期限(月)": str(loan_term),
                "还款方式": "等额本息",
                "期供计算期(月)": "4",
                "贷款种类": "个人住房贷款",
                "申请贷款利率基准利率浮动": "按同期全国银行间同业拆借中心公布的贷款市场报价利率LPR+45个基点"
            },
            "借款人信息": {
                "职业性质": random.choice(occupations),
                "年龄(20-65岁)": str(borrower_age),
                "婚姻状况": marital_status,
                "家庭现有住房套数": str(random.randint(0, 3)),
                "是否本地常住": random.choice(["是", "否"]),
                "借款人及其配偶有无不良信用记录": random.choice(credit_record)
            },
            "偿还能力评估": {
                "借款人工作单位/岗位": f"{random.choice(companies)}/{random.choice(positions)}",
                "借款人收入证明材料": random.choice(["单位开具收入证明", "银行代发流水", "税务记录", "社保缴纳记录"]),
                "借款人月收入(元)": self._format_currency(borrower_monthly_income),
                "收入认定过程": random.choice(["工资代发及年终奖金", "银行流水统计", "多维度收入核实", "综合收入评估"]),
                "配偶工作单位/岗位": f"{random.choice(companies)}/{random.choice(positions)}" if has_spouse else "",
                "配偶收入证明材料": random.choice(["银行代发流水", "单位开具收入证明", "税务记录", "社保缴纳记录"]) if has_spouse else "",
                "配偶月收入(元)": self._format_currency(spouse_monthly_income) if has_spouse else "",
                "统计期间": (datetime.now() - timedelta(days=30)).strftime("%Y%m%d") + "-" + datetime.now().strftime("%Y%m%d"),
                "流入资金总笔数": str(random.randint(15, 50)),
                "流入总资金": self._format_currency(int(family_monthly_income * random.uniform(1.1, 1.5))),
                "月平均流入资金": self._format_currency(int(family_monthly_income * random.uniform(0.9, 1.1))),
                "本笔贷款月供支出(元)": self._format_currency(int(monthly_payment)),
                "家庭月收入总额(元)": self._format_currency(family_monthly_income),
                "本笔贷款所购房产物业费(元)": self._format_currency(property_fee),
                "本笔收入负债比(DTI≤50%)": f"{loan_dti:.2f}%",
                "家庭其余贷款月负债(不含本笔,元)": self._format_currency(other_monthly_debt),
                "总收入负债比(DTI≤55%)": f"{total_dti:.2f}%",
                "家庭月债总额": self._format_currency(int(total_monthly_debt))
            },
            "风险抵押详细信息": {
                "LTV(申请金额/押品评估价值)": f"{ltv:.2f}%",
                "抵押物现使用状态": random.choice(["自住", "出租", "空置"]),
                "房产名称及座别(座落地址)": property_address,
                "建筑面积(平方米)": f"{property_area:.1f}",
                "楼龄(年)": str(property_age),
                "评估价值(元)": self._format_currency(int(property_value)),
                "交易价格(元)": self._format_currency(int(transaction_price)),
                "评估单价(元/平方米)": self._format_currency(int(property_value / property_area)),
                "认定价值(元)": self._format_currency(int(property_value))
            },
            "调查结论": {
                "借款人基础资料真实齐全，贷款申请事实清晰、真实、有效": random.choice(["是", "否"]),
                "贷款用途合法合规，贷款担保物权属关系清晰": random.choice(["是", "否"]),
                "抵押物估值符合规定，抵押率符合审批要求": random.choice(["是", "否"]),
                "借款人及其配偶征信良好，无重大风险": random.choice(["是", "否"]),
                "经调查本住房贷款为借款人家庭自住使用": random.choice(["是", "否"])
            }
        }

        # 生成整体结论
        conclusions = loan_data["调查结论"]
        positive_count = sum(1 for v in conclusions.values() if v == "是")

        if positive_count >= 4:
            conclusion_text = "借款人资质良好，各项指标符合要求。"
        elif positive_count >= 2:
            conclusion_text = "借款人基本符合贷款条件，但存在部分风险点。"
        else:
            conclusion_text = "借款人存在较多风险因素，需谨慎评估。"

        # 添加具体分析和风险提示
        details = []
        risks = []
        if conclusions["借款人基础资料真实齐全，贷款申请事实清晰、真实、有效"] == "是":
            details.append("基础资料真实完整")
        else:
            risks.append("基础资料需核实")

        if conclusions["贷款用途合法合规，贷款担保物权属关系清晰"] == "是":
            details.append("贷款用途合规")
        else:
            risks.append("贷款用途需关注")

        if conclusions["抵押物估值符合规定，抵押率符合审批要求"] == "是":
            details.append("抵押物评估合规")
        else:
            risks.append("抵押物估值有疑问")

        if conclusions["借款人及其配偶征信良好，无重大风险"] == "是":
            details.append("征信状况良好")
        else:
            risks.append("征信存在风险")

        if conclusions["经调查本住房贷款为借款人家庭自住使用"] == "是":
            details.append("房产用途明确")
        else:
            risks.append("房产用途存疑")

        if details:
            conclusion_text += f"主要优势：{', '.join(details)}。"
        if risks:
            conclusion_text += f"需关注风险：{', '.join(risks)}。"

        if positive_count >= 4:
            conclusion_text += "建议批准贷款申请。"
        elif positive_count >= 2:
            conclusion_text += "建议补充材料后重新评估。"
        else:
            conclusion_text += "建议暂缓审批，要求补充完善相关材料。"

        loan_data["调查结论"]["整体结论"] = conclusion_text

        return loan_data

    def _get_next_sequence_number(self) -> str:
        """获取下一个序号（7位数字格式）"""
        # 读取当前序号
        if os.path.exists(self._sequence_file):
            with open(self._sequence_file, 'r', encoding='utf-8') as f:
                current = int(f.read().strip())
        else:
            current = 0
            # 如果有起始序号设置，优先使用
            if self._start_sequence > 0:
                current = self._start_sequence - 1
            else:
                # 从现有JSON文件获取最大序号
                if os.path.exists(self._data_dir):
                    for filename in os.listdir(self._data_dir):
                        if filename.startswith("虚拟贷款调查报告_") and filename.endswith(".json"):
                            match = re.search(r'虚拟贷款调查报告_(\d{7})-', filename)
                            if match:
                                seq = int(match.group(1))
                                if seq > current:
                                    current = seq

        next_num = current + 1

        # 更新计数器文件
        os.makedirs(self._data_dir, exist_ok=True)
        with open(self._sequence_file, 'w', encoding='utf-8') as f:
            f.write(str(next_num))

        return f"{next_num:07d}"

    def _save_loan_data(self, data: Dict[str, Any], sequence_number: str, borrower_name: str) -> str:
        """保存数据到JSON文件"""
        filename = f"虚拟贷款调查报告_{sequence_number}-{borrower_name}.json"
        filepath = os.path.join(self._data_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return filepath

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据生成"""
        file_path = sample.get('filePath')
        if not file_path.endswith('.docx') or os.path.normpath(file_path).count(os.sep) > 3:
            return sample

        logger.info(f"开始生成 {self._batch_count} 条贷款数据...")

        # 初始化序号计数器
        self._output_dir = sample['export_path']
        self._sequence_file = os.path.join(self._output_dir, ".sequence")
        self._data_dir = self._output_dir

        for i in range(self._batch_count):
            loan_data = self._generate_loan_data()
            borrower_name = loan_data['贷款申请信息']['借款人姓名']
            sequence_number = self._get_next_sequence_number()
            filepath = self._save_loan_data(loan_data, sequence_number, borrower_name)

            logger.info(f"[{i+1}/{self._batch_count}] 生成数据: {os.path.basename(filepath)}")

        os.remove(self._sequence_file)

        logger.info(f"完成生成 {self._batch_count} 条贷款数据，保存至: {self._data_dir}")

        return sample
