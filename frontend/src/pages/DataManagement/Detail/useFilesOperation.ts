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
  createDatasetDirectoryUsingPost,
  downloadDirectoryUsingGet,
  deleteDirectoryUsingDelete,
  renameDatasetFileUsingPut,
  renameDirectoryUsingPut,
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
  const [previewUrl, setPreviewUrl] = useState<string | undefined>();
  const [previewFileDetail, setPreviewFileDetail] = useState<any | undefined>();
  const [previewLoading, setPreviewLoading] = useState(false);

  const fetchFiles = async (prefix?: string, current?, pageSize?) => {
    // 如果明确传了 prefix（包括空字符串），使用传入的值；否则使用当前 pagination.prefix
    const targetPrefix = prefix !== undefined ? prefix : (pagination.prefix || '');
    
    const params: any = {
      page: current !== undefined ? current : pagination.current,
      size: pageSize !== undefined ? pageSize : pagination.pageSize,
      isWithDirectory: true,
      prefix: targetPrefix,
    };

    const { data } = await queryDatasetFilesUsingGet(id!, params);
    setFileList(data.content || []);

    // Update pagination with current prefix
    setPagination(prev => ({
      ...prev,
      current: params.page,
      pageSize: params.size,
      prefix: targetPrefix,
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

  const isImageFile = (fileName?: string, fileType?: string) => {
    const lowerType = (fileType || "").toLowerCase();
    if (lowerType.includes("image")) return true;
    const name = (fileName || "").toLowerCase();
    return [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"].some((ext) =>
      name.endsWith(ext)
    );
  };

  const handlePreviewFile = async (file: any) => {
    if (!file || !file.id) return;
    const datasetId = dataset.id;
    setPreviewVisible(true);
    setPreviewLoading(true);
    setPreviewFileName(file.fileName || "");
    setPreviewContent("");
    setPreviewUrl(undefined);
    setPreviewFileDetail(undefined);
    try {
      // 获取文件元信息（来自 t_dm_dataset_files）
      const detailRes: any = await (await import("../dataset.api")).getDatasetFileByIdUsingGet(
        datasetId,
        file.id
      );
      const detail = detailRes?.data || detailRes;
      setPreviewFileDetail(detail);

      const downloadUrl = `/api/data-management/datasets/${datasetId}/files/${file.id}/download`;
      const image = isImageFile(detail?.fileName || file.fileName, detail?.fileType);

      if (image) {
        setPreviewUrl(downloadUrl);
      } else {
        const res = await fetch(downloadUrl);
        const text = await res.text();
        setPreviewContent(text);
      }
    } catch (error) {
      message.error({ content: "文件预览失败" });
    } finally {
      setPreviewLoading(false);
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

  const deleteDirectoryRecursively = async (directoryPath: string) => {
    // 递归删除指定目录下的所有文件和子目录，然后再删除目录本身
    const pageSize = 1000;

    while (true) {
      const { data } = await queryDatasetFilesUsingGet(id!, {
        page: 0,
        size: pageSize,
        isWithDirectory: true,
        prefix: directoryPath,
      });

      const content = data?.content || [];
      if (!content.length) {
        break;
      }

      const directories = content.filter(
        (item: any) => typeof item.id === "string" && item.id.startsWith("directory-")
      );
      const files = content.filter(
        (item: any) => !(typeof item.id === "string" && item.id.startsWith("directory-"))
      );

      // 先删除文件
      for (const file of files) {
        try {
          await deleteDatasetFileUsingDelete(dataset.id, file.id);
        } catch (e) {
          console.error("删除文件失败", file, e);
        }
      }

      // 再递归删除子目录
      for (const dir of directories) {
        const childPath = `${directoryPath}${dir.fileName}/`;
        await deleteDirectoryRecursively(childPath);
      }
    }

    // 最后尝试删除当前目录本身（若后端目录为空即可删除）
    try {
      await deleteDirectoryUsingDelete(dataset.id, directoryPath);
    } catch (e) {
      console.error("删除目录失败", directoryPath, e);
    }
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
      previewUrl,
      previewFileDetail,
      previewLoading,
    setPreviewContent,
    setPreviewFileName,
    fetchFiles,
    setFileList,
    handleBatchDeleteFiles,
    handleDownloadFile,
    handlePreviewFile,
    handleDeleteFile,
    handleBatchExport,
    handleCreateDirectory: async (directoryName: string) => {
      const currentPrefix = pagination.prefix || "";
      try {
        await createDatasetDirectoryUsingPost(dataset.id, {
          parentPrefix: currentPrefix,
          directoryName,
        });
        // 创建成功后刷新当前目录，重置到第一页
        await fetchFiles(currentPrefix, 1, pagination.pageSize);
        message.success({ content: `文件夹 ${directoryName} 创建成功` });
      } catch (error) {
        message.error({ content: `文件夹 ${directoryName} 创建失败` });
        throw error;
      }
    },
    handleDownloadDirectory: async (directoryPath: string, directoryName: string) => {
      try {
        await downloadDirectoryUsingGet(dataset.id, directoryPath);
        message.success({ content: `文件夹 ${directoryName} 下载成功` });
      } catch (error) {
        message.error({ content: `文件夹 ${directoryName} 下载失败` });
      }
    },
    handleDeleteDirectory: async (directoryPath: string, directoryName: string) => {
      try {
        await deleteDirectoryRecursively(directoryPath);
        // 删除成功后刷新当前目录
        const currentPrefix = pagination.prefix || "";
        await fetchFiles(currentPrefix, 1, pagination.pageSize);
        message.success({ content: `文件夹 ${directoryName} 已删除` });
      } catch (error) {
        console.error("删除文件夹失败", error);
        message.error({ content: `文件夹 ${directoryName} 删除失败` });
      }
    },
    handleRenameFile: async (file, newBaseName: string) => {
      try {
        const trimmed = (newBaseName || "").trim();
        if (!trimmed) {
          message.warning({ content: "请输入文件名称" });
          return;
        }
        await renameDatasetFileUsingPut(dataset.id, file.id, { newName: trimmed });
        const currentPrefix = pagination.prefix || "";
        await fetchFiles(currentPrefix, 1, pagination.pageSize);
        message.success({ content: `文件 ${file.fileName} 重命名成功` });
      } catch (error) {
        message.error({ content: `文件 ${file.fileName} 重命名失败` });
        throw error;
      }
    },
    handleRenameDirectory: async (directoryPath: string, oldName: string, newName: string) => {
      try {
        const trimmed = (newName || "").trim();
        if (!trimmed) {
          message.warning({ content: "请输入文件夹名称" });
          return;
        }
        await renameDirectoryUsingPut(dataset.id, { prefix: directoryPath, newName: trimmed });
        const currentPrefix = pagination.prefix || "";
        await fetchFiles(currentPrefix, 1, pagination.pageSize);
        message.success({ content: `文件夹 ${oldName} 重命名为 ${trimmed} 成功` });
      } catch (error) {
        message.error({ content: `文件夹 ${oldName} 重命名失败` });
        throw error;
      }
    },
  };
}
