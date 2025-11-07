import { Divider, Input, Select, Switch, Button, Form, App, Table } from "antd";
import { PlusOutlined } from "@ant-design/icons";
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
  const configData = [
    {
      key: "1",
      parameter: "站点名称",
      value: systemConfig.siteName,
      description: "系统的显示名称",
    },
    {
      key: "2",
      parameter: "最大文件大小 (MB)",
      value: systemConfig.maxFileSize,
      description: "允许上传的最大文件大小",
    },
    {
      key: "3",
      parameter: "自动备份",
      value: systemConfig.autoBackup ? "启用" : "禁用",
      description: "定期自动备份系统数据",
    },
    {
      key: "4",
      parameter: "日志级别",
      value: systemConfig.logLevel,
      description: "系统日志的详细程度",
    },
    {
      key: "5",
      parameter: "会话超时 (分钟)",
      value: systemConfig.sessionTimeout,
      description: "用户会话的超时时间",
    },
  ];

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

  const columns = [
    {
      title: "参数",
      dataIndex: "parameter",
      key: "parameter",
    },
    {
      title: "值",
      dataIndex: "value",
      key: "value",
    },
    {
      title: "描述",
      dataIndex: "description",
      key: "description",
    },
    {
      title: "是否启用",
      dataIndex: "enabled",
      key: "enabled",
      render: (_: any, record: any) => (
        <Switch
          checked={
            record.key === "3"
              ? systemConfig.autoBackup
              : record.key === "5"
              ? systemConfig.enableNotifications
              : false
          }
          onChange={(checked) => {
            if (record.key === "3") {
              setSystemConfig((prevConfig) => ({
                ...prevConfig,
                autoBackup: checked,
              }));
            } else if (record.key === "5") {
              setSystemConfig((prevConfig) => ({
                ...prevConfig,
                enableNotifications: checked,
              }));
            }
          }}
        />
      ),
    }
  ];

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-top justify-between">
        <h2 className="text-lg font-medium mb-4">参数配置</h2>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setIsEditMode(false);
            form.resetFields();
            setNewModel({
              name: "",
              provider: "",
              model: "",
              apiKey: "",
              endpoint: "",
            });
            setShowModelDialog(true);
          }}
        >
          添加模型
        </Button>
      </div>
      <div className="flex-1 border-card overflow-auto p-6">
        <Table columns={columns} data={configData} />
        <Form
          onValuesChange={(changedValues) => {
            setSystemConfig((prevConfig) => ({
              ...prevConfig,
              ...changedValues,
            }));
          }}
          layout="vertical"
        >
          <div className="grid grid-cols-2 gap-6 mt-6">
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
      </div>
    </div>
  );
}
