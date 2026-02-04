import React, { useState, useEffect } from 'react';
import { Button, Form, Input, Select, message, Modal, Row, Col, Table, Space } from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import { queryDatasetsUsingGet } from "@/pages/DataManagement/dataset.api.ts";
import { mapDataset } from "@/pages/DataManagement/dataset.const.tsx";
import { queryModelListUsingGet } from "@/pages/SettingsPage/settings.apis.ts";
import { ModelI } from "@/pages/SettingsPage/ModelAccess.tsx";
import { createEvaluationTaskUsingPost } from "@/pages/DataEvaluation/evaluation.api.ts";
import { queryPromptTemplatesUsingGet } from "@/pages/DataEvaluation/evaluation.api.ts";
import PreviewPromptModal from "@/pages/DataEvaluation/Create/PreviewPrompt.tsx";
import { getEvalMethods, getTaskTypes } from "@/pages/DataEvaluation/evaluation.const.tsx";
import { useTranslation } from "react-i18next";

interface Dataset {
  id: string;
  name: string;
  fileCount: number;
  size: string;
}

interface Dimension {
  key: string;
  dimension: string;
  description: string;
}

interface PromptTemplate {
  evalType: string;
  prompt: string;
  defaultDimensions: Dimension[];
}

interface CreateTaskModalProps {
  visible: boolean;
  onCancel: () => void;
  onSuccess: () => void;
}

const DEFAULT_EVAL_METHOD = 'AUTO';
const DEFAULT_TASK_TYPE = 'QA';

