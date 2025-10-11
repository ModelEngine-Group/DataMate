# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
The class hierarchy for built-in exceptions is:
see https://docs.python.org/3/library/exceptions.html

BaseException
 ├── SystemExit
 ├── KeyboardInterrupt
 ├── GeneratorExit
 └── Exception
      ├── ArithmeticError
      │    ├── FloatingPointError
      │    ├── OverflowError
      │    └── ZeroDivisionError
      ├── AssertionError
      ├── AttributeError
      ├── BufferError
      ├── EOFError
      ├── ImportError
      │    └── ModuleNotFoundError
      ├── LookupError
      │    ├── IndexError
      │    └── KeyError
      ├── MemoryError
      ├── NameError
      │    └── UnboundLocalError
      ├── OSError
      │    ├── BlockingIOError
      │    ├── ChildProcessError
      │    ├── ConnectionError
      │    │    ├── BrokenPipeError
      │    │    ├── ConnectionAbortedError
      │    │    ├── ConnectionRefusedError
      │    │    └── ConnectionResetError
      │    ├── FileExistsError
      │    ├── FileNotFoundError
      │    ├── InterruptedError
      │    ├── IsADirectoryError
      │    ├── NotADirectoryError
      │    ├── PermissionError
      │    ├── ProcessLookupError
      │    └── TimeoutError
      ├── ReferenceError
      ├── RuntimeError
      │    ├── NotImplementedError
      │    └── RecursionError
      ├── SyntaxError
      │    └── IndentationError
      │         └── TabError
      ├── SystemError
      ├── TypeError
      ├── ValueError
      │    └── UnicodeError
      │         ├── DecodeError
      │         ├── EncodeError
      │         └── UnicodeTranslateError
      └── Warning
           ├── DeprecationWarning
           ├── PendingDeprecationWarning
           ├── RuntimeWarning
           ├── SyntaxWarning
           ├── UserWarning
           ├── FutureWarning
           ├── ImportWarning
           └── UnicodeWarning
"""
from enum import Enum

ERROR_CODE_TABLE = {
    ImportError: "ops.0001",
    ModuleNotFoundError: "ops.0002",
    NameError: "ops.0003",
    KeyError: "ops.0004",
    IndexError: "ops.0005",
    ValueError: "ops.0006",
    TypeError: "ops.0007",
    SyntaxError: "ops.0008",
    AttributeError: "ops.0009",
    ArithmeticError: "ops.0010",
    MemoryError: "ops.0011",
    OSError: "ops.0012",
    FileNotFoundError: "ops.0013",
    NotADirectoryError: "ops.0014",
    PermissionError: "ops.0015",
    TimeoutError: "ops.0016",
}

UNKNOWN_ERROR_CODE = "ops.9999"


class ErrorCode(Enum):
    # 通用错误
    SUCCESS = (0, "Success")
    UNKNOWN_ERROR = (1, "Unknown error")
    FILE_NOT_FOUND_ERROR = (1000, "File not found!")
    SUBMIT_TASK_ERROR = (1001, "Task submitted Failed!")
    CANCEL_TASK_ERROR = (1002, "Task canceled Failed!")