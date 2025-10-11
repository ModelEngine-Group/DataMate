# -*- coding: utf-8 -*-
#  Copyright (c) 2025. Huawei Technologies Co., Ltd. All rights reserved.
#  This file is a part of the ModelEngine Project.
#  Licensed under the MIT License. See License.txt in the project root for license information.
"""
Description: 指令数据生成常量
Create: 2023/11/20 16:20
"""

EVAL_DIMENSION_MAP = [
    {
        "dimension": "完备性",
        "description": "数据的记录和信息是否是完整的，是否存在缺失的情况",
        "score_name": "qua_score"
    },
    {
        "dimension": "一致性",
        "description": "同一指标在不同地方的结果是否一致",
        "score_name": "logic_score"
    },
    {
        "dimension": "有效性",
        "description": "该样本涉及某领域的信息量",
        "score_name": "effective_score"
    }
]

BUSINESS_EVAL_DIMENSION_MAP = [
    {
        "dimension": "金融",
        "description": "涉及保险合同、保险问答、年报、资产负债表、金融新闻、保险从业资格CICE、基金从业资格、期货从业资格、注册会计师（CPA"
                       "）、理财规划师、税务师、精算师-金融数学、经济师、证券从业资格、银行从业资格等相关金融行业知识",
        "score_name": "finance_score"
    },
    {
        "dimension": "存储",
        "description": "存储",
        "score_name": "storage_score"
    },
    {
        "dimension": "医疗",
        "description": "涵盖中医科、儿科、内科、口腔科、外科、妇产科、心理科学、急诊科、感染与免疫科、生殖健康科、男性健康科、皮肤性病科、眼耳鼻喉科、神经科学、肿瘤科等医疗相关领域",
        "score_name": "medical_score"
    }
]
