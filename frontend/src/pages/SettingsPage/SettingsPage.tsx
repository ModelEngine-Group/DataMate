import { useState } from "react";
import { Tabs } from "antd";
import { SettingOutlined, ApiOutlined } from "@ant-design/icons";
import WebhookConfig from "./WebhookConfig";
import ModelAccess from "./ModelAccess";
import SystemConfig from "./SystemConfig";
import { Component } from "lucide-react";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("modelAccess");

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">系统设置</h1>
        </div>
      </div>

      {/* Settings Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          // {
          //   key: "system",
          //   label: (
          //     <span>
          //       <SettingOutlined className="mr-1" />
          //       系统设置
          //     </span>
          //   ),
          //   children: <SystemConfig />,
          // },
          {
            key: "modelAccess",
            label: (
              <span className="flex items-center">
                <Component className="w-4 h-4 mr-1" />
                模型接入
              </span>
            ),
            children: <ModelAccess key="modelAccess" />,
          },
          // {
          //   key: "webhook",
          //   label: (
          //     <span>
          //       <ApiOutlined className="mr-1" />
          //       Webhook
          //     </span>
          //   ),
          //   children: <WebhookConfig />,
          // },
        ]}
      />
    </div>
  );
}
