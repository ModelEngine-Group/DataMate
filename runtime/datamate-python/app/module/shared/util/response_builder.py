"""
用于创建统一API响应的响应构建工具
"""
from typing import Any

from app.module.shared.schema.common import StandardResponse, ResponseCode


class ResponseBuilder:
    """响应构建工具类"""

    @staticmethod
    def success(data: Any = None, message: str = "success", code: str = ResponseCode.SUCCESS.value) -> StandardResponse:
        """
        构建成功响应

        Args:
            data: 响应数据
            message: 响应消息
            code: 响应码，默认为 "0"

        Returns:
            StandardResponse: 统一响应对象
        """
        return StandardResponse(code=code, message=message, data=data)

    @staticmethod
    def error(message: str = "操作失败", code: str = ResponseCode.INTERNAL_ERROR.value, data: Any = None) -> StandardResponse:
        """
        构建错误响应

        Args:
            message: 错误消息
            code: 错误码
            data: 附加数据

        Returns:
            StandardResponse: 统一响应对象
        """
        return StandardResponse(code=code, message=message, data=data)

    @staticmethod
    def bad_request(message: str = "请求参数错误", data: Any = None) -> StandardResponse:
        """构建400错误请求响应"""
        return ResponseBuilder.error(
            message=message,
            code=ResponseCode.BAD_REQUEST.value,
            data=data
        )

    @staticmethod
    def not_found(message: str = "资源未找到", data: Any = None) -> StandardResponse:
        """构建404未找到响应"""
        return ResponseBuilder.error(
            message=message,
            code=ResponseCode.NOT_FOUND.value,
            data=data
        )

    @staticmethod
    def validation_error(errors: list = None, message: str = "验证错误") -> StandardResponse:
        """构建422验证错误响应"""
        return ResponseBuilder.error(
            message=message,
            code=ResponseCode.VALIDATION_ERROR.value,
            data={"errors": errors} if errors else None
        )

    @staticmethod
    def unauthorized(message: str = "未授权访问") -> StandardResponse:
        """构建401未授权响应"""
        return ResponseBuilder.error(
            message=message,
            code=ResponseCode.UNAUTHORIZED.value
        )
