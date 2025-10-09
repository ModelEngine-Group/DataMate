# -- encoding: utf-8 --
import pickle

import base64
from io import BytesIO

import cv2
import numpy as np
from PIL import Image


def bytes_to_numpy(image_bytes):
    """bytes转数组"""
    image_np = np.frombuffer(image_bytes, dtype=np.uint8)
    image_np2 = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
    return image_np2


def numpy_to_bytes(image_np, file_type):
    """
    数组转bytes
    
    Params:
    
        file_type: as required by OpenCV, extension must have a leading period.
    """
    if not image_np.size:
        return b""
    data = cv2.imencode(file_type, image_np)[1]
    image_bytes = data.tobytes()
    return image_bytes


def pil_to_bytes(src: Image.Image) -> bytes:
    """将 PIL.Image 转换为字节流"""
    # 确保图像是 RGB 模式
    src = src.convert("RGB")
    with BytesIO() as bytes_io:
        src.save(bytes_io, format='PNG')
        im_bytes = bytes_io.getvalue()
        return im_bytes


def bytes_to_pil(src: bytes) -> Image.Image:
    """将字节流转换为 PIL.Image"""
    with BytesIO() as bytes_io:
        with Image.open(bytes_io) as pil_img:  # 使用with/as语句确保资源被正确释放
            pil_img.load()  # 确保图像数据被加载
            return pil_img.copy()  # 返回图像的副本以避免资源被关闭后无法使用


def pil_to_base64(src: Image.Image):
    """PIl.Image转base64"""
    with BytesIO() as img_buffer:
        src.save(img_buffer, format='png')
        byte_data = img_buffer.getvalue()
        base64_str = base64.b64encode(byte_data)
        return base64_str


def obj_to_bytes(src: object) -> bytes:
    return pickle.dumps(src)


def bytes_to_obj(src: bytes) -> object:
    return pickle.loads(src)
