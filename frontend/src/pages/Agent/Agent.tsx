import type React from "react";

import { useState, useRef, useEffect } from "react";
import { Card, Input, Button, Badge } from "antd";
import { HomeOutlined } from "@ant-design/icons";
import {
  MessageSquare,
  Send,
  Bot,
  User,
  Sparkles,
  Database,
  BarChart3,
  Settings,
  Zap,
  CheckCircle,
  Clock,
  Download,
  ArrowLeft,
} from "lucide-react";
import { useNavigate } from "react-router";
import DevelopmentInProgress from "@/components/DevelopmentInProgress";

interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp: Date;
  actions?: Array<{
    type:
      | "create_dataset"
      | "run_analysis"
      | "start_synthesis"
      | "export_report";
    label: string;
    data?: any;
  }>;
  status?: "pending" | "completed" | "error";
}

interface QuickAction {
  id: string;
  label: string;
  icon: any;
  prompt: string;
  category: string;
}

const quickActions: QuickAction[] = [
  {
    id: "create_dataset",
    label: "创建数据集",
    icon: Database,
    prompt: "帮我创建一个新的数据集",
    category: "数据管理",
  },
  {
    id: "analyze_quality",
    label: "质量分析",
    icon: BarChart3,
    prompt: "分析我的数据集质量",
    category: "数据评估",
  },
  {
    id: "start_synthesis",
    label: "数据合成",
    icon: Sparkles,
    prompt: "启动数据合成任务",
    category: "数据合成",
  },
  {
    id: "process_data",
    label: "数据处理",
    icon: Settings,
    prompt: "对数据集进行预处理",
    category: "数据处理",
  },
  {
    id: "export_report",
    label: "导出报告",
    icon: Download,
    prompt: "导出最新的分析报告",
    category: "报告导出",
  },
  {
    id: "check_status",
    label: "查看状态",
    icon: Clock,
    prompt: "查看所有任务的运行状态",
    category: "状态查询",
  },
];

const mockResponses = {
  创建数据集: {
    content:
      "我来帮您创建一个新的数据集。请告诉我以下信息：\n\n1. 数据集名称\n2. 数据类型（图像、文本、问答对等）\n3. 预期数据量\n4. 数据来源\n\n您也可以直接说出您的需求，我会为您推荐最适合的配置。",
    actions: [
      { type: "create_dataset", label: "开始创建", data: { step: "config" } },
    ],
  },
  质量分析: {
    content:
      "正在为您分析数据集质量...\n\n📊 **分析结果概览：**\n- 图像分类数据集：质量分 92/100\n- 问答对数据集：质量分 87/100\n- 多模态数据集：质量分 78/100\n\n🔍 **发现的主要问题：**\n- 23个重复图像\n- 156个格式不正确的问答对\n- 78个图文不匹配项\n\n💡 **改进建议：**\n- 建议进行去重处理\n- 优化问答对格式\n- 重新标注图文匹配项",
    actions: [
      {
        type: "run_analysis",
        label: "查看详细报告",
        data: { type: "detailed" },
      },
    ],
  },
  数据合成: {
    content:
      "我可以帮您启动数据合成任务。目前支持以下合成类型：\n\n🖼️ **图像数据合成**\n- 数据增强（旋转、翻转、亮度调整）\n- 风格迁移\n- GAN生成\n\n📝 **文本数据合成**\n- 同义词替换\n- 回译增强\n- GPT生成\n\n❓ **问答对合成**\n- 基于知识库生成\n- 模板变换\n- 多轮对话生成\n\n请告诉我您需要合成什么类型的数据，以及目标数量。",
    actions: [
      {
        type: "start_synthesis",
        label: "配置合成任务",
        data: { step: "config" },
      },
    ],
  },
  导出报告: {
    content:
      "正在为您准备最新的分析报告...\n\n📋 **可用报告：**\n- 数据质量评估报告（PDF）\n- 数据分布统计报告（Excel）\n- 模型性能评估报告（PDF）\n- 偏见检测报告（PDF）\n- 综合分析报告（PDF + Excel）\n\n✅ 报告已生成完成，您可以选择下载格式。",
    actions: [
      { type: "export_report", label: "下载报告", data: { format: "pdf" } },
    ],
  },
  查看状态: {
    content:
      "📊 **当前任务状态概览：**\n\n🟢 **运行中的任务：**\n- 问答对生成任务：65% 完成\n- 图像质量分析：运行中\n- 知识库构建：等待中\n\n✅ **已完成的任务：**\n- 图像分类数据集创建：已完成\n- PDF文档提取：已完成\n- 训练集配比任务：已完成\n\n⚠️ **需要关注的任务：**\n- 多模态数据合成：暂停（需要用户确认参数）\n\n所有任务运行正常，预计2小时内全部完成。",
    actions: [],
  },
};

