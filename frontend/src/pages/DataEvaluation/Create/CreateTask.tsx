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

const TASK_TYPES = [
  { label: 'QA评估', value: 'QA' },
];

const EVAL_METHODS = [
  { label: '模型自动评估', value: 'AUTO' },
];

const DEFAULT_EVAL_METHOD = 'AUTO';
const DEFAULT_TASK_TYPE = 'QA';

const CreateTaskModal: React.FC<CreateTaskModalProps> = ({ visible, onCancel, onSuccess }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [models, setModels] = useState<ModelI[]>([]);
  const [dimensions, setDimensions] = useState<Dimension[]>([]);
  const [newDimension, setNewDimension] = useState<Omit<Dimension, 'key'>>({
    dimension: '',
    description: ''
  });
  const [taskType, setTaskType] = useState<string>("QA");
  const [promptTemplates, setPromptTemplates] = useState<PromptTemplate[]>([]);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [evaluationPrompt, setEvaluationPrompt] = useState('');

  const handleAddDimension = () => {
    if (!newDimension.dimension.trim()) {
      message.warning('请输入维度名称');
      return;
    }
    setDimensions([...dimensions, { ...newDimension, key: `dim-${Date.now()}` }]);
    setNewDimension({ dimension: '', description: '' });
  };

  const handleDeleteDimension = (key: string) => {
    if (dimensions.length <= 1) {
      message.warning('至少需要保留一个评估维度');
      return;
    }
    setDimensions(dimensions.filter(item => item.key !== key));
  };

  useEffect(() => {
    if (visible) {
      fetchDatasets().then();
      fetchModels().then();
      fetchPromptTemplates().then();
    }
  }, [visible]);

  const fetchDatasets = async () => {
    try {
      const { data } = await queryDatasetsUsingGet({ page: 1, size: 1000 });
      setDatasets(data.content.map(mapDataset) || []);
    } catch (error) {
      console.error('Error fetching datasets:', error);
      message.error('获取数据集列表失败');
    }
  };

  const fetchModels = async () => {
    try {
      const { data } = await queryModelListUsingGet({ page: 0, size: 1000 });
      setModels(data.content || []);
    } catch (error) {
      console.error('Error fetching models:', error);
      message.error('获取模型列表失败');
    }
  };

  const formatDimensionsForPrompt = (dimensions: Dimension[]) => {
    let result = "\n";
    dimensions.forEach((dim, index) => {
      result += `### ${index + 1}. ${dim.dimension}\n**评估标准：**\n${dim.description}\n\n`;
    });
    return result;
  };

  const formatResultExample = (dimensions: Dimension[]) => {
    return dimensions.map(dim => `\n    "${dim.dimension}": "Y",`).join('');
  };

  const fetchPromptTemplates = async () => {
    try {
      const response = await queryPromptTemplatesUsingGet();
      const templates: PromptTemplate[] = response.data?.templates
      setPromptTemplates(templates)
      if (taskType) {
        const template = templates.find(t => t.evalType === taskType);
        if (template) {
          setDimensions(template.defaultDimensions.map((dim: any, index: number) => ({
            key: `dim-${index}`,
            dimension: dim.dimension,
            description: dim.description
          })));
        }
      }
    } catch (error) {
      console.error('Error fetching prompt templates:', error);
      message.error('获取评估维度失败');
    }
  };

  const generateEvaluationPrompt = () => {
    if (dimensions.length === 0) {
      message.warning('请先添加评估维度');
      return;
    }
    const template = promptTemplates.find(t => t.evalType === taskType);
    setEvaluationPrompt(template?.prompt.replace("{dimensions}", formatDimensionsForPrompt(dimensions))
      .replace('{result_example}', formatResultExample(dimensions)));
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
      message.warning('请至少添加一个评估维度');
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
      message.success('评估任务创建成功');
      onSuccess();
      form.resetFields();
      onCancel();
    } catch (error: any) {
      console.error('Error creating task:', error);
      message.error(error.response?.data?.message || '创建评估任务失败');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: '维度',
      dataIndex: 'dimension',
      key: 'dimension',
      width: '30%',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      width: '60%',
    },
    {
      title: '操作',
      key: 'action',
      width: '10%',
      render: (_: any, record: any) => (
        <Space size="middle">
          <a
            onClick={() => handleDeleteDimension(record.key)}
            style={{ color: dimensions.length <= 1 ? '#ccc' : '#ff4d4f' }}
            className={dimensions.length <= 1 ? 'disabled-link' : ''}
          >
            删除
          </a>
        </Space>
      ),
    },
  ];

  return (
    <Modal
      title="创建评估任务"
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
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="任务名称"
              name="name"
              rules={[{ required: true, message: '请输入任务名称' }]}
            >
              <Input placeholder="输入任务名称" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              label="任务类型"
              name="taskType"
              rules={[{ required: true, message: '请选择任务类型' }]}
            >
              <Select options={TASK_TYPES} />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          label="任务描述"
          name="description"
        >
          <Input.TextArea placeholder="输入任务描述（可选）" rows={3} />
        </Form.Item>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              label="选择数据集"
              name="datasetId"
              rules={[{ required: true, message: '请选择数据集' }]}
            >
              <Select
                placeholder="请选择要评估的数据集"
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
              label="评估方式"
              name="evalMethod"
              initialValue={DEFAULT_EVAL_METHOD}
            >
              <Select options={EVAL_METHODS} />
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
                label="评估模型"
                name="modelId"
                rules={[{ required: true, message: '请选择评估模型' }]}
              >
                <Select
                  placeholder="请选择模型"
                  options={chatModelOptions}
                  showSearch
                  optionFilterProp="label"
                />
              </Form.Item>

              <Form.Item label="评估维度">
                <Table
                  columns={columns}
                  dataSource={dimensions}
                  pagination={false}
                  size="small"
                  rowKey="key"
                />
                <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                  <Input
                    placeholder="输入维度名称"
                    value={newDimension.dimension}
                    onChange={(e) => setNewDimension({...newDimension, dimension: e.target.value})}
                    style={{ flex: 1 }}
                  />
                  <Input
                    placeholder="输入维度描述"
                    value={newDimension.description}
                    onChange={(e) => setNewDimension({...newDimension, description: e.target.value})}
                    style={{ flex: 2 }}
                  />
                  <Button
                    type="primary"
                    onClick={handleAddDimension}
                    disabled={!newDimension.dimension.trim()}
                  >
                    添加维度
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
              查看评估提示词
            </Button>
          </div>
        </Form.Item>

        <Form.Item>
          <div style={{ textAlign: 'right' }}>
            <Button onClick={onCancel} style={{ marginRight: 8 }}>
              取消
            </Button>
            <Button type="primary" htmlType="submit" loading={loading}>
              创建任务
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
