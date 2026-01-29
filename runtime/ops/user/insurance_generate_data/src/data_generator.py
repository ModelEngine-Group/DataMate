import csv
import os
import random
import string
from datetime import datetime, timedelta

# -------------------------- 1. 基础数据配置 --------------------------
provinces = [
    "北京市", "上海市", "广东省", "江苏省", "浙江省", "山东省",
    "四川省", "湖北省", "河南省", "湖南省", "河北省", "安徽省"
]

first_names = ["王", "李", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴","徐", "孙", "胡", "朱",
               "高", "林", "何", "郭", "马", "罗","梁", "宋", "郑", "谢", "韩", "唐", "冯", "于",
               "董", "萧","程", "曹", "袁", "邓", "许", "傅", "沈", "曾", "彭", "吕","苏", "卢",
               "蒋", "蔡", "贾", "丁", "魏", "薛", "叶", "阎"]
last_names = ["伟", "芳", "娜", "敏", "静", "强", "磊", "军", "洋", "杰","伟芳", "伟娜", "伟敏", "伟静", "伟强", "伟磊", "伟军",
              "伟洋", "伟杰","芳伟", "芳娜", "芳敏", "芳静", "芳强", "芳磊", "芳军", "芳洋", "芳杰","娜伟", "娜芳", "娜敏", "娜静",
              "娜强", "娜磊", "娜军", "娜洋", "娜杰","敏伟", "敏芳", "敏娜", "敏静", "敏强", "敏磊", "敏军", "敏洋", "敏杰","静伟",
              "静芳", "静娜", "静敏", "静强", "静磊", "静军", "静洋", "静杰","强伟", "强芳", "强娜", "强敏", "强静", "强磊", "强军",
              "强洋", "强杰","磊伟", "磊芳", "磊娜", "磊敏", "磊静", "磊强", "磊军", "磊洋", "磊杰","军伟", "军芳", "军娜", "军敏",
              "军静", "军强", "军磊", "军洋", "军杰","洋伟", "洋芳", "洋娜", "洋敏", "洋静", "洋强", "洋磊", "洋军", "洋杰","杰伟",
              "杰芳", "杰娜", "杰敏", "杰静", "杰强", "杰磊", "杰军", "杰洋","伟军", "伟洋", "伟杰", "伟磊", "伟强", "杰军", "杰洋",
              "杰磊", "杰强","军洋", "军杰", "军磊", "军强", "洋杰", "洋磊", "洋强", "磊强", "磊杰","强杰", "强军", "强洋", "强磊",
              "伟骁", "伟钧", "伟漾", "伟捷", "伟蔚","芳骁", "芳钧", "芳漾", "芳捷", "芳芬", "娜骁", "娜钧", "娜漾", "娜捷","娜囡",
              "敏骁", "敏钧", "敏漾", "敏捷", "敏闵", "静骁", "静钧", "静漾","静捷", "静婧", "强骁", "强钧", "强漾", "强捷", "强锵",
              "磊骁", "磊钧","磊漾", "磊捷", "磊碚", "军骁", "军钧", "军漾", "军捷", "军骏", "洋骁","洋钧", "洋漾", "洋捷", "洋烊",
              "杰骁", "杰钧", "杰漾", "杰捷", "杰隽","芬伟", "芬强", "芬磊", "芬军", "芬洋", "囡伟", "囡芳", "囡娜", "囡敏","闵静",
              "闵强", "闵磊", "闵军", "婧杰", "婧伟", "婧芳", "婧娜", "骁敏","骁静", "骁强", "骁磊", "骁军", "垒洋", "垒杰", "垒伟",
              "垒芳", "钧娜","钧敏", "钧静", "钧强", "漾磊", "漾军", "漾洋", "漾杰", "捷伟", "捷芳","捷娜", "捷敏", "捷静", "捷强",
              "捷磊", "捷军", "捷洋", "捷杰", "蔚强","蔚磊", "蔚军", "蔚洋", "蔚杰", "芬静", "芬杰", "囡静", "囡强", "闵洋","闵杰",
              "婧敏", "婧静", "婧强", "骁洋", "骁杰", "垒敏", "垒静", "垒强","钧磊", "钧军", "钧洋", "钧杰", "漾伟", "漾芳", "漾娜",
              "漾敏", "静芬","敏芬", "娜芬", "芳芬", "伟芬", "伟囡", "伟闵", "伟婧", "伟垒", "芳闵","芳婧", "芳垒", "芳钧", "娜闵",
              "娜婧", "娜垒", "娜钧", "敏闵", "敏婧"]

companies = [
    "XX科技有限公司", "XX建筑工程公司", "XX贸易有限公司", "XX公立医院",
    "XX教育咨询有限公司", "XX物流集团", "XX制造股份有限公司", "XX事业单位"
]

id_type = "居民身份证"


def generate_18_idcard():
    """生成18位随机身份证号（格式合规，最后一位支持X）"""
    area_codes = ["110101", "310101", "440101", "330106", "510104"]
    area_code = random.choice(area_codes)

    start_date = datetime(1970, 1, 1)
    end_date = datetime(2000, 12, 31)
    random_days = random.randint(0, (end_date - start_date).days)
    birth_date = start_date + timedelta(days=random_days)
    birth_code = birth_date.strftime("%Y%m%d")

    seq_code = random.randint(100, 999)
    check_codes = string.digits + "X"
    check_code = random.choice(check_codes)

    return f"{area_code}{birth_code}{seq_code}{check_code}"


def generate_insurance_time():
    """生成参保起止时间，格式：某年某月 - 某年某月（跨度1-10年）"""
    start_year = random.randint(2010, 2020)
    start_month = random.randint(1, 12)
    end_year = min(start_year + random.randint(1, 10), 2025)
    end_month = random.randint(1, 12)

    start_str = f"{start_year}年{start_month:02d}月"
    end_str = f"{end_year}年{end_month:02d}月"
    return f"{start_str} - {end_str}"


def generate_proof_date():
    """生成证明日期：2025年随机月份/日期"""
    year = 2025
    month = random.randint(1, 12)
    max_day = 28 if month == 2 else 30 if month in [4, 6, 9, 11] else 31
    day = random.randint(1, max_day)
    return f"{year}年{month:02d}月{day:02d}日"


def generate_random_person():
    """生成单条随机人员社保数据"""
    province = random.choice(provinces)
    name = random.choice(first_names) + random.choice(last_names)
    gender = random.choice(["男", "女"])
    id_card = generate_18_idcard()
    insurance_period = generate_insurance_time()
    company = random.choice(companies)
    pension = random.randint(12, 120)
    injury = random.randint(12, 120)
    unemployment = random.randint(12, 120)
    proof_date = generate_proof_date()

    return [
        province, name, gender, id_card, id_type,
        insurance_period, company, pension, injury, unemployment, proof_date
    ]


def generate_csv(count=5, output_dir="output/data"):
    """生成CSV文件"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    headers = [
        "省份名", "姓名", "性别", "证件号码", "证件类型",
        "参保起止时间", "单位", "养老", "工伤", "失业", "证明时间"
    ]

    rows = [headers]
    for _ in range(count):
        rows.append(generate_random_person())

    csv_path = os.path.join(output_dir, "data.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(
            f,
            quoting=csv.QUOTE_ALL,
            quotechar='"',
            escapechar='\\'
        )
        for row in rows:
            if row != headers:
                row[3] = f"\t{row[3]}"
            writer.writerow(row)

    return csv_path, len(rows) - 1