const CreateTaskModal: React.FC<CreateTaskModalProps> = ({ visible, onCancel, onSuccess }) => {
  const { t } = useTranslation();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [models, setModels] = useState<ModelI[]>([]);
  const [dimensions, setDimensions] = useState<Dimension[]>([]);
  const [newDimension, setNewDimension] = useState<Omit<Dimension, 'key'>>({
    dimension: '',
    description: ''
  });
  const [taskType, setTaskType] = useState<string>(DEFAULT_TASK_TYPE);
  const [promptTemplates, setPromptTemplates] = useState<PromptTemplate[]>([]);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [evaluationPrompt, setEvaluationPrompt] = useState('');

  const handleAddDimension = () => {
    if (!newDimension.dimension.trim()) {
      message.warning(t("dataEvaluation.create.messages.dimensionNameRequired"));
      return;
    }
    setDimensions([...dimensions, { ...newDimension, key: `dim-${Date.now()}` }]);
    setNewDimension({ dimension: '', description: '' });
  };

  const handleDeleteDimension = (key: string) => {
    if (dimensions.length <= 1) {
      message.warning(t("dataEvaluation.create.messages.keepAtLeastOneDimension"));
      return;
    }
    setDimensions(dimensions.filter(item => item.key !== key));
  };

  useEffect(() => {
    if (visible) {
      fetchDatasets().then();
      fetchModels().then();
      fetchPromptTemplates().then();
      // sync form with local taskType default
      form.setFieldsValue({ taskType: DEFAULT_TASK_TYPE });
    }
  }, [visible]);

  // when promptTemplates or taskType change, switch dimensions to template defaults (COT/QA)
  useEffect(() => {
    if (!promptTemplates || promptTemplates.length === 0) return;
    const template = promptTemplates.find(t => t.evalType === taskType);
    if (template && template.defaultDimensions) {
      setDimensions(template.defaultDimensions.map((dim: any, index: number) => ({
        key: `dim-${index}`,
        dimension: dim.dimension,
        description: dim.description
      })));
    }
  }, [taskType, promptTemplates]);

  const fetchDatasets = async () => {
    try {
      const { data } = await queryDatasetsUsingGet({ page: 1, size: 1000 });
      setDatasets(data.content.map(mapDataset) || []);
    } catch (error) {
      console.error('Error fetching datasets:', error);
      message.error(t("dataEvaluation.create.messages.fetchDatasetsFailed"));
    }
  };

  const fetchModels = async () => {
    try {
      const { data } = await queryModelListUsingGet({ page: 0, size: 1000 });
      setModels(data.content || []);
    } catch (error) {
      console.error('Error fetching models:', error);
      message.error(t("dataEvaluation.create.messages.fetchModelsFailed"));
    }
  };

  const formatDimensionsForPrompt = (dimensions: Dimension[]) => {
    let result = "";
    dimensions.forEach((dim, index) => {
      if (index > 0) {
        result += "\n";
      }
      result += `### ${index + 1}. ${dim.dimension}\n**评估标准：**\n${dim.description}`;
      if (index < dimensions.length - 1) {
        result += "\n";
      }
    });
    return result;
  };

  const formatResultExample = (dimensions: Dimension[]) => {
    let result = "";
    dimensions.forEach((dim, index) => {
      if (index > 0) {
        result += "\n    ";
      }
      result += `"${dim.dimension}": "Y"`;
      if (index < dimensions.length - 1) {
        result += ",";
      }
    });
    return result;
  };

  const fetchPromptTemplates = async () => {
    try {
      const response = await queryPromptTemplatesUsingGet();
      const templates: PromptTemplate[] = response.data?.templates || [];
      setPromptTemplates(templates);
      // if a template exists for current taskType, initialize dimensions (handled also by useEffect)
      const template = templates.find(t => t.evalType === taskType);
      if (template) {
        setDimensions(template.defaultDimensions.map((dim: any, index: number) => ({
          key: `dim-${index}`,
          dimension: dim.dimension,
          description: dim.description
        })));
      }
    } catch (error) {
      console.error('Error fetching prompt templates:', error);
      message.error(t("dataEvaluation.create.messages.fetchDimensionsFailed"));
    }
  };

  const generateEvaluationPrompt = () => {
    if (dimensions.length === 0) {
      message.warning(t("dataEvaluation.create.messages.addDimensionFirst"));
      return;
    }
    const template = promptTemplates.find(t => t.evalType === taskType);
    const basePrompt = template?.prompt || '';
    const filled = basePrompt
      .replace('{dimensions}', formatDimensionsForPrompt(dimensions))
      .replace('{result_example}', formatResultExample(dimensions));
    setEvaluationPrompt(filled);
    setPreviewVisible(true);
  };

  const chatModelOptions = models
    .filter((model) => model.type === "CHAT")
    .map((model) => ({
      label: `${model.modelName} (${model.provider})`,
      value: model.id,
    }));

  const handleSubmit = async (values: any) => {
    if (dimensions.length === 0) {
      message.warning(t("dataEvaluation.create.messages.addDimensionFirst"));
      return;
    }

    try {
      setLoading(true);
      const { datasetId, modelId, ...rest } = values;
      const selectedDataset = datasets.find(d => d.id === datasetId);
      const selectedModel = models.find(d => d.id === modelId);

      const payload = {
        ...rest,
        sourceType: 'DATASET',
        sourceId: datasetId,
        sourceName: selectedDataset?.name,
        evalConfig: {
          modelId: selectedModel?.id,
          dimensions: dimensions.map(d => ({
            dimension: d.dimension,
            description: d.description
          }))
        }
      };

      await createEvaluationTaskUsingPost(payload);
      message.success(t("dataEvaluation.create.messages.createSuccess"));
      onSuccess();
      form.resetFields();
      onCancel();
    } catch (error: any) {
      console.error('Error creating task:', error);
      message.error(error.response?.data?.message || t("dataEvaluation.create.messages.createFailed"));
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: t("dataEvaluation.create.form.dimension"),
      dataIndex: 'dimension',
      key: 'dimension',
      width: '30%',
    },
    {
      title: t("dataEvaluation.create.form.descriptionCol"),
      dataIndex: 'description',
      key: 'description',
      width: '60%',
    },
    {
      title: t("dataEvaluation.create.form.actions"),
      key: 'action',
      width: '10%',
      render: (_: any, record: any) => (
        <Space size="middle">
          <a
            onClick={() => handleDeleteDimension(record.key)}
            style={{ color: dimensions.length <= 1 ? '#ccc' : '#ff4d4f' }}
            className={dimensions.length <= 1 ? 'disabled-link' : ''}
          >
            {t("dataEvaluation.create.delete")}
          </a>
        </Space>
      ),
    },
  ];

  return (
    <Modal
      title={t("dataEvaluation.create.title")}
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={800}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          evalMethod: DEFAULT_EVAL_METHOD,
          taskType: DEFAULT_TASK_TYPE,
        }}
        onValuesChange={(changed) => {
          if (changed.taskType) {
            setTaskType(changed.taskType);
            setEvaluationPrompt('');
            setPreviewVisible(false);
          }
        }}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label={t("dataEvaluation.create.form.name")}
              name="name"
              rules={[{ required: true, message: t("dataEvaluation.create.messages.nameRequired") }]}
            >
              <Input placeholder={t("dataEvaluation.create.placeholders.name")} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label={t("dataEvaluation.create.form.taskType")}
              name="taskType"
              rules={[{ required: true, message: t("dataEvaluation.create.messages.taskTypeRequired") }]}
            >
              <Select options={getTaskTypes(t)} />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          label={t("dataEvaluation.create.form.description")}
          name="description"
        >
          <Input.TextArea placeholder={t("dataEvaluation.create.placeholders.description")} rows={3} />
        </Form.Item>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label={t("dataEvaluation.create.form.selectDataset")}
              name="datasetId"
              rules={[{ required: true, message: t("dataEvaluation.create.messages.datasetRequired") }]}
            >
              <Select
                placeholder={t("dataEvaluation.create.placeholders.dataset")}
                showSearch
                optionFilterProp="label"
              >
                {datasets.map((dataset) => (
                  <Select.Option key={dataset.id} value={dataset.id} label={dataset.name}>
                    <div className="flex justify-between w-full">
                      <span>{dataset.name}</span>
                      <span className="text-gray-500">{dataset.size}</span>
                    </div>
                  </Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label={t("dataEvaluation.create.form.evalMethod")}
              name="evalMethod"
              initialValue={DEFAULT_EVAL_METHOD}
            >
              <Select options={getEvalMethods(t)} />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          noStyle
          shouldUpdate={(prevValues, currentValues) =>
            prevValues.evalMethod !== currentValues.evalMethod
          }
        >
          {({ getFieldValue }) => getFieldValue('evalMethod') === 'AUTO' && (
            <>
              <Form.Item
                label={t("dataEvaluation.create.form.evalModel")}
                name="modelId"
                rules={[{ required: true, message: t("dataEvaluation.create.messages.modelRequired") }]}
              >
                <Select
                  placeholder={t("dataEvaluation.create.placeholders.model")}
                  options={chatModelOptions}
                  showSearch
                  optionFilterProp="label"
                />
              </Form.Item>

              <Form.Item label={t("dataEvaluation.create.form.dimensions")}>
                <Table
                  columns={columns}
                  dataSource={dimensions}
                  pagination={false}
                  size="small"
                  rowKey="key"
                />
                <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                  <Input
                    placeholder={t("dataEvaluation.create.placeholders.dimensionName")}
                    value={newDimension.dimension}
                    onChange={(e) => setNewDimension({...newDimension, dimension: e.target.value})}
                    style={{ flex: 1 }}
                  />
                  <Input
                    placeholder={t("dataEvaluation.create.placeholders.dimensionDesc")}
                    value={newDimension.description}
                    onChange={(e) => setNewDimension({...newDimension, description: e.target.value})}
                    style={{ flex: 2 }}
                  />
                  <Button
                    type="primary"
                    onClick={handleAddDimension}
                    disabled={!newDimension.dimension.trim()}
                  >
                    {t("dataEvaluation.create.addDimension")}
                  </Button>
                </div>
              </Form.Item>
            </>
          )}
        </Form.Item>
        <Form.Item>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px' }}>
            <Button
              type="link"
              icon={<EyeOutlined />}
              onClick={generateEvaluationPrompt}
            >
              {t("dataEvaluation.create.viewPrompt")}
            </Button>
          </div>
        </Form.Item>

        <Form.Item>
          <div style={{ textAlign: 'right' }}>
            <Button onClick={onCancel} style={{ marginRight: 8 }}>
              {t("dataEvaluation.create.cancel")}
            </Button>
            <Button type="primary" htmlType="submit" loading={loading}>
              {t("dataEvaluation.create.submit")}
            </Button>
          </div>
        </Form.Item>
      </Form>
      <PreviewPromptModal
        previewVisible={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        evaluationPrompt={evaluationPrompt}
      />
    </Modal>
  );
};

export default CreateTaskModal;
