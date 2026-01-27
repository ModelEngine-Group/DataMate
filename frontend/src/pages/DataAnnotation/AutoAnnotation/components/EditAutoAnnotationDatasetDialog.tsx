import { useEffect, useState } from "react";
import { Modal, Form, Input, message } from "antd";
import type { AutoAnnotationTask } from "../../annotation.model";
import { getAutoAnnotationTaskFilesUsingGet, updateAutoAnnotationTaskFilesUsingPut } from "../../annotation.api";
import DatasetFileTransfer from "@/components/business/DatasetFileTransfer";
import type { DatasetFile, Dataset } from "@/pages/DataManagement/dataset.model";
import { DatasetType } from "@/pages/DataManagement/dataset.model";

interface EditAutoAnnotationDatasetDialogProps {
  visible: boolean;
  task: AutoAnnotationTask;
  onCancel: () => void;
  onSuccess: () => void;
}

const imageExtensions = [
  ".jpg",
  ".jpeg",
  ".png",
  ".bmp",
  ".gif",
  ".tiff",
  ".webp",
];

export default function EditAutoAnnotationDatasetDialog({
  visible,
  task,
  onCancel,
  onSuccess,
}: EditAutoAnnotationDatasetDialogProps) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [selectedFilesMap, setSelectedFilesMap] = useState<Record<string, DatasetFile>>({});
  const [initialFilesMap, setInitialFilesMap] = useState<Record<string, DatasetFile>>({});
  const [initialFileIds, setInitialFileIds] = useState<Set<string>>(new Set());
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [imageFileCount, setImageFileCount] = useState(0);

  // 预计算当前已选中的图像文件数量
  useEffect(() => {
    const count = Object.values(selectedFilesMap).filter((file) => {
      const ext = file.fileName?.toLowerCase().match(/\.[^.]+$/)?.[0] || "";
      return imageExtensions.includes(ext);
    }).length;
    setImageFileCount(count);
  }, [selectedFilesMap]);

  // 打开弹窗时，拉取任务当前关联的文件列表，作为默认选中项
  useEffect(() => {
    if (!visible || !task?.id) {
      return;
    }

    let cancelled = false;

    (async () => {
      try {
        const resp = await getAutoAnnotationTaskFilesUsingGet(task.id);
        const list: any[] = resp?.data || resp || [];
        if (cancelled) return;

        const nextMap: Record<string, DatasetFile> = {};
        list.forEach((item) => {
          if (!item || item.id == null) return;
          const idStr = String(item.id);
          nextMap[idStr] = {
            // DatasetFile 接口字段与后端返回字段对齐，这里做最小映射
            id: idStr,
            fileName: item.fileName,
            filePath: item.filePath,
            fileSize: item.fileSize,
            fileType: item.fileType,
            status: "ACTIVE",
            // 额外附加 datasetId/datasetName 供 DatasetFileTransfer 使用
            // eslint-disable-next-line @typescript-eslint/ban-ts-comment
            // @ts-ignore
            datasetId: item.datasetId,
            // eslint-disable-next-line @typescript-eslint/ban-ts-comment
            // @ts-ignore
            datasetName: item.datasetName,
          } as unknown as DatasetFile;
        });

        setSelectedFilesMap(nextMap);
        setInitialFilesMap(nextMap);
        setInitialFileIds(new Set(Object.keys(nextMap)));
      } catch (e) {
        console.error("Failed to fetch auto annotation task files:", e);
        message.error("获取任务当前数据集文件失败");
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [visible, task?.id]);

  useEffect(() => {
    if (visible) {
      form.setFieldsValue({
        name: task?.name,
      });
    }
  }, [visible, task?.name, form]);

  const handleSubmit = async () => {
    try {
      if (imageFileCount === 0) {
        message.error("请至少选择一个图像文件");
        return;
      }

      setLoading(true);

      const selectedFiles = Object.values(selectedFilesMap) as any[];
      const datasetIds = Array.from(
        new Set(
          selectedFiles
            .map((file) => (
              // eslint-disable-next-line @typescript-eslint/ban-ts-comment
              // @ts-ignore
              file?.datasetId
            ))
            .filter((id) => id !== undefined && id !== null && id !== ""),
        ),
      );

      // 主数据集：优先沿用任务原有 datasetId，其次取当前选择中的第一个
      const effectiveDatasetId = task.datasetId || datasetIds[0];

      const imageFileIds = Object.values(selectedFilesMap)
        .filter((file) => {
          const ext = file.fileName?.toLowerCase().match(/\.[^.]+$/)?.[0] || "";
          return imageExtensions.includes(ext);
        })
        .map((file) => file.id);

      const payload = {
        datasetId: effectiveDatasetId,
        fileIds: imageFileIds,
      };

      await updateAutoAnnotationTaskFilesUsingPut(task.id, payload);
      message.success("任务数据集已更新，将仅对新增的图像执行自动标注");
      onSuccess();
    } catch (error: any) {
      console.error("Failed to update auto annotation task files:", error);
      message.error(error?.message || "更新任务数据集失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title="编辑任务数据集"
      open={visible}
      onCancel={onCancel}
      onOk={handleSubmit}
      confirmLoading={loading}
      width={800}
      destroyOnClose
    >
      <Form form={form} layout="vertical" preserve={false}>
        <Form.Item label="任务名称">
          <Input value={task?.name} disabled />
        </Form.Item>

        <Form.Item label="选择数据集和图像文件" required>
          <DatasetFileTransfer
            open={visible}
            selectedFilesMap={selectedFilesMap}
            onSelectedFilesChange={(next) => {
              // 不允许删除任务最初已包含的文件：
              // 无论在 UI 中如何操作，这些初始文件都会被强制保留
              const merged: Record<string, DatasetFile> = { ...next };
              initialFileIds.forEach((id) => {
                if (!merged[id] && initialFilesMap[id]) {
                  merged[id] = initialFilesMap[id];
                }
              });
              setSelectedFilesMap(merged);
            }}
            onDatasetSelect={(dataset) => {
              setSelectedDataset(dataset);
            }}
            datasetTypeFilter={DatasetType.IMAGE}
            singleDatasetOnly
            fixedDatasetId={task.datasetId}
            lockedFileIds={Array.from(initialFileIds)}
          />
          {selectedDataset && (
            <div className="mt-2 p-2 bg-blue-50 rounded border border-blue-200 text-xs">
              当前数据集：<span className="font-medium">{selectedDataset.name}</span> - 已选择
              <span className="font-medium text-blue-600"> {imageFileCount} </span>个图像文件
            </div>
          )}
        </Form.Item>
      </Form>
    </Modal>
  );
}
