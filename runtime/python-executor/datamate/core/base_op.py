# -*- coding: utf-8 -*-

import json
import os
import time
import traceback
import uuid
from pathlib import Path
from typing import List, Dict, Any, Tuple

import cv2
import numpy as np
from loguru import logger
from unstructured.partition.auto import partition

from datamate.common.error_code import ERROR_CODE_TABLE, UNKNOWN_ERROR_CODE
from datamate.common.utils.llm_request import LlmReq
from datamate.common.utils.registry import Registry
from datamate.common.utils import check_valid_path
from datamate.core.constant import Fields
from datamate.sql_manager.persistence_atction import TaskInfoPersistence

OPERATORS = Registry('Operators')

FAILED_STATUS = "FAILED"
SUCCESS_STATUS = "COMPLETED"


def get_exception_info(e):
    exc_type = type(e).__name__  # 异常类型（如 'ZeroDivisionError'）
    exc_msg = str(e)  # 异常原因（如 'division by zero'）

    # 提取详细的堆栈信息
    tb = traceback.extract_tb(e.__traceback__)  # 解析 traceback 对象
    error_line = tb[-1].lineno  # 错误发生的行号
    error_file = tb[-1].filename  # 错误发生的文件名
    code_snippet = tb[-1].line  # 错误行的代码

    # 组合输出信息
    error_info = (
        f"错误类型: {exc_type}\n"
        f"错误原因: {exc_msg}\n"
        f"文件名: {error_file}\n"
        f"行号: {error_line}\n"
        f"代码行: {code_snippet}"
    )
    return error_info


class BaseOp:
    """
    所有算子类的父类
    """

    use_model = False
    custom_ops = False

    def __init__(self, *args, **kwargs):
        self.accelerator = kwargs.get('accelerator', "cpu")
        self.is_last_op = kwargs.get('is_last_op', False)
        self.is_first_op = kwargs.get('is_first_op', False)
        self._name = kwargs.get('op_name', None)
        self.infer_model = None
        self.text_key = kwargs.get('text_key', "text")
        self.data_key = kwargs.get('data_key', "data")
        self.image_key = kwargs.get('image_key', "image")
        self.video_key = kwargs.get('video_key', "video")
        self.audio_key = kwargs.get('audio_key', "audio")
        self.filename_key = kwargs.get('fileName_key', "fileName")
        self.filetype_key = kwargs.get('fileType_key', "fileType")
        self.fileid_key = kwargs.get('fileId_key', "fileId")
        self.filepath_key = kwargs.get('filePath_key', "filePath")
        self.filesize_key = kwargs.get('fileSize_key', "fileSize")
        self.export_path_key = kwargs.get('export_path_key', "export_path")
        self.ext_params_key = kwargs.get('ext_params_key', "ext_params")
        self.target_type_key = kwargs.get('target_type_key', "target_type")

    @property
    def name(self):
        if self._name:
            return self._name
        else:
            return "UnknownOp"

    @staticmethod
    def is_npu_available():
        try:
            import torch_npu
            return torch_npu.npu.is_available()
        except ImportError as e:
            logger.warning("Import torch_npu failed.")
            return False

    @staticmethod
    def update_kwargs(sample: Dict[str, Any], not_update_keys=("text", "data", "meta")) -> Dict:
        """获取sample_data中文件相关的信息"""
        res = {}
        for k, v in sample.items():
            if k not in not_update_keys:
                res[k] = v
        return res

    @staticmethod
    def _get_error_info(e: BaseException) -> Tuple[str, str]:

        error_code = UNKNOWN_ERROR_CODE
        exc_info = get_exception_info(e)

        for exc_type in type(e).__mro__:
            if exc_type in ERROR_CODE_TABLE.keys():
                error_code = ERROR_CODE_TABLE[exc_type]
                break

        return error_code, exc_info

    def use_npu(self):
        """确认算子是否可以使用npu"""
        return self.accelerator == 'npu' and self.is_npu_available()

    def get_model(self, *args, **kwargs):
        if self.infer_model is None and self.use_model:
            return self.init_model(*args, **kwargs)
        else:
            logger.info(f"Op named {self.name} get infer model Failed. please "
                        f" check Attribute self.use_model: {self.use_model} or model has been initialized!")
        return self.infer_model

    def init_model(self, *args, **kwargs):
        """执行函数（子类实现）"""
        raise NotImplementedError("This is in BaseOp, plese re-define this method in Sub-classes")

    def fill_sample_params(self, sample: Dict[str, Any], **kwargs):
        if not sample.get(self.text_key, None):
            sample[self.text_key] = ""

        if not sample.get(self.data_key, None):
            sample[self.data_key] = b""

        if not sample[self.data_key] and not sample[self.text_key]:
            sample.update(kwargs)

    def create_failure_sample(self, sample: Dict[str, Any], op_name, excp: BaseException):
        sample["execute_result"] = False
        error_code, exc_info = self._get_error_info(excp)
        failed_reason = {"op_name": op_name, "error_code": error_code, "reason": exc_info}
        sample["failed_reason"] = failed_reason

    def read_file(self, sample):
        filepath = sample[self.filepath_key]
        filetype = sample[self.filetype_key]
        if filetype in ["ppt", "pptx", "docx", "doc", "xlsx", "csv", "md", "pdf"]:
            elements = partition(filename=filepath)
            sample[self.text_key] = "\n\n".join([str(el) for el in elements])
        elif filetype in ["txt", "md", "markdown", "xml", "html", "json", "jsonl"]:
            with open(filepath, 'rb') as f:
                content = f.read()
                sample[self.text_key] = content.decode("utf-8-sig").replace("\r\n", "\n")
        elif filetype in ['jpg', 'jpeg', 'png', 'bmp']:
            image_np = cv2.imdecode(np.fromfile(filepath, dtype=np.uint8), -1)
            if image_np.size:
                data = cv2.imencode(f".{filetype}", image_np)[1]
                image_bytes = data.tobytes()
                sample[self.data_key] = image_bytes

    def read_file_first(self, sample):
        if self.is_first_op:
            self.read_file(sample)


