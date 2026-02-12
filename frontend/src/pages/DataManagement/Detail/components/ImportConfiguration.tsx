import { Select, Input, Form, Radio, Modal, Button, UploadFile, Switch, App, Tag } from "antd";
import { InboxOutlined } from "@ant-design/icons";
import {getDataSourceMap, getDatasetTypeMap} from "../../dataset.const";
import { Dataset, DataSource, DatasetType } from "../../dataset.model";
import { useEffect, useMemo, useState } from "react";
import { queryTasksUsingGet } from "@/pages/DataCollection/collection.apis";
import { updateDatasetByIdUsingPut, createDatasetDirectoryUsingPost } from "../../dataset.api";
import { sliceFile } from "@/utils/file.util";
import Dragger from "antd/es/upload/Dragger";
import { useTranslation } from "react-i18next";

const DATASET_TYPE_SAFE_SUFFIXES: Record<DatasetType, string[]> = {
  [DatasetType.TEXT]: [
    ".txt",
    ".md",
    ".markdown",
    ".json",
    ".jsonl",
    ".csv",
    ".tsv",
    ".xml",
    ".html",
    ".htm",
    ".log",
    ".pdf",
    ".doc",
    ".docx",
  ],
  [DatasetType.IMAGE]: [
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".gif",
    ".webp",
    ".tif",
    ".tiff",
  ],
  [DatasetType.AUDIO]: [
    ".mp3",
    ".wav",
    ".flac",
    ".aac",
    ".ogg",
    ".m4a",
  ],
  [DatasetType.VIDEO]: [
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".flv",
    ".wmv",
    ".webm",
  ],
};

const GENERIC_ARCHIVE_SUFFIXES = [
  ".zip",
  ".tar",
  ".tar.gz",
  ".tgz",
  ".rar",
  ".7z",
];

// 判断是否为通过文件夹上传带来的文件（依赖 webkitRelativePath）
const isFolderFile = (file: UploadFile) => {
  const fileObj: any = file;
  const originFile = (fileObj.originFileObj as File) || fileObj;
  const relativePath = (originFile as any).webkitRelativePath || "";

  // 1）通过 webkitRelativePath 判断：有路径且包含 /，说明来源于文件夹
  if (relativePath && relativePath.includes("/")) {
    return true;
  }

  // 2）某些浏览器在非 directory 上传区域拖入文件夹时，会产生一个 0 字节、无类型、无扩展名的占位 File
  // 将这种情况也视为“文件夹”，避免被当成普通文件加入上传列表
  const isZeroSize = (originFile as any).size === 0;
  const hasNoType = !(originFile as any).type;
  const hasNoExtension = typeof originFile.name === "string" && !originFile.name.includes(".");

  if (!relativePath && isZeroSize && hasNoType && hasNoExtension) {
    return true;
  }

  return false;
};

function getFileExtension(name?: string): string | null {
  if (!name) return null;
  const lower = name.toLowerCase();

  // 先处理多段压缩包后缀（如 .tar.gz）
  for (const ext of GENERIC_ARCHIVE_SUFFIXES) {
    if (lower.endsWith(ext)) return ext;
  }

  const lastDot = lower.lastIndexOf(".");
  if (lastDot === -1) return null;
  return lower.slice(lastDot);
}

function resolveDatasetType(data: Dataset | null | undefined, t: (key: string) => string): DatasetType | undefined {
  if (!data) return undefined;

  const rawDatasetType = (data as any).datasetType as string | undefined;
  const datasetTypeValues = Object.values(DatasetType) as string[];

  // 1. 直接使用后端返回的 datasetType 字段（如果正好是 TEXT/IMAGE/AUDIO/VIDEO）
  if (rawDatasetType && datasetTypeValues.includes(rawDatasetType)) {
    return rawDatasetType as DatasetType;
  }

  // 2. 尝试通过 type 字段的中文标签匹配（mapDataset 中会把 type 设置为中文标签）
  const typeLabel = (data as any).type as string | undefined;
  if (typeLabel) {
    const matched = Object.values(getDatasetTypeMap(t)).find((item) => item.label === typeLabel);
    if (matched) return matched.value;
  }

  // 3. 兜底：如果 type 字段本身就是 TEXT/IMAGE/... 也兼容一下
  if (typeLabel && datasetTypeValues.includes(typeLabel)) {
    return typeLabel as DatasetType;
  }

  return undefined;
}

