"""
自定义异常类定义
"""

class LabelStudioAdapterException(Exception):
    """Label Studio Adapter 基础异常类"""
    pass

class DatasetMappingNotFoundError(LabelStudioAdapterException):
    """数据集映射未找到异常"""
    def __init__(self, mapping_id: str):
        self.mapping_id = mapping_id
        super().__init__(f"Dataset mapping not found: {mapping_id}")

class NoDatasetInfoFoundError(LabelStudioAdapterException):
    """无法获取数据集信息异常"""
    def __init__(self, dataset_uuid: str):
        self.dataset_uuid = dataset_uuid
        super().__init__(f"Failed to get dataset info: {dataset_uuid}")

class LabelStudioClientError(LabelStudioAdapterException):
    """Label Studio 客户端错误"""
    pass

class DMServiceClientError(LabelStudioAdapterException):
    """DM 服务客户端错误"""
    pass

class SyncServiceError(LabelStudioAdapterException):
    """同步服务错误"""
    pass