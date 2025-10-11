# QA评估插件
## 背景
基于维度和描述对QA对进行评估，支持用户自定义维度。
### 约束：
- 维度小于10个
- 维度名称低于20个字
- 依赖大模型服务，服务输入输出如下：
```python
# 输入
request_template = {
    "prompt": "你好",
    "max_length": 2024,
    "top_n": 0.9,
    "temperature": 0.9
}
# 输出
response_template = {
    "response":"XXX"
}
```
#### 默认3个维度：
- 问题是否独立
- 问答是否针对
- 语法是否错误

## 调用接口输入
```python
inputs = [[
        {
            "businessData": {
                "params": {
                    "taskId":1,
                    "LLMUrl":"https://x.x.x.x:xxxx/qwen",
                    "LLMHeaders":{"Content-Type": "application/json","User-Agent":"Client"},
                    "LLMBody":{
                        "prompt": "你好",
                        "max_length": 2024,
                        "top_n": 0.9,
                        "temperature": 0.9
                        },
                    "dimension":[
                        {"dimension":"回答是否有针对性",
                        "description":"回答应对问题中的所有疑问点提供正面、直接的回答，不应引起疑惑。同时，答案不应有任何内容的遗漏，需构成一个完整的陈述。"
                        },
                        {"dimension":"问题是否独立",
                        "description":"仅分析问题，问题的主体和客体都比较明确，即使有省略，也符合语言习惯。在不需要补充其他信息的情况下不会引起疑惑。"
                        },
                        {"dimension":"语法是否错误",
                        "description":"问题为疑问句，答案为陈述句; 不存在词语搭配不当的情况;连接词和标点符号不存在错用情况；逻辑混乱的情况不存在；语法结构都正确且完整;"
                        }
                        ]
                }
            },
            "passData": {
                "data": "",
                "text": "[{\"question\":\"什么是秋燥、秋困和秋冻？\",\"answer\":\"秋燥、秋困和秋冻是秋天常见的三种症状和养生问题。秋燥是指秋天天气干燥，导致人体水分流失，出现皮肤发痒、嘴唇起皮、鼻咽干燥等症状；秋困是指秋天天气凉爽，人体代谢下降，导致人感到无精打采、呵欠连天、昏昏欲睡等症状；秋冻是指秋天气温下降，人体需要适应气温的变化，不能一下子穿上很多衣服，让身体适应气温的变化。\",\"qaId\":1}]",
                "meta": {
                }
            },
            "contextData": {}
        }
]]

```
调用接口输出
```python
outputs = [
    {
        "businessData": {
            "params": {
                "taskId": 1,
                "LLMUrl": "https://x.x.x.x:xxxx/qwen",
                "LLMHeaders": {
                    "Content-Type": "application/json",
                    "User-Agent": "Client"
                },
                "LLMBody": {
                    "prompt": "你好",
                    "max_length": 2024,
                    "top_n": 0.9,
                    "temperature": 0.9
                },
                "dimension": [
                    {
                        "dimension": "回答是否有针对性",
                        "description": "回答应对问题中的所有疑问点提供正面、直接的回答，不应引起疑惑。同时，答案不应有任何内容的遗漏，需构成一个完整的陈述。"
                    },
                    {
                        "dimension": "问题是否独立",
                        "description": "仅分析问题，问题的主体和客体都比较明确，即使有省略，也符合语言习惯。在不需要补充其他信息的情况下不会引起疑惑。"
                    },
                    {
                        "dimension": "语法是否错误",
                        "description": "问题为疑问句，答案为陈述句; 不存在词语搭配不当的情况;连接词和标点符号不存在错用情况；逻辑混乱的情况不存在；语法结构都正确且完整;"
                    }
                ]
            }
        },
        "passData": {
            "data": "",
            "text": "[{\"qaId\": 1, \"result\": [{\"dimension\": \"\回\答\是\否\有\针\对\性\", \"result\": true}, {\"dimension\": \"\问\题\是\否\独\立\", \"result\": true}, {\"dimension\": \"\语\法\是\否\错\误\", \"result\": true}]}]",
            "meta": {}
        },
        "contextData": {}
    }
]
```