import {
  mockKnowledgeBases,
  sliceOperators,
  vectorDatabases,
} from "@/mock/knowledgeBase";
import { useState } from "react";
import {
  Button,
  Card,
  Input,
  Select,
  Checkbox,
  Switch,
  Tabs,
  Divider,
  Upload,
  message,
  Form,
} from "antd";
import {
  BookOpen,
  Database,
  Brain,
  Scissors,
  Split,
  Upload as UploadIcon,
  Folder,
  CheckCircle,
  File,
  ArrowLeft,
} from "lucide-react";
import { useNavigate } from "react-router";
import type { Dataset } from "@/pages/DataManagement/dataset.model";
import DevelopmentInProgress from "@/components/DevelopmentInProgress";

const { TextArea } = Input;
const { Option } = Select;

const KnowledgeBaseCreatePage: React.FC = () => {
  return <DevelopmentInProgress showTime="2025.10.30" />;
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [knowledgeBases, setKnowledgeBases] =
    useState<KnowledgeBase[]>(mockKnowledgeBases);
  const [datasetSearchQuery, setDatasetSearchQuery] = useState("");
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(
    null
  );
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetFiles, setSelectedDatasetFiles] = useState<
    {
      datasetId: string;
      fileId: string;
      name: string;
      size: string;
      type: string;
    }[]
  >([]);
  const [selectedSliceOperators, setSelectedSliceOperators] = useState<
    string[]
  >(["semantic-split", "paragraph-split"]);

  // Form initial values
  const initialValues = {
    name: "",
    description: "",
    type: "unstructured" as "unstructured" | "structured",
    embeddingModel: "text-embedding-3-large",
    llmModel: "gpt-4o",
    chunkSize: 512,
    overlap: 50,
    sliceMethod: "semantic" as
      | "paragraph"
      | "length"
      | "delimiter"
      | "semantic",
    delimiter: "",
    enableQA: true,
    vectorDatabase: "pinecone",
  };

  // Dataset file selection helpers
  const handleDatasetFileToggle = (
    datasetId: string,
    file: MockDataset["files"][0]
  ) => {
    setSelectedDatasetFiles((prev) => {
      const isSelected = prev.some(
        (f) => f.datasetId === datasetId && f.fileId === file.id
      );
      if (isSelected) {
        return prev.filter(
          (f) => !(f.datasetId === datasetId && f.fileId === file.id)
        );
      } else {
        return [...prev, { datasetId, ...file }];
      }
    });
  };

  const handleSelectAllDatasetFiles = (
    dataset: MockDataset,
    checked: boolean
  ) => {
    setSelectedDatasetFiles((prev) => {
      let newSelectedFiles = [...prev];
      if (checked) {
        dataset.files.forEach((file) => {
          if (
            !newSelectedFiles.some(
              (f) => f.datasetId === dataset.id && f.fileId === file.id
            )
          ) {
            newSelectedFiles.push({ datasetId: dataset.id, ...file });
          }
        });
      } else {
        newSelectedFiles = newSelectedFiles.filter(
          (f) => f.datasetId !== dataset.id
        );
      }
      return newSelectedFiles;
    });
  };

  const isDatasetFileSelected = (datasetId: string, fileId: string) => {
    return selectedDatasetFiles.some(
      (f) => f.datasetId === datasetId && f.fileId === fileId
    );
  };

  const isAllDatasetFilesSelected = (dataset: MockDataset) => {
    return dataset.files.every((file) =>
      isDatasetFileSelected(dataset.id, file.id)
    );
  };

  const handleSliceOperatorToggle = (operatorId: string) => {
    setSelectedSliceOperators((prev) =>
      prev.includes(operatorId)
        ? prev.filter((id) => id !== operatorId)
        : [...prev, operatorId]
    );
  };

  // 文件上传
  const handleFileChange = (info: any) => {
    setUploadedFiles(info.fileList.map((f: any) => f.originFileObj));
  };

  // 提交表单
  const handleFinish = (values: any) => {
    const newKB: KnowledgeBase = {
      id: Date.now(),
      name: values.name,
      description: values.description,
      type: values.type,
      status: "importing",
      fileCount: uploadedFiles.length + selectedDatasetFiles.length,
      chunkCount: 0,
      vectorCount: 0,
      size: "0 MB",
      progress: 0,
      createdAt: new Date().toISOString().split("T")[0],
      lastUpdated: new Date().toISOString().split("T")[0],
      vectorDatabase: values.vectorDatabase,
      config: {
        embeddingModel: values.embeddingModel,
        llmModel: values.llmModel,
        chunkSize: values.chunkSize,
        overlap: values.overlap,
        sliceMethod: values.sliceMethod,
        delimiter: values.delimiter,
        enableQA: values.enableQA,
        vectorDimension: values.embeddingModel.includes("3-large")
          ? 3072
          : 1536,
        sliceOperators: selectedSliceOperators,
      },
      files: [
        ...uploadedFiles.map((file) => ({
          id: Date.now() + Math.random(),
          name: file.name,
          type: file.type.split("/")[1] || "unknown",
          size: `${(file.size / (1024 * 1024)).toFixed(2)} MB`,
          status: "processing" as const,
          chunkCount: 0,
          progress: 0,
          uploadedAt: new Date().toISOString().split("T")[0],
          source: "upload" as const,
          vectorizationStatus: "pending" as const,
        })),
        ...selectedDatasetFiles.map((file) => ({
          id: Date.now() + Math.random(),
          name: file.name,
          type: file.type,
          size: file.size,
          status: "processing" as const,
          chunkCount: 0,
          progress: 0,
          uploadedAt: new Date().toISOString().split("T")[0],
          source: "dataset" as const,
          datasetId: file.datasetId,
          vectorizationStatus: "pending" as const,
        })),
      ],
      vectorizationHistory: [],
    };

    setKnowledgeBases([newKB, ...knowledgeBases]);
    form.resetFields();
    setUploadedFiles([]);
    setSelectedDatasetFiles([]);
    setSelectedSliceOperators(["semantic-split", "paragraph-split"]);
    setSelectedDatasetId(null);
    message.success("知识库创建成功！");
    navigate("/data/knowledge-generation");
  };

  return (
    <div className="min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center">
          <Button
            type="text"
            onClick={() => navigate("/data/knowledge-generation")}
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
          </Button>
          <h1 className="text-xl font-bold bg-clip-text">创建知识库</h1>
        </div>
      </div>

      <Card className="overflow-y-auto p-2">
        <Form
          form={form}
          layout="vertical"
          initialValues={initialValues}
          onFinish={handleFinish}
        >
          {/* 基本信息 */}
          <h2 className="font-medium text-gray-900 text-lg mb-2">基本信息</h2>
          <Form.Item
            label="知识库名称"
            name="name"
            rules={[{ required: true, message: "请输入知识库名称" }]}
          >
            <Input placeholder="输入知识库名称" />
          </Form.Item>
          <Form.Item label="描述" name="description">
            <TextArea placeholder="描述知识库的用途和内容" rows={3} />
          </Form.Item>
          <Form.Item label="知识库类型" name="type">
            <div className="grid grid-cols-2 gap-4">
              <Button
                onClick={() => form.setFieldValue("type", "unstructured")}
                type={
                  form.getFieldValue("type") === "unstructured"
                    ? "primary"
                    : "default"
                }
                className="h-auto py-4 flex flex-col items-center gap-2"
              >
                <BookOpen className="w-6 h-6" />
                <p className="font-medium">非结构化知识库</p>
                <p className="text-xs text-center opacity-80">
                  支持文档、PDF等文件
                </p>
              </Button>
              <Button
                onClick={() => form.setFieldValue("type", "structured")}
                type={
                  form.getFieldValue("type") === "structured"
                    ? "primary"
                    : "default"
                }
                className="h-auto py-4 flex flex-col items-center gap-2"
              >
                <Database className="w-6 h-6" />
                <p className="font-medium">结构化知识库</p>
                <p className="text-xs text-center opacity-80">
                  支持问答对、表格数据
                </p>
              </Button>
            </div>
          </Form.Item>

          <Divider />

          {/* 模型配置 */}
          <h2 className="font-medium text-gray-900 text-lg mb-2 flex items-center gap-2">
            <Brain className="w-5 h-5" />
            模型配置
          </h2>
          <Form.Item label="嵌入模型" name="embeddingModel">
            <Select>
              <Option value="text-embedding-3-large">
                text-embedding-3-large (推荐)
              </Option>
              <Option value="text-embedding-3-small">
                text-embedding-3-small
              </Option>
              <Option value="text-embedding-ada-002">
                text-embedding-ada-002
              </Option>
            </Select>
          </Form.Item>
          <Form.Item
            shouldUpdate={(prev, curr) =>
              prev.type !== curr.type || prev.enableQA !== curr.enableQA
            }
            noStyle
          >
            {() =>
              form.getFieldValue("type") === "unstructured" &&
              form.getFieldValue("enableQA") && (
                <Form.Item label="LLM模型 (用于Q&A生成)" name="llmModel">
                  <Select>
                    <Option value="gpt-4o">GPT-4o (推荐)</Option>
                    <Option value="gpt-4o-mini">GPT-4o Mini</Option>
                    <Option value="gpt-3.5-turbo">GPT-3.5 Turbo</Option>
                  </Select>
                </Form.Item>
              )
            }
          </Form.Item>
          <Form.Item label="向量数据库" name="vectorDatabase">
            <Select>
              {vectorDatabases.map((db) => (
                <Option key={db.id} value={db.id}>
                  <div className="flex flex-col">
                    <span className="font-medium">{db.name}</span>
                    <span className="text-xs text-gray-500">
                      {db.description}
                    </span>
                  </div>
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Divider />

          {/* 切片算子配置 */}
          <Form.Item
            shouldUpdate={(prev, curr) => prev.type !== curr.type}
            noStyle
          >
            {() =>
              form.getFieldValue("type") === "unstructured" && (
                <>
                  <h2 className="font-medium text-gray-900 text-lg mb-2 flex items-center gap-2">
                    <Scissors className="w-5 h-5" />
                    切片算子配置
                  </h2>
                  <div className="grid grid-cols-2 gap-3 mb-4">
                    {sliceOperators.map((operator) => (
                      <div
                        key={operator.id}
                        className={`border rounded-lg p-3 cursor-pointer transition-all ${
                          selectedSliceOperators.includes(operator.id)
                            ? "border-blue-500 bg-blue-50"
                            : "border-gray-200 hover:border-gray-300"
                        }`}
                        onClick={() => handleSliceOperatorToggle(operator.id)}
                      >
                        <div className="flex items-start gap-3">
                          <Checkbox
                            checked={selectedSliceOperators.includes(
                              operator.id
                            )}
                            onChange={() =>
                              handleSliceOperatorToggle(operator.id)
                            }
                          />
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-lg">{operator.icon}</span>
                              <span className="font-medium text-sm">
                                {operator.name}
                              </span>
                              <span className="ant-badge text-xs">
                                {operator.type}
                              </span>
                            </div>
                            <p className="text-xs text-gray-600">
                              {operator.description}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  <Divider />

                  {/* 文档分割配置 */}
                  <h2 className="font-medium text-gray-900 text-lg mb-2 flex items-center gap-2">
                    <Split className="w-5 h-5" />
                    文档分割配置
                  </h2>
                  <Form.Item label="分割方式" name="sliceMethod">
                    <Select>
                      <Option value="semantic">语义分割 (推荐)</Option>
                      <Option value="paragraph">段落分割</Option>
                      <Option value="length">长度分割</Option>
                      <Option value="delimiter">分隔符分割</Option>
                    </Select>
                  </Form.Item>
                  <Form.Item
                    noStyle
                    shouldUpdate={(prev, curr) =>
                      prev.sliceMethod !== curr.sliceMethod
                    }
                  >
                    {() =>
                      form.getFieldValue("sliceMethod") === "delimiter" && (
                        <Form.Item
                          label="分隔符"
                          name="delimiter"
                          rules={[
                            {
                              required: true,
                              message: "请输入分隔符",
                            },
                          ]}
                        >
                          <Input placeholder="输入分隔符，如 \\n\\n" />
                        </Form.Item>
                      )
                    }
                  </Form.Item>
                  <div className="grid grid-cols-2 gap-3">
                    <Form.Item
                      label="分块大小"
                      name="chunkSize"
                      rules={[
                        {
                          required: true,
                          message: "请输入分块大小",
                        },
                      ]}
                    >
                      <Input type="number" />
                    </Form.Item>
                    <Form.Item
                      label="重叠长度"
                      name="overlap"
                      rules={[
                        {
                          required: true,
                          message: "请输入重叠长度",
                        },
                      ]}
                    >
                      <Input type="number" />
                    </Form.Item>
                  </div>
                  <Form.Item
                    label="启用Q&A生成"
                    name="enableQA"
                    valuePropName="checked"
                  >
                    <Switch />
                  </Form.Item>
                  <Divider />
                </>
              )
            }
          </Form.Item>

          {/* 数据源选择 */}
          <h2 className="font-medium text-gray-900 text-lg mb-2 flex items-center gap-2">
            <UploadIcon className="w-5 h-5" />
            {form.getFieldValue("type") === "structured"
              ? "导入模板文件"
              : "选择数据源"}
          </h2>
          <Tabs
            defaultActiveKey="upload"
            items={[
              {
                key: "upload",
                label: "上传文件",
                children: (
                  <div className="space-y-3">
                    <Upload
                      multiple
                      beforeUpload={() => false}
                      onChange={handleFileChange}
                      fileList={uploadedFiles.map((file, idx) => ({
                        uid: String(idx),
                        name: file.name,
                        status: "done",
                        originFileObj: file,
                      }))}
                      showUploadList={false}
                    >
                      <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center relative cursor-pointer">
                        <UploadIcon className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                        <p className="text-sm text-gray-600">
                          {form.getFieldValue("type") === "structured"
                            ? "拖拽或点击上传Excel/CSV模板文件"
                            : "拖拽或点击上传文档文件"}
                        </p>
                        <Button
                          className="mt-2 bg-transparent pointer-events-none"
                          disabled
                        >
                          选择文件
                        </Button>
                      </div>
                    </Upload>
                    {uploadedFiles.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-sm font-medium">已选择文件:</p>
                        <ul className="list-disc pl-5 text-sm text-gray-700">
                          {uploadedFiles.map((file, index) => (
                            <li key={index}>{file.name}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ),
              },
              {
                key: "dataset",
                label: "从数据集选择",
                children: (
                  <div className="space-y-3">
                    <div className="flex gap-2 mb-4">
                      <Input
                        placeholder="搜索数据集..."
                        value={datasetSearchQuery}
                        onChange={(e) => setDatasetSearchQuery(e.target.value)}
                        className="flex-1"
                      />
                      <Button onClick={() => setSelectedDatasetId(null)}>
                        重置选择
                      </Button>
                    </div>
                    <div className="grid grid-cols-3 gap-4 h-80">
                      <div className="col-span-1 border rounded-lg overflow-y-auto p-2 space-y-2">
                        {datasets.length === 0 && (
                          <p className="text-center text-gray-500 py-4 text-sm">
                            无匹配数据集
                          </p>
                        )}
                        {datasets.map((dataset) => (
                          <div
                            key={dataset.id}
                            className={`flex items-center justify-between p-3 border rounded-lg cursor-pointer ${
                              selectedDatasetId === dataset.id
                                ? "bg-blue-50 border-blue-500"
                                : "hover:bg-gray-50"
                            }`}
                            onClick={() => setSelectedDatasetId(dataset.id)}
                          >
                            <div className="flex items-center gap-3">
                              <Folder className="w-5 h-5 text-blue-400" />
                              <div>
                                <p className="font-medium">{dataset.name}</p>
                                <p className="text-xs text-gray-500">
                                  {dataset.files.length} 个文件
                                </p>
                              </div>
                            </div>
                            {selectedDatasetId === dataset.id && (
                              <CheckCircle className="w-5 h-5 text-blue-600" />
                            )}
                          </div>
                        ))}
                      </div>
                      <div className="col-span-2 border rounded-lg overflow-y-auto p-2 space-y-2">
                        {!selectedDatasetId ? (
                          <div className="text-center py-8 text-gray-500">
                            <Folder className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                            <p className="text-sm">请选择一个数据集</p>
                          </div>
                        ) : (
                          <>
                            <div className="flex items-center gap-2 p-2 border-b pb-2">
                              <Checkbox
                                checked={isAllDatasetFilesSelected(
                                  datasets.find(
                                    (d) => d.id === selectedDatasetId
                                  )!
                                )}
                                onChange={(e) =>
                                  handleSelectAllDatasetFiles(
                                    datasets.find(
                                      (d) => d.id === selectedDatasetId
                                    )!,
                                    e.target.checked
                                  )
                                }
                              />
                              <span className="font-medium">
                                全选 (
                                {
                                  datasets.find(
                                    (d) => d.id === selectedDatasetId
                                  )?.files.length
                                }{" "}
                                个文件)
                              </span>
                            </div>
                            {datasets
                              .find((d) => d.id === selectedDatasetId)
                              ?.files.map((file) => (
                                <div
                                  key={file.id}
                                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                                >
                                  <div className="flex items-center gap-3">
                                    <Checkbox
                                      checked={isDatasetFileSelected(
                                        selectedDatasetId!,
                                        file.id
                                      )}
                                      onChange={() =>
                                        handleDatasetFileToggle(
                                          selectedDatasetId!,
                                          file
                                        )
                                      }
                                    />
                                    <File className="w-5 h-5 text-gray-400" />
                                    <div>
                                      <p className="font-medium">{file.name}</p>
                                      <p className="text-sm text-gray-500">
                                        {file.size} • {file.type}
                                      </p>
                                    </div>
                                  </div>
                                </div>
                              ))}
                          </>
                        )}
                      </div>
                    </div>
                    {selectedDatasetFiles.length > 0 && (
                      <div className="mt-4 text-sm font-medium text-gray-700">
                        已选择数据集文件总数: {selectedDatasetFiles.length}
                      </div>
                    )}
                  </div>
                ),
              },
            ]}
          />

          <Divider />
          <div className="flex gap-2 justify-end">
            <Button onClick={() => navigate("/data/knowledge-generation")}>
              取消
            </Button>
            <Button type="primary" htmlType="submit">
              创建知识库
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  );
};

export default KnowledgeBaseCreatePage;
