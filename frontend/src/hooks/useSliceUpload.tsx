import { TaskItem } from "@/pages/DataManagement/dataset.model";
import { calculateSHA256, checkIsFilesExist } from "@/utils/file.util";
import { App } from "antd";
import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";

export function useFileSliceUpload(
  {
    preUpload,
    uploadChunk,
    cancelUpload,
  }: {
    preUpload: (id: string, params: any) => Promise<{ data: number }>;
    uploadChunk: (id: string, formData: FormData, config: any) => Promise<any>;
    cancelUpload: ((reqId: number) => Promise<any>) | null;
  },
  showTaskCenter = true // Whether to show task center during upload
) {
  const { message } = App.useApp();
  const { t } = useTranslation();
  const [taskList, setTaskList] = useState<TaskItem[]>([]);
  const taskListRef = useRef<TaskItem[]>([]); // 用于固定任务顺序

  const createTask = (detail: any = {}) => {
    const { dataset } = detail;
    const title = `${t('hooks.sliceUpload.uploadDataset')}: ${dataset.name} `;
    const controller = new AbortController();
    const task: TaskItem = {
      key: dataset.id,
      title,
      percent: 0,
      reqId: -1,
      controller,
      size: 0,
      updateEvent: detail.updateEvent,
      hasArchive: detail.hasArchive,
      prefix: detail.prefix,
    };
    taskListRef.current = [task, ...taskListRef.current];

    setTaskList(taskListRef.current);
    return task;
  };

  const updateTaskList = (task: TaskItem) => {
    taskListRef.current = taskListRef.current.map((item) =>
      item.key === task.key ? task : item
    );
    setTaskList(taskListRef.current);
  };

  const removeTask = (task: TaskItem) => {
    const { key } = task;
    taskListRef.current = taskListRef.current.filter(
      (item) => item.key !== key
    );
    setTaskList(taskListRef.current);
    if (task.isCancel && task.cancelFn) {
      task.cancelFn();
    }
    if (task.updateEvent) {
      // Carry prefix info to stay in current directory after refresh
      window.dispatchEvent(
        new CustomEvent(task.updateEvent, {
          detail: { prefix: (task as any).prefix },
        })
      );
    }
    if (showTaskCenter) {
      window.dispatchEvent(
        new CustomEvent("show:task-popover", { detail: { show: false } })
      );
    }
  };

  async function buildFormData({ file, reqId, i, j }) {
    const formData = new FormData();
    const { slices, name, size } = file;
    const checkSum = await calculateSHA256(slices[j]);
    formData.append("file", slices[j]);
    formData.append("reqId", reqId.toString());
    formData.append("fileNo", (i + 1).toString());
    formData.append("chunkNo", (j + 1).toString());
    formData.append("fileName", name);
    formData.append("fileSize", size.toString());
    formData.append("totalChunkNum", slices.length.toString());
    formData.append("checkSumHex", checkSum);
    return formData;
  }

  async function uploadSlice(task: TaskItem, fileInfo) {
    if (!task) {
      return;
    }
    const { reqId, key } = task;
    const { loaded, i, j, files, totalSize } = fileInfo;
    const formData = await buildFormData({
      file: files[i],
      i,
      j,
      reqId,
    });

    let newTask = { ...task };
    await uploadChunk(key, formData, {
      onUploadProgress: (e) => {
        const loadedSize = loaded + e.loaded;
        const curPercent = Number((loadedSize / totalSize) * 100).toFixed(2);

        newTask = {
          ...newTask,
          ...taskListRef.current.find((item) => item.key === key),
          size: loadedSize,
          percent: curPercent >= 100 ? 99.99 : curPercent,
        };
        updateTaskList(newTask);
      },
    });
  }

  async function uploadFile({ task, files, totalSize }) {
    console.log('[useSliceUpload] Calling preUpload with prefix:', task.prefix);
    const { data: reqId } = await preUpload(task.key, {
      totalFileNum: files.length,
      totalSize,
      datasetId: task.key,
      hasArchive: task.hasArchive,
      prefix: task.prefix,
    });
    console.log('[useSliceUpload] PreUpload response reqId:', reqId);

    const newTask: TaskItem = {
      ...task,
      reqId,
      isCancel: false,
      cancelFn: () => {
        task.controller.abort();
        cancelUpload?.(reqId);
        if (task.updateEvent) window.dispatchEvent(new Event(task.updateEvent));
      },
    };
    updateTaskList(newTask);
    if (showTaskCenter) {
      window.dispatchEvent(
        new CustomEvent("show:task-popover", { detail: { show: true } })
      );
    }
    // // 更新数据状态
    if (task.updateEvent) window.dispatchEvent(new Event(task.updateEvent));

    let loaded = 0;
    for (let i = 0; i < files.length; i++) {
      const { slices } = files[i];
      for (let j = 0; j < slices.length; j++) {
        await uploadSlice(newTask, {
          loaded,
          i,
          j,
          files,
          totalSize,
        });
        loaded += slices[j].size;
      }
    }
    removeTask(newTask);
  }

  const handleUpload = async ({ task, files }) => {
    const isErrorFile = await checkIsFilesExist(files);
    if (isErrorFile) {
      message.error(t('hooks.sliceUpload.fileModifiedOrDeleted'));
      removeTask({
        ...task,
        isCancel: false,
        ...taskListRef.current.find((item) => item.key === task.key),
      });
      return;
    }

    try {
      const totalSize = files.reduce((acc, file) => acc + file.size, 0);
      await uploadFile({ task, files, totalSize });
    } catch (err) {
      console.error(err);
      message.error(t('hooks.sliceUpload.uploadFailed'));
      removeTask({
        ...task,
        isCancel: true,
        ...taskListRef.current.find((item) => item.key === task.key),
      });
    }
  };

  return {
    taskList,
    createTask,
    removeTask,
    handleUpload,
  };
}
