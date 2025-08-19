import { Upload, type UploadFile } from "antd";
import { InboxOutlined } from "@ant-design/icons";
import { useState } from "react";
import type { Dataset } from "@/types/dataset";

const { Dragger } = Upload;

export const useImportFile = (message, dataset: Dataset) => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  const handleUpload = () => {
    const formData = new FormData();
    fileList.forEach((file) => {
      console.log(file);
      formData.append("files[]", file);
    });

    console.log("Uploading files for dataset ID:", formData, dataset.id);
    fetch(`/api/dataset/v2/file/upload/${dataset.id}`, {
      method: "POST",
      body: formData,
    })
      .then((res) => res.json())
      .then(() => {
        setFileList([]);
        message.success("数据集创建成功");
      })
      .catch(() => {
        message.error("上传失败.");
      })
      .finally(() => {});
  };

  const importFileRender = () => (
    <Dragger
      className="w-full"
      fileList={fileList}
      onRemove={(file) => {
        const index = fileList.indexOf(file);
        const newFileList = fileList.slice();
        newFileList.splice(index, 1);
        setFileList(newFileList);
      }}
      beforeUpload={(file) => {
        setFileList([...fileList, file]);

        return false;
      }}
    >
      <p className="ant-upload-drag-icon">
        <InboxOutlined />
      </p>
      <p className="ant-upload-text">本地文件上传</p>
      <p className="ant-upload-hint">
        拖拽文件到此处或点击选择文件,支持 JPG, PNG, TXT, JSON 等格式
      </p>
    </Dragger>
  );

  return { fileList, handleUpload, importFileRender };
};
