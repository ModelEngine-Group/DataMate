import { useState } from "react";
import { Button, Menu } from "antd";
import { SettingOutlined, ApiOutlined } from "@ant-design/icons";
import { Component, X } from "lucide-react";
import { useNavigate } from "react-router";
import SystemConfig from "./SystemConfig";
import ModelAccess from "./ModelAccess";
import WebhookConfig from "./WebhookConfig";

export default function SettingsPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("model-access");

  return (
    <div className="h-screen flex">
      <div className="border-right h-full">
        {/* <h1 className="min-w-[200px] w-full border-bottom flex gap-2 text-lg font-bold text-gray-900 p-4">
          <Button icon={<X />} type="text" onClick={() => navigate(-1)} />
          设置中心
        </h1> */}
        <div className="h-full">
          <Menu
            mode="inline"
            items={[
              {
                key: "model-access",
                icon: <Component className="w-4 h-4" />,
                label: "模型接入",
              },
              {
                key: "system-config",
                icon: <SettingOutlined />,
                label: "参数配置",
              },
              {
                key: "webhook-config",
                icon: <ApiOutlined />,
                label: "Webhook",
                disabled: true,
                title: "暂未开放"
              },
            ]}
            selectedKeys={[activeTab]}
            onClick={({ key }) => {
              setActiveTab(key);
            }}
          />
        </div>
      </div>
      <div className="flex-1 h-full p-4">
        {/* 内容区域，根据 activeTab 渲染不同的组件 */}
        {activeTab === "system-config" && <SystemConfig />}
        {activeTab === "model-access" && <ModelAccess />}
        {activeTab === "webhook-config" && <WebhookConfig />}
      </div>
    </div>
  );
}
