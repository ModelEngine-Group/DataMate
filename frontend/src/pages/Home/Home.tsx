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
import { features, menuItems } from "../Layout/Menu.tsx";
import { useState } from 'react';
import { useNavigate } from "react-router";
import { Card, Dropdown, Button } from "antd";
import type { MenuProps } from 'antd';
import { Globe } from "lucide-react";
import { useTranslation } from "react-i18next";
import i18n from "@/i18n";

export default function WelcomePage() {
  const navigate = useNavigate();
  const [isChecking, setIsChecking] = useState(false);
  const { t } = useTranslation();

  const languageMenuItems: MenuProps['items'] = [
    {
      key: 'zh',
      label: t('header.simplifiedChinese'),
      onClick: () => {
        i18n.changeLanguage('zh');
        localStorage.setItem('language', 'zh');
      },
    },
    {
      key: 'en',
      label: t('header.english'),
      onClick: () => {
        i18n.changeLanguage('en');
        localStorage.setItem('language', 'en');
      },
    }
  ];

  // 检查接口连通性的函数
  const checkDeerFlowDeploy = async (): Promise<boolean> => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      
      const response = await fetch('/deer-flow-backend/config', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: controller.signal,
        cache: 'no-store'
      });
      
      clearTimeout(timeoutId);

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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 relative">
      <Dropdown
        menu={{ items: languageMenuItems }}
        placement="bottomRight"
      >
        <Button type="text" className="flex items-center gap-2 absolute top-4 right-4 z-50 bg-white/80 hover:bg-white">
          <Globe className="h-4 w-4" />
          <span>{i18n.language === 'zh' ? t('header.simplifiedChinese') : t('header.english')}</span>
        </Button>
      </Dropdown>

      <div className="max-w-7xl mx-auto px-4 py-12">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-800 px-4 py-2 rounded-full text-sm font-medium mb-6">
            <Sparkles className="w-4 h-4" />
            {t('home.hero.subtitle')}
          </div>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            DataMate
            <span className="text-blue-600"> {t('home.hero.title')}</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
            {t('home.hero.description')}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <span
              onClick={() => navigate("/data/management")}
              className="cursor-pointer rounded px-4 py-2 inline-flex items-center bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-lg"
            >
              <Database className="mr-2 w-4 h-4" />
              {t('home.hero.getStartedButton')}
            </span>
            <span
              onClick={handleChatClick}
              className="cursor-pointer rounded px-4 py-2 inline-flex items-center bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <MessageSquare className="mr-2 w-4 h-4" />
                      {isChecking ? t('home.hero.checkingButton') : t('home.hero.chatAssistantButton')}
            </span>
            <span
              onClick={() => navigate("/orchestration")}
              className="cursor-pointer rounded px-4 py-2 inline-flex items-center bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-700 hover:to-amber-700 text-white shadow-lg"
            >
              {t('home.hero.dataOrchestrationButton')}
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
                <div className="text-lg">{t(feature.titleKey || 'home.features.title' + index)}</div>
              </div>
              <div className="text-center">
                <p className="text-gray-600 text-sm">{t(feature.descriptionKey || 'home.features.description' + index)}</p>
              </div>
            </Card>
          ))}
        </div>

        {/* Menu Items Grid */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            {t('home.sections.featuresTitle')}
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
                    {t(item.i18Key)}
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-sm group-hover:text-gray-700 transition-colors">
                    {t(item.descriptionKey)}
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
                  {t('home.orchestrationHighlight.title')}
                </h3>
                <p className="text-orange-700">
                  {t('home.orchestrationHighlight.description')}
                </p>
              </div>

              <div className="grid md:grid-cols-2 gap-8 mb-6">
                <div className="space-y-3">
                  <h4 className="font-semibold text-orange-900">
                    {t('home.orchestrationHighlight.coreFeaturesTitle')}
                  </h4>
                  <div className="space-y-2">
                    <div className="bg-white/60 rounded-lg p-3 text-sm text-orange-800">
                      {t('home.orchestrationHighlight.feature1')}
                    </div>
                    <div className="bg-white/60 rounded-lg p-3 text-sm text-orange-800">
                      {t('home.orchestrationHighlight.feature2')}
                    </div>
                    <div className="bg-white/60 rounded-lg p-3 text-sm text-orange-800">
                      {t('home.orchestrationHighlight.feature3')}
                    </div>
                  </div>
                </div>
                <div className="space-y-3">
                  <h4 className="font-semibold text-orange-900">
                    {t('home.orchestrationHighlight.smartFeaturesTitle')}
                  </h4>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm text-orange-800">
                      <Zap className="w-4 h-4 text-orange-500" />
                      {t('home.orchestrationHighlight.smartFeature1')}
                    </div>
                    <div className="flex items-center gap-2 text-sm text-orange-800">
                      <Target className="w-4 h-4 text-orange-500" />
                      {t('home.orchestrationHighlight.smartFeature2')}
                    </div>
                    <div className="flex items-center gap-2 text-sm text-orange-800">
                      <Sparkles className="w-4 h-4 text-orange-500" />
                      {t('home.orchestrationHighlight.smartFeature3')}
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
                  {t('home.orchestrationHighlight.startButton')}
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
                  {t('home.dataAgentHighlight.title')}
                </h3>
                <p className="text-purple-700">
                  {t('home.dataAgentHighlight.description')}
                </p>
              </div>

              <div className="grid md:grid-cols-2 gap-8 mb-6">
                <div className="space-y-3">
                  <h4 className="font-semibold text-purple-900">
                    {t('home.dataAgentHighlight.examplesTitle')}
                  </h4>
                  <div className="space-y-2">
                    <div className="bg-white/60 rounded-lg p-3 text-sm text-purple-800">
                      "{t('home.dataAgentHighlight.example1')}"
                    </div>
                    <div className="bg-white/60 rounded-lg p-3 text-sm text-purple-800">
                      "{t('home.dataAgentHighlight.example2')}"
                    </div>
                    <div className="bg-white/60 rounded-lg p-3 text-sm text-purple-800">
                      "{t('home.dataAgentHighlight.example3')}"
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
                      {t('home.dataAgentHighlight.smartFeature1')}
                    </div>
                    <div className="flex items-center gap-2 text-sm text-purple-800">
                      <Target className="w-4 h-4 text-purple-500" />
                      {t('home.dataAgentHighlight.smartFeature2')}
                    </div>
                    <div className="flex items-center gap-2 text-sm text-purple-800">
                      <Sparkles className="w-4 h-4 text-purple-500" />
                      {t('home.dataAgentHighlight.smartFeature3')}
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
                        {isChecking ? t('home.hero.checkingButton') : t('home.dataAgentHighlight.startButton')}
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
                  {t('home.workflowShowcase.title')}
                </h3>
                <p className="text-blue-700">
                  {t('home.workflowShowcase.description')}
                </p>
              </div>

              <div className="grid md:grid-cols-4 gap-6 mb-8">
                <div className="text-center">
                  <div className="w-16 h-16 bg-blue-500 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <FolderOpen className="w-8 h-8 text-white" />
                  </div>
                  <h4 className="font-semibold text-blue-900 mb-2">{t('home.workflowShowcase.step1Title')}</h4>
                  <p className="text-sm text-blue-700">
                    {t('home.workflowShowcase.step1Description')}
                  </p>
                </div>
                <div className="text-center">
                  <div className="w-16 h-16 bg-orange-500 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <GitBranch className="w-8 h-8 text-white" />
                  </div>
                  <h4 className="font-semibold text-blue-900 mb-2">{t('home.workflowShowcase.step2Title')}</h4>
                  <p className="text-sm text-blue-700">
                    {t('home.workflowShowcase.step2Description')}
                  </p>
                </div>
                <div className="text-center">
                  <div className="w-16 h-16 bg-purple-500 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <Settings className="w-8 h-8 text-white" />
                  </div>
                  <h4 className="font-semibold text-blue-900 mb-2">{t('home.workflowShowcase.step3Title')}</h4>
                  <p className="text-sm text-blue-700">
                    {t('home.workflowShowcase.step3Description')}
                  </p>
                </div>
                <div className="text-center">
                  <div className="w-16 h-16 bg-green-500 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <Target className="w-8 h-8 text-white" />
                  </div>
                  <h4 className="font-semibold text-blue-900 mb-2">{t('home.workflowShowcase.step4Title')}</h4>
                  <p className="text-sm text-blue-700">
                    {t('home.workflowShowcase.step4Description')}
                  </p>
                </div>
              </div>

              <div className="text-center">
                <span
                  onClick={() => navigate("/data/management")}
                  className="cursor-pointer rounded px-4 py-2 inline-flex items-center bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white shadow-lg"
                >
                  <Sparkles className="mr-2 w-4 h-4" />
                  {t('home.workflowShowcase.startButton')}
                </span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
