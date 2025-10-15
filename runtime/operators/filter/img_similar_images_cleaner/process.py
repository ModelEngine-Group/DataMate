# -- encoding: utf-8 --
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description:
    1.本算子结合感知哈希算法和ORB两个算法判断图片的相似性
    2.感知哈希算法则是从图像的整体结构和特征维度来计算图片的相似度。
    3.ORB算法可以用来对图像中的关键点快速创建特征向量，这些特征向量可以用来识别图像中的对象。通过比较两张图片的特征向量计算相似度。
    4.感知哈希算法和ORB算法计算相似度高于0.75，则选择二者较大值；若低于0.75，则选择二者最小值作为相似度
    5.将文件特征数据存到数据库。根据任务uuid获取历史文件特征，遍历特征并进行去重比较
Create: 2025/1/7
"""
import json
import logging as logger
import time
import zlib
from pathlib import Path
from typing import List, Dict, Any

import cv2
import numpy as np
from sqlalchemy import text

from data_platform.sql_manager.sql_manager import SQLManager
from data_platform.common.utils import get_now_time
from data_platform.common.utils import bytes_to_numpy
from data_platform.core.base_op import Filter

MAX_RETRIES = 5
BASE_DELAY = 1
MAX_DELAY = 30  # 最大延时设置为30秒
JITTER_FACTOR = 0.25  # 抖动因子为等待时间的25%
MAX_FEATURES_NUM = 200


def get_orb_des(image: np.ndarray) -> np.ndarray:
    """检测图像中的特征点kp和计算这些特征点的描述符矩阵des_matrix"""
    if not image.size:
        return np.array([])
    orb = cv2.ORB_create()  # 初始化ORB检测器
    orb.setMaxFeatures(MAX_FEATURES_NUM)  # 设置最大特征点数量为200
    kp, des_matrix = orb.detectAndCompute(image, None)
    if des_matrix is None:
        # 若没有提取出图像特征，描述符矩阵置为空
        des_matrix = np.array([])
    return des_matrix


class ImgSimilarImagesCleaner(Filter):
    """去除相似图片的插件"""

    DEFAULT_SIMILAR_THRESHOLD = 0.8  # 默认相似度阈值
    DEFAULT_TASK_UUID = "uuid"  # 默认任务UUID
    DEFAULT_ORB_RATIO = 0.8  # 默认特征点距离比率
    DEFAULT_MIX_SIMILARITY = 0.75  # 默认相似度算法阈值
    DEFAULT_IMG_RESIZE = 200  # 默认图片压缩尺寸
    DEFAULT_PAGE_SIZE = 500  # 默认每页数据量

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.similar_threshold = kwargs.get("similarThreshold", self.DEFAULT_SIMILAR_THRESHOLD)  # 默认相似度阈值为0.8
        # task_uuid为标识该数据集的唯一标志
        self.task_uuid = kwargs.get("uuid", self.DEFAULT_TASK_UUID)
        self.orb_ratio = self.DEFAULT_ORB_RATIO  # 特征点距离的比率，该数值为经验值
        self.mix_similarity = self.DEFAULT_MIX_SIMILARITY  # 选择相似度算法的阈值，该数值为经验值
        self.img_resize = self.DEFAULT_IMG_RESIZE  # 图片压缩尺寸
        self.conn = None  # 数据库连接
        self.trans = None  # 数据库事务
        self.page_size = self.DEFAULT_PAGE_SIZE  # 每页数据量
        # 获取数据库sql
        self.sql_dict = self.load_sql_dict()

    @staticmethod
    def load_sql_dict():
        """获取sql语句"""
        sql_config_path = str(Path(__file__).parent / 'sql' / 'sql_config.json')
        with open(sql_config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def get_p_hash(image: np.ndarray) -> str:
        """计算pHash值"""
        hashed_value = ""
        if not image.size:
            return hashed_value
        gray_image = cv2.cvtColor(cv2.resize(image, (8, 8), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
        dct_image = cv2.dct(np.float32(gray_image))
        hashed_value = ''.join(['1' if x >= 0 else '0' for x in dct_image[:8, :8].flatten()])
        return hashed_value

    @staticmethod
    def get_phash_similarity(hash_comparison: str, hash_compared: str) -> float:
        """通过计算汉明距离，获取图片相似度"""
        # 若哈希值为空，则相似度为0
        if not hash_comparison or not hash_compared:
            return 0.0
        # 计算汉明距离
        distance = sum(
            bit_comparison != bit_compared for bit_comparison, bit_compared in zip(hash_comparison, hash_compared))
        similarity = 1 - distance / len(hash_comparison)
        return similarity

    def filter_similar_images(self, img: np.ndarray, file_name: str) -> np.ndarray:
        """判断数据集中是否存在相似图片"""
        # 如果文件为空，则无需去重，返回原图
        if not img.size:
            return img
        p_hash = self.get_p_hash(img)
        height, width = img.shape[:2]  # 获取原图像的水平方向尺寸和垂直方向尺寸。
        img_resize = cv2.resize(img, (int(width / height * self.img_resize), self.img_resize),
                                interpolation=cv2.INTER_AREA)
        des_matrix = get_orb_des(img_resize)
        return self.execute_sql(p_hash, des_matrix, file_name, img)

    def get_orb_similarity(self, des_matrix: np.ndarray, des_matrix_history: np.ndarray, file_name: str,
                           file_name_history: str) -> float:
        """获取图片orb相似度"""
        # 若描述符矩阵为空，则相似度为0
        if not des_matrix.size or not des_matrix_history.size:
            return 0.0
        # 根据矩阵对角线上元素和的大小，选择描述符矩阵作为训练或查询矩阵
        train_matrix, query_matrix = des_matrix, des_matrix_history
        if train_matrix.shape[0] > des_matrix_history.shape[0]:
            train_matrix, query_matrix = des_matrix_history, des_matrix
        elif des_matrix.shape[0] == des_matrix_history.shape[0]:
            if np.trace(des_matrix) > np.trace(des_matrix_history):
                train_matrix, query_matrix = des_matrix_history, des_matrix

        try:
            # knn筛选结果
            matches = (cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False).
                       knnMatch(query_matrix, trainDescriptors=train_matrix, k=2))
            if not matches:
                return 0.0
            # 遍历每一对特征点，筛选距离更近的特征点
            count = 0
            for (m, n) in matches:
                if m.distance < self.orb_ratio * n.distance:
                    count += 1
            orb_similarity = count / len(matches)
            return orb_similarity
        except Exception as e:
            logger.error("dataset: %s, failed to compare the similarity between %s and %s: %s", self.task_uuid,
                         file_name, file_name_history, e, exc_info=True)
            return 0.0

    def execute_sql(self, p_hash: str, des_matrix: np.ndarray, file_name: str,
                    img: np.ndarray) -> np.ndarray:
        des_matrix_binary = zlib.compress(des_matrix.tobytes())  # 使用 zlib 进行压缩数组
        timestamp = get_now_time('Asia/Shanghai', '%Y-%m-%d %H:%M:%S', file_name,
                                 "ImgSimilarCleaner")
        query_task_uuid_sql = str(self.sql_dict.get("query_task_uuid_sql"))
        insert_sql = str(self.sql_dict.get("insert_sql"))
        create_tables_sql = str(self.sql_dict.get("create_tables_sql"))

        db_manager = SQLManager()
        try:
            self.conn = db_manager.create_connect()
        except Exception as e:
            logger.error("fileName: %s, database connection failed: %s", file_name, str(e))
            raise RuntimeError(82000, str(e)) from None

        with self.conn as connection:
            """从数据库中获取文件特征、比较相似度，插入新的文件特征"""
            with self.conn as connection:
                connection.execute(text(create_tables_sql))
            result = connection.execute(query_task_uuid_sql, {"task_uuid": self.task_uuid}).fetchall()
            total_count = len(result)
            if self.has_similar_images(connection, des_matrix, file_name, p_hash, total_count):
                    return np.array([])

            insert_data = {
                "task_uuid": self.task_uuid,
                "p_hash": p_hash,
                "des_matrix": des_matrix_binary,
                "matrix_shape": str(des_matrix.shape),
                "file_name": file_name.encode("utf-8").hex(),
                "timestamp": timestamp
            }
            connection.execute(text(insert_sql),insert_data)
        return img

    def has_similar_images(self, connection, des_matrix, file_name, p_hash, total_count):
        for i in range(0, total_count, self.page_size):
            query_sql = self.sql_dict.get("query_sql")
            rows = connection.execute(text(query_sql), {"task_uuid": self.task_uuid, "ge": self.page_size, "le": i}).fetchall()
            # 对应任务uuid，最后一页没有数据，跳出循环
            if not rows:
                break            # 对两张图片进行相似度比较
            if self.determine_similar_images(rows, p_hash, des_matrix, file_name):
                return True
        return False

    def determine_similar_images(self, file_features: List, p_hash: str, des_matrix: np.ndarray,
                                 file_name: str) -> bool:
        """根据文件特征，判断两张图片相似度是否超过指定阈值"""
        for signature in file_features:
            pash_feature, orb_feature, matrix_shape, file_name_history = signature[2], signature[3], signature[4], \
                signature[5]
            if not pash_feature:
                # 若图片为空，p_hash、des_matrix为空，跳过比对
                continue
            # 解压缩数据
            decompressed_data = zlib.decompress(orb_feature)
            # 将字节流转换回矩阵
            des_matrix_history = np.frombuffer(decompressed_data, dtype=np.uint8).reshape(eval(matrix_shape))
            # 移除转义字符 '\' 并将十六进制字符串转换为字节序列
            bytes_data = bytes.fromhex(file_name_history)
            # 解码字节序列为 UTF-8 编码的字符串
            file_name_decoded = bytes_data.decode('utf-8')

            phash_similarity = self.get_phash_similarity(p_hash, pash_feature)
            orb_similarity = self.get_orb_similarity(des_matrix, des_matrix_history, file_name, file_name_decoded)
            max_similarity = max(phash_similarity, orb_similarity)
            min_similarity = min(phash_similarity, orb_similarity)
            if max_similarity >= self.mix_similarity:
                result = max_similarity
            else:
                result = min_similarity
            similarity = round(result, 2)
            if similarity >= self.similar_threshold:
                logger.info(
                    "fileName: %s, method: ImgSimilarCleaner, dataset: %s. This picture is similar to %s, "
                    "and the similarity is %.4f. The picture is filtered.", file_name, self.task_uuid,
                    file_name_decoded, similarity)
                return True
        return False

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """去除相似图片算子执行入口"""
        start = time.time()
        file_name = sample[self.filename_key]
        img_bytes = sample[self.data_key]
        data = bytes_to_numpy(img_bytes) if img_bytes else np.array([])
        similar_images = self.filter_similar_images(data, file_name)
        # 若相似图片，sample[self.data_key]设为空
        if not similar_images.size:
            sample[self.data_key] = b""
        logger.info("fileName: %s, method: ImgSimilarCleaner costs %.6f s", file_name,
                    time.time() - start)
        return sample
