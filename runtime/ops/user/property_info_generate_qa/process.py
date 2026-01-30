"""
QA对生成算子 - process.py
根据模拟图片和不动产数据，生成问答对格式的JSON文件
"""

import os
import json
import re
import base64
import requests
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger

from datamate.core.base_op import Mapper


# 定义所有可能的字段名称
ALL_FIELDS = [
    "省份",
    "姓名",
    "证件号码",
    "姓名（证件号码）",
    "申请查询人",
    "查询目的",
    "序号",
    "状态",
    "登记字号",
    "合同号",
    "登记字号/合同号",
    "土地、房屋地址",
    "地址",
    "产权证号",
    "规划用途",
    "房屋性质",
    "规划用途（房屋性质）",
    "建筑面积",
    "建筑面积（㎡）",
    "数据来源",
    "电脑查册人",
    "证明流水号",
    "打印日期",
    "表格数据",
]

# 定义字段分组（用于简化输出）
FIELD_GROUPS = {
    "省份": ["省份"],
    "姓名（证件号码）": ["姓名（证件号码）", "姓名", "证件号码"],
    "申请查询人": ["申请查询人"],
    "查询目的": ["查询目的"],
    "表格数据": [
        "序号",
        "状态",
        "登记字号/合同号",
        "登记字号",
        "合同号",
        "土地、房屋地址",
        "地址",
        "产权证号",
        "规划用途（房屋性质）",
        "规划用途",
        "房屋性质",
        "建筑面积（㎡）",
        "建筑面积",
        "数据来源",
    ],
    "电脑查册人": ["电脑查册人"],
    "证明流水号": ["证明流水号"],
    "打印日期": ["打印日期"],
}


class FieldDetector:
    """字段检测类 - 使用大模型API识别图片中的字段"""

    def __init__(self, use_llm: bool = True, config: Dict[str, Any] = None):
        """
        初始化字段检测器

        Args:
            use_llm: 是否使用大模型API（默认True）
            config: 大模型配置字典
        """
        self.use_llm = use_llm
        self.config = config or {}
        self.llm_config = self.config.get("llm", {})
        # 缓存大模型识别结果，避免对同一文档的不同背景图重复调用API
        self._cache = {}

    def detect_fields_from_image(self, image_path: str) -> Dict[str, bool]:
        """
        从图片中检测包含的字段

        Args:
            image_path: 图片路径（支持绝对路径或相对路径）

        Returns:
            字段存在字典 {字段名: 是否存在}
        """
        # 初始化所有字段为False
        field_presence = {field: False for field in FIELD_GROUPS.keys()}

        # 处理路径：优先使用绝对路径，如果绝对路径不可用则尝试相对路径
        abs_image_path = None

        # 1. 如果是绝对路径，直接使用
        if os.path.isabs(image_path):
            abs_image_path = image_path
        # 2. 如果是相对路径，尝试转换为绝对路径
        else:
            # 尝试转换为绝对路径
            abs_image_path = os.path.abspath(image_path)

        # 检查文件是否存在
        if not os.path.exists(abs_image_path):
            logger.error(f"图片文件不存在: {abs_image_path}")
            return field_presence

        # 使用大模型识别字段
        if self.use_llm:
            field_presence = self._detect_with_llm(abs_image_path)
        else:
            # 使用预设字段分布（所有字段都返回False，由调用方根据页码决定）
            pass

        return field_presence

    def _detect_with_llm(self, image_path: str) -> Dict[str, bool]:
        """
        使用大模型API识别图片中的字段

        Args:
            image_path: 图片路径

        Returns:
            字段存在字典
        """
        try:
            # 使用文件名作为缓存键（同一文档的不同背景图使用相同的结果）
            # 提取文档编号和页码作为缓存键
            filename = os.path.basename(image_path)
            # 匹配：不动产查询表_001-1_2-桌面实景图.jpg
            match = re.search(r"不动产查询表_(\d+)-(\d+)_", filename)
            if match:
                doc_num = match.group(1)
                page_num = match.group(2)
                cache_key = f"{doc_num}_{page_num}"

                # 检查缓存
                if cache_key in self._cache:
                    logger.info(
                        f"[大模型缓存] 使用缓存结果: 文档{doc_num}第{page_num}页"
                    )
                    return self._cache[cache_key]

            # 将图片编码为base64
            image_base64 = self._encode_image_to_base64(image_path)

            # 构建提示词
            prompt = self._build_prompt()

            # 构建请求
            payload = {
                "model": self.llm_config.get(
                    "model_name", "Qwen/Qwen2-VL-72B-Instruct"
                ),
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}"
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.1,
            }

            # 发送请求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.llm_config.get('api_key', '')}",
            }

            response = requests.post(
                self.llm_config.get("api_url", ""),
                json=payload,
                headers=headers,
                timeout=self.llm_config.get("timeout", 60),
            )

            # 解析响应
            if response.status_code == 200:
                result = response.json()
                content = (
                    result.get("choices", [{}])[0].get("message", {}).get("content", "")
                )
                field_presence = self._parse_llm_response(content)

                # 缓存结果
                if match:
                    doc_num = match.group(1)
                    page_num = match.group(2)
                    cache_key = f"{doc_num}_{page_num}"
                    self._cache[cache_key] = field_presence

                return field_presence
            elif response.status_code == 429:
                logger.warning(
                    f"大模型API请求被限流: {response.status_code}, {response.text}"
                )
                return {field: False for field in FIELD_GROUPS.keys()}
            else:
                logger.error(
                    f"大模型API请求失败: {response.status_code}, {response.text}"
                )
                return {field: False for field in FIELD_GROUPS.keys()}

        except Exception as e:
            logger.error(f"大模型识别失败: {e}")
            return {field: False for field in FIELD_GROUPS.keys()}

    def _encode_image_to_base64(self, image_path: str) -> str:
        """将图片编码为base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _build_prompt(self) -> str:
        """构建提示词"""
        fields_list = "\n".join([f"- {field}" for field in ALL_FIELDS])
        prompt = f"""请识别这张图片中包含的字段名称。

