import {
  cancelUploadUsingPut,
  preUploadUsingPost,
  uploadFileChunkUsingPost,
} from "@/pages/DataManagement/dataset.api";
import { Button, Empty, Progress } from "antd";
import { DeleteOutlined } from "@ant-design/icons";
import { useEffect } from "react";
import { useFileSliceUpload } from "@/hooks/useSliceUpload";

export default function TaskUpload() {
  const { createTask, taskList, removeTask, handleUpload } = useFileSliceUpload(
    {
      preUpload: preUploadUsingPost,
      uploadChunk: uploadFileChunkUsingPost,
      cancelUpload: cancelUploadUsingPut,
    }
  );

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
                  })
                }
                icon={<DeleteOutlined />}
              ></Button>
            </div>

            <Progress size="small" percent={task.percent} />
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
