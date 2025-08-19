import { DatasetStatus, DatasetType } from "@/types/dataset";
import { BarChart3, MessageCircleQuestion, FileImage, FileText, AudioLines, Video, AlarmCheck, ChartArea, CheckCircle, FileArchive, Telescope, SofaIcon } from "lucide-react";

export const DatasetTypeMap = {
    [DatasetType.PRETRAIN]: {
        value: DatasetType.PRETRAIN,
        label: "预训练",
        order: 1,
        children: [DatasetType.PRETRAIN_TEXT, DatasetType.PRETRAIN_IMAGE, DatasetType.PRETRAIN_AUDIO, DatasetType.PRETRAIN_VIDEO],
        description: "用于大规模预训练模型的数据集",
    },
    [DatasetType.FINE_TUNE]: {
        value: DatasetType.FINE_TUNE,
        label: "微调",
        order: 2,
        children: [DatasetType.FINE_TUNE_ALPACA, DatasetType.FINE_TUNE_CHATGLM, DatasetType.FINE_TUNE_BLOOMZ, DatasetType.FINE_TUNE_LLAMA],
        description: "用于微调特定任务或领域模型的数据集",
    },
    [DatasetType.EVAL]: {
        value: DatasetType.EVAL,
        label: "评测",
        order: 3,
        children: [DatasetType.EVAL_GSM8K, DatasetType.EVAL_SQUAD, DatasetType.EVAL_MNLI, DatasetType.EVAL_IMDB, DatasetType.EVAL_SINGLE_CHOICE_QA],
        description: "用于评测模型性能和效果的数据集",
    },
}

export const TypeMap = {
    [DatasetType.PRETRAIN_TEXT]: {
        value: DatasetType.PRETRAIN_TEXT,
        label: "文本预训练",
        color: "blue",
        icon: FileText,
        description: "用于大规模文本预训练模型的数据集"
    },
    [DatasetType.PRETRAIN_IMAGE]: {
        value: DatasetType.PRETRAIN_IMAGE,
        label: "图像预训练",
        color: "green",
        icon: FileImage,
        description: "用于大规模图像预训练模型的数据集"
    },
    [DatasetType.PRETRAIN_AUDIO]: {
        value: DatasetType.PRETRAIN_AUDIO,
        label: "音频预训练", color: "purple",
        icon: AudioLines,
        description: "用于大规模音频预训练模型的数据集"
    },
    [DatasetType.PRETRAIN_VIDEO]: {
        value: DatasetType.PRETRAIN_VIDEO,
        label: "视频预训练",
        color: "orange",
        icon: Video,
        description: "用于大规模视频预训练模型的数据集"
    },
    [DatasetType.FINE_TUNE_ALPACA]: {
        value: DatasetType.FINE_TUNE_ALPACA,
        label: "Alpaca微调",
        color: "cyan",
        icon: BarChart3,
        description: "用于Alpaca模型微调的数据集"
    },
    [DatasetType.FINE_TUNE_CHATGLM]: {
        value: DatasetType.FINE_TUNE_CHATGLM,
        label: "ChatGLM微调",
        color: "teal ",
        icon: MessageCircleQuestion,
        description: "用于ChatGLM模型微调的数据集"
    },
    [DatasetType.FINE_TUNE_BLOOMZ]: {
        value: DatasetType.FINE_TUNE_BLOOMZ,
        label: "BLOOMZ微调",
        color: "pink",
        icon: Telescope,
        description: "用于BLOOMZ模型微调的数据集"
    },
    [DatasetType.FINE_TUNE_LLAMA]: {
        value: DatasetType.FINE_TUNE_LLAMA,
        label: "LLAMA微调",
        color: "red",
        icon: AlarmCheck,
        description: "用于LLAMA模型微调的数据集"
    },
    [DatasetType.EVAL_GSM8K]: {
        value: DatasetType.EVAL_GSM8K,
        label: "GSM8K评测",
        color: "gray",
        icon: ChartArea,
        description: "用于GSM8K数学题评测的数据集"
    },
    [DatasetType.EVAL_SQUAD]: {
        value: DatasetType.EVAL_SQUAD,
        label: "SQuAD评测",
        color: "indigo",
        icon: SofaIcon,
        description: "用于SQuAD问答评测的数据集"
    },
    [DatasetType.EVAL_MNLI]: {
        value: DatasetType.EVAL_MNLI,
        label: "MNLI评测",
        color: "lime",
        icon: FileArchive,
        description: "用于MNLI自然语言推断评测的数据集"
    },
    [DatasetType.EVAL_IMDB]: {
        value: DatasetType.EVAL_IMDB,
        label: "IMDB评测",
        color: "yellow",
        icon: FileText,
        description: "用于IMDB情感分析评测的数据集"
    },
    [DatasetType.EVAL_SINGLE_CHOICE_QA]: {
        value: DatasetType.EVAL_SINGLE_CHOICE_QA,
        label: "单选题评测",
        color: "brown",
        icon: CheckCircle,
        description: "用于单选题问答评测的数据集"
    },
}

export const DatasetStatusMap = {
    [DatasetStatus.DRAFT]: { value: DatasetStatus.DRAFT, label: "草稿", color: "gray" },
    [DatasetStatus.PROCESSING]: { value: DatasetStatus.PROCESSING, label: "处理中", color: "blue" },
    [DatasetStatus.ARCHIVED]: { value: DatasetStatus.ARCHIVED, label: "已归档", color: "orange" },
    [DatasetStatus.PUBLISHED]: { value: DatasetStatus.PUBLISHED, label: "已发布", color: "green" },
}