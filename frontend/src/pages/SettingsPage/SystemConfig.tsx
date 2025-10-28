import { Card, Divider, Input, Select, Switch, Button, Form, App } from "antd";
import { useState } from "react";

export default function SystemConfig() {
  const { message } = App.useApp();
  // System Settings State
  const [systemConfig, setSystemConfig] = useState({
    siteName: "DataMate",
    maxFileSize: "100",
    autoBackup: true,
    logLevel: "info",
    sessionTimeout: "30",
    enableNotifications: true,
  });

  const logLevelOptions = [
    { value: "debug", label: "Debug" },
    { value: "info", label: "Info" },
    { value: "warn", label: "Warning" },
    { value: "error", label: "Error" },
  ];

  const handleSaveSystemSettings = () => {
    // Save system settings logic
    console.log("Saving system settings:", systemConfig);
    message.success("系统设置已保存");
  };

  return (
    <Card>
      <Form
        onValuesChange={(changedValues) => {
          setSystemConfig((prevConfig) => ({
            ...prevConfig,
            ...changedValues,
          }));
        }}
        layout="vertical"
      >
        <div className="grid grid-cols-2 gap-6">
          <Form.Item name="siteName" label="站点名称">
            <Input />
          </Form.Item>
          <Form.Item name="maxFileSize" label="最大文件大小 (MB)">
            <Input type="number" />
          </Form.Item>
          <Form.Item name="logLevel" label="日志级别">
            <Select options={logLevelOptions}></Select>
          </Form.Item>
          <Form.Item name="sessionTimeout" label="会话超时 (分钟)">
            <Input type="number" />
          </Form.Item>
        </div>
        <Divider />
        <div className="space-y-4">
          <h4 className="font-medium">功能开关</h4>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <span>自动备份</span>
                <p className="text-sm text-gray-500">定期自动备份系统数据</p>
              </div>
              <Form.Item name="autoBackup" valuePropName="checked">
                <Switch />
              </Form.Item>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <span>启用通知</span>
                <p className="text-sm text-gray-500">接收系统通知和提醒</p>
              </div>
              <Form.Item name="enableNotifications" valuePropName="checked">
                <Switch />
              </Form.Item>
            </div>
          </div>
        </div>
        <div className="flex justify-end mt-6">
          <Button type="primary" onClick={handleSaveSystemSettings}>
            保存设置
          </Button>
        </div>
      </Form>
    </Card>
  );
}
