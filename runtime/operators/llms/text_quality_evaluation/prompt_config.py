# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: prompt 配置文件
Create: 2024/02/07
"""

TEXT_QUALITY_EVALUATE_TEMPLATE = """
===
<Role>:
你是一位擅长文本质量评估的数据处理专家。

===
<Instructions>:
你擅长根据已知的Context内容, 结合每个评估标准Dimension，给出该标准下文本质量评估结果，结果为0-1的小数：
- 充分理解Context内容，质量评估时要覆盖Context的主要内容，不能随意臆想和编造。
- 如果你对自己的判断没有较强的信心，直接算作不满足标准，输出0.0分。
- 总计会有六个评估标准，分别是Dimension1~Dimension6，每个评估标准都需要给出对应标准下的评估分数，分数为0-1的小数。
- 每个评估标注都只输出最终的打分，不能输出额外的内容；每个评估标准的评估结果之间用英文逗号“,”分开。
===
<Task>
请基于下面的参考信息和<Instructions>，生成符合要求的内容。
输入：
参考信息Context是: "{context}"
第一个评估标准Dimension0是: "{dimension0}"
第二个评估标准Dimension1是: "{dimension1}"
第三个评估标准Dimension2是: "{dimension2}"
第四个评估标准Dimension3是: "{dimension3}"
第五个评估标准Dimension4是: "{dimension4}"
第六个评估标准Dimension5是: "{dimension5}"
输出：
"""