图片是不动产信息查询结果，可能包含以下字段：
{fields_list}

请只返回图片中实际存在的字段名称，用逗号分隔。不要返回任何其他内容。

示例输出格式：
省份,姓名（证件号码）,查询目的,申请查询人,表格数据"""
        return prompt

    def _parse_llm_response(self, response: str) -> Dict[str, bool]:
        """
        解析大模型响应

        Args:
            response: 大模型返回的文本

        Returns:
            字段存在字典
        """
        # 初始化所有字段为False
        field_presence = {field: False for field in FIELD_GROUPS.keys()}

        # 解析响应中的字段名称
        detected_fields = []
        for field in ALL_FIELDS:
            if field in response:
                detected_fields.append(field)

        # 根据字段分组设置存在状态
        for group_name, group_fields in FIELD_GROUPS.items():
            for field in group_fields:
                if field in detected_fields:
                    field_presence[group_name] = True
                    break  # 组内有一个字段存在即可

        return field_presence

    def get_field_names_from_presence(
        self, field_presence: Dict[str, bool]
    ) -> List[str]:
        """
        根据字段存在情况获取字段名称列表

        Args:
            field_presence: 字段存在字典

        Returns:
            存在的字段名称列表
        """
        return [field for field, exists in field_presence.items() if exists]


class PropertyQAJsonGeneratorMapper(Mapper):
    """
    QA对生成算子：QAJsonGeneratorMapper
    对应 metadata.yml 中的 raw_id
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 获取算子参数
        self.output_filename = kwargs.get("outputFilenameParam", "output.json")
        self.use_llm = kwargs.get("useLLMParam", False)

        # 字段检测器延迟初始化（仅在检测到分页时才初始化）
        self.field_detector = None
        self.dataset_dir = None

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        config_path = self.dataset_dir / "config.yaml"
        if not config_path.exists():
            logger.warning(f"配置文件不存在: {config_path}，将使用默认配置")
            return {}

        try:
            import yaml

            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}，将使用默认配置")
            return {}

    def _extract_name_and_id(self, data: Dict[str, Any]) -> tuple:
        """
        从"姓名（证件号码）"提取姓名和证件号码

        Args:
            data: 数据字典

        Returns:
            (姓名, 证件号码)
        """
        name_id = data.get("姓名（证件号码）", "")
        if "（" in name_id and "）" in name_id:
            name = name_id.split("（")[0]
            id_num = name_id.split("（")[1].rstrip("）")
            return name, id_num
        return name_id, ""

    def _is_paged(self, doc_number: int, image_dir: str) -> bool:
        """
        判断文档是否分页（检查是否存在第二页图片）

        Args:
            doc_number: 文档编号
            image_dir: 图片目录

        Returns:
            是否分页
        """
        # 使用正则表达式检查是否存在第二页图片
        page2_pattern = re.compile(rf"不动产查询表_{doc_number:03d}[-_]2")

        if os.path.exists(image_dir):
            image_files = os.listdir(image_dir)
            for f in image_files:
                if page2_pattern.match(f):
                    logger.info(f"[分页检测] 文档已分页（检测到第2页图片）")
                    return True
        logger.info(f"[分页检测] 文档未分页")
        return False

    def _get_placeholder_data(
        self,
        data: Dict[str, Any],
        page_number: int = 1,
        image_path: str = None,
        doc_number: int = 1,
        image_dir: str = None,
    ) -> Dict[str, Any]:
        """
        获取所有占位符数据字典

        Args:
            data: 数据字典
            page_number: 页码
            image_path: 图片路径（用于大模型识别字段）
            doc_number: 文档编号
            image_dir: 图片目录

        Returns:
            占位符数据字典
        """
        # 提取姓名和证件号码
        name, id_num = self._extract_name_and_id(data)

        # 获取表格数据
        table_data = data.get("表格数据", [])

        # 判断是否分页
        is_paged = False
        if image_dir and doc_number:
            is_paged = self._is_paged(doc_number, image_dir)

        # 构建占位符数据字典
        placeholder_data = {}

        # 如果没分页，直接获取全量字段（不调用大模型）
        if not is_paged:
            placeholder_data = {
                "省份": data.get("省份", ""),
                "姓名": name,
                "证件号码": id_num,
                "申请查询人": name,
                "查询目的": data.get("查询目的", ""),
                "表格数据": table_data,
                "电脑查册人": data.get("电脑查册人", ""),
                "证明流水号": data.get("证明流水号", ""),
                "打印日期": data.get("打印日期", ""),
            }
        # 如果分页了，调用大模型识别每一张图片的内容
        else:
            # 延迟初始化字段检测器（仅在检测到分页时才初始化）
            if self.field_detector is None:
                try:
                    logger.info("[大模型初始化] 检测到分页文档，开始初始化字段检测器")
                    config = self._load_config()
                    self.field_detector = FieldDetector(
                        use_llm=self.use_llm, config=config
                    )
                    logger.info("字段检测器初始化成功")
                except Exception as e:
                    logger.error(f"字段检测器初始化失败: {e}")
                    raise RuntimeError(
                        "文档已分页，但字段检测器不可用。请检查config.yaml中的大模型API配置。"
                    )

            logger.info(
                f"[大模型调用] 文档{doc_number}第{page_number}页 - 开始调用大模型识别字段"
            )
            try:
                field_presence = self.field_detector.detect_fields_from_image(
                    image_path
                )
                detected_fields = self.field_detector.get_field_names_from_presence(
                    field_presence
                )
                logger.info(
                    f"[大模型结果] 文档{doc_number}第{page_number}页检测到字段: {', '.join(detected_fields)}"
                )

                # 使用大模型检测结果
                if "省份" in detected_fields:
                    placeholder_data["省份"] = data.get("省份", "")
                if "姓名（证件号码）" in detected_fields or "姓名" in detected_fields:
                    placeholder_data["姓名"] = name
                    placeholder_data["证件号码"] = id_num
                if "申请查询人" in detected_fields:
                    placeholder_data["申请查询人"] = name
                if "查询目的" in detected_fields:
                    placeholder_data["查询目的"] = data.get("查询目的", "")
                if "表格数据" in detected_fields:
                    placeholder_data["表格数据"] = table_data
                if "电脑查册人" in detected_fields:
                    placeholder_data["电脑查册人"] = data.get("电脑查册人", "")
                if "证明流水号" in detected_fields:
                    placeholder_data["证明流水号"] = data.get("证明流水号", "")
                if "打印日期" in detected_fields:
                    placeholder_data["打印日期"] = data.get("打印日期", "")
            except Exception as e:
                logger.warning(f"字段识别失败: {e}，使用预设字段分布")
                # 降级使用预设字段分布
                if page_number == 1:
                    placeholder_data = {
                        "省份": data.get("省份", ""),
                        "姓名": name,
                        "证件号码": id_num,
                        "申请查询人": name,
                        "查询目的": data.get("查询目的", ""),
                        "表格数据": table_data,
                    }
                elif page_number == 2:
                    placeholder_data = {
                        "电脑查册人": data.get("电脑查册人", ""),
                        "证明流水号": data.get("证明流水号", ""),
                        "打印日期": data.get("打印日期", ""),
                    }

        return placeholder_data

    def _generate_human_question(self, placeholder_data: Dict[str, Any]) -> str:
        """
        生成human问题（动态获取占位符名称）

        Args:
            placeholder_data: 占位符数据字典

        Returns:
            human问题字符串
        """
        # 获取所有占位符名称（排除空数组）
        placeholder_names = []
        for key, value in placeholder_data.items():
            if isinstance(value, list) and len(value) > 0:
                placeholder_names.append(key)
            elif isinstance(value, str) and value:
                placeholder_names.append(key)

        # 构建问题
        question = "<image>\n"
        question += "你是一个专业的图片识别助手，按照以下要求，将图片中指定的内容提取为json格式，提取json的具体要求有：\n"
        question += f"要求提取{'、'.join(placeholder_names)}这些字段。\n"
        question += "要返回的json格式为图片中提取的实际值。\n"
        question += "识别过程中，请确保准确提取每个字段的值。"

        return question

    def _generate_gpt_answer(self, placeholder_data: Dict[str, Any]) -> str:
        """
        生成gpt答案（动态获取占位符数据）

        Args:
            placeholder_data: 占位符数据字典

        Returns:
            gpt答案JSON字符串
        """
        return json.dumps(placeholder_data, ensure_ascii=False)

    def _generate_single_json_entry(
        self,
        data: Dict[str, Any],
        image_path: str,
        index: int,
        page_number: int = 1,
        image_full_path: str = None,
        image_dir: str = None,
    ) -> Dict[str, Any]:
        """
        生成单条JSON记录（新格式）

        Args:
            data: 数据字典
            image_path: 图片路径
            index: 序号
            page_number: 页码（1表示第一页，2表示第二页）
            image_full_path: 图片完整路径
            image_dir: 图片目录

        Returns:
            JSON记录字典
        """
        # 获取占位符数据（使用大模型动态识别字段）
        # 优先使用绝对路径进行识别
        detect_image_path = image_full_path if image_full_path else image_path
        placeholder_data = self._get_placeholder_data(
            data, page_number, detect_image_path, index, image_dir
        )

        # 生成human问题
        human_question = self._generate_human_question(placeholder_data)

        # 生成gpt答案
        gpt_answer = self._generate_gpt_answer(placeholder_data)

        # 构建记录（新格式）
        record = {
            "images": image_path,
            "conversations": [
                {
                    "from": "human",
                    "value": human_question,
                },
                {
                    "from": "gpt",
                    "value": gpt_answer,
                },
            ],
        }

        return record

    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        """
        核心执行逻辑

        Args:
            sample: 输入样本

        Returns:
            处理后的样本
        """
        file_path = sample.get("filePath")
        if (
            not file_path.endswith(".docx")
            or os.path.normpath(file_path).count(os.sep) > 3
        ):
            return sample

        try:
            # 获取输出路径
            export_path = sample.get("export_path")
            if not export_path:
                logger.error("export_path is empty")
                return sample

            # 构建图片目录
            parent_path = Path(file_path).parent
            self.dataset_dir = parent_path
            image_dir = Path(str(sample['export_path'])) / "simulated_images"

            if not image_dir.exists():
                logger.warning(f"图片目录不存在: {image_dir}")
                return sample

            # 获取数据列表
            text = sample.get("text", "")
            if text:
                try:
                    data_list = json.loads(text)
                except Exception as e:
                    logger.warning(f"解析 JSON 数据失败: {e}")
                    return sample

            logger.info(f"[步骤6-QA对生成] 开始生成QA对，共{len(data_list)}组数据")

            # 获取目录下所有JPG文件并排序
            image_files = [f for f in os.listdir(image_dir) if f.endswith(".jpg")]
            image_files.sort()
            logger.info(f"[步骤6-QA对生成] 找到{len(image_files)}张图片")

            # 为每张模拟图片生成JSON记录
            json_records = []

            for image_file in image_files:
                # 从文件名提取序号
                # 匹配模式：不动产查询表_{doc_number:03d}[-_]{page_number}[-_]{bg_number}_.*\.jpg
                match = re.search(
                    r"不动产查询表_(\d+)[-_.](\d+)[-_.](\d+)[-_.].*\.jpg", image_file
                )
                if not match:
                    logger.warning(f"[文件解析] 无法解析文件名: {image_file}，跳过")
                    continue

                # 提取文档编号（基础编号，不包含页码）
                doc_number = int(match.group(1))
                # 提取页码，默认为1
                page_number = int(match.group(2)) if match.group(2) else 1

                # 检查数据索引是否有效
                if doc_number - 1 < 0 or doc_number - 1 >= len(data_list):
                    logger.info(
                        f"[数据跳过] 跳过旧图片: {image_file}（文档编号{doc_number}，当前数据共{len(data_list)}组）"
                    )
                    continue

                # 获取对应的数据
                data = data_list[doc_number - 1]

                # 生成JSON记录（使用项目中的相对路径）
                image_full_path = os.path.abspath(os.path.join(image_dir, image_file))
                # 使用相对于 export_path 的路径
                image_path = os.path.relpath(image_full_path, export_path).replace(
                    "/", "\\"
                )

                record = self._generate_single_json_entry(
                    data,
                    image_path,
                    doc_number,
                    page_number,
                    image_full_path,
                    str(image_dir),
                )
                json_records.append(record)

            # 保存JSON文件（数组格式）
            output_path = os.path.join(export_path, self.output_filename)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(json_records, f, ensure_ascii=False, indent=2)

            logger.info(
                f"[步骤6-QA对生成] JSON文件已保存到 {output_path}，共{len(json_records)}条记录"
            )

        except Exception as e:
            logger.error(f"Error in QAJsonGeneratorMapper: {e}")
            import traceback

            traceback.print_exc()

        return sample
