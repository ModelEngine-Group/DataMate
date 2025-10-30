import { Select, Input, Form, Radio, Modal, Button, UploadFile } from "antd";
import { InboxOutlined } from "@ant-design/icons";
import { dataSourceOptions } from "../../dataset.const";
import { Dataset, DataSource } from "../../dataset.model";
import { useEffect, useMemo, useState } from "react";
import { queryTasksUsingGet } from "@/pages/DataCollection/collection.apis";
import { updateDatasetByIdUsingPut } from "../../dataset.api";
import { sliceFile } from "@/utils/file.util";
import Dragger from "antd/es/upload/Dragger";

export default function ImportConfiguration({
  data,
  open,
  onClose,
  updateEvent = "update:dataset",
}: {
  data: Dataset | null;
  open: boolean;
  onClose: () => void;
  updateEvent?: string;
}) {
  const [form] = Form.useForm();
  const [collectionOptions, setCollectionOptions] = useState([]);
  const [importConfig, setImportConfig] = useState<any>({
    source: DataSource.UPLOAD,
  });

  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const fileSliceList = useMemo(() => {
    const sliceList = fileList.map((file) => {
      const slices = sliceFile(file);
      return { originFile: file, slices, name: file.name, size: file.size };
    });
    return sliceList;
  }, [fileList]);

  // 本地上传文件相关逻辑

  const resetFiles = () => {
    setFileList([]);
  };

  const handleUpload = async (dataset: Dataset) => {
    const formData = new FormData();
    fileList.forEach((file) => {
      formData.append("file", file);
    });
    window.dispatchEvent(
      new CustomEvent("upload:dataset", {
        detail: {
          dataset,
          files: fileSliceList,
          updateEvent,
        },
      })
    );
    resetFiles();
  };

  const handleBeforeUpload = (_, files: UploadFile[]) => {
    setFileList([...fileList, ...files]);
    return false;
  };

  const handleRemoveFile = (file: UploadFile) => {
    setFileList((prev) => prev.filter((f) => f.uid !== file.uid));
  };

  const fetchCollectionTasks = async () => {
    if (importConfig.source !== DataSource.COLLECTION) return;
    try {
      const res = await queryTasksUsingGet({ page: 0, size: 100 });
      const options = res.data.content.map((task: any) => ({
        label: task.name,
        value: task.id,
      }));
      setCollectionOptions(options);
    } catch (error) {
      console.error("Error fetching collection tasks:", error);
    }
  };

  const resetState = () => {
    form.resetFields();
    setFileList([]);
    form.setFieldsValue({ files: null });
    setImportConfig({ source: DataSource.UPLOAD });
  };

  const handleImportData = async () => {
    if (!data) return;
    if (importConfig.source === DataSource.UPLOAD) {
      await handleUpload(data);
    } else if (importConfig.source === DataSource.COLLECTION) {
      await updateDatasetByIdUsingPut(data.id, {
        ...importConfig,
      });
    }
    onClose();
  };

  useEffect(() => {
    if (open) {
      resetState();
      fetchCollectionTasks();
    }
  }, [open, importConfig.source]);

  return (
    <Modal
      title="导入数据"
      open={open}
      width={600}
      onCancel={() => {
        onClose();
        resetState();
      }}
      maskClosable={false}
      footer={
        <>
          <Button onClick={onClose}>取消</Button>
          <Button
            type="primary"
            disabled={!fileList?.length && !importConfig.dataSource}
            onClick={handleImportData}
          >
            确定
          </Button>
        </>
      }
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={importConfig || {}}
        onValuesChange={(_, allValues) => setImportConfig(allValues)}
      >
        <Form.Item
          label="数据源"
          name="source"
          rules={[{ required: true, message: "请选择数据源" }]}
        >
          <Radio.Group
            buttonStyle="solid"
            options={dataSourceOptions}
            optionType="button"
          />
        </Form.Item>
        {importConfig?.source === DataSource.COLLECTION && (
          <Form.Item name="dataSource" label="归集任务" required>
            <Select placeholder="请选择归集任务" options={collectionOptions} />
          </Form.Item>
        )}

        {/* obs import */}
        {importConfig?.source === DataSource.OBS && (
          <div className="grid grid-cols-2 gap-3 p-4 bg-blue-50 rounded-lg">
            <Form.Item
              name="endpoint"
              rules={[{ required: true }]}
              label="Endpoint"
            >
              <Input
                className="h-8 text-xs"
                placeholder="obs.cn-north-4.myhuaweicloud.com"
              />
            </Form.Item>
            <Form.Item
              name="bucket"
              rules={[{ required: true }]}
              label="Bucket"
            >
              <Input className="h-8 text-xs" placeholder="my-bucket" />
            </Form.Item>
            <Form.Item
              name="accessKey"
              rules={[{ required: true }]}
              label="Access Key"
            >
              <Input className="h-8 text-xs" placeholder="Access Key" />
            </Form.Item>
            <Form.Item
              name="secretKey"
              rules={[{ required: true }]}
              label="Secret Key"
            >
              <Input
                type="password"
                className="h-8 text-xs"
                placeholder="Secret Key"
              />
            </Form.Item>
          </div>
        )}

        {/* Local Upload Component */}
        {importConfig?.source === DataSource.UPLOAD && (
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
              <p className="ant-upload-hint">拖拽文件到此处或点击选择文件</p>
            </Dragger>
          </Form.Item>
        )}

        {/* Target Configuration */}
        {importConfig?.target && importConfig?.target !== DataSource.UPLOAD && (
          <div className="space-y-3 p-4 bg-blue-50 rounded-lg">
            {importConfig?.target === DataSource.DATABASE && (
              <div className="grid grid-cols-2 gap-3">
                <Form.Item
                  name="databaseType"
                  rules={[{ required: true }]}
                  label="数据库类型"
                >
                  <Select
                    className="w-full"
                    options={[
                      { label: "MySQL", value: "mysql" },
                      { label: "PostgreSQL", value: "postgresql" },
                      { label: "MongoDB", value: "mongodb" },
                    ]}
                  ></Select>
                </Form.Item>
                <Form.Item
                  name="tableName"
                  rules={[{ required: true }]}
                  label="表名"
                >
                  <Input className="h-8 text-xs" placeholder="dataset_table" />
                </Form.Item>
                <Form.Item
                  name="connectionString"
                  rules={[{ required: true }]}
                  label="连接字符串"
                >
                  <Input
                    className="h-8 text-xs col-span-2"
                    placeholder="数据库连接字符串"
                  />
                </Form.Item>
              </div>
            )}
          </div>
        )}
      </Form>
    </Modal>
  );
}
