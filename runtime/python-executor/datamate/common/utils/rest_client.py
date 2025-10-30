# -*- coding: utf-8 -*-
import requests
from typing import Optional, Dict, Any

from starlette.responses import JSONResponse


def http_request(method: str, url: str, data: Optional[Dict[str, Any]] = None):
	"""
	通用HTTP请求方法

	Args:
		method: 请求方法 ('GET', 'POST', 'PUT', 'DELETE', 'PATCH')
		url: 请求URL
		data: 请求数据（JSON格式）

	Returns: 格式化响应体

	Raises:
		requests.exceptions.RequestException: 请求异常
		ValueError: 响应状态码错误
	"""
	success_codes = [200, 201, 202, 204]

	# 设置默认请求头
	headers = {"Content-Type": "application/json"}

	method = method.upper()

	try:
		# 准备请求参数
		request_kwargs = {"url": url, "headers": headers}

		# 根据请求方法添加数据
		if data is not None:
			if method in ["POST", "PUT", "DELETE"]:
				request_kwargs["json"] = data
			elif method == "GET":
				request_kwargs["params"] = data

		# 发送请求
		response = requests.request(method, **request_kwargs)

		# 检查响应状态码
		if response.status_code not in success_codes:
			raise ValueError(
				f"Request failed! Status code: {response.status_code}, "
				f"content: {response.text}, "
				f"URL: {url}"
			)
		return response
	except requests.exceptions.RequestException as e:
		raise requests.exceptions.RequestException(f"Request exception: {str(e)}")
