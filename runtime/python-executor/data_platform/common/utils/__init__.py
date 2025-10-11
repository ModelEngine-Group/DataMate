# -*- coding: utf-8 -*-
from datetime import datetime

import cv2
import numpy as np
import os

import pytz
from loguru import logger


def check_valid_path(file_path):
    full_path = os.path.abspath(file_path)
    return os.path.exists(full_path)


def get_realpath_with_prefix_check(path, prefix):
    realpath = os.path.realpath(path)

    if realpath.startswith(prefix):
        return realpath
    else:
        raise ValueError(f"The path {realpath} does not start with the prefix '{prefix}'.")


def bytes_to_numpy(image_bytes):
    """bytes转数组"""
    image_np = np.frombuffer(image_bytes, dtype=np.uint8)
    image_np2 = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    return image_np2


def numpy_to_bytes(image_np, file_type):
    """数组转bytes"""
    if not image_np.size:
        return b""
    data = cv2.imencode(file_type, image_np)[1]
    image_bytes = data.tobytes()
    return image_bytes


def get_now_time(timezone, time_format, file_name, method):
    timestamp = ""
    try:
        china_tz = pytz.timezone(timezone)  # 设置时区
        china_time = datetime.now(tz=china_tz)  # 获取当前时间并转换为对应的时区
        timestamp = china_time.strftime(time_format)  # 格式化输出时间
    except ValueError as e:
        logger.error("fileName: %s, method: %s, formatting time failed: %s", file_name, method, e, exc_info=True)
    return timestamp


def decrypt(enc_pass):
    import kmc.kmc as K
    os.environ['KMC_DATA_USER'] = 'modelenginepublic'
    os.environ['KMC_PYTHON_ENCRYPT_DATA'] = enc_pass
    dec_pass = K.API().decrypt(0)
    os.environ['KMC_PYTHON_ENCRYPT_DATA'] = ""
    return dec_pass