class Mapper(BaseOp):
    def __init__(self, *args, **kwargs):
        super(Mapper, self).__init__(*args, **kwargs)

    def __call__(self, sample: Dict[str, Any], **kwargs):
        # 该算子前已有算子执行该文件失败
        if sample.get(Fields.result) is False:
            return sample

        self.fill_sample_params(sample, **kwargs)
        execute_status = FAILED_STATUS
        try:
            sample = self.execute(sample)
            execute_status = SUCCESS_STATUS
        except Exception as e:
            # 算子执行失败，记录文件执行信息到数据库，并更该文件执行结果状态
            self.create_failure_sample(sample, self.name, e)
            logger.error(f"Ops named {self.name} map failed, Error Info: \n"
                         f"{str(get_exception_info(e))}")
            sample["execute_status"] = execute_status
            sample[self.filesize_key] = "0"
            sample[self.filetype_key] = ""
            TaskInfoPersistence().update_task_result(sample)
            raise e

        sample["execute_status"] = execute_status
        # 加载文件成功执行信息到数据库
        if self.is_last_op:
            if FileExporter().execute(sample):
                TaskInfoPersistence().persistence_task_info(sample)
        return sample

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """执行函数（子类实现）"""
        raise NotImplementedError("This is in Mapper Class, plese re-define this method in Sub-classes")


