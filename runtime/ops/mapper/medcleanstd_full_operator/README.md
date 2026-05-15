# MedCleanStd 全流程算子

## 概述

这个算子将原来的 4 个 MedCleanStd 阶段整合到了一个 Mapper 中：

- 文档解析或原始文本读取
- 医学文本纠错
- 基于 SiameseUIE 的医学实体识别
- 术语标准化并将最终结果落盘为 JSON

## 模型路径

- `/models/MedCleanStd/SiameseUIE`
- `/models/MedCleanStd/bge-small-zh-v1.5`

## 输出说明

最终输出会保留各阶段的中间结果，并将完整 JSON 写入目标数据集的导出目录。
