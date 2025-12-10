import type {
  Dataset,
  DatasetFile,
} from "@/pages/DataManagement/dataset.model";
import { App } from "antd";
import { useState } from "react";
import {
  deleteDatasetFileUsingDelete,
  downloadFileByIdUsingGet,
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
  const [pagination, setPagination] = useState<{
    current: number;
    pageSize: number;
    total: number;
    prefix?: string;
  }>({ current: 1, pageSize: 10, total: 0, prefix: '' });

  // 文件预览相关状态
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewContent, setPreviewContent] = useState("");
  const [previewFileName, setPreviewFileName] = useState("");

  const fetchFiles = async (prefix: string = '', current, pageSize) => {
    const params: any = {
      page: current ? current : pagination.current,
      size: pageSize ? pageSize : pagination.pageSize,
    };

    if (prefix !== undefined) {
      params.prefix = prefix;
    } else if (pagination.prefix) {
      params.prefix = pagination.prefix;
    }

    const { data } = await queryDatasetFilesUsingGet(id!, params);
    setFileList(data.content || []);

    // Update pagination with current prefix
    setPagination(prev => ({
      ...prev,
      prefix: prefix !== undefined ? prefix : prev.prefix,
      total: data.totalElements || 0,
    }));
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
    // 实际导出逻辑
    await downloadFileByIdUsingGet(dataset.id, file.id, file.fileName);
    // 假设导出成功
    message.success({
      content: `已导出 1 个文件`,
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
    pagination,
    setPagination,
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