class Slicer(BaseOp):
    def __init__(self, *args, **kwargs):
        super(Slicer, self).__init__(*args, **kwargs)
        self.target_file_type = None

    def __call__(self, sample: Dict[str, Any], **kwargs):
        # 该算子前已有算子执行该文件失败
        if sample.get(Fields.result) is False:
            return sample

        self.fill_sample_params(sample, **kwargs)
        sample_list = []
        execute_status = FAILED_STATUS
        try:
            sample_list = self.execute(sample)
            execute_status = SUCCESS_STATUS
        except Exception as e:
            # 算子执行失败，记录文件执行信息到数据库，并更该文件执行结果状态
            self.create_failure_sample(sample, self.name, e)
            self.load_sample_to_sample(sample, sample_list)
            logger.error(f"Ops named {self.name} map failed, Error Info: \n"
                         f"{str(get_exception_info(e))}")
            sample["execute_status"] = execute_status
            sample[self.filesize_key] = "0"
            sample[self.filetype_key] = ""
            TaskInfoPersistence().update_task_result(sample)
            return [sample]

        self.load_sample_to_sample(sample, sample_list)
        sample["execute_status"] = execute_status

        # 加载文件成功执行信息到数据库
        if self.is_last_op:
            if FileExporter().execute(sample):
                TaskInfoPersistence().persistence_task_info(sample)

        return [sample]

    @staticmethod
    def load_sample_to_sample(sample: Dict, sample_list: List[Dict]):
        """使用sample中的k-v更新sample"""
        for sample_i in sample_list:
            for k, v in sample_i.items():
                sample[k] = v
        if not sample.get("fileNum", None):
            sample["fileNum"] = 1

    def execute(self, sample: Dict[str, Any]) -> List[Dict]:
        """执行函数（子类实现）"""
        raise NotImplementedError("This is in Mapper Class, plese re-define this method in Sub-classes")

    def save_patch_sample(self, sample: Dict[str, Any], patch_no, save_format="text"):
        if save_format == "text":
            target_file_type = 'txt'
        elif save_format == "image":
            target_file_type = 'png'
        else:
            target_file_type = None
            raise RuntimeError(f"target file type is {target_file_type}!")

        if self.target_file_type:
            target_file_type = self.target_file_type
        save_path = self.get_save_path(sample, patch_no, target_file_type)
        self.save_file(sample, save_path)

    def get_save_path(self, sample: Dict[str, Any], patch_no, target_type) -> str:
        export_path = os.path.abspath(sample[self.export_path_key])
        logger.info(f"export path: {export_path}.")
        base_file_name, _ = os.path.splitext(sample[self.filename_key])
        file_id = str(sample[self.fileid_key])
        new_file_name = file_id + '_' + str(patch_no) + '.' + target_type
        logger.info(f"base_file_name: {base_file_name}, new file name: {new_file_name}.")
        if not check_valid_path(export_path):
            os.makedirs(export_path, exist_ok=True)
        res = os.path.join(export_path, new_file_name)
        return res

    def save_file(self, sample, save_path):
        # 以二进制格式保存文件
        file_sample = sample[self.text_key].encode('utf-8') if sample[self.text_key] else sample[self.data_key]
        with open(save_path, 'wb') as f:
            f.write(file_sample)

        os.chmod(save_path, 0o640)
        try:
            parent_dir = os.path.dirname(save_path)
            os.chmod(parent_dir, 0o770)
        except Exception as e:
            logger.warning("Failed to modify the permission on the parent_dir.")

        logger.info(f"patch sample has been save to {save_path}.")


class Filter(BaseOp):
    def __init__(self, *args, **kwargs):
        super(Filter, self).__init__(*args, **kwargs)

    def __call__(self, sample: Dict[str, Any], **kwargs):
        # 该算子前已有算子执行该文件失败
        if sample.get(Fields.result) is False:
            return sample

        self.fill_sample_params(sample, **kwargs)
        execute_status = FAILED_STATUS
        try:
            sample = self.execute(sample)
            execute_status = SUCCESS_STATUS
        except Exception as e:
            # 如果filter算子过滤失败, 不保留文件， 并记录文件执行信息到数据库
            self.create_failure_sample(sample, self.name, e)
            sample["execute_status"] = execute_status
            logger.error(f"Ops named {self.name} map failed, Error Info: \n"
                         f"{str(get_exception_info(e))}")
            sample[self.filesize_key] = "0"
            sample[self.filetype_key] = ""
            TaskInfoPersistence().update_task_result(sample)
            raise e

        sample["execute_status"] = execute_status
        # 文件无内容会被过滤
        if sample[self.text_key] == "" and sample[self.data_key] == b"":
            task_info = TaskInfoPersistence()
            sample[self.filesize_key] = "0"
            sample[self.filetype_key] = ""
            task_info.update_task_result(sample)
            return False

        # 加载文件成功执行信息到数据库
        if self.is_last_op:
            if FileExporter().execute(sample):
                TaskInfoPersistence().persistence_task_info(sample)
        return True

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """执行函数（子类实现）"""
        raise NotImplementedError("This is in Filter Class, plese re-define this method in Sub-classes")


