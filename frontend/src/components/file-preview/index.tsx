import React from 'react';
import { ImagePreview } from './ImagePreview';
import { MarkdownPreview } from './MarkdownPreview';
import { DocxPreview } from './DocxPreview';
import { PdfPreview } from './PdfPreview';
import { TextPreview } from './TextPreview';

export interface FilePreviewProps {
  fileName?: string;
  content?: string;
  blobUrl?: string;
  blob?: Blob;
  loading?: boolean;
  error?: string;
}

export const FilePreview: React.FC<FilePreviewProps> = ({
  fileName = '',
  content,
  blobUrl,
  blob,
  loading = false,
  error
}) => {
  const ext = fileName?.toLowerCase().split('.').pop() || '';

  // 错误状态
  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-red-500">
        <div className="text-center">
          <p className="text-lg mb-2">⚠️ Preview Failed</p>
          <p className="text-sm text-gray-400">{error}</p>
        </div>
      </div>
    );
  }

  // 加载状态
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        <div className="flex flex-col items-center gap-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <span>Loading preview...</span>
        </div>
      </div>
    );
  }

  // 根据文件扩展名选择预览器
  // 图片文件
  if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'].includes(ext)) {
    return <ImagePreview fileName={fileName} blobUrl={blobUrl} />;
  }

  // Markdown 文件
  if (ext === 'md' || ext === 'markdown') {
    return <MarkdownPreview fileName={fileName} content={content} />;
  }

  // Word 文档
  if (ext === 'docx') {
    return <DocxPreview fileName={fileName} blob={blob} />;
  }

  // PDF 文档
  if (ext === 'pdf') {
    return <PdfPreview fileName={fileName} blob={blob} />;
  }

  // 其他文件（纯文本）
  return <TextPreview fileName={fileName} content={content} />;
};

export default FilePreview;
