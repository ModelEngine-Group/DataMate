import {
  Card,
  Button,
  Form,
  Input,
  Modal,
  Select,
  Table,
  Tooltip,
  Popconfirm,
  message,
} from "antd";
import {
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import { useEffect, useState } from "react";
import { SearchControls } from "@/components/SearchControls";
import useFetchData from "@/hooks/useFetchData";
import {
  createModelUsingPost,
  deleteModelByIdUsingDelete,
  queryModelListUsingGet,
  queryModelProvidersUsingGet,
  updateModelByIdUsingPut,
} from "./settings.apis";

interface ModelI {
  id: string;
  name: string;
  provider: string;
  model: string;
  apiKey: string;
  isEnabled: boolean;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  updatedBy: string;
}

interface ProviderI {
  id: string;
  modelName: string;
  value: string;
  label: string;
  baseUrl: string;
  provider: string;
  apiKey: string;
  type: string;
  isEnabled: boolean;
}

export default function EnvironmentAccess() {
  const [form] = Form.useForm();
  const [showModelDialog, setShowModelDialog] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [newModel, setNewModel] = useState({
    name: "",
    provider: "openai",
    model: "",
    apiKey: "",
    endpoint: "",
  });
  const [typeOptions] = useState([
    { value: "CHAT", label: "CHAT" },
    { value: "EMBEDDING", label: "EMBEDDING" },
  ]);

  const {
    loading,
    tableData,
    pagination,
    searchParams,
    setSearchParams,
    fetchData,
    handleFiltersChange,
  } = useFetchData(queryModelListUsingGet);

  const handleAddModel = async () => {
    try {
      const formValues = await form.validateFields();
      const fn = isEditMode
        ? () => updateModelByIdUsingPut(newModel.id, formValues)
        : () => createModelUsingPost(formValues);
      await fn();
      setShowModelDialog(false);
      fetchData();
      message.success("模型添加成功");
    } catch (error) {
      message.error(`${error?.data?.message}：${error?.data?.data}`);
    }
  };
  const [providerOptions, setProviderOptions] = useState<ProviderI[]>([]);

  const fetchProviderOptions = async () => {
    const { data } = await queryModelProvidersUsingGet();
    setProviderOptions(
      data.map((provider: ProviderI) => ({
        ...provider,
        value: provider.provider,
        label: provider.provider,
      }))
    );
  };

  const generateApiKey = () => {
    const chars =
      "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    let result = "sk-";
    for (let i = 0; i < 48; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  };

  const handleDeleteModel = async (modelId: string) => {
    await deleteModelByIdUsingDelete(modelId);
    fetchData();
  };

  useEffect(() => {
    fetchProviderOptions();
  }, []);

  const columns = [
    {
      title: "模型名称",
      dataIndex: "modelName",
      key: "modelName",
      fixed: "left",
      width: 200,
      ellipsis: true,
    },
    {
      title: "创建时间",
      dataIndex: "createdAt",
      key: "createdAt",
      ellipsis: true,
    },
    {
      title: "模型提供商",
      dataIndex: "provider",
      key: "provider",
      ellipsis: true,
    },
    {
      title: "模型类型",
      dataIndex: "type",
      key: "type",
      ellipsis: true,
    },
    {
      title: "更新时间",
      dataIndex: "updatedAt",
      key: "updatedAt",
      ellipsis: true,
    },
    {
      title: "操作",
      key: "action",
      fixed: "right" as const,
      ellipsis: true,
      render: (_: any, record: ModelI) => {
        return [
          {
            key: "edit",
            label: "编辑",
            icon: <EditOutlined />,
            onClick: () => {
              setIsEditMode(true);
              setNewModel(record);
              form.setFieldsValue(record);
              setShowModelDialog(true);
            },
          },
          {
            key: "delete",
            label: "删除",
            danger: true,
            icon: <DeleteOutlined />,
            confirm: {
              title: "确定要删除该任务吗？此操作不可撤销。",
              okText: "删除",
              cancelText: "取消",
              okType: "danger",
            },
            onClick: () => handleDeleteModel(record.id),
          },
        ].map((op) => {
          const button = (
            <Tooltip key={op.key} title={op.label}>
              <Button
                type="text"
                icon={op.icon}
                danger={op?.danger}
                onClick={() => op.onClick(record)}
              />
            </Tooltip>
          );
          if (op.confirm) {
            return (
              <Popconfirm
                key={op.key}
                title={op.confirm.title}
                okText={op.confirm.okText}
                cancelText={op.confirm.cancelText}
                okType={op.danger ? "danger" : "primary"}
                onConfirm={() => op.onClick(record)}
              >
                <Tooltip key={op.key} title={op.label}>
                  <Button type="text" icon={op.icon} danger={op?.danger} />
                </Tooltip>
              </Popconfirm>
            );
          }
          return button;
        });
      },
    },
  ];

  return (
    <>
      <div className="flex items-top justify-between">
        <h2 className="text-lg font-medium mb-4">模型接入</h2>
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
      <SearchControls
        searchTerm={searchParams.keyword}
        onSearchChange={(newSearchTerm) =>
          setSearchParams((prev) => ({
            ...prev,
            keyword: newSearchTerm,
            current: 1,
          }))
        }
        searchPlaceholder="搜索模型描述..."
        filters={[
          {
            key: "provider",
            label: "模型提供商",
            options: [{ value: "all", label: "全部" }, ...providerOptions],
          },
          {
            key: "type",
            label: "模型类型",
            options: [{ value: "all", label: "全部" }, ...typeOptions],
          },
        ]}
        onFiltersChange={handleFiltersChange}
        showViewToggle={false}
        onReload={fetchData}
        onClearFilters={() =>
          setSearchParams((prev) => ({
            ...prev,
            filters: {},
          }))
        }
        className="mb-4"
      />
      <Card>
        <Table
          rowKey="id"
          columns={columns}
          dataSource={tableData}
          loading={loading}
          pagination={pagination}
          scroll={{ x: "max-content", y: "calc(100vh - 26rem)" }}
        />
      </Card>
      <Modal
        open={showModelDialog}
        onCancel={() => setShowModelDialog(false)}
        title={isEditMode ? "编辑模型" : "添加模型"}
        footer={[
          <Button key="cancel" onClick={() => setShowModelDialog(false)}>
            取消
          </Button>,
          <Button key="ok" type="primary" onClick={handleAddModel}>
            确定
          </Button>,
        ]}
      >
        <Form
          form={form}
          onValuesChange={(changedValues) => {
            setNewModel({ ...newModel, ...changedValues });
          }}
          layout="vertical"
        >
          <Form.Item
            name="provider"
            label="服务提供商"
            required
            rules={[{ required: true, message: "请选择服务提供商" }]}
          >
            <Select
              placeholder="选择服务提供商"
              options={providerOptions}
              onChange={(value) => {
                const selectedProvider = providerOptions.find(
                  (p) => p.value === value
                );
                form.setFieldsValue({ baseUrl: selectedProvider?.baseUrl });
              }}
            ></Select>
          </Form.Item>
          <Form.Item
            name="baseUrl"
            label="接口地址"
            required
            rules={[
              { required: true, message: "请输入接口地址" },
              {
                pattern: /^https?:\/\/.+/,
                message: "请输入有效的URL地址，必须以http://或https://开头",
              },
            ]}
          >
            <Input placeholder="输入接口地址，如：https://api.openai.com" />
          </Form.Item>
          <Form.Item
            name="modelName"
            label="模型名称"
            required
            tooltip="请输入模型名称"
            rules={[{ required: true, message: "请输入模型名称" }]}
          >
            <Input placeholder="输入模型名称" />
          </Form.Item>
          <Form.Item
            name="apiKey"
            label="API密钥"
            required
            rules={[{ required: true, message: "请输入API密钥" }]}
          >
            <Input
              placeholder="输入或生成API密钥"
              addonAfter={
                <ReloadOutlined
                  onClick={() => {
                    form.setFieldsValue({ apiKey: generateApiKey() });
                    setNewModel({ ...newModel, apiKey: generateApiKey() });
                  }}
                />
              }
            />
          </Form.Item>
          <Form.Item
            name="type"
            label="模型类型"
            required
            rules={[{ required: true, message: "请选择模型类型" }]}
          >
            <Select options={typeOptions} placeholder="选择模型类型"></Select>
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
