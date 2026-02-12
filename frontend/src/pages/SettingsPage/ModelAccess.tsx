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
  message, Switch,
} from "antd";
import {
  EditOutlined,
  DeleteOutlined,
  ReloadOutlined,
  PlusOutlined,
} from "@ant-design/icons";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { SearchControls } from "@/components/SearchControls";
import useFetchData from "@/hooks/useFetchData";
import {
  createModelUsingPost,
  deleteModelByIdUsingDelete,
  queryModelListUsingGet,
  queryModelProvidersUsingGet,
  updateModelByIdUsingPut,
} from "./settings.apis";

export interface ModelI {
  id: string;
  modelName: string;
  provider: string;
  model: string;
  baseUrl: string;
  apiKey: string;
  type: string;
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

export default function ModelAccess() {
  const { t } = useTranslation();
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
      message.success(t('settings.modelAccess.messages.addSuccess'));
    } catch (error) {
      message.error(t('settings.modelAccess.messages.error', { 
        message: error?.data?.message, 
        detail: error?.data?.data 
      }));
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
      title: t('settings.modelAccess.columns.modelName'),
      dataIndex: "modelName",
      key: "modelName",
      fixed: "left",
      width: 200,
      ellipsis: true,
    },
    {
      title: t('settings.modelAccess.columns.createdAt'),
      dataIndex: "createdAt",
      key: "createdAt",
      ellipsis: true,
    },
    {
      title: t('settings.modelAccess.columns.provider'),
      dataIndex: "provider",
      key: "provider",
      ellipsis: true,
    },
    {
      title: t('settings.modelAccess.columns.type'),
      dataIndex: "type",
      key: "type",
      ellipsis: true,
    },
    {
      title: t('settings.modelAccess.columns.updatedAt'),
      dataIndex: "updatedAt",
      key: "updatedAt",
      ellipsis: true,
    },
    {
      title: t('common.actions.actions'), // Reuse existing key for "Actions"
      key: "action",
      fixed: "right" as const,
      ellipsis: true,
      render: (_: any, record: ModelI) => {
        return [
          {
            key: "edit",
            label: t('dataManagement.actions.edit'), // Reuse existing key for "Edit"
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
            label: t('dataManagement.actions.delete'), // Reuse existing key for "Delete"
            danger: true,
            icon: <DeleteOutlined />,
            confirm: {
              title: t('dataCollection.taskManagement.messages.deleteConfirm'), // Reuse existing delete confirm
              okText: t('dataCollection.taskManagement.messages.confirmDelete'), // Reuse existing confirm delete
              cancelText: t('dataCollection.taskManagement.messages.cancel'), // Reuse existing cancel
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
        <h2 className="text-lg font-medium mb-4">{t('settings.modelAccess.title')}</h2>
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
          {t('settings.modelAccess.addModel')}
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
        searchPlaceholder={t('settings.modelAccess.searchPlaceholder')}
        filters={[
          {
            key: "provider",
            label: t('settings.modelAccess.filters.provider'),
            options: [{ value: "all", label: t('settings.modelAccess.filters.all') }, ...providerOptions],
          },
          {
            key: "type",
            label: t('settings.modelAccess.filters.type'),
            options: [{ value: "all", label: t('settings.modelAccess.filters.all') }, ...typeOptions],
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
      <div className="flex flex-col h-[calc(100vh-12rem)]">
        <Card className="flex-1 overflow-auto">
          <Table
            rowKey="id"
            columns={columns}
            dataSource={tableData}
            loading={loading}
            pagination={pagination}
            scroll={false}
          />
        </Card>
      </div>
      <Modal
        open={showModelDialog}
        onCancel={() => setShowModelDialog(false)}
        title={isEditMode ? t('settings.modelAccess.modal.titleEdit') : t('settings.modelAccess.modal.titleAdd')}
        footer={[
          <Button key="cancel" onClick={() => setShowModelDialog(false)}>
            {t('dataManagement.actions.cancel')}
          </Button>,
          <Button key="ok" type="primary" onClick={handleAddModel}>
            {t('dataManagement.actions.confirm')}
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
            label={t('settings.modelAccess.modal.form.provider')}
            required
            rules={[{ required: true, message: t('settings.modelAccess.modal.form.providerRequired') }]}
          >
            <Select
              placeholder={t('settings.modelAccess.modal.form.providerPlaceholder')}
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
            label={t('settings.modelAccess.modal.form.baseUrl')}
            required
            rules={[
              { required: true, message: t('settings.modelAccess.modal.form.baseUrlRequired') },
              {
                pattern: /^https?:\/\/.+/,
                message: t('settings.modelAccess.modal.form.baseUrlInvalid'),
              },
            ]}
          >
            <Input placeholder={t('settings.modelAccess.modal.form.baseUrlPlaceholder')} />
          </Form.Item>
          <Form.Item
            name="modelName"
            label={t('settings.modelAccess.modal.form.modelName')}
            required
            tooltip={t('settings.modelAccess.modal.form.modelNameTooltip')}
            rules={[{ required: true, message: t('settings.modelAccess.modal.form.modelNameRequired') }]}
          >
            <Input placeholder={t('settings.modelAccess.modal.form.modelNamePlaceholder')} />
          </Form.Item>
          <Form.Item
            name="apiKey"
            label={t('settings.modelAccess.modal.form.apiKey')}
            required
            rules={[{ required: true, message: t('settings.modelAccess.modal.form.apiKeyRequired') }]}
          >
            <Input
              placeholder={t('settings.modelAccess.modal.form.apiKeyPlaceholder')}
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
            label={t('settings.modelAccess.modal.form.type')}
            required
            rules={[{ required: true, message: t('settings.modelAccess.modal.form.typeRequired') }]}
          >
            <Select options={typeOptions} placeholder={t('settings.modelAccess.modal.form.typePlaceholder')}></Select>
          </Form.Item>
          <Form.Item
            name="isDefault"
            label={t('settings.modelAccess.modal.form.isDefault')}
            required
            tooltip={t('settings.modelAccess.modal.form.isDefaultTooltip')}
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
