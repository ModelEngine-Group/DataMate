import { useEffect, useState } from "react";
import { Modal, Form, Input, message } from "antd";
import type { AnnotationTask } from "./annotation.model";
import DatasetFileTransfer from "@/components/business/DatasetFileTransfer";
import type { DatasetFile, Dataset } from "@/pages/DataManagement/dataset.model";
import { getManualAnnotationMappingFilesUsingGet, updateManualAnnotationMappingFilesUsingPut } from "./annotation.api";

interface EditManualAnnotationDatasetDialogProps {
  visible: boolean;
  task: AnnotationTask;
  onCancel: () => void;
  onSuccess: () => void;
}

export default function EditManualAnnotationDatasetDialog({
  visible,
  task,
  onCancel,
  onSuccess,
}: EditManualAnnotationDatasetDialogProps) {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [selectedFilesMap, setSelectedFilesMap] = useState<Record<string, DatasetFile>>({});
  const [initialFilesMap, setInitialFilesMap] = useState<Record<string, DatasetFile>>({});
  const [initialFileIds, setInitialFileIds] = useState<Set<string>>(new Set());
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [selectedCount, setSelectedCount] = useState(0);

  // 统计当前选中的文件数量（所有类型）
  useEffect(() => {
    setSelectedCount(Object.keys(selectedFilesMap).length);
  }, [selectedFilesMap]);

  // 打开弹窗时，拉取当前映射在 LS 中已有的文件列表，作为默认选中且锁定的文件
  useEffect(() => {
    if (!visible || !task?.id) {
      return;
    }

    let cancelled = false;

    (async () => {
      try {
        const resp = await getManualAnnotationMappingFilesUsingGet(task.id);
        const list: any[] = (resp as any)?.data || (resp as any) || [];

        const nextMap: Record<string, DatasetFile> = {};
        list.forEach((item) => {
          if (!item || item.id == null) return;
          const idStr = String(item.id);
          nextMap[idStr] = {
            // DatasetFile 接口字段与后端返回字段对齐，这里做最小映射
            // 类型上按需扩展，运行时以实际字段为准
            // eslint-disable-next-line @typescript-eslint/ban-ts-comment
            // @ts-ignore
            id: idStr,
            // eslint-disable-next-line @typescript-eslint/ban-ts-comment
            // @ts-ignore
            fileName: item.fileName,
            // eslint-disable-next-line @typescript-eslint/ban-ts-comment
            // @ts-ignore
            filePath: item.filePath,
            // eslint-disable-next-line @typescript-eslint/ban-ts-comment
            // @ts-ignore
            fileSize: item.fileSize,
            // eslint-disable-next-line @typescript-eslint/ban-ts-comment
            // @ts-ignore
            fileType: item.fileType,
            // 附加 datasetId/datasetName 供 DatasetFileTransfer 使用
            // eslint-disable-next-line @typescript-eslint/ban-ts-comment
            // @ts-ignore
            datasetId: item.datasetId,
            // eslint-disable-next-line @typescript-eslint/ban-ts-comment
            // @ts-ignore
            datasetName: item.datasetName,
            // 其余字段保持为空/默认值
          } as unknown as DatasetFile;
        });

        if (!cancelled) {
          setSelectedFilesMap(nextMap);
          setInitialFilesMap(nextMap);
          setInitialFileIds(new Set(Object.keys(nextMap)));
        }
      } catch (e) {
        console.error("Failed to fetch manual mapping files:", e);
        if (!cancelled) {
          message.error("获取任务当前数据集文件失败");
        }
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
      if (selectedCount === 0) {
        message.error("请至少选择一个文件");
        return;
      }

      setLoading(true);

      const fileIds = Object.values(selectedFilesMap).map((file: any) => String(file.id));

      const payload = {
        // datasetId 字段在后端目前未强依赖，这里沿用任务主体数据集以保持一致
        datasetId: task.datasetId,
        fileIds,
      };

      await updateManualAnnotationMappingFilesUsingPut(task.id, payload);
      message.success("任务数据集已更新，将仅为新增文件在 Label Studio 中创建任务");
      onSuccess();
    } catch (error: any) {
      console.error("Failed to update manual annotation mapping files:", error);
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

        <Form.Item label="选择数据集和文件" required>
          <DatasetFileTransfer
            open={visible}
            selectedFilesMap={selectedFilesMap}
            onSelectedFilesChange={(next) => {
              // 不允许删除任务最初已包含的文件：
              // 无论在 UI 中如何操作，这些初始文件都会被强制保留
              const merged: Record<string, DatasetFile> = { ...next } as any;
              initialFileIds.forEach((id) => {
                if (!merged[id] && initialFilesMap[id]) {
                  merged[id] = initialFilesMap[id];
                }
              });
              setSelectedFilesMap(merged);
            }}
            onDatasetSelect={(dataset) => {
              setSelectedDataset(dataset as Dataset | null);
            }}
            // 手动标注支持所有数据集/文件类型，但编辑时仅允许在创建任务的数据集中追加
            singleDatasetOnly
            fixedDatasetId={task.datasetId}
            lockedFileIds={Array.from(initialFileIds)}
          />
          <div className="mt-2 p-2 bg-blue-50 rounded border border-blue-200 text-xs">
            {selectedDataset ? (
              <>
                当前数据集：<span className="font-medium">{selectedDataset.name}</span> - 已选择
                <span className="font-medium text-blue-600"> {selectedCount} </span>个文件
              </>
            ) : (
              <>
                已选择<span className="font-medium text-blue-600"> {selectedCount} </span>个文件
              </>
            )}
          </div>
        </Form.Item>
      </Form>
    </Modal>
  );
}
