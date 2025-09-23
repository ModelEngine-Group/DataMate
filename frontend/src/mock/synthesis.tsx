// Add mock files data
export const mockFiles = [
  { id: "file1", name: "dataset_part_001.jsonl", size: "2.5MB", type: "JSONL" },
  { id: "file2", name: "dataset_part_002.jsonl", size: "2.3MB", type: "JSONL" },
  { id: "file3", name: "dataset_part_003.jsonl", size: "2.7MB", type: "JSONL" },
  { id: "file4", name: "training_data.txt", size: "1.8MB", type: "TXT" },
  { id: "file5", name: "validation_set.csv", size: "856KB", type: "CSV" },
  { id: "file6", name: "test_samples.json", size: "1.2MB", type: "JSON" },
  { id: "file7", name: "raw_text_001.txt", size: "3.1MB", type: "TXT" },
  { id: "file8", name: "raw_text_002.txt", size: "2.9MB", type: "TXT" },
];

export const mockSynthesisTasks: SynthesisTask[] = [
  {
    id: 1,
    name: "文字生成问答对_判断题",
    type: "qa",
    status: "completed",
    progress: 100,
    sourceDataset: "orig_20250724_64082",
    targetCount: 1000,
    generatedCount: 1000,
    createdAt: "2025-01-20",
    template: "判断题生成模板",
    estimatedTime: "已完成",
    quality: 95,
  },
  {
    id: 2,
    name: "知识蒸馏数据集",
    type: "distillation",
    status: "running",
    progress: 65,
    sourceDataset: "teacher_model_outputs",
    targetCount: 5000,
    generatedCount: 3250,
    createdAt: "2025-01-22",
    template: "蒸馏模板v2",
    estimatedTime: "剩余 15 分钟",
    quality: 88,
  },
  {
    id: 3,
    name: "多模态对话生成",
    type: "multimodal",
    status: "failed",
    progress: 25,
    sourceDataset: "image_text_pairs",
    targetCount: 2000,
    generatedCount: 500,
    createdAt: "2025-01-23",
    template: "多模态对话模板",
    errorMessage: "模型API调用失败，请检查配置",
  },
  {
    id: 4,
    name: "金融问答数据生成",
    type: "qa",
    status: "pending",
    progress: 0,
    sourceDataset: "financial_qa_dataset",
    targetCount: 800,
    generatedCount: 0,
    createdAt: "2025-01-24",
    template: "金融问答模板",
    estimatedTime: "等待开始",
    quality: 0,
  },
  {
    id: 5,
    name: "医疗文本蒸馏",
    type: "distillation",
    status: "paused",
    progress: 45,
    sourceDataset: "medical_corpus",
    targetCount: 3000,
    generatedCount: 1350,
    createdAt: "2025-01-21",
    template: "医疗蒸馏模板",
    estimatedTime: "已暂停",
    quality: 92,
  },
];

export const mockTemplates: Template[] = [
  {
    id: 1,
    name: "判断题生成模板",
    type: "preset",
    category: "问答对生成",
    prompt: `根据给定的文本内容，生成一个判断题。

文本内容：{text}

请按照以下格式生成：
1. 判断题：[基于文本内容的判断题]
2. 答案：[对/错]
3. 解释：[简要解释为什么这个答案是正确的]

要求：
- 判断题应该基于文本的核心内容
- 答案必须明确且有依据
- 解释要简洁清晰`,
    variables: ["text"],
    description: "根据文本内容生成判断题，适用于教育和培训场景",
    usageCount: 156,
    lastUsed: "2025-01-20",
    quality: 95,
  },
  {
    id: 2,
    name: "选择题生成模板",
    type: "preset",
    category: "问答对生成",
    prompt: `基于以下文本，创建一个多选题：

{text}

请按照以下格式生成：
问题：[基于文本的问题]
A. [选项A]
B. [选项B] 
C. [选项C]
D. [选项D]
正确答案：[A/B/C/D]
解析：[详细解释]

要求：
- 问题要有一定难度
- 选项要有迷惑性
- 正确答案要有充分依据`,
    variables: ["text"],
    description: "生成多选题的标准模板，适用于考试和评估",
    usageCount: 89,
    lastUsed: "2025-01-19",
    quality: 92,
  },
  {
    id: 3,
    name: "知识蒸馏模板",
    type: "preset",
    category: "蒸馏数据集",
    prompt: `作为学生模型，学习教师模型的输出：

输入：{input}
教师输出：{teacher_output}

请模仿教师模型的推理过程和输出格式，生成相似质量的回答。

要求：
- 保持教师模型的推理逻辑
- 输出格式要一致
- 质量要接近教师模型水平`,
    variables: ["input", "teacher_output"],
    description: "用于知识蒸馏的模板，帮助小模型学习大模型的能力",
    usageCount: 234,
    lastUsed: "2025-01-22",
    quality: 88,
  },
  {
    id: 4,
    name: "金融问答模板",
    type: "custom",
    category: "问答对生成",
    prompt: `基于金融领域知识，生成专业问答对：

参考内容：{content}

生成格式：
问题：[专业的金融问题]
答案：[准确的专业回答]
关键词：[相关金融术语]

要求：
- 问题具有实用性
- 答案准确专业
- 符合金融行业标准`,
    variables: ["content"],
    description: "专门用于金融领域的问答对生成",
    usageCount: 45,
    lastUsed: "2025-01-18",
    quality: 89,
  },
  {
    id: 5,
    name: "医疗蒸馏模板",
    type: "custom",
    category: "蒸馏数据集",
    prompt: `医疗知识蒸馏模板：

原始医疗文本：{medical_text}
专家标注：{expert_annotation}

生成医疗知识点：
1. 核心概念：[提取关键医疗概念]
2. 临床意义：[说明临床应用价值]
3. 注意事项：[重要提醒和禁忌]

要求：
- 确保医疗信息准确性
- 遵循医疗伦理规范
- 适合医学教育使用`,
    variables: ["medical_text", "expert_annotation"],
    description: "医疗领域专用的知识蒸馏模板",
    usageCount: 67,
    lastUsed: "2025-01-21",
    quality: 94,
  },
];
