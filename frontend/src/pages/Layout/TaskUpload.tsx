import {
  cancelUploadUsingPut,
  preUploadUsingPost,
  uploadFileChunkUsingPost,
} from "@/pages/DataManagement/dataset.api";
import { TaskItem } from "@/pages/DataManagement/dataset.model";
import { calculateSHA256, checkIsFilesExist } from "@/utils/file.util";
import { App, Button, Empty, Progress } from "antd";
import { DeleteOutlined } from "@ant-design/icons";
import { useState, useRef, useEffect } from "react";

export default function TaskUpload() {
  const { message } = App.useApp();
  const [taskList, setTaskList] = useState<TaskItem[]>([]);
  const taskListRef = useRef<TaskItem[]>([]); // 用于固定任务顺序

  const createTask = (detail: any = {}) => {
    const { dataset } = detail;
    const title = `上传数据集: ${dataset.name} `;
    const controller = new AbortController();
    const task: TaskItem = {
      key: dataset.id,
      title,
      percent: 0,
      reqId: -1,
      controller,
      updateEvent: detail.updateEvent || "update:dataset",
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
    window.dispatchEvent(new Event(task.updateEvent || "update:dataset"));
    window.dispatchEvent(
      new CustomEvent("show:task-popover", { detail: { show: false } })
    );
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
    const { reqId, key, signal } = task;
    const { loaded, i, j, files, totalSize } = fileInfo;
    const formData = await buildFormData({
      file: files[i],
      i,
      j,
      reqId,
    });

    let newTask = { ...task };
    await uploadFileChunkUsingPost(key, formData, {
      onUploadProgress: (e) => {
        const loadedSize = loaded + e.loaded;
        const curPercent = Math.round(loadedSize / totalSize) * 100;
        newTask = {
          ...newTask,
          ...taskListRef.current.find((item) => item.key === key),
          percent: curPercent >= 100 ? 99.99 : curPercent,
        };
        updateTaskList(newTask);
      },
      signal,
    });
  }

  async function uploadFile({ task, files, totalSize }) {
    const { data: reqId } = await preUploadUsingPost(task.key, {
      totalFileNum: files.length,
      totalSize,
      datasetId: task.key,
    });

    const newTask: TaskItem = {
      ...task,
      reqId,
      isCancel: false,
      cancelFn: () => {
        task.controller.abort();
        cancelUploadUsingPut(reqId);
        window.dispatchEvent(new Event(task.updateEvent || "update:dataset"));
      },
    };
    updateTaskList(newTask);
    window.dispatchEvent(
      new CustomEvent("show:task-popover", { detail: { show: true } })
    );
    // 更新数据状态
    window.dispatchEvent(new Event("update:dataset-status"));

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
      message.error("文件被修改或删除，请重新选择文件上传");
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
      message.error("文件上传失败，请稍后重试");
      removeTask({
        ...task,
        isCancel: true,
        ...taskListRef.current.find((item) => item.key === task.key),
      });
    }
  };

  useEffect(() => {
    const uploadHandler = (e: any) => {
      const { files } = e.detail;
      const task = createTask(e.detail);
      handleUpload({ task, files });
    };
    window.addEventListener("upload:dataset", uploadHandler);
    return () => {
      window.removeEventListener("upload:dataset", uploadHandler);
    };
  }, []);

  return (
    <div
      className="w-90 max-w-90 max-h-96 overflow-y-auto p-2"
      id="header-task-popover"
    >
      {taskList.length > 0 &&
        taskList.map((task) => (
          <div key={task.key} className="border-b border-gray-200 pb-2">
            <div className="flex items-center justify-between">
              <div>{task.title}</div>
              <Button
                type="text"
                danger
                disabled={!task?.cancelFn}
                onClick={() =>
                  removeTask({
                    ...task,
                    isCancel: true,
                    ...taskListRef.current.find(
                      (item) => item.key === task.key
                    ),
                  })
                }
                icon={<DeleteOutlined />}
              ></Button>
            </div>

            <Progress size="small" percent={Number(task.percent.toFixed(2))} />
          </div>
        ))}
      {taskList.length === 0 && (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="暂无上传任务"
        />
      )}
    </div>
  );
}
