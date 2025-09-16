import { Upload, type UploadFile } from "antd";
import { InboxOutlined } from "@ant-design/icons";
import { useState } from "react";
import type { Dataset } from "@/types/dataset";
import { uploadDatasetFileUsingPost } from "../dataset-apis";

const { Dragger } = Upload;

export const useImportFile = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);

  const resetFiles = () => {
    setFileList([]);
  };

  const handleUpload = async (message: any, dataset: Dataset) => {
    const formData = new FormData();
    fileList.forEach((file) => {
      console.log(file);
      formData.append("files[]", file);
    });
    await uploadDatasetFileUsingPost(dataset?.id, formData);
    resetFiles();
    message.success("文件上传成功");
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

  return { fileList, resetFiles, handleUpload, importFileRender };
};
