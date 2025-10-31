import { useEffect, useState } from "react";
import {
  Button,
  App,
  Input,
  Select,
  Form,
  Modal,
  UploadFile,
  Radio,
  Tree,
} from "antd";
import { InboxOutlined, PlusOutlined } from "@ant-design/icons";
import { KnowledgeBaseItem } from "../knowledge-base.model";
import Dragger from "antd/es/upload/Dragger";
import {
  queryDatasetFilesUsingGet,
  queryDatasetsUsingGet,
} from "@/pages/DataManagement/dataset.api";
import { datasetTypeMap } from "@/pages/DataManagement/dataset.const";
import { addKnowledgeBaseFilesUsingPost } from "../knowledge-base.api";
import { DatasetType } from "@/pages/DataManagement/dataset.model";

const dataSourceOptions = [
  { label: "本地上传", value: "local" },
  { label: "数据集", value: "dataset" },
];

const sliceOptions = [
  { label: "章节分块", value: "CHAPTER_CHUNK" },
  { label: "段落分块", value: "PARAGRAPH_CHUNK" },
  { label: "长度分块", value: "LENGTH_CHUNK" },
  { label: "自定义分割符分块", value: "CUSTOM_SEPARATOR_CHUNK" },
  { label: "默认分块", value: "DEFAULT_CHUNK" },
];

const columns = [
  {
    dataIndex: "name",
    title: "名称",
    ellipsis: true,
  },
  {
    dataIndex: "datasetType",
    title: "类型",
    ellipsis: true,
    render: (type) => datasetTypeMap[type].label,
  },
  {
    dataIndex: "size",
    title: "大小",
    ellipsis: true,
  },
  {
    dataIndex: "fileCount",
    title: "文件数",
    ellipsis: true,
  },
];

export default function AddDataDialog({ knowledgeBase }) {
  const [isOpen, setIsOpen] = useState(false);
  const { message } = App.useApp();
  const [form] = Form.useForm();
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  // Form initial values
  const [newKB, setNewKB] = useState<Partial<KnowledgeBaseItem>>({
    dataSource: "dataset",
    processType: "DEFAULT_CHUNK",
    chunkSize: 500,
    overlap: 50,
    datasetIds: [],
  });

  const [filesTree, setFilesTree] = useState<any[]>([]);

  const fetchDatasets = async () => {
    const { data } = await queryDatasetsUsingGet({
      page: 0,
      size: 1000,
      type: DatasetType.TEXT,
    });
    const datasets =
      data.content.map((item) => ({
        ...item,
        key: item.id,
        title: item.name,
        isLeaf: item.fileCount === 0,
        disabled: item.fileCount === 0,
      })) || [];
    setFilesTree(datasets);
  };

  useEffect(() => {
    if (isOpen) fetchDatasets();
  }, [isOpen]);

  const updateTreeData = (list, key: React.Key, children) =>
    list.map((node) => {
      if (node.key === key) {
        return {
          ...node,
          children,
        };
      }
      if (node.children) {
        return {
          ...node,
          children: updateTreeData(node.children, key, children),
        };
      }
      return node;
    });

  const onLoadFiles = async ({ key, children }) =>
    new Promise<void>((resolve) => {
      if (children) {
        resolve();
        return;
      }
      queryDatasetFilesUsingGet(key, {
        page: 0,
        size: 1000,
      }).then(({ data }) => {
        const children = data.content.map((file) => ({
          title: file.fileName,
          key: file.id,
          isLeaf: true,
        }));
        setFilesTree((origin) => updateTreeData(origin, key, children));
        resolve();
      });
    });

  const handleBeforeUpload = (_, files: UploadFile[]) => {
    setFileList([...fileList, ...files]);
    return false;
  };

  const handleRemoveFile = (file: UploadFile) => {
    setFileList((prev) => prev.filter((f) => f.uid !== file.uid));
  };

  const handleAddData = async () => {
    await addKnowledgeBaseFilesUsingPost(knowledgeBase.id, {
      knowledgeBaseId: knowledgeBase.id,
      files: newKB.dataSource === "local" ? fileList : newKB.files,
      processType: newKB.processType,
      chunkSize: newKB.chunkSize,
      overlap: newKB.overlap,
      delimiter: newKB.delimiter,
    });
    message.success("数据添加成功");
    form.resetFields();
    setIsOpen(false);
  };

  return (
    <>
      <Button
        type="primary"
        icon={<PlusOutlined />}
        onClick={() => setIsOpen(true)}
      >
        添加数据
      </Button>
      <Modal
        title="添加数据"
        open={isOpen}
        onCancel={() => setIsOpen(false)}
        onOk={handleAddData}
        okText="确定"
        cancelText="取消"
        width={1000}
      >
        <div className="overflow-auto p-6">
          <Form
            form={form}
            layout="vertical"
            initialValues={newKB}
            onValuesChange={(_, allValues) => setNewKB(allValues)}
          >
            <Form.Item
              label="分块方式"
              name="processType"
              required
              rules={[{ required: true }]}
            >
              <Select options={sliceOptions}></Select>
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
            {newKB.processType === "CUSTOM_SEPARATOR_CHUNK" && (
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
            )}
            <Form.Item
              label="数据来源"
              name="dataSource"
              rules={[
                {
                  required: true,
                  message: "请选择数据来源",
                },
              ]}
            >
              <Radio.Group options={dataSourceOptions} />
            </Form.Item>
            {newKB.dataSource === "local" && (
              <Form.Item
                label="上传文件"
                name="files"
                rules={[
                  {
                    required: true,
                    message: "请上传文件",
                  },
                ]}
              >
                <Dragger
                  className="w-full"
                  onRemove={handleRemoveFile}
                  beforeUpload={handleBeforeUpload}
                  multiple
                >
                  <p className="ant-upload-drag-icon">
                    <InboxOutlined />
                  </p>
                  <p className="ant-upload-text">本地文件上传</p>
                  <p className="ant-upload-hint">
                    拖拽文件到此处或点击选择文件
                  </p>
                </Dragger>
              </Form.Item>
            )}
            {newKB.dataSource === "dataset" && (
              <Form.Item
                label="选择数据集文件"
                name="datasetId"
                rules={[
                  {
                    required: true,
                    message: "请选择数据集",
                  },
                ]}
              >
                <div className="border-card p-4 overflow-auto h-[300px]">
                  <Tree
                    blockNode
                    multiple
                    loadData={onLoadFiles}
                    treeData={filesTree}
                    onSelect={(_, { selectedNodes }) => {
                      console.log({
                        ...newKB,
                        files: selectedNodes
                          .filter((node) => node.isLeaf)
                          .map((node) => ({
                            ...node,
                            id: node.key,
                            name: node.title,
                          })),
                      });

                      setNewKB({
                        ...newKB,
                        files: selectedNodes
                          .filter((node) => node.isLeaf)
                          .map((node) => ({
                            ...node,
                            id: node.key,
                            name: node.title,
                          })),
                      });
                    }}
                  />
                </div>
              </Form.Item>
            )}
          </Form>
        </div>
      </Modal>
    </>
  );
}
