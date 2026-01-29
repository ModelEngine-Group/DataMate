# 结婚证流水线算子（marriage）

本包提供结婚证数据生成与 QA 构建流水线的 DataMate 自定义算子，执行顺序建议：

1. **MarriageRandomText**：从坐标 JSON 生成多组随机结婚证文本，输出 `random_content.json`
2. **MarriageImageCompositing**：将文本渲染到模板图，按 group_id 输出多张图片
3. **MarriageAddSeal**：在图片上添加结婚登记专用章
4. **MarriageAugmentImages**：将结婚证图合成到实拍背景（斜拍、阴影、水印等）
5. **MarriageFormQA**：根据图片与 random_content 生成 llama 格式 QA 对（`output_qa_pairs.jsonl`）

## 源数据集

用户创建的源数据集中需包含以下文件（可来自 `MarriageCertificate/input`）：

- `coordinate_info.json`：Label Studio 风格坐标
- `template.jpg`：结婚证模板图
- `effect_image/*.jpg`：背景/实拍图（用于 augment_images；也可通过算子参数指定目录）

各算子通过 `sample['filePath']`、`sample['export_path']` 串联，模板/坐标未显式配置时从任务目录或上级目录查找。
