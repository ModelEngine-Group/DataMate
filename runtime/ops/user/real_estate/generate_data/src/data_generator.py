"""
数据生成器 - 不动产权证
"""
import random
from faker import Faker

class DataGenerator:
    """不动产权证数据生成器"""

    def __init__(self, seed=None):
        """
        初始化数据生成器

        Args:
            seed: 随机种子，用于复现结果
        """
        if seed is not None:
            random.seed(seed)
            Faker.seed(seed)
        self.fake = Faker('zh_CN')

        # 固定 bbox 值（不动产权证13个字段的坐标）
        self.bboxes = [
            [530, 128, 565, 157],   # 地区标识
            [575, 125, 630, 154],   # 年份
            [642, 128, 720, 157],   # 县名
            [818, 125, 903, 154],   # 文档编号
            [642, 177, 920, 227],   # 权利人姓名
            [642, 227, 920, 277],  # 所有权形式
            [642, 277, 920, 327],  # 登记地址
            [642, 327, 920, 377],  # 不动产权证书号
            [642, 377, 920, 427],  # 权利类型
            [642, 427, 920, 477],  # 权利性质
            [642, 477, 920, 527],  # 用途
            [642, 527, 920, 577],  # 面积信息
            [642, 577, 920, 627]   # 土地使用期限
        ]

    def generate_county_name(self):
        """生成县名"""
        county_base = self.fake.random_element([
            "峰泾", "临安", "桐庐", "淳安", "建德", "宁海", "象山",
            "德清", "长兴", "安吉", "余姚", "慈溪", "诸暨", "义乌"
        ])
        return f"{county_base}县"

    def generate_doc_number(self):
        """生成文档编号（7位数字）"""
        return f"{self.fake.random_number(digits=7, fix_len=True)}"

    def generate_certificate_number(self):
        """生成不动产权证书号（15位数字）"""
        return f"{self.fake.random_number(digits=15, fix_len=True)}"

    def generate_area_info(self):
        """生成面积信息"""
        land_area = round(random.uniform(200, 500), 1)
        building_area = round(random.uniform(250, 600), 1)
        return f"土地使用权面积：{land_area}㎡/房屋建筑面积：{building_area}㎡"

    def generate_land_use_period(self):
        """生成土地使用期限"""
        start_year = self.fake.random_int(min=2000, max=2020)
        end_year = start_year + 70
        return f"{start_year}.01.07-{end_year}.01.07"

    def generate_single_record(self):
        """
        生成一条完整的不动产权证记录

        Returns:
            包含13个字段的字典
        """
        # 生成13个字段
        fields = [
            "沧",  # 地区标识（固定）
            str(self.fake.random_int(min=2020, max=2030)),  # 年份
            self.generate_county_name(),  # 县名
            self.generate_doc_number(),  # 文档编号
            self.fake.name(),  # 权利人姓名
            self.fake.random_element(["共同拥有", "单独所有", "家庭共有"]),  # 所有权形式
            self.fake.address().replace('\n', ' '),  # 登记地址
            self.generate_certificate_number(),  # 不动产权证书号
            self.fake.random_element(["房屋所有权/宅基地使用权", "国有建设用地使用权/房屋所有权"]),  # 权利类型
            self.fake.random_element(["划拨/个人产权", "出让/个人产权", "集体/家庭产权"]),  # 权利性质
            self.fake.random_element(["住宅", "商业", "办公", "工业", "仓储"]),  # 用途
            self.generate_area_info(),  # 面积信息
            self.generate_land_use_period()  # 土地使用期限
        ]

        # 组合字段和bbox
        return [{"type": field, "bbox": bbox} for field, bbox in zip(fields, self.bboxes)]

    def generate_records(self, count):
        """
        批量生成记录

        Args:
            count: 生成记录的数量

        Returns:
            记录列表
        """
        return [self.generate_single_record() for _ in range(count)]
