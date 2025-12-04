EVALUATION_PROMPT_TEMPLATE = [
    {
        "evalType": "QA",
        "defaultDimensions": [
            {
                "dimension": "问题是否独立",
                "description": "仅分析问题，问题的主体和客体都比较明确，即使有省略，也符合语言习惯。在不需要补充其他信息的情况下不会引起疑惑。"
            },
            {
                "dimension": "语法是否错误",
                "description": "问题为疑问句，答案为陈述句; 不存在词语搭配不当的情况;连接词和标点符号不存在错用情况；逻辑混乱的情况不存在；语法结构都正确且完整。"
            },
            {
                "dimension": "回答是否有针对性",
                "description": "回答应对问题中的所有疑问点提供正面、直接的回答，不应引起疑惑。同时，答案不应有任何内容的遗漏，需构成一个完整的陈述。"
            }
        ],
        "prompt": """
# Role: 问答对质量评估专家
## Profile:
- Description: 你是一名专业的对话文本质量评估专家，擅长从多个维度对问答对进行质量评估，为机器学习模型训练提供高质量的数据筛选建议。具备深度学习、自然语言处理和数据科学的专业背景。

## Skills:
1. 能够从多个维度对问答对进行综合评估
2. 擅长识别问答对中的潜在问题，如答案不准确、问题模糊、文本不匹配、逻辑错误等
3. 能够给出具体的改进建议和质量评分，并提供可操作的优化方案
4. 熟悉机器学习训练数据的质量标准和最佳实践
5. 能够区分不同类型的问题（事实性、推理性、创造性）并采用相应的评估标准

## 评估维度:
{dimensions}

## 原始文本块内容:
{content}

## 问题:
{question}

## 答案:
{answer}

## 评估说明:
1. **数据集类型识别**：如果原始文本块内容为空或显示"Distilled Content"，说明这是一个蒸馏数据集，没有原始文本参考。请重点评估问题的质量、答案的合理性和逻辑性，以及问答的一致性。
2. **评估原则**：采用严格的评估标准，确保筛选出的数据集能够有效提升模型性能。

## 注意事项:
- 评估结论要具体指出优点和不足，提供可操作的改进建议
- 评估结论控制在150字以内，简洁明了但要涵盖关键信息

## 输出要求:
请按照以下JSON格式输出评估结果，评估结果为Y/N，符合标注输出Y，不符合标准输出N：

{
  "result": {{result_example}
  },
  "evaluation": "这是一个高质量的问答数据集。问题表述清晰具体，答案准确完整且逻辑性强，与原始文本高度相关。建议：可以进一步丰富答案的细节描述。"
}
"""
    }
]

def get_dimensions_for_qa(dimensions: list[dict]) -> str:
    dimensions_str = "\n"
    index = 1
    for dimension in dimensions:
        dimensions_str += f"### {index}. {dimension.get("dimension")}\n**评估标准：**\n{dimension.get("description")}\n\n"
        index += 1
    return dimensions_str

def get_result_example_for_qa(dimensions: list[dict]) -> str:
    result_example = ""
    for dimension in dimensions:
        result_example += f'\n    "{dimension.get("dimension")}": "Y",'
    return result_example

def get_prompt(task_type: str, dimensions: list[dict]) -> str:
    template = None
    for t in EVALUATION_PROMPT_TEMPLATE:
        if t.get("evalType") == task_type:
            template = t.get("prompt")
            break
    if not template:
        template = EVALUATION_PROMPT_TEMPLATE[0].get("prompt", "")
    if not dimensions or len(dimensions) == 0:
        return template
    return (template.replace("{dimensions}", get_dimensions_for_qa(dimensions))
                       .replace("{result_example}", get_result_example_for_qa(dimensions)))
