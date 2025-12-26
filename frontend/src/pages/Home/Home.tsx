import {
  FolderOpen,
  Settings,
  ArrowRight,
  Sparkles,
  Target,
  Zap,
  Database,
  MessageSquare,
  GitBranch,
} from "lucide-react";
import { features, menuItems } from "../Layout/menu";
import { useState } from 'react';
import { useNavigate } from "react-router";
import { Card } from "antd";

export default function WelcomePage() {
  const navigate = useNavigate();
  const [isChecking, setIsChecking] = useState(false);

  // 检查接口连通性的函数
  const checkDeerFlowDeploy = async (): Promise<boolean> => {
    try {
      const response = await fetch('/deer-flow-backend/config', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 5000, // 5秒超时
        cache: 'no-store'
      });

      // 检查 HTTP 状态码在 200-299 范围内
      if (response.ok) {
        return true;
      }
    } catch (error) {
      console.error('接口检查失败:', error);
    }
    return false;
  };

  const handleChatClick = async () => {
    if (isChecking) return; // 防止重复点击

    setIsChecking(true);

    try {
      const isDeerFlowDeploy = await checkDeerFlowDeploy();

      if (isDeerFlowDeploy) {
        // 接口正常，执行原有逻辑
        window.location.href = "/chat";
      } else {
        // 接口异常，使用 navigate 跳转
        navigate("/chat");
      }
    } catch (error) {
      // 发生错误时也使用 navigate 跳转
      console.error('检查过程中发生错误:', error);
      navigate("/chat");
    } finally {
      setIsChecking(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto px-4 py-12">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-medium mb-6">
            <Sparkles className="w-4 h-4" />
            AI数据集准备工具
          </div>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            构建高质量
            <span className="text-blue-600"> AI数据集</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
            从数据管理到知识生成，一站式解决企业AI数据处理的场景问题。
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <span
              onClick={() => navigate("/data/management")}
              className="cursor-pointer rounded px-4 py-2 inline-flex items-center bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-lg"
            >
              <Database className="mr-2 w-4 h-4" />
              开始使用
            </span>
            <span
              onClick={handleChatClick}
              className="cursor-pointer rounded px-4 py-2 inline-flex items-center bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <MessageSquare className="mr-2 w-4 h-4" />
                      {isChecking ? '检查中...' : '对话助手'}
            </span>
            <span
              onClick={() => navigate("/orchestration")}
              className="cursor-pointer rounded px-4 py-2 inline-flex items-center bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-700 hover:to-amber-700 text-white shadow-lg"
            >
              数据智能编排
              <ArrowRight className="ml-2 w-4 h-4" />
            </span>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-6 mb-16">
          {features.map((feature, index) => (
            <Card
              key={index}
              className="border-0 shadow-lg hover:shadow-xl transition-shadow"
            >
              <div className="text-center pb-4">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <feature.icon className="w-6 h-6 text-blue-600" />
                </div>
                <div className="text-lg">{feature.title}</div>
              </div>
              <div className="text-center">
                <p className="text-gray-600 text-sm">{feature.description}</p>
              </div>
            </Card>
          ))}
        </div>

        {/* Menu Items Grid */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            功能模块
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {menuItems.map((item) => (
              <Card
                key={item.id}
                onClick={() => navigate(item.children ? `/data/${item.children[0].id}`: `/data/${item.id}`)}
                className="cursor-pointer hover:shadow-lg transition-all duration-200 border-0 shadow-md relative overflow-hidden group"
              >
                <div className="text-center relative">
                  <div
                    className={`w-16 h-16 ${item.color} rounded-xl flex items-center justify-center mx-auto mb-4 shadow-lg group-hover:scale-110 transition-transform duration-200`}
                  >
                    <item.icon className="w-8 h-8 text-white" />
                  </div>
                  <div className="flex items-center justify-center gap-2 mb-2"></div>
                  <div className="text-xl group-hover:text-blue-600 transition-colors">
                    {item.title}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-sm group-hover:text-gray-700 transition-colors">
                    {item.description}
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Data Orchestration Highlight */}
        <div className="mb-16">
          <Card className="bg-gradient-to-br from-orange-50 to-amber-50 border-orange-200 shadow-lg">
            <div className="p-8">
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-gradient-to-br from-orange-500 to-amber-500 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <GitBranch className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-orange-900 mb-2">
                  数据智能编排 - 可视化流程设计
                </h3>
                <p className="text-orange-700">
                  拖拽式设计复杂数据清洗管道，让数据流转更加直观高效
                </p>
              </div>

              <div className="grid md:grid-cols-2 gap-8 mb-6">
                <div className="space-y-3">
                  <h4 className="font-semibold text-orange-900">
                    🎯 核心功能：
                  </h4>
                  <div className="space-y-2">
                    <div className="bg-white/60 rounded-lg p-3 text-sm text-orange-800">
                      可视化流程设计器
                    </div>
                    <div className="bg-white/60 rounded-lg p-3 text-sm text-orange-800">
                      丰富的数据清洗组件库
                    </div>
                    <div className="bg-white/60 rounded-lg p-3 text-sm text-orange-800">
                      实时流程执行监控
                    </div>
                  </div>
                </div>
                <div className="space-y-3">
                  <h4 className="font-semibold text-orange-900">
                    ⚡ 智能特性：
                  </h4>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm text-orange-800">
                      <Zap className="w-4 h-4 text-orange-500" />
                      自动优化数据流转路径
                    </div>
                    <div className="flex items-center gap-2 text-sm text-orange-800">
                      <Target className="w-4 h-4 text-orange-500" />
                      智能错误检测和修复建议
                    </div>
                    <div className="flex items-center gap-2 text-sm text-orange-800">
                      <Sparkles className="w-4 h-4 text-orange-500" />
                      模板化流程快速复用
                    </div>
                  </div>
                </div>
              </div>

              <div className="text-center">
                <span
                  onClick={() => navigate("/orchestration")}
                  className="cursor-pointer rounded px-4 py-2 inline-flex items-center bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-700 hover:to-amber-700 text-white shadow-lg"
                >
                  <GitBranch className="mr-2 w-4 h-4" />
                  开始编排
                </span>
              </div>
            </div>
          </Card>
        </div>

        {/* Data Agent Highlight */}
        <div className="mb-16">
          <Card className="bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200 shadow-lg">
            <div className="p-8">
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <MessageSquare className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-2xl font-bold text-purple-900 mb-2">
                  Data Agent - 对话式业务操作
                </h3>
                <p className="text-purple-700">
                  告别复杂界面，用自然语言完成所有数据集相关业务
                </p>
              </div>

              <div className="grid md:grid-cols-2 gap-8 mb-6">
                <div className="space-y-3">
                  <h4 className="font-semibold text-purple-900">
                    💬 对话示例：
                  </h4>
                  <div className="space-y-2">
                    <div className="bg-white/60 rounded-lg p-3 text-sm text-purple-800">
                      "帮我创建一个图像分类数据集"
                    </div>
                    <div className="bg-white/60 rounded-lg p-3 text-sm text-purple-800">
                      "分析一下数据质量，生成报告"
                    </div>
                    <div className="bg-white/60 rounded-lg p-3 text-sm text-purple-800">
                      "启动合成任务，目标1000条数据"
                    </div>
                  </div>
                </div>
                <div className="space-y-3">
                  <h4 className="font-semibold text-purple-900">
                    🚀 智能特性：
                  </h4>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm text-purple-800">
                      <Zap className="w-4 h-4 text-purple-500" />
                      理解复杂需求，自动执行
                    </div>
                    <div className="flex items-center gap-2 text-sm text-purple-800">
                      <Target className="w-4 h-4 text-purple-500" />
                      提供专业建议和优化方案
                    </div>
                    <div className="flex items-center gap-2 text-sm text-purple-800">
                      <Sparkles className="w-4 h-4 text-purple-500" />
                      学习使用习惯，个性化服务
                    </div>
                  </div>
                </div>
              </div>

              <div className="text-center">
                <span
                    onClick={handleChatClick}
                    className="cursor-pointer rounded px-4 py-2 inline-flex items-center bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white shadow-lg"
                >
                  <MessageSquare className="mr-2 w-4 h-4" />
                        {isChecking ? '检查中...' : '开始对话'}
                </span>
              </div>
            </div>
          </Card>
        </div>

        {/* Workflow Showcase */}
        <div className="mb-16">
          <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200 shadow-lg">
            <div className="p-8">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-blue-900 mb-2">
                  完整的数据清洗工作流
                </h3>
                <p className="text-blue-700">
                  从原始数据到高质量数据集的全流程解决方案
                </p>
              </div>

              <div className="grid md:grid-cols-4 gap-6 mb-8">
                <div className="text-center">
                  <div className="w-16 h-16 bg-blue-500 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <FolderOpen className="w-8 h-8 text-white" />
                  </div>
                  <h4 className="font-semibold text-blue-900 mb-2">数据收集</h4>
                  <p className="text-sm text-blue-700">
                    支持多种数据源导入，包括本地文件、数据库、API等
                  </p>
                </div>
                <div className="text-center">
                  <div className="w-16 h-16 bg-orange-500 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <GitBranch className="w-8 h-8 text-white" />
                  </div>
                  <h4 className="font-semibold text-blue-900 mb-2">智能编排</h4>
                  <p className="text-sm text-blue-700">
                    可视化设计数据清洗流程，自动化执行复杂任务
                  </p>
                </div>
                <div className="text-center">
                  <div className="w-16 h-16 bg-purple-500 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <Settings className="w-8 h-8 text-white" />
                  </div>
                  <h4 className="font-semibold text-blue-900 mb-2">智能处理</h4>
                  <p className="text-sm text-blue-700">
                    自动化的数据清洗、标注和质量评估流程
                  </p>
                </div>
                <div className="text-center">
                  <div className="w-16 h-16 bg-green-500 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <Target className="w-8 h-8 text-white" />
                  </div>
                  <h4 className="font-semibold text-blue-900 mb-2">质量保证</h4>
                  <p className="text-sm text-blue-700">
                    全面的质量评估和偏见检测，确保数据集可靠性
                  </p>
                </div>
              </div>

              <div className="text-center">
                <span
                  onClick={() => navigate("/data/management")}
                  className="cursor-pointer rounded px-4 py-2 inline-flex items-center bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white shadow-lg"
                >
                  <Sparkles className="mr-2 w-4 h-4" />
                  开始构建数据集
                </span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
