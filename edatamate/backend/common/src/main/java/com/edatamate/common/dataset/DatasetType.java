package com.edatamate.common.dataset;

/**
 * 数据集类型枚举
 */
public enum DatasetType {
    PRETRAIN,   // 预训练数据集
    FINE_TUNE,  // 微调数据集
    EVAL,        // 评测数据集

    // 预训练数据集子类型
    PRETRAIN_TEXT,    // 泛文本
    PRETRAIN_IMAGE,   // 图片
    PRETRAIN_AUDIO,   // 音频
    PRETRAIN_VIDEO,   // 视频

    // 微调数据集子类型
    FINE_TUNE_ALPACA, // Alpaca格式

    // 评测数据集子类型
    EVAL_GSM8K,       // GSM8K评测
    EVAL_SINGLE_CHOICE_QA // 单选问答对
}
