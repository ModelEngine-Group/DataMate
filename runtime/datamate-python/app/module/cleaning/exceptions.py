from typing import Optional


class CleaningException(Exception):
    """Base exception for cleaning module"""
    def __init__(self, message: str, details: Optional[dict] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class CleaningNameDuplicationError(CleaningException):
    """Exception raised when cleaning task name is duplicated"""
    def __init__(self, name: str):
        super().__init__(f"Cleaning task name '{name}' is duplicated")


class CleaningTaskNotFoundError(CleaningException):
    """Exception raised when cleaning task is not found"""
    def __init__(self, task_id: str):
        super().__init__(f"Cleaning task '{task_id}' not found")


class CleaningTemplateNotFoundError(CleaningException):
    """Exception raised when cleaning template is not found"""
    def __init__(self, template_id: str):
        super().__init__(f"Cleaning template '{template_id}' not found")


class InvalidOperatorInputError(CleaningException):
    """Exception raised when operator input/output types are invalid"""
    def __init__(self, message: str = "Invalid operator input/output types"):
        super().__init__(message)


class ExecutorTypeError(CleaningException):
    """Exception raised when executor type is invalid"""
    def __init__(self, message: str = "Invalid executor type"):
        super().__init__(message)


class DatasetNotFoundError(CleaningException):
    """Exception raised when dataset is not found"""
    def __init__(self, dataset_id: str):
        super().__init__(f"Dataset '{dataset_id}' not found")


class FileSystemError(CleaningException):
    """Exception raised when file system operations fail"""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(f"File system error: {message}", details)


class SettingsParseError(CleaningException):
    """Exception raised when operator settings parsing fails"""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(f"Settings parse error: {message}", details)
