# -*- coding: utf-8 -*-

import json
import os
import ssl
from pathlib import Path
from typing import Dict
from urllib.request import Request, urlopen

import requests
import urllib3
from loguru import logger

from data_platform.common.utils import decrypt


class LlmReq:
    # 定义常量用于解释错误码
    ERRORCODE_INCOMPLETE_CONFIG = 83005
    ERRORCODE_INVALID_RESPONSE = 83006
    ERRORCODE_SERVICE_UNAVAILABLE = 83007

    def __init__(self, url: str = None, header: Dict = None, body: Dict = None, access_type: int = None,
                 is_https: bool = False, is_certificate: bool = False, certificate_path: Path = None):
        self.url = url
        self.header = header
        self.access_type = access_type
        self.is_https = is_https
        self.context = self._load_certificate(certificate_path, is_certificate) if is_https else None
        self.body = body
        if not self.body.get("messages", [])[0].get("content"):
            self.body["messages"][0]["content"] = "你好"

    def __call__(self, input_str: str) -> str:
        outputs = ''
        try:
            self.body["messages"][0]["content"] = input_str
            outputs = self._call_service()
        except KeyError as e:
            logger.error(f"The body format is not completed, error detail: {e}")
        self.body["messages"][0]["content"] = "你好"
        return outputs

    @staticmethod
    def _load_certificate(certificate_path: Path, is_certificate: bool) -> ssl.SSLContext:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        if is_certificate:
            context.load_verify_locations(certificate_path)
            context.verify_mode = ssl.CERT_REQUIRED
        else:
            context.verify_mode = ssl.CERT_NONE
        return context

    @staticmethod
    def _pool_manager():
        cert_file = os.getenv("RAY_TLS_SERVER_CERT", "/certPersonal/global/identity/global.crt")
        key_file = os.getenv("RAY_TLS_SERVER_KEY", "/certPersonal/global/identity/global.key")
        ca_crt = os.getenv("RAY_TLS_CA_CERT", "/certPersonal/global/trust/ca.crt")
        pwd = os.getenv("RAY_TLS_SERVER_KEY_PASSWORD", "/certPersonal/global/identity/pwd.txt")
        key_password = os.getenv("GLOBAL_PWD", None)
        if not key_password:
            with open(pwd, "r") as f:
                key_password = f.read().strip()
        key_password = decrypt(key_password)

        pool_manager = urllib3.PoolManager(cert_file=cert_file,
                                           key_file=key_file,
                                           key_password=key_password,
                                           cert_reqs='CERT_REQUIRED',
                                           ca_certs=ca_crt,
                                           assert_hostname='edatamate',
                                           ssl_version='TLSv1_2')
        return pool_manager

    def _call_service(self):
        if not all([self.url, self.header, self.body.get("messages", [])[0].get("content")]):
            logger.error("LLM is not configured completely")
            raise RuntimeError(self.ERRORCODE_INCOMPLETE_CONFIG, "LLM is not configured completely") from None
        if not self.access_type:
            try:
                pool_manager = self._pool_manager()
                response = pool_manager.request(
                    "POST",
                    url=self.url,
                    body=json.dumps(self.body).encode(),
                    headers=self.header
                )
                logger.info(f"Response status code: {response.status}")
                response_json = json.loads(response.data.decode('utf-8'))
                outputs = response_json.get("choices", [])[0].get("message", {}).get("content")
                if not outputs:
                    logger.error("Invalid response format for LLM, missing the 'prompt' key word")
                    raise RuntimeError(self.ERRORCODE_INVALID_RESPONSE,
                                       "Invalid response format for LLM, missing the 'prompt' key word") from None
                return outputs
            except Exception as e:
                logger.error(f"LLM service is not available, error detail: {e}")
                raise RuntimeError(self.ERRORCODE_SERVICE_UNAVAILABLE, "LLM service is not available") from None
        if self.access_type:
            try:
                if self.is_https:
                    req = Request(url=self.url, data=json.dumps(self.body).encode(), headers=self.header, method="POST")
                    response_json = urlopen(req, context=self.context).read().decode("utf-8")
                    response = json.loads(response_json)
                else:
                    response = requests.post(url=self.url, data=json.dumps(self.body), headers=self.header,
                                             stream=False).json()
                outputs = response.get("choices", [])[0].get("message", {}).get("content")
                if not outputs:
                    logger.error("Invalid response format for LLM, missing the 'prompt' key word")
                    raise RuntimeError(self.ERRORCODE_INVALID_RESPONSE,
                                       "Invalid response format for LLM, missing the 'prompt' key word") from None
                return outputs
            except Exception as e:
                logger.error(f"LLM service is not available, error detail: {e}")
                raise RuntimeError(self.ERRORCODE_SERVICE_UNAVAILABLE, "LLM service is not available") from None
        return None  # 确保在所有情况下都返回