export default function ImportConfiguration({
  data,
  open,
  onClose,
  updateEvent = "update:dataset",
  prefix,
}: {
  data: Dataset | null;
  open: boolean;
  onClose: () => void;
  updateEvent?: string;
  prefix?: string;
}) {
  const { message } = App.useApp();
  const { t } = useTranslation();
  const dataSourceMap = getDataSourceMap(t);
  const datasetTypeMap = getDatasetTypeMap(t);
  const [form] = Form.useForm();
  const [collectionOptions, setCollectionOptions] = useState([]);
  const [importConfig, setImportConfig] = useState<any>({
    source: DataSource.UPLOAD,
  });
  const [currentPrefix, setCurrentPrefix] = useState<string>("");

  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const fileSliceList = useMemo(() => {
    const sliceList = fileList.map((file) => {
      const fileObj: any = file;
      const originFile = (fileObj.originFileObj as File) || fileObj;
      const relativePath = (originFile as any).webkitRelativePath || originFile.name;
      const slices = sliceFile(originFile);
      return {
        originFile,
        slices,
        // 使用相对路径作为后端接收的 fileName，以保留目录结构
        name: relativePath,
        size: originFile.size,
      };
    });
    return sliceList;
  }, [fileList]);

  const folderNames = useMemo(() => {
    const dirSet = new Set<string>();
    fileSliceList.forEach((file) => {
      const path = file.name || "";
      const parts = path.split("/").filter(Boolean);
      if (parts.length > 1) {
        dirSet.add(parts[0]);
      }
    });
    return Array.from(dirSet);
  }, [fileSliceList]);

  const hasFolderUploads = folderNames.length > 0;
  const pureFileList = useMemo(
    () => fileList.filter((f) => !isFolderFile(f as UploadFile)),
    [fileList]
  );

  // 本地上传文件相关逻辑

  const resetFiles = () => {
    setFileList([]);
  };

  const handleUpload = async (dataset: Dataset) => {
    console.log('[ImportConfiguration] Uploading with currentPrefix:', currentPrefix);

    // 在上传文件前，确保按文件路径在数据集中创建对应的目录结构（支持多级目录）
    try {
      const basePrefix = currentPrefix || "";
      const dirSet = new Set<string>();

      fileSliceList.forEach((file) => {
        const path = file.name || "";
        const parts = path.split("/").filter(Boolean);
        if (parts.length <= 1) return; // 没有目录

        let accumulated = "";
        for (let i = 0; i < parts.length - 1; i++) {
          accumulated += parts[i] + "/";
          dirSet.add(basePrefix + accumulated);
        }
      });

      const dirList = Array.from(dirSet).sort((a, b) => a.length - b.length);

      for (const fullPrefix of dirList) {
        const relative = fullPrefix.slice((basePrefix || "").length);
        const segments = relative.split("/").filter(Boolean);
        if (!segments.length) continue;
        const directoryName = segments[segments.length - 1];
        const parentPrefix =
          segments.length > 1
            ? basePrefix + segments.slice(0, -1).join("/") + "/"
            : basePrefix || undefined;

        try {
          await createDatasetDirectoryUsingPost(dataset.id, {
            parentPrefix,
            directoryName,
          });
        } catch (e) {
          // 目录已存在等错误不阻断整个上传流程
          console.warn("createDirectory failed for", fullPrefix, e);
        }
      }
    } catch (e) {
      console.warn("ensure directories before upload failed", e);
    }

    window.dispatchEvent(
      new CustomEvent("upload:dataset", {
        detail: {
          dataset,
          files: fileSliceList,
          updateEvent,
          hasArchive: importConfig.hasArchive,
          prefix: currentPrefix,
        },
      })
    );
    resetFiles();
  };
  const runTypeCheck = (checkFiles: UploadFile[]) => {
    if (!checkFiles || checkFiles.length === 0) return;
    const datasetType = resolveDatasetType(data, t);
    if (datasetType) {
      const safeSuffixes = DATASET_TYPE_SAFE_SUFFIXES[datasetType] || [];
      const typeLabel =
        datasetTypeMap[datasetType as keyof typeof datasetTypeMap]?.label ||
        "当前";
      const mismatchedFiles = checkFiles.filter((f) => {
        const ext = getFileExtension(f.name);
        if (!ext) return true;
        if (GENERIC_ARCHIVE_SUFFIXES.includes(ext)) return false;
        if (safeSuffixes.includes(ext)) return false;
        return true;
      });

      if (mismatchedFiles.length > 0) {
        message.warning(
          t("dataManagement.import.warningTypeMismatch", { type: typeLabel })
        );
      }
    }
    return false;
  };

  // 仅接收“单个文件”的上传区域
  const handleBeforeUploadFile = (file: UploadFile, batchFiles: UploadFile[]) => {
    const isLastFileInBatch =
      batchFiles.length > 0 && file.uid === batchFiles[batchFiles.length - 1].uid;
    if (!isLastFileInBatch) {
      return false;
    }

    const folderFiles = batchFiles.filter((f) => isFolderFile(f));
    const pureFiles = batchFiles.filter((f) => !isFolderFile(f));

    if (folderFiles.length > 0) {
      message.warning("如需上传文件夹，请使用右侧“本地文件夹上传”区域。");
    }

    if (pureFiles.length > 0) {
      setFileList((prev) => [...prev, ...pureFiles]);
      runTypeCheck(pureFiles);
    }

    return false;
  };

  // 仅接收“文件夹（含其中文件）”的上传区域
  const handleBeforeUploadFolder = (file: UploadFile, batchFiles: UploadFile[]) => {
    const isLastFileInBatch =
      batchFiles.length > 0 && file.uid === batchFiles[batchFiles.length - 1].uid;
    if (!isLastFileInBatch) {
      return false;
    }

    const folderFiles = batchFiles.filter((f) => isFolderFile(f));
    const pureFiles = batchFiles.filter((f) => !isFolderFile(f));

    if (pureFiles.length > 0) {
      message.warning("如需上传单个文件，请使用左侧“本地文件上传”区域。");
    }

    if (folderFiles.length > 0) {
      setFileList((prev) => [...prev, ...folderFiles]);
      runTypeCheck(folderFiles);
    }

    return false;
  };

  const handleRemoveFile = (file: UploadFile) => {
    setFileList((prev) => prev.filter((f) => f.uid !== file.uid));
  };

  const handleRemoveFolder = (folderName: string) => {
    if (!folderName) return;
    setFileList((prev) =>
      prev.filter((file) => {
        const fileObj: any = file;
        const originFile = (fileObj.originFileObj as File) || fileObj;
        const relativePath = (originFile as any).webkitRelativePath || originFile.name || "";
        const parts = relativePath.split("/").filter(Boolean);
        // 仅当顶层目录名与要删除的文件夹一致时才移除
        return !(parts.length > 1 && parts[0] === folderName);
      })
    );
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
    console.log(
      '[ImportConfiguration] resetState called, preserving currentPrefix:',
      currentPrefix
    );
    form.resetFields();
    setFileList([]);
    form.setFieldsValue({ files: null });
    setImportConfig({ source: importConfig.source ? importConfig.source : DataSource.UPLOAD });
    console.log('[ImportConfiguration] resetState done, currentPrefix still:', currentPrefix);
  };

  const handleImportData = async () => {
    if (!data) return;
    console.log('[ImportConfiguration] handleImportData called, currentPrefix:', currentPrefix);
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
      setCurrentPrefix(prefix || "");
      console.log('[ImportConfiguration] Modal opened with prefix:', prefix);
      resetState();
      fetchCollectionTasks();
    }
  }, [open]);

  // Separate effect for fetching collection tasks when source changes
  useEffect(() => {
    if (open && importConfig.source === DataSource.COLLECTION) {
      fetchCollectionTasks();
    }
  }, [importConfig.source]);

  return (
    <Modal
      title={t("dataManagement.import.title")}
      open={open}
      width={600}
      onCancel={() => {
        onClose();
        resetState();
      }}
      maskClosable={false}
      footer={
        <>
          <Button onClick={onClose}>{t("dataManagement.actions.cancel")}</Button>
          <Button
            type="primary"
            disabled={!fileList?.length && !importConfig.dataSource}
            onClick={handleImportData}
          >
            {t("dataManagement.actions.confirm")}
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
          label={t("dataManagement.formLabels.dataSource")}
          name="source"
          rules={[{ required: true, message: t("dataManagement.import.validation.selectDataSource") }]}
        >
          <Radio.Group
            buttonStyle="solid"
            options={[...Object.values(dataSourceMap)]}
            optionType="button"
          />
        </Form.Item>
        {importConfig?.source === DataSource.COLLECTION && (
          <Form.Item name="dataSource" label={t("dataManagement.formLabels.collectionTask")} required>
            <Select placeholder={t("dataManagement.placeholders.selectCollectionTask")} options={collectionOptions} />
          </Form.Item>
        )}

        {/* obs import */}
        {importConfig?.source === DataSource.OBS && (
          <div className="grid grid-cols-2 gap-3 p-4 bg-blue-50 rounded-lg">
            <Form.Item
              name="endpoint"
              rules={[{ required: true }]}
              label={t("dataManagement.import.obsEndpoint")}
            >
              <Input
                className="h-8 text-xs"
                placeholder={t("dataManagement.placeholders.obsEndpoint")}
              />
            </Form.Item>
            <Form.Item
              name="bucket"
              rules={[{ required: true }]}
              label={t("dataManagement.import.obsBucket")}
            >
              <Input className="h-8 text-xs" placeholder={t("dataManagement.placeholders.obsBucket")} />
            </Form.Item>
            <Form.Item
              name="accessKey"
              rules={[{ required: true }]}
              label={t("dataManagement.import.obsAccessKey")}
            >
              <Input className="h-8 text-xs" placeholder={t("dataManagement.import.obsAccessKeyPlaceholder")} />
            </Form.Item>
            <Form.Item
              name="secretKey"
              rules={[{ required: true }]}
              label={t("dataManagement.import.obsSecretKey")}
            >
              <Input
                type="password"
                className="h-8 text-xs"
                placeholder={t("dataManagement.import.obsSecretKeyPlaceholder")}
              />
            </Form.Item>
          </div>
        )}

        {/* Local Upload Component */}
        {importConfig?.source === DataSource.UPLOAD && (
          <>
            <Form.Item
              label={t("dataManagement.import.autoExtract")}
              name="hasArchive"
              valuePropName="checked"
              initialValue={true}
            >
              <Switch />
            </Form.Item>
            <Form.Item
              label={t("dataManagement.import.uploadFiles")}
              name="files"
              rules={[
                {
                  required: true,
                  message: t("dataManagement.validation.filesRequired"),
                },
              ]}
            >
              <div className="flex gap-6 justify-center">
                {/* 左侧：仅文件上传 */}
                <div className="flex flex-col items-center">
                  <Dragger
                    className="dataset-import-dragger"
                    multiple
                    showUploadList={false}
                    beforeUpload={handleBeforeUploadFile}
                  >
                    <p className="ant-upload-drag-icon">
                      <InboxOutlined />
                    </p>
                    <p className="ant-upload-text">{t("dataManagement.import.uploadFileTitle")}</p>
                    <p className="ant-upload-hint">{t("dataManagement.import.uploadFileHint")}</p>
                  </Dragger>
                </div>

                {/* 右侧：仅文件夹上传 */}
                <div className="flex flex-col items-center">
                  <Dragger
                    className="dataset-import-dragger"
                    directory
                    multiple
                    showUploadList={false}
                    beforeUpload={handleBeforeUploadFolder}
                  >
                    <p className="ant-upload-drag-icon">
                      <InboxOutlined />
                    </p>
                    <p className="ant-upload-text">{t("dataManagement.import.uploadFolderTitle")}</p>
                    <p className="ant-upload-hint">{t("dataManagement.import.uploadFolderHint")}</p>
                  </Dragger>
                </div>
              </div>

              {/* 统一的文件 / 文件夹列表区域，固定高度可滚动 */}
              {fileList.length > 0 && (
                <div className="mt-3 border border-dashed rounded-md max-h-40 overflow-y-auto p-2 text-xs text-gray-700 space-y-2">
                  {pureFileList.length > 0 && (
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-semibold">{t("dataManagement.import.fileLabel")}</span>
                      {pureFileList.map((file) => {
                        const name = file.name || t("dataManagement.defaults.unnamedFile");
                        const displayName = name.length > 20 ? `${name.slice(0, 20)}...` : name;
                        return (
                          <Tag
                            key={file.uid}
                            closable
                            onClose={(e) => {
                              e.preventDefault();
                              handleRemoveFile(file);
                            }}
                            title={name}
                          >
                            {displayName}
                          </Tag>
                        );
                      })}
                    </div>
                  )}

                  {hasFolderUploads && (
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-semibold">{t("dataManagement.import.folderLabel")}</span>
                      {folderNames.map((name) => {
                        const displayName = name.length > 20 ? `${name.slice(0, 20)}...` : name;
                        return (
                          <Tag
                            key={name}
                            closable
                            onClose={(e) => {
                              e.preventDefault();
                              handleRemoveFolder(name);
                            }}
                            title={name}
                          >
                            {displayName}
                          </Tag>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </Form.Item>
          </>
        )}

        {/* Target Configuration */}
        {importConfig?.target && importConfig?.target !== DataSource.UPLOAD && (
          <div className="space-y-3 p-4 bg-blue-50 rounded-lg">
            {importConfig?.target === DataSource.DATABASE && (
              <div className="grid grid-cols-2 gap-3">
                <Form.Item
                  name="databaseType"
                  rules={[{ required: true }]}
                  label={t("dataManagement.import.dbType")}
                >
                  <Select
                    className="w-full"
                    options={[
                      { label: t("dataManagement.import.dbTypeMysql"), value: "mysql" },
                      { label: t("dataManagement.import.dbTypePostgres"), value: "postgresql" },
                      { label: t("dataManagement.import.dbTypeMongo"), value: "mongodb" },
                    ]}
                  ></Select>
                </Form.Item>
                <Form.Item
                  name="tableName"
                  rules={[{ required: true }]}
                  label={t("dataManagement.import.dbTableName")}
                >
                  <Input className="h-8 text-xs" placeholder={t("dataManagement.placeholders.databaseTable")} />
                </Form.Item>
                <Form.Item
                  name="connectionString"
                  rules={[{ required: true }]}
                  label={t("dataManagement.import.dbConnectionString")}
                >
                  <Input
                    className="h-8 text-xs col-span-2"
                    placeholder={t("dataManagement.placeholders.databaseConnection")}
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
