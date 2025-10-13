import type {
  Dataset,
  DatasetFile,
} from "@/pages/DataManagement/dataset.model";
import { App } from "antd";
import { useState } from "react";
import {
  deleteDatasetFileUsingDelete,
  downloadFile,
  exportDatasetUsingPost,
  queryDatasetFilesUsingGet,
} from "../dataset.api";
import { useParams } from "react-router";

export function useFilesOperation(dataset: Dataset) {
  const { message } = App.useApp();
  const { id } = useParams(); // 获取动态路由参数

  // 文件相关状态
  const [fileList, setFileList] = useState<DatasetFile[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<number[]>([]);

  // 文件预览相关状态
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewContent, setPreviewContent] = useState("");
  const [previewFileName, setPreviewFileName] = useState("");

  const fetchFiles = async () => {
    const { data } = await queryDatasetFilesUsingGet(id!);
    setFileList(data.content || []);
  };

  const handleBatchDeleteFiles = () => {
    if (selectedFiles.length === 0) {
      message.warning({ content: "请先选择要删除的文件" });
      return;
    }
    // 执行批量删除逻辑
    selectedFiles.forEach(async (fileId) => {
      await fetch(`/api/datasets/${dataset.id}/files/${fileId}`, {
        method: "DELETE",
      });
    });
    fetchFiles(); // 刷新文件列表
    setSelectedFiles([]); // 清空选中状态
    message.success({
      content: `已删除 ${selectedFiles.length} 个文件`,
    });
  };

  const handleDownloadFile = async (file: DatasetFile) => {
    console.log("批量下载文件:", selectedFiles);
    // 实际导出逻辑
    await downloadFile(dataset.id, file.id, file.fileName);
    // 假设导出成功
    message.success({
      content: `已导出 ${selectedFiles.length} 个文件`,
    });
    setSelectedFiles([]); // 清空选中状态
  };

  const handleShowFile = (file: any) => async () => {
    // 请求文件内容并弹窗预览
    try {
      const res = await fetch(`/api/datasets/${dataset.id}/file/${file.id}`);
      const data = await res.text();
      setPreviewFileName(file.fileName);
      setPreviewContent(data);
      setPreviewVisible(true);
    } catch (err) {
      message.error({ content: "文件预览失败" });
    }
  };

  const handleDeleteFile = async (file) => {
    try {
      await deleteDatasetFileUsingDelete(dataset.id, file.id);
      fetchFiles(); // 刷新文件列表
      message.success({ content: `文件 ${file.fileName} 已删除` });
    } catch (error) {
      message.error({ content: `文件 ${file.fileName} 删除失败` });
    }
  };

  const handleBatchExport = () => {
    if (selectedFiles.length === 0) {
      message.warning({ content: "请先选择要导出的文件" });
      return;
    }
    // 执行批量导出逻辑
    console.log("批量导出文件:", selectedFiles);
    exportDatasetUsingPost(dataset.id, { fileIds: selectedFiles })
      .then(() => {
        message.success({
          content: `已导出 ${selectedFiles.length} 个文件`,
        });
        setSelectedFiles([]); // 清空选中状态
      })
      .catch(() => {
        message.error({
          content: "导出失败，请稍后再试",
        });
      });
  };

  return {
    fileList,
    selectedFiles,
    setSelectedFiles,
    previewVisible,
    setPreviewVisible,
    previewContent,
    previewFileName,
    setPreviewContent,
    setPreviewFileName,
    fetchFiles,
    setFileList,
    handleBatchDeleteFiles,
    handleDownloadFile,
    handleShowFile,
    handleDeleteFile,
    handleBatchExport,
  };
}