class LLM(Mapper):
    def __init__(self, *args, **kwargs):
        super(LLM, self).__init__(*args, **kwargs)
        self.llm = self.get_llm(*args, **kwargs)
        self.prompt_template = None

        self.target_file_type = None

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """执行函数（子类实现）"""
        raise NotImplementedError("This is in LLM Class, plese re-define this method in Sub-classes")

    @staticmethod
    def get_llm(*args, **kwargs):
        url = kwargs.get("LLMUrl", '')
        header = kwargs.get("LLMHeaders", {"Content-type": "application/json"})
        body = kwargs.get("LLMBody", {})
        access_type = kwargs.get("accessType", False)
        is_https = kwargs.get("isHttps", False)
        is_certificate = kwargs.get("isCertificate", False)
        certificate_path = kwargs.get("certificatePath", None)
        return LlmReq(url=url, header=header, body=body, access_type=access_type, is_https=is_https,
                      is_certificate=is_certificate, certificate_path=certificate_path)

    def build_llm_prompt(self, *args, **kwargs):
        """执行函数（子类实现）"""
        raise NotImplementedError("This is in LLM Class, plese re-define this method in Sub-classes")

    def save_sample(self, object_list: List, sample: Dict[str, Any]):
        if self.target_file_type:
            target_file_type = self.target_file_type
        else:
            target_file_type = "jsonl"
        save_path = self.get_save_path(sample, target_file_type)
        self.save_json_file(object_list, save_path)

    def get_save_path(self, sample: Dict[str, Any], target_type) -> str:
        export_path = os.path.abspath(sample[self.export_path_key])
        logger.info(f"export path: {export_path}.")
        base_file_name, _ = os.path.splitext(sample[self.filename_key])
        file_id = str(sample[self.fileid_key])
        new_file_name = file_id + '.' + target_type
        logger.info(f"base_file_name: {base_file_name}, new file name: {new_file_name}.")
        if not check_valid_path(export_path):
            os.makedirs(export_path, exist_ok=True)
        res = os.path.join(export_path, new_file_name)
        return res

    @staticmethod
    def save_json_file(object_list: List, save_path):
        if len(object_list) == 0:
            logger.warning("Please check the param: object_list, which has length equal to 0.")
            return
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                for item in object_list:
                    json_str = json.dumps(item, ensure_ascii=False)
                    f.write(json_str + '\n')

            os.chmod(save_path, 0o640)
            try:
                parent_dir = os.path.dirname(save_path)
                os.chmod(parent_dir, 0o770)
            except Exception as e:
                logger.warning("Failed to modify the permission on the parent_dir.")

        except Exception as e:
            raise RuntimeError(f"Save jsonl file Failed!, save_path: {save_path}.") from e

        logger.info(f"LLM output has been save to {save_path}.")