export default function AgentPage() {
  return <DevelopmentInProgress />;
  const navigate = useNavigate();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      type: "assistant",
      content:
        "👋 您好！我是 Data Agent，您的AI数据助手。\n\n我可以帮您：\n• 创建和管理数据集\n• 分析数据质量\n• 启动处理任务\n• 生成分析报告\n• 回答数据相关问题\n\n请告诉我您需要什么帮助，或者点击下方的快捷操作开始。",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<any>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: content.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsTyping(true);

    // 模拟AI响应
    setTimeout(() => {
      const response = generateResponse(content);
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: response.content,
        timestamp: new Date(),
        actions: response.actions,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setIsTyping(false);
    }, 1500);
  };

  const generateResponse = (
    input: string
  ): { content: string; actions?: any[] } => {
    const lowerInput = input.toLowerCase();

    if (lowerInput.includes("创建") && lowerInput.includes("数据集")) {
      return mockResponses["创建数据集"];
    } else if (lowerInput.includes("质量") || lowerInput.includes("分析")) {
      return mockResponses["质量分析"];
    } else if (lowerInput.includes("合成") || lowerInput.includes("生成")) {
      return mockResponses["数据合成"];
    } else if (lowerInput.includes("导出") || lowerInput.includes("报告")) {
      return mockResponses["导出报告"];
    } else if (lowerInput.includes("状态") || lowerInput.includes("任务")) {
      return mockResponses["查看状态"];
    } else if (lowerInput.includes("你好") || lowerInput.includes("帮助")) {
      return {
        content:
          "很高兴为您服务！我是专门为数据集管理设计的AI助手。\n\n我的主要能力包括：\n\n🔧 **数据集操作**\n- 创建、导入、导出数据集\n- 数据预处理和清洗\n- 批量操作和自动化\n\n📊 **智能分析**\n- 数据质量评估\n- 分布统计分析\n- 性能和偏见检测\n\n🤖 **AI增强**\n- 智能数据合成\n- 自动标注建议\n- 知识库构建\n\n请告诉我您的具体需求，我会为您提供最合适的解决方案！",
      };
    } else {
      return {
        content: `我理解您想要「${input}」。让我为您分析一下...\n\n基于您的需求，我建议：\n\n1. 首先确认具体的操作目标\n2. 选择合适的数据集和参数\n3. 执行相应的处理流程\n\n您可以提供更多详细信息，或者选择下方的快捷操作来开始。如果需要帮助，请说"帮助"获取完整功能列表。`,
        actions: [
          { type: "run_analysis", label: "开始分析", data: { query: input } },
        ],
      };
    }
  };

  const handleQuickAction = (action: QuickAction) => {
    handleSendMessage(action.prompt);
  };

  const handleActionClick = (action: any) => {
    const actionMessage: Message = {
      id: Date.now().toString(),
      type: "assistant",
      content: `✅ 正在执行「${action.label}」...\n\n操作已启动，您可以在相应的功能模块中查看详细进度。`,
      timestamp: new Date(),
      status: "completed",
    };
    setMessages((prev) => [...prev, actionMessage]);
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(inputValue);
    }
  };

  const formatMessage = (content: string) => {
    return content.split("\n").map((line, index) => (
      <div key={index} className="mb-1">
        {line || <br />}
      </div>
    ));
  };

  const onBack = () => {
    navigate("/");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50">
      <div className="h-screen flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white p-6">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                  <MessageSquare className="w-6 h-6" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold">Data Agent</h1>
                  <p className="text-purple-100">
                    AI驱动的智能数据助手，通过对话完成复杂数据操作
                  </p>
                </div>
              </div>
              <Button
                type="default"
                icon={<ArrowLeft className="w-4 h-4 mr-2" />}
                onClick={onBack}
                className="bg-white/10 border-white/20 text-white hover:bg-white/20 hover:border-white/30"
              >
                返回首页
              </Button>
            </div>
          </div>
        </div>

        <div className="flex-1 max-w-7xl mx-auto h-full w-full p-6">
          <div className="h-full flex gap-6">
            {/* Chat Area */}
            <div className="lg:col-span-3 flex flex-1 flex-col h-full">
              <div className="flex-1 flex flex-col h-full shadow-lg">
                <div className="pb-3 bg-white rounded-t-lg">
                  <div className="flex items-center justify-between p-4">
                    <span className="text-lg font-semibold">对话窗口</span>
                    <div>
                      <span className="w-2 h-2 bg-green-500 rounded-full mr-1 inline-block" />
                      在线
                    </div>
                  </div>
                </div>
                <div className="flex-1 flex flex-col justify-between h-full p-0 min-h-0">
                  {/* Messages */}
                  <div className="flex-1 overflow-y-auto p-6 bg-white">
                    <div className="space-y-4 pb-4">
                      {messages.map((message) => (
                        <div
                          key={message.id}
                          className={`flex gap-3 ${
                            message.type === "user"
                              ? "justify-end"
                              : "justify-start"
                          }`}
                        >
                          {message.type === "assistant" && (
                            <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center flex-shrink-0">
                              <Bot className="w-4 h-4 text-white" />
                            </div>
                          )}
                          <div
                            className={`max-w-[80%] rounded-lg px-4 py-3 ${
                              message.type === "user"
                                ? "bg-blue-500 text-white"
                                : "bg-white text-gray-900 shadow-sm border border-gray-100"
                            }`}
                          >
                            <div className="text-sm whitespace-pre-wrap">
                              {formatMessage(message.content)}
                            </div>
                            {message.actions && message.actions.length > 0 && (
                              <div className="mt-3 space-y-2">
                                {message.actions.map((action, index) => (
                                  <Button
                                    key={index}
                                    type="default"
                                    size="small"
                                    className="mr-2 mb-2"
                                    onClick={() => handleActionClick(action)}
                                  >
                                    {action.label}
                                  </Button>
                                ))}
                              </div>
                            )}
                            <div className="text-xs opacity-70 mt-2">
                              {message.timestamp.toLocaleTimeString()}
                            </div>
                          </div>
                          {message.type === "user" && (
                            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                              <User className="w-4 h-4 text-white" />
                            </div>
                          )}
                        </div>
                      ))}
                      {isTyping && (
                        <div className="flex gap-3 justify-start">
                          <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center">
                            <Bot className="w-4 h-4 text-white" />
                          </div>
                          <div className="bg-white rounded-lg px-4 py-3 shadow-sm border border-gray-100">
                            <div className="flex items-center gap-1">
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                    <div ref={messagesEndRef} />
                  </div>

                  {/* Input Area */}
                  <div className="border-t border-gray-200 p-4 bg-white rounded-b-lg">
                    <div className="flex gap-2">
                      <Input
                        ref={inputRef}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyPress}
                        placeholder="输入您的需求，例如：创建一个图像分类数据集..."
                        disabled={isTyping}
                      />
                      <Button
                        type="primary"
                        onClick={() => handleSendMessage(inputValue)}
                        disabled={!inputValue.trim() || isTyping}
                        className="bg-gradient-to-r from-purple-400 to-pink-400 border-none hover:from-purple-500 hover:to-pink-500"
                      >
                        <Send className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions Sidebar */}
            <div className="w-72 flex flex-col gap-6">
              <Card className="shadow-lg">
                <div className="">
                  <span className="text-lg font-semibold">快捷操作</span>
                  <div className="text-sm text-gray-500">
                    点击快速开始常用操作
                  </div>
                </div>
                <div className="space-y-2 p-4">
                  {quickActions.map((action) => (
                    <Button
                      key={action.id}
                      type="default"
                      className="w-full justify-start h-auto p-3 text-left"
                      onClick={() => handleQuickAction(action)}
                    >
                      <action.icon className="w-4 h-4 mr-2 flex-shrink-0" />
                      <div className="text-left">
                        <div className="font-medium text-sm">
                          {action.label}
                        </div>
                      </div>
                    </Button>
                  ))}
                </div>
              </Card>

              <Card className="shadow-lg">
                <div className="pb-3">
                  <span className="text-lg font-semibold">系统状态</span>
                </div>
                <div className="space-y-3 p-4 pt-0">
                  <div className="flex items-center gap-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>AI服务正常</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <Clock className="w-4 h-4 text-blue-500" />
                    <span>3个任务运行中</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <Database className="w-4 h-4 text-purple-500" />
                    <span>12个数据集就绪</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <Zap className="w-4 h-4 text-orange-500" />
                    <span>响应时间: 0.8s</span>
                  </div>
                </div>
              </Card>

              <Card className="shadow-lg">
                <div className="pb-3">
                  <span className="text-lg font-semibold">使用提示</span>
                </div>
                <div className="space-y-2 text-sm text-gray-600 p-4 pt-0">
                  <div>💡 您可以用自然语言描述需求</div>
                  <div>🔍 支持复杂的多步骤操作</div>
                  <div>📊 可以询问数据统计和分析</div>
                  <div>⚡ 使用快捷操作提高效率</div>
                </div>
              </Card>

              <Card className="shadow-lg">
                <div className="pt-6 p-4">
                  <Button
                    type="default"
                    className="w-full"
                    icon={<HomeOutlined />}
                    onClick={onBack}
                  >
                    返回主应用
                  </Button>
                </div>
              </Card>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
