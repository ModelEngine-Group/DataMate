import { mockFiles } from "@/mock/dataset";
import type { DatasetFile } from "@/types/dataset";
import { useState } from "react";

export function useFilesOperation(messageApi: any, dataset: Dataset) {
  // 文件相关状态
  const [fileList, setFileList] = useState(mockFiles);
  const [selectedFiles, setSelectedFiles] = useState<number[]>([]);

  // 文件预览相关状态
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewContent, setPreviewContent] = useState("");
  const [previewFileName, setPreviewFileName] = useState("");

  const fetchFiles = async () => {
    const res = await fetch(`/api/datasets/${dataset.id}/files`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        datasetId: id,
        page: 1,
        size: 20,
        fileType: "all",
        status: "active",
      }),
    });
    setFileList(await res.json());
  };

  const handleBatchDeleteFiles = () => {
    if (selectedFiles.length === 0) {
      messageApi.open({ type: "warning", content: "请先选择要删除的文件" });
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
    messageApi.open({
      type: "success",
      content: `已删除 ${selectedFiles.length} 个文件`,
    });
  };

  const handleDownloadFile = async (file: DatasetFile) => {
    console.log("批量下载文件:", selectedFiles);
    // 实际导出逻辑
    await fetch(`/api/datasets/${dataset.id}/files/${file.id}download`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ fileIds: selectedFiles }),
    });
    // 假设导出成功
    messageApi.open({
      type: "success",
      content: `已导出 ${selectedFiles.length} 个文件`,
    });
    setSelectedFiles([]); // 清空选中状态
  };

  const handleShowFile = (file: any) => async () => {
    // 请求文件内容并弹窗预览
    try {
      const res = await fetch(`/api/datasets/${dataset.id}/file/${file.id}`);
      const data = await res.text();
      setPreviewFileName(file.name);
      setPreviewContent(data);
      setPreviewVisible(true);
    } catch (err) {
      messageApi.open({ type: "error", content: "文件预览失败" });
    }
  };

  const handleDeleteFile = async (file) => {
    try {
      const res = await fetch(`/api/datasets/${dataset.id}/files/${file.id}`, {
        method: "DELETE",
      });
      await res.json();
      fetchFiles(); // 刷新文件列表
      messageApi.open({
        type: "success",
        content: `文件 ${file.name} 已删除`,
      });
    } catch (error) {
      messageApi.open({
        type: "error",
        content: `文件 ${file.name} 删除失败`,
      });
    }
  };

  const handleBatchExport = () => {
    if (selectedFiles.length === 0) {
      messageApi.open({ type: "warning", content: "请先选择要导出的文件" });
      return;
    }
    // 执行批量导出逻辑
    console.log("批量导出文件:", selectedFiles);
    fetch(`/api/datasets/${dataset.id}/files/export`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ fileIds: selectedFiles }),
    })
      .then((res) => res.json())
      .then(() => {
        messageApi.open({
          type: "success",
          content: `已导出 ${selectedFiles.length} 个文件`,
        });
        setSelectedFiles([]); // 清空选中状态
      })
      .catch(() => {
        messageApi.open({
          type: "error",
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
