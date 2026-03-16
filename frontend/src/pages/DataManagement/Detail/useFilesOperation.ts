import type {
  Dataset,
  DatasetFile,
} from "@/pages/DataManagement/dataset.model";
import { App } from "antd";
import { useState } from "react";
import JSZip from "jszip";
import {
  deleteDatasetFileUsingDelete,
  downloadFileByIdUsingGet,
  queryDatasetFilesUsingGet,
  createDatasetDirectoryUsingPost,
  downloadDirectoryUsingGet,
  deleteDirectoryUsingDelete,
  renameDatasetFileUsingPut,
  renameDirectoryUsingPut,
  getDatasetFileByIdUsingGet,
  batchDeleteFilesUsingDelete,
} from "../dataset.api";
import { useParams } from "react-router";

export function useFilesOperation(dataset: Dataset, onDatasetUpdate?: () => Promise<void>) {
  const { message } = App.useApp();
  const { id } = useParams(); // 获取动态路由参数

  // 文件相关状态
  const [fileList, setFileList] = useState<DatasetFile[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<React.Key[]>([]);
  // 保存跨页选中的文件的完整信息
  const [selectedFilesMap, setSelectedFilesMap] = useState<Map<React.Key, DatasetFile>>(new Map());
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
  const [previewBlob, setPreviewBlob] = useState<Blob | undefined>();
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

  // 处理文件选择变化（支持跨页选择）
  const handleSelectionChange = (selectedRowKeys: React.Key[], selectedRows: DatasetFile[]) => {
    setSelectedFiles(selectedRowKeys);

    // 更新文件映射
    const newMap = new Map(selectedFilesMap);

    // 添加当前页选中的文件
    selectedRows.forEach(file => {
      newMap.set(file.id, file);
    });

    // 移除被取消选择的文件（不在 selectedRowKeys 中的）
    const allKeysInMap = Array.from(newMap.keys());
    allKeysInMap.forEach(key => {
      if (!selectedRowKeys.includes(key)) {
        newMap.delete(key);
      }
    });

    setSelectedFilesMap(newMap);
  };

  // 清空选中状态
  const clearSelection = () => {
    setSelectedFiles([]);
    setSelectedFilesMap(new Map());
  };

  const handleBatchDeleteFiles = async () => {
    if (selectedFiles.length === 0) {
      message.warning({ content: "请先选择要删除的文件" });
      return;
    }

    const hide = message.loading({ content: `正在删除 ${selectedFiles.length} 个项目...`, duration: 0 });

    try {
      const prefix = pagination.prefix || "";
      let successCount = 0;
      let failCount = 0;

      // 分类：文件和目录
      const directories: any[] = [];
      const fileIds: string[] = [];

      selectedFiles.forEach((fileId) => {
        const file = selectedFilesMap.get(fileId);
        if (!file) return;

        if (typeof fileId === "string" && fileId.startsWith("directory-")) {
          directories.push(file);
        } else {
          fileIds.push(file.id);
        }
      });

      // 批量删除文件（一次性删除所有文件，后端使用悲观锁保证并发安全）
      if (fileIds.length > 0) {
        try {
          await batchDeleteFilesUsingDelete(dataset.id, { fileIds, prefix });
          successCount += fileIds.length;
        } catch (error: any) {
          // 部分文件可能删除失败，后端会返回详细信息
          console.error("批量删除文件失败", error);
          const failedCount = error?.response?.data?.failedCount || fileIds.length;
          failCount += failedCount;
          successCount += (fileIds.length - failedCount);
        }
      }

      // 删除目录（后端会递归删除所有内容）
      const deleteDirectory = async (dir: any) => {
        try {
          const dirPath = `${prefix}${dir.fileName}/`;
          await deleteDirectoryUsingDelete(dataset.id, dirPath);
          successCount++;
        } catch (error) {
          console.error(`删除目录失败: ${dir.fileName}`, error);
          failCount++;
        }
      };

      await Promise.all(directories.map(deleteDirectory));

      // 刷新文件列表和数据集信息
      await fetchFiles(prefix, 1, pagination.pageSize);
      setSelectedFiles([]);
      setSelectedFilesMap(new Map());

      if (onDatasetUpdate) {
        try {
          await onDatasetUpdate();
        } catch (error) {
          console.error("Failed to refresh dataset info after deletion:", error);
        }
      }

      hide();

      if (failCount === 0) {
        message.success({ content: `成功删除 ${successCount} 个项目` });
      } else {
        message.warning({ content: `删除完成：成功 ${successCount} 个，失败 ${failCount} 个` });
      }
    } catch (error) {
      hide();
      message.error({ content: "批量删除失败" });
    }
  };

  const handleDownloadFile = async (file: DatasetFile) => {
    // 实际导出逻辑
    const prefix = pagination.prefix || "";
    await downloadFileByIdUsingGet(dataset.id, prefix, file.id, file.fileName);
    // 假设导出成功
    message.success({
      content: `已导出 1 个文件`,
    });
    setSelectedFiles([]); // 清空选中状态
  };

  const getFileExtension = (fileName?: string) => {
    if (!fileName) return '';
    const parts = fileName.toLowerCase().split('.');
    return parts.length > 1 ? parts[parts.length - 1] : '';
  };

  const isImageFile = (fileName?: string, fileType?: string) => {
    const lowerType = (fileType || "").toLowerCase();
    if (lowerType.includes("image")) return true;
    const name = (fileName || "").toLowerCase();
    return [".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"].some((ext) =>
      name.endsWith(ext)
    );
  };

  const isMarkdownFile = (fileName?: string) => {
    const ext = getFileExtension(fileName);
    return ext === 'md' || ext === 'markdown';
  };

  const isDocxFile = (fileName?: string) => {
    return getFileExtension(fileName) === 'docx';
  };

  const isPdfFile = (fileName?: string) => {
    return getFileExtension(fileName) === 'pdf';
  };

  const handlePreviewFile = async (file: any) => {
    if (!file || !file.id) return;
    const datasetId = dataset.id;
    setPreviewVisible(true);
    setPreviewLoading(true);
    setPreviewFileName(file.fileName || "");
    setPreviewContent("");
    setPreviewUrl(undefined);
    setPreviewBlob(undefined);
    setPreviewFileDetail(undefined);

    try {
      // 获取文件元信息（来自 t_dm_dataset_files）
      const prefix = pagination.prefix || "";
      const detailRes: any = await getDatasetFileByIdUsingGet(datasetId, file.id, prefix);
      const detail = detailRes?.data || detailRes;
      setPreviewFileDetail(detail);

      const fileName = detail?.fileName || file.fileName;
      const { blob, blobUrl } = await downloadFileByIdUsingGet(datasetId, prefix, file.id, file.fileName, "preview");

      // 图片文件
      if (isImageFile(fileName, detail?.fileType)) {
        setPreviewUrl(blobUrl);
      }
      // Markdown 文件
      else if (isMarkdownFile(fileName)) {
        const text = await blob.text();
        setPreviewContent(text);
      }
      // Word 文档
      else if (isDocxFile(fileName)) {
        setPreviewBlob(blob);
      }
      // PDF 文档
      else if (isPdfFile(fileName)) {
        setPreviewBlob(blob);
      }
      // 其他文件（纯文本）
      else {
        const text = await blob.text();
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
      const prefix = pagination.prefix || "";
      await deleteDatasetFileUsingDelete(dataset.id, file.id, prefix);
      fetchFiles(); // 刷新文件列表
      message.success({ content: `文件 ${file.fileName} 已删除` });
    } catch (error) {
      message.error({ content: `文件 ${file.fileName} 删除失败` });
    }
  };

  const handleBatchExport = async () => {
    if (selectedFiles.length === 0) {
      message.warning({ content: "请先选择要导出的文件" });
      return;
    }

    try {
      // 检查选中的是否包含目录
      const hasDirectory = selectedFiles.some(
        (fileId) => typeof fileId === "string" && fileId.startsWith("directory-")
      );

      if (hasDirectory) {
        message.warning({ content: "暂不支持导出目录，请仅选择文件" });
        return;
      }

      // 获取选中的文件列表并计算总大小
      const files = Array.from(selectedFilesMap.values());
      const totalSize = files.reduce((sum, f) => sum + (f.fileSize || 0), 0);
      const MAX_SIZE = 500 * 1024 * 1024; // 500MB 限制

      if (totalSize > MAX_SIZE) {
        message.warning({
          content: `所选文件总大小超过 500MB，建议分批导出（当前：${(totalSize / 1024 / 1024).toFixed(2)} MB）`,
        });
        return;
      }

      const hide = message.loading({
        content: `正在准备下载 ${files.length} 个文件...`,
        duration: 0
      });

      const prefix = pagination.prefix || "";
      const zip = new JSZip();
      let successCount = 0;
      let failCount = 0;
      let downloadedSize = 0;

      // 并发下载文件（动态调整并发数）
      const CONCURRENT_LIMIT = files.length > 20 ? 6 : 4;

      for (let i = 0; i < files.length; i += CONCURRENT_LIMIT) {
        const batch = files.slice(i, i + CONCURRENT_LIMIT);

        // 更新进度提示
        hide();
        const progressMsg = message.loading({
          content: `正在下载 ${successCount + 1}/${files.length} 个文件 (${((downloadedSize / totalSize) * 100).toFixed(0)}%)...`,
          duration: 0
        });

        await Promise.all(
          batch.map(async (file) => {
            try {
              const { blob } = await downloadFileByIdUsingGet(
                dataset.id,
                prefix,
                file.id,
                file.fileName,
                "preview"
              );

              downloadedSize += blob.size;

              // 处理文件路径（移除前缀，保留相对路径）
              let relativePath = file.fileName;
              if (prefix && file.fileName.startsWith(prefix)) {
                relativePath = file.fileName.substring(prefix.length);
              }

              // 添加到 zip
              zip.file(relativePath, blob);
              successCount++;
            } catch (error) {
              console.error(`下载文件失败: ${file.fileName}`, error);
              failCount++;
            }
          })
        );

        progressMsg();
      }

      if (successCount === 0) {
        hide();
        message.error({ content: "所有文件下载失败" });
        return;
      }

      // 生成 zip 文件
      hide();
      const loading = message.loading({
        content: `正在压缩 ${successCount} 个文件（大小：${(totalSize / 1024 / 1024).toFixed(2)} MB）...`,
        duration: 0
      });

      // 使用分块生成，避免大文件阻塞
      try {
        const zipBlob = await zip.generateAsync({
          type: "blob",
          compression: "DEFLATE",
          compressionOptions: { level: 6 } // 平衡速度和压缩率
        });

        const downloadUrl = window.URL.createObjectURL(zipBlob);
        const link = document.createElement("a");
        link.href = downloadUrl;
        link.download = `${dataset.name || 'dataset'}_${Date.now()}.zip`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(downloadUrl);

        loading();

        if (failCount === 0) {
          message.success({
            content: `成功导出 ${successCount} 个文件（${(totalSize / 1024 / 1024).toFixed(2)} MB）`,
          });
        } else {
          message.warning({
            content: `导出完成：成功 ${successCount} 个，失败 ${failCount} 个`,
          });
        }

        setSelectedFiles([]);
        setSelectedFilesMap(new Map());
      } catch (error) {
        loading();
        message.error({ content: "生成压缩包失败，可能文件过大" });
      }
    } catch (error) {
      message.error({
        content: "导出失败，请稍后再试",
      });
    }
  };

  return {
    fileList,
    selectedFiles,
    setSelectedFiles,
    clearSelection,
    pagination,
    setPagination,
    previewVisible,
    setPreviewVisible,
    previewContent,
    previewFileName,
    previewUrl,
    previewBlob,
    previewFileDetail,
    previewLoading,
    setPreviewContent,
    setPreviewFileName,
    fetchFiles,
    setFileList,
    handleSelectionChange,
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
        // 直接调用后端API删除目录（后端会递归删除所有内容）
        await deleteDirectoryUsingDelete(dataset.id, directoryPath);
        // 删除成功后刷新当前目录
        const currentPrefix = pagination.prefix || "";
        await fetchFiles(currentPrefix, 1, pagination.pageSize);

        // 刷新数据集信息（更新 fileCount 和 totalSize）
        if (onDatasetUpdate) {
          try {
            await onDatasetUpdate();
          } catch (error) {
            console.error("Failed to refresh dataset info after directory deletion:", error);
          }
        }

        message.success({ content: `文件夹 ${directoryName} 已删除` });
      } catch (error) {
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
      } catch (error: any) {
        // 解析错误信息，提取更友好的提示
        const errorMsg = error?.response?.data?.message || error?.message || error?.toString();

        if (errorMsg?.includes("已存在") || errorMsg?.includes("already exists") || errorMsg?.includes("duplicate")) {
          message.error({ content: `文件名 "${trimmed}" 已存在，请使用其他名称` });
        } else {
          message.error({ content: `文件 ${file.fileName} 重命名失败：${errorMsg}` });
        }
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
      } catch (error: any) {
        // 解析错误信息，提取更友好的提示
        const errorMsg = error?.response?.data?.message || error?.message || error?.toString();

        if (errorMsg?.includes("已存在") || errorMsg?.includes("already exists") || errorMsg?.includes("duplicate")) {
          message.error({ content: `文件夹名 "${trimmed}" 已存在，请使用其他名称` });
        } else {
          message.error({ content: `文件夹 ${oldName} 重命名失败：${errorMsg}` });
        }
      }
    },
  };
}