class FileExporter(BaseOp):
    """把输入的json文件流抽取为txt"""

    def __init__(self, *args, **kwargs):
        super(FileExporter, self).__init__(*args, **kwargs)
        self.last_ops = True
        self.text_support_ext = kwargs.get("text_support_ext", ['txt', 'html', 'md', 'markdown',
                                                                'xlsx', 'xls', 'csv', 'pptx', 'ppt',
                                                                'xml', 'json', 'doc', 'docx', 'pdf'])
        self.data_support_ext = kwargs.get("data_support_ext", ['jpg', 'jpeg', 'png', 'bmp'])
        self.medical_support_ext = kwargs.get("medical_support_ext", ['svs', 'tif', 'tiff'])

    def execute(self, sample: Dict[str, Any]):
        file_name = sample[self.filename_key]
        file_type = sample[self.filetype_key]

        try:
            start = time.time()
            if file_type in self.text_support_ext:
                sample, save_path = self.get_textfile_handler(sample)
            elif file_type in self.data_support_ext:
                sample, save_path = self.get_datafile_handler(sample)
            elif file_type in self.medical_support_ext:
                sample, save_path = self.get_medicalfile_handler(sample)
            else:
                return False

            if sample[self.text_key] == '' and sample[self.data_key] == b'':
                sample[self.filesize_key] = "0"
                return False

            if save_path:
                save_path = self.save_file(sample, save_path)
                sample[self.text_key] = ''
                sample[self.data_key] = b''
                sample[Fields.result] = True

                file_type = save_path.split('.')[-1]
                sample[self.filetype_key] = file_type

                file_name = os.path.basename(save_path)
                base_name, _ = os.path.splitext(file_name)
                new_file_name = base_name + '.' + file_type
                sample[self.filename_key] = new_file_name

                sample[self.filepath_key] = save_path
                file_size = os.path.getsize(save_path)
                sample[self.filesize_key] = f"{file_size}"

            logger.info(f"origin file named {file_name} has been save to {save_path}")
            logger.info(f"fileName: {sample[self.filename_key]}, "
                        f"method: FileExporter costs {time.time() - start:.6f} s")
        except UnicodeDecodeError as err:
            logger.error(f"fileName: {sample[self.filename_key]}, "
                         f"method: FileExporter causes decode error: {err}")
            raise
        return True

    def get_save_path(self, sample: Dict[str, Any], target_type):
        export_path = os.path.abspath(sample[self.export_path_key])
        file_name = sample[self.filename_key]
        new_file_name = os.path.splitext(file_name)[0] + '.' + target_type

        if not check_valid_path(export_path):
            os.makedirs(export_path, exist_ok=True)
        return os.path.join(export_path, new_file_name)

    def get_textfile_handler(self, sample: Dict[str, Any]):
        target_type = sample.get("target_type", None)

        # target_type存在则保存为扫描件, docx格式
        if target_type:
            sample = self._get_from_text_or_data(sample)
            save_path = self.get_save_path(sample, target_type)
        # 不存在则保存为txt文件，正常文本清洗
        else:
            sample = self._get_from_text_or_data(sample)
            save_path = self.get_save_path(sample, 'txt')
        return sample, save_path

    def get_datafile_handler(self, sample: Dict[str, Any]):
        target_type = sample.get("target_type", None)

        # target_type存在, 图转文保存为target_type，markdown格式
        if target_type:
            sample = self._get_from_text_or_data(sample)
            save_path = self.get_save_path(sample, target_type)
        # 不存在则保存为原本图片文件格式，正常图片清洗
        else:
            sample = self._get_from_text_or_data(sample)
            save_path = self.get_save_path(sample, sample[self.filetype_key])
        return sample, save_path

    def get_medicalfile_handler(self, sample: Dict[str, Any]):
        target_type = 'png'

        sample = self._get_from_data(sample)
        save_path = self.get_save_path(sample, target_type)

        return sample, save_path

    def save_file(self, sample, save_path):
        # 以二进制格式保存文件
        file_sample = sample[self.text_key].encode('utf-8') if sample[self.text_key] else sample[self.data_key]
        path_obj = Path(save_path).resolve()
        parent_dir = path_obj.parent
        stem = path_obj.stem   # 文件名不含后缀
        suffix = path_obj.suffix # 后缀 (.txt)

        counter = 0
        current_path = path_obj
        while True:
            try:
                # x 模式保证：如果文件存在则报错，如果不存在则创建。
                # 这个检查+创建的过程是操作系统级的原子操作，没有竞态条件。
                with open(current_path, 'xb') as f:
                    f.write(file_sample)
                break
            except FileExistsError:
                # 文件已存在（被其他线程/进程抢占），更新文件名重试
                counter += 1
                new_filename = f"{stem}_{counter}{suffix}"
                current_path = parent_dir / new_filename
        os.chmod(parent_dir, 0o770)
        os.chmod(current_path, 0o640)
        return str(current_path)

    def _get_from_data(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        sample[self.data_key] = bytes(sample[self.data_key])
        sample[self.text_key] = ''
        return sample

    def _get_from_text(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        sample[self.data_key] = b''
        sample[self.text_key] = str(sample[self.text_key])
        return sample

    def _get_from_text_or_data(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        if sample[self.data_key] is not None and sample[self.data_key] != b'':
            return self._get_from_data(sample)
        else:
            return self._get_from_text(sample)


    @staticmethod
    def _get_uuid():
        return str(uuid.uuid4())
