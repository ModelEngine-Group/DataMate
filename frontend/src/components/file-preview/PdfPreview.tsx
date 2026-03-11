import React, { useState, useEffect, useMemo } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { DownloadOutlined } from '@ant-design/icons';

// 配置 PDF.js worker - 使用 Vite 的 ?url 语法处理 npm 包
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
pdfjs.GlobalWorkerOptions.workerSrc = workerUrl;

export interface PdfPreviewProps {
  blob?: Blob;
  fileName?: string;
}

export const PdfPreview: React.FC<PdfPreviewProps> = ({
  blob,
  fileName = 'document.pdf'
}) => {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  // 使用 useMemo 创建稳定的 Blob 对象（带有正确的 MIME 类型）
  const pdfBlob = useMemo(() => {
    if (!blob) return null;
    return new Blob([blob], { type: 'application/pdf' });
  }, [blob]);

  // 当 blob 变化时重置状态
  useEffect(() => {
    if (blob) {
      setLoading(true);
      setError('');
      setPageNumber(1);
      setNumPages(0);
    }
  }, [blob]);

  const onDocumentLoadSuccess = ({ numPages: pages }: { numPages: number }) => {
    setNumPages(pages);
    setPageNumber(1);
    setLoading(false);
  };

  const onDocumentLoadError = (error: any) => {
    setError(`Failed to load PDF: ${error?.message || 'Unknown error'}`);
    setLoading(false);
  };

  const onSourceError = (error: any) => {
    setError(`PDF source error: ${error?.message || 'Unknown error'}`);
    setLoading(false);
  };

  const changePage = (offset: number) => {
    setPageNumber((prevPageNumber) => prevPageNumber + offset);
  };

  const previousPage = () => changePage(-1);
  const nextPage = () => changePage(1);

  const handleDownload = () => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (!blob) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        No PDF content available
      </div>
    );
  }

  // 显示错误状态
  if (error) {
    return (
      <div className="flex items-center justify-center h-full text-red-500">
        <div className="text-center">
          <p className="text-lg mb-2">⚠️ PDF Preview Failed</p>
          <p className="text-sm text-gray-400 mb-4">{error}</p>
          <button
            onClick={handleDownload}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Download File
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-100">
      {/* 工具栏 */}
      <div className="flex items-center justify-between px-4 py-2 bg-white border-b border-gray-200">
        <div className="text-sm text-gray-600">
          Page {pageNumber} of {numPages}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={previousPage}
            disabled={pageNumber <= 1}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <button
            onClick={nextPage}
            disabled={pageNumber >= numPages}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
          <button
            onClick={handleDownload}
            className="px-3 py-1.5 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 flex items-center gap-1"
          >
            <DownloadOutlined className="text-xs" />
            Download
          </button>
        </div>
      </div>

      {/* PDF 预览区域 */}
      <div className="flex-1 overflow-auto flex justify-center p-4 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100 z-10">
            <div className="flex flex-col items-center gap-3">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              <span className="text-sm text-gray-600">Loading PDF...</span>
            </div>
          </div>
        )}
        <Document
          key={blob?.size || 'pdf'}
          file={pdfBlob}
          onLoadSuccess={onDocumentLoadSuccess}
          onLoadError={onDocumentLoadError}
          onSourceError={onSourceError}
          className="pdf-document"
        >
          <Page
            pageNumber={pageNumber}
            renderTextLayer={false}
            renderAnnotationLayer={false}
            className="pdf-page"
          />
        </Document>
      </div>
    </div>
  );
};
